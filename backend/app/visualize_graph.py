"""Generate a Mermaid visualization of the PeopleGuide LangGraph workflow."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.agents.graph import build_graph
from app.config import REPOSITORY_ROOT, get_settings
from app.services.case_service import CaseDataService
from app.services.policy_service import PolicySearchService


DEFAULT_OUTPUT = REPOSITORY_ROOT / "docs" / "agent-graph.md"


def render_graph(output_path: Path) -> None:
    """Build the application graph and write it as a Mermaid Markdown diagram."""
    settings = get_settings()
    policy_service = PolicySearchService(settings)
    case_service = CaseDataService(
        settings.employee_data_path,
        settings.reference_data_path,
    )

    try:
        graph = build_graph(
            settings=settings,
            policy_service=policy_service,
            case_service=case_service,
        )
        mermaid = graph.get_graph().draw_mermaid()
    finally:
        policy_service.close()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "# PeopleGuide agent graph\n\n"
        "Generated from the application LangGraph definition.\n\n"
        f"```mermaid\n{mermaid}\n```\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Write the PeopleGuide LangGraph workflow to a Mermaid Markdown file."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Destination Markdown file (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    output_path = args.output.expanduser().resolve()
    render_graph(output_path)
    print(f"Agent graph written to {output_path}")


if __name__ == "__main__":
    main()
