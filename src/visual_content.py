import re
from dataclasses import dataclass
from typing import Iterable


PDF_PAGE_MARKER_PATTERN = re.compile(r"(?m)^\[PDF_PAGE:(\d+)\]\s*$")
PICTURE_DESCRIPTION_PATTERN = re.compile(
    r"(?m)^\[PICTURE_DESCRIPTION:([A-Za-z0-9][A-Za-z0-9._-]*)\|AI_GENERATED\]\s*$"
)
REGION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True)
class PictureDescription:
    region_id: str
    description: str
    page_number: int | None = None
    source_kind: str = "picture"
    confidence: float | None = None

    def __post_init__(self) -> None:
        if not REGION_ID_PATTERN.fullmatch(self.region_id):
            raise ValueError("region_id must contain only letters, numbers, '.', '_', or '-'")
        if not self.description.strip():
            raise ValueError("description must not be empty")
        if self.page_number is not None and self.page_number < 1:
            raise ValueError("page_number must be at least 1")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

    def to_marked_text(self) -> str:
        description = " ".join(self.description.split())
        return (
            f"[PICTURE_DESCRIPTION:{self.region_id}|AI_GENERATED]\n"
            f"{description}"
        )


def attach_picture_descriptions(
    text: str,
    descriptions: Iterable[PictureDescription],
) -> str:
    """Attach generated descriptions to their physical PDF pages as labeled text."""
    descriptions_by_page: dict[int | None, list[PictureDescription]] = {}
    for description in descriptions:
        descriptions_by_page.setdefault(description.page_number, []).append(description)

    if not descriptions_by_page:
        return text

    page_markers = list(PDF_PAGE_MARKER_PATTERN.finditer(text))
    if not page_markers:
        blocks = _description_blocks(descriptions_by_page.get(None, []))
        return _append_blocks(text, blocks)

    parts: list[str] = [text[:page_markers[0].start()].rstrip()]
    found_pages: set[int] = set()

    for marker_index, marker in enumerate(page_markers):
        page_number = int(marker.group(1))
        found_pages.add(page_number)
        page_end = (
            page_markers[marker_index + 1].start()
            if marker_index + 1 < len(page_markers)
            else len(text)
        )
        page_text = text[marker.start():page_end].strip()
        blocks = _description_blocks(descriptions_by_page.get(page_number, []))
        parts.append(_append_blocks(page_text, blocks))

    missing_pages = sorted(
        page_number
        for page_number in descriptions_by_page
        if page_number is not None and page_number not in found_pages
    )
    if missing_pages:
        missing_label = ", ".join(str(page_number) for page_number in missing_pages)
        raise ValueError(f"picture descriptions reference missing PDF pages: {missing_label}")

    unpaged_blocks = _description_blocks(descriptions_by_page.get(None, []))
    if unpaged_blocks:
        parts.append(unpaged_blocks)

    return "\n\n".join(part for part in parts if part).strip()


def extract_picture_descriptions(texts: Iterable[str]) -> list[dict[str, str]]:
    """Extract unique generated descriptions from selected chunks."""
    extracted: list[dict[str, str]] = []
    seen_region_ids: set[str] = set()

    for text in texts:
        matches = list(PICTURE_DESCRIPTION_PATTERN.finditer(text))
        for match_index, match in enumerate(matches):
            region_id = match.group(1)
            if region_id in seen_region_ids:
                continue
            description_end = (
                matches[match_index + 1].start()
                if match_index + 1 < len(matches)
                else len(text)
            )
            description = text[match.end():description_end].strip()
            if not description:
                continue
            extracted.append(
                {"region_id": region_id, "description": " ".join(description.split())}
            )
            seen_region_ids.add(region_id)

    return extracted


def _description_blocks(descriptions: Iterable[PictureDescription]) -> str:
    return "\n\n".join(description.to_marked_text() for description in descriptions)


def _append_blocks(text: str, blocks: str) -> str:
    if not blocks:
        return text.strip()
    if not text.strip():
        return blocks
    return f"{text.strip()}\n\n{blocks}"