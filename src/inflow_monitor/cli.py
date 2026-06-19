"""Command-line interface for the AI Inflow Transaction Monitor."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from inflow_monitor.memory import FeedbackLabel
from inflow_monitor.models.decision import DecisionOutcome
from inflow_monitor.pipeline.monitoring_pipeline import (
    MonitoringPipeline,
    load_cases_from_json,
)
from inflow_monitor.utils.config import EngineConfig, load_config

app = typer.Typer(
    add_completion=False,
    help="Automated inbound-transaction monitoring and flagging engine.",
)
console = Console()

_OUTCOME_STYLE = {
    DecisionOutcome.CLEAR.value: "green",
    DecisionOutcome.REVIEW.value: "yellow",
    DecisionOutcome.FLAG.value: "red",
}


def _load_config_with_memory(
    config_file: Path | None,
    memory_path: Path | None,
) -> EngineConfig:
    """Load configuration, enabling collective memory when a path is supplied."""
    config = load_config(config_file)
    if memory_path is not None:
        config.memory.enabled = True
        config.memory.path = str(memory_path)
    return config


@app.command()
def monitor(
    input_file: Path = typer.Argument(..., help="Path to a JSON file of case inputs."),
    config_file: Path = typer.Option(None, "--config", "-c", help="Path to config.yaml."),
    output_dir: Path = typer.Option(None, "--output", "-o", help="Directory for reports."),
    memory_path: Path = typer.Option(
        None,
        "--memory",
        "-m",
        help="Enable collective memory at this SQLite path (persist and recall history).",
    ),
) -> None:
    """Monitor one or more inbound transactions from a JSON input file."""
    load_dotenv()
    config = _load_config_with_memory(config_file, memory_path)
    pipeline = MonitoringPipeline(config=config)

    cases = load_cases_from_json(input_file)
    results = pipeline.run_batch(cases, output_dir=output_dir)

    table = Table(title="Inflow Monitoring Results")
    table.add_column("Case ID", style="cyan", no_wrap=True)
    table.add_column("Event", style="white")
    table.add_column("Amount", justify="right")
    table.add_column("Risk", justify="right")
    table.add_column("Decision", justify="center")
    table.add_column("Confidence", justify="right")

    for result in results:
        decision = result.decision
        style = _OUTCOME_STYLE.get(decision.outcome.value, "white")
        event = result.report["event"]
        table.add_row(
            decision.case_id,
            event["event_id"],
            f"{event['amount']:,.2f} {event['currency']}",
            f"{decision.risk_score:.1f}",
            f"[{style}]{decision.outcome.value.upper()}[/{style}]",
            f"{decision.confidence:.0%}",
        )

    console.print(table)
    if output_dir:
        console.print(f"Reports written to [bold]{output_dir}[/bold].")


@app.command()
def explain(
    input_file: Path = typer.Argument(..., help="Path to a JSON file with a single case."),
    config_file: Path = typer.Option(None, "--config", "-c", help="Path to config.yaml."),
) -> None:
    """Monitor the first case in a file and print its full reasoning report."""
    load_dotenv()
    config = load_config(config_file)
    pipeline = MonitoringPipeline(config=config)

    cases = load_cases_from_json(input_file)
    if not cases:
        console.print("[red]No cases found in input file.[/red]")
        raise typer.Exit(code=1)

    result = pipeline.run_one(cases[0])
    console.print_json(json.dumps(result.report))


@app.command()
def feedback(
    case_id: str = typer.Argument(..., help="Case identifier to label."),
    label: str = typer.Argument(
        ...,
        help="Confirmed outcome: confirmed_suspicious, cleared, or unreviewed.",
    ),
    note: str = typer.Option(None, "--note", "-n", help="Optional analyst note."),
    config_file: Path = typer.Option(None, "--config", "-c", help="Path to config.yaml."),
    memory_path: Path = typer.Option(
        None, "--memory", "-m", help="SQLite memory path (overrides config)."
    ),
) -> None:
    """Record an analyst-confirmed outcome for a stored case."""
    load_dotenv()
    try:
        feedback_label = FeedbackLabel(label.strip().lower())
    except ValueError:
        valid = ", ".join(item.value for item in FeedbackLabel)
        console.print(f"[red]Invalid label '{label}'. Choose one of: {valid}.[/red]")
        raise typer.Exit(code=1)

    config = _load_config_with_memory(config_file, memory_path)
    if not config.memory.enabled:
        console.print(
            "[red]Collective memory is disabled. Pass --memory PATH or enable it in "
            "config.yaml.[/red]"
        )
        raise typer.Exit(code=1)

    pipeline = MonitoringPipeline(config=config)
    updated = pipeline.record_feedback(case_id, feedback_label, note)
    if updated:
        console.print(
            f"Recorded [bold]{feedback_label.value}[/bold] feedback for case "
            f"[cyan]{case_id}[/cyan]."
        )
    else:
        console.print(f"[yellow]No stored case found for '{case_id}'.[/yellow]")
        raise typer.Exit(code=1)


@app.command()
def calibrate(
    config_file: Path = typer.Option(None, "--config", "-c", help="Path to config.yaml."),
    memory_path: Path = typer.Option(
        None, "--memory", "-m", help="SQLite memory path (overrides config)."
    ),
) -> None:
    """Recommend decision thresholds from labeled feedback (advisory only)."""
    load_dotenv()
    config = _load_config_with_memory(config_file, memory_path)
    if not config.memory.enabled:
        console.print(
            "[red]Collective memory is disabled. Pass --memory PATH or enable it in "
            "config.yaml.[/red]"
        )
        raise typer.Exit(code=1)

    pipeline = MonitoringPipeline(config=config)
    report = pipeline.calibrate()

    table = Table(title="Threshold Calibration (advisory)")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    table.add_row("Labeled cases", str(report.labeled_cases))
    table.add_row("Confirmed suspicious", str(report.confirmed_suspicious_cases))
    table.add_row("Cleared", str(report.cleared_cases))
    table.add_row("Current flag threshold", f"{report.current_flag_threshold:.1f}")
    table.add_row("Current review threshold", f"{report.current_review_threshold:.1f}")
    table.add_row(
        "Suggested flag threshold",
        "-" if report.suggested_flag_threshold is None
        else f"{report.suggested_flag_threshold:.1f}",
    )
    table.add_row(
        "Suggested review threshold",
        "-" if report.suggested_review_threshold is None
        else f"{report.suggested_review_threshold:.1f}",
    )
    console.print(table)
    for line in report.rationale:
        console.print(f"- {line}")


if __name__ == "__main__":
    app()
