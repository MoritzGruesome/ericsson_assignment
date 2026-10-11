from pathlib import Path

from app.config import REPOSITORY_ROOT
from app.rag.parser import load_policy_chunks, parse_policy_file


def test_loads_all_policy_documents_into_section_chunks() -> None:
    policy_directory = REPOSITORY_ROOT / "data" / "policies"
    chunks = load_policy_chunks(policy_directory, REPOSITORY_ROOT)

    policy_ids = {chunk.policy_id for chunk in chunks}
    assert len(policy_ids) == 12
    assert "HR-LEAVE-001" in policy_ids
    assert "HR-LOC-HK-001" in policy_ids
    assert all(chunk.document_status == "active" for chunk in chunks)
    assert all(chunk.text.startswith(chunk.policy_title) for chunk in chunks)


def test_annual_leave_section_has_stable_citation_metadata() -> None:
    path = REPOSITORY_ROOT / "data" / "policies" / "annual-leave.md"
    chunks = parse_policy_file(path, repository_root=REPOSITORY_ROOT)
    probation = next(chunk for chunk in chunks if chunk.section_number == "5")

    assert probation.chunk_id == "HR-LEAVE-001:v1.0:section-5:0"
    assert probation.section_title == "Taking leave during probation"
    assert "three days" in probation.text
    assert probation.source_path == "data/policies/annual-leave.md"


def test_every_chunk_id_is_unique() -> None:
    chunks = load_policy_chunks(REPOSITORY_ROOT / "data" / "policies", REPOSITORY_ROOT)
    ids = [chunk.chunk_id for chunk in chunks]
    assert len(ids) == len(set(ids))

