from __future__ import annotations

import hashlib
import re
from pathlib import Path

import frontmatter

from app.models.rag import PolicyChunk


SECTION_PATTERN = re.compile(r"^##\s+(?P<number>\d+(?:\.\d+)*)\.\s+(?P<title>.+?)\s*$", re.MULTILINE)


def _split_long_section(text: str, max_chars: int, overlap_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text.strip()]

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_length = 0

    for paragraph in paragraphs:
        paragraph_length = len(paragraph) + 2
        if current and current_length + paragraph_length > max_chars:
            chunk = "\n\n".join(current)
            chunks.append(chunk)
            overlap = chunk[-overlap_chars:] if overlap_chars else ""
            current = [overlap, paragraph] if overlap else [paragraph]
            current_length = sum(len(item) + 2 for item in current)
        else:
            current.append(paragraph)
            current_length += paragraph_length

    if current:
        chunks.append("\n\n".join(current))
    return chunks


def parse_policy_file(
    path: Path,
    *,
    repository_root: Path,
    max_chars: int = 3_200,
    overlap_chars: int = 240,
) -> list[PolicyChunk]:
    post = frontmatter.load(path)
    metadata = post.metadata
    body = post.content

    required = {
        "title",
        "policy_id",
        "version",
        "effective_date",
        "document_status",
        "locations",
        "applies_to",
    }
    missing = required.difference(metadata)
    if missing:
        raise ValueError(f"{path} is missing metadata: {', '.join(sorted(missing))}")

    matches = list(SECTION_PATTERN.finditer(body))
    if not matches:
        raise ValueError(f"{path} contains no numbered level-two sections")

    chunks: list[PolicyChunk] = []
    for section_index, match in enumerate(matches):
        start = match.end()
        end = matches[section_index + 1].start() if section_index + 1 < len(matches) else len(body)
        section_text = body[start:end].strip()
        section_number = match.group("number")
        section_title = match.group("title").strip()
        breadcrumb = f"{metadata['title']} ({metadata['policy_id']})\nSection {section_number}: {section_title}"

        for chunk_index, part in enumerate(
            _split_long_section(section_text, max_chars=max_chars, overlap_chars=overlap_chars)
        ):
            text = f"{breadcrumb}\n\n{part}".strip()
            content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            chunk_id = (
                f"{metadata['policy_id']}:v{metadata['version']}:"
                f"section-{section_number}:{chunk_index}"
            )
            chunks.append(
                PolicyChunk(
                    chunk_id=chunk_id,
                    text=text,
                    policy_id=str(metadata["policy_id"]),
                    policy_title=str(metadata["title"]),
                    version=str(metadata["version"]),
                    document_status=str(metadata["document_status"]),
                    effective_date=metadata["effective_date"],
                    locations=list(metadata["locations"]),
                    applies_to=list(metadata["applies_to"]),
                    section_number=section_number,
                    section_title=section_title,
                    source_path=str(path.relative_to(repository_root)),
                    chunk_index=chunk_index,
                    content_hash=content_hash,
                )
            )

    return chunks


def load_policy_chunks(policy_directory: Path, repository_root: Path) -> list[PolicyChunk]:
    paths = sorted(policy_directory.glob("*.md"))
    if not paths:
        raise FileNotFoundError(f"No Markdown policies found in {policy_directory}")

    chunks: list[PolicyChunk] = []
    for path in paths:
        chunks.extend(parse_policy_file(path, repository_root=repository_root))
    return chunks

