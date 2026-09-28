"""Package entry point — delegates to the CLI app."""

from .cli import app


def main() -> None:
    app()


if __name__ == "__main__":
    main()
