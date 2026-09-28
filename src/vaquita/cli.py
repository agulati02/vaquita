"""Vaquita CLI — entry point for the `vaquita` command."""

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
    model_provider: str = typer.Option("openai", "--model-provider", help="LLM provider (openai, anthropic, etc.)."),
    model_name: str = typer.Option("gpt-oss-120b", "--model-name", help="Name of the LLM to use.")
) -> None:
    """Generate release notes between two refs."""
    config = Config(
        from_ref=from_ref,
        to_ref=to_ref,
        repo_path=repo,
        output_format=output_format,
        output_file=output_file,
        model_provider=model_provider,
        model_name=model_name
    )

    console.print(
        f"[bold]vaquita[/bold] · generating notes from "
        f"[cyan]{config.from_ref}[/cyan] → [cyan]{config.to_ref}[/cyan]"
    )
    
    console.print(generate_notes(config))

