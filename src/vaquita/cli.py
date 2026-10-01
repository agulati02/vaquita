"""Vaquita CLI — entry point for the `vaquita` command."""

import json
from pathlib import Path

import typer
from rich.console import Console

from .config import Config, OutputFormat
from .generator import generate_notes


app = typer.Typer(
    name="vaquita",
    help="AI-powered release note generation for high-velocity repositories.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def generate(
    from_ref: str = typer.Option(..., "--from", help="Base ref (tag, branch, or SHA)."),
    to_ref: str = typer.Option("HEAD", "--to", help="Target ref (tag, branch, or SHA)."),
    repo: Path = typer.Option(Path.cwd(), "--repo", help="Path to the git repository."),
    output_format: OutputFormat = typer.Option(
        OutputFormat.MARKDOWN, "--format", help="Output format."
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="Write output to this file instead of stdout."
    ),
    model_provider: str = typer.Option("openai", "--model-provider", help="LLM provider (openai, anthropic, mistral)."),
    model_name: str = typer.Option("gpt-4o-mini", "--model-name", help="Name of the LLM to use."),
    trace_file: Path | None = typer.Option(
        None, "--trace", help="Write agent trace JSON to this file."
    ),
) -> None:
    """Generate release notes between two refs."""
    config = Config(
        from_ref=from_ref,
        to_ref=to_ref,
        repo_path=repo,
        output_format=output_format,
        output_file=output_file,
        provider=model_provider,
        model=model_name,
    )

    console.print(
        f"[bold]vaquita[/bold] · generating notes from "
        f"[cyan]{config.from_ref}[/cyan] → [cyan]{config.to_ref}[/cyan]"
    )

    notes, trace = generate_notes(config)

    console.print(notes)

    if trace_file:
        trace_file.write_text(
            json.dumps(
                {
                    "total_tool_calls": trace.total_tool_calls,
                    "final_output": trace.final_output,
                    "turns": [
                        {
                            "turn": t.turn,
                            "type": t.type,
                            "tool_name": t.tool_name,
                            "tool_args": t.tool_args,
                            "tool_result_preview": t.tool_result_preview,
                            "model_output_preview": t.model_output_preview,
                        }
                        for t in trace.turns
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        console.print(f"[dim]trace written to {trace_file}[/dim]")
