from app.agents.graph import normalise_answer_provenance
from app.agents.models import AnswerBlock, AnswerSegment, FinalResponse


def test_answer_sources_are_limited_to_tools_that_actually_ran() -> None:
    response = FinalResponse(
        answer_markdown="The policy allows 20 days. Your estimate is 2.29 days.",
        answer_blocks=[
            AnswerBlock(
                segments=[
                    AnswerSegment(
                        text="The policy allows 20 days.",
                        source_refs=["search_policies", "invented_tool"],
                    ),
                    AnswerSegment(
                        text="Your estimate is 2.29 days.",
                        source_refs=["calculate_leave_balance"],
                    ),
                ]
            )
        ],
    )

    normalised = normalise_answer_provenance(
        response,
        ["search_policies", "calculate_leave_balance", "supervisor_final"],
        fallback_source="supervisor_final",
    )

    assert normalised.answer_blocks[0].segments[0].source_refs == ["search_policies"]
    assert normalised.answer_blocks[0].segments[1].source_refs == [
        "calculate_leave_balance"
    ]


def test_missing_provenance_falls_back_to_supervisor() -> None:
    response = FinalResponse(answer_markdown="Hello!", answer_blocks=[])

    normalised = normalise_answer_provenance(
        response,
        ["supervisor_final"],
        fallback_source="supervisor_final",
    )

    segment = normalised.answer_blocks[0].segments[0]
    assert segment.text == "Hello!"
    assert segment.source_refs == ["supervisor_final"]

