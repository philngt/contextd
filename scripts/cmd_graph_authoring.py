"""Authoring validator and pending OES import/export (opt-in)."""

if __package__:
    from .lib.graph_authoring import main
    from .lib.runtime_resources import resource_path
else:
    from lib.graph_authoring import main
    from lib.runtime_resources import resource_path

if __name__ == "__main__":
    raise SystemExit(main(resources=resource_path("templates/graph-authoring")))
