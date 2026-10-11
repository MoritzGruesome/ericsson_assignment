from langchain_core.messages import AIMessage, HumanMessage

from app.agents.graph import (
    MAX_CONTEXT_CHARACTERS,
    MAX_CONTEXT_MESSAGES,
    _conversation_transcript,
)


def test_transcript_preserves_follow_up_context_in_order() -> None:
    transcript = _conversation_transcript(
        {
            "messages": [
                HumanMessage(
                    content="I joined on 15 June and took four days off. What is my balance?"
                ),
                AIMessage(content="What year did you join?"),
                HumanMessage(content="It was 2025."),
            ]
        }
    )

    assert transcript.splitlines() == [
        "User: I joined on 15 June and took four days off. What is my balance?",
        "Assistant: What year did you join?",
        "User: It was 2025.",
    ]


def test_transcript_uses_a_bounded_recent_window() -> None:
    messages = [HumanMessage(content=f"message {index}") for index in range(20)]

    transcript = _conversation_transcript({"messages": messages})

    assert "message 7" not in transcript
    assert "message 8" in transcript
    assert "message 19" in transcript
    assert transcript.count("User:") == MAX_CONTEXT_MESSAGES
    assert len(transcript) <= MAX_CONTEXT_CHARACTERS


def test_transcript_enforces_character_limit() -> None:
    transcript = _conversation_transcript(
        {"messages": [HumanMessage(content="x" * (MAX_CONTEXT_CHARACTERS + 100))]}
    )

    assert transcript.startswith("[Earlier messages omitted]")
    assert len(transcript) == MAX_CONTEXT_CHARACTERS

