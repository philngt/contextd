"""PyInstaller entry point; build from a non-editable installed distribution."""

from contextd.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
