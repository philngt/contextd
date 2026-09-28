"""Source-checkout-only, read-only graph proposal validator (opt-in)."""
from pathlib import Path

from lib.graph_authoring import main

if __name__ == "__main__":
    raise SystemExit(main(resources=Path(__file__).resolve().parent.parent / "templates/graph-authoring"))
