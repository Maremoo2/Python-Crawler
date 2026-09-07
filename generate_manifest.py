from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
import re


ROOT = Path(__file__).resolve().parent
KNOWLEDGE_BASE_DIR = ROOT / "KnowledgeBase"
MANIFEST_PATH = ROOT / "manifest.jsonl"


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}

    frontmatter_block = parts[1]
    metadata: dict[str, str] = {}
    for line in frontmatter_block.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata


def extract_source_urls(text: str) -> list[str]:
    return re.findall(r"^URL:\s+(https?://\S+)\s*$", text, flags=re.MULTILINE)


def extract_title(text: str, file_path: Path) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return file_path.stem


def build_keywords(metadata: dict[str, str], title: str, source_urls: list[str]) -> list[str]:
    raw_tokens: list[str] = []
    raw_tokens.extend(metadata.get("category", "").split())
    raw_tokens.extend(metadata.get("product_area", "").split())
    raw_tokens.extend(title.split())

    for url in source_urls:
        cleaned = re.sub(r"https?://|www\.|[/?#=&:_\-.]+", " ", url)
        raw_tokens.extend(cleaned.split())

    keywords: list[str] = []
    seen: set[str] = set()
    for token in raw_tokens:
        normalized = re.sub(r"[^A-Za-z0-9]+", "", token).lower()
        if len(normalized) < 3:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        keywords.append(normalized)

    return keywords[:40]


def infer_doc_type(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".md":
        return "md"
    if suffix == ".pdf":
        return "pdf"
    return suffix.lstrip(".") or "unknown"


def build_manifest_entry(file_path: Path) -> dict[str, object]:
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    metadata = parse_frontmatter(content)
    relative_path = file_path.relative_to(ROOT).as_posix()
    source_urls = extract_source_urls(content)
    title = extract_title(content, file_path)
    keywords = build_keywords(metadata, title, source_urls)

    doc_id_source = "::".join(
        [
            metadata.get("category", ""),
            metadata.get("product_area", ""),
            relative_path,
        ]
    )

    return {
        "doc_id": sha256(doc_id_source.encode("utf-8")).hexdigest()[:16],
        "file_path": relative_path,
        "type": infer_doc_type(file_path),
        "title": title,
        "category": metadata.get("category", ""),
        "product_area": metadata.get("product_area", ""),
        "keywords": keywords,
        "source": metadata.get("source", ""),
        "source_urls": source_urls,
        "last_crawled": metadata.get("last_crawled", ""),
        "content_type": metadata.get("content_type", ""),
        "checksum": sha256(content.encode("utf-8")).hexdigest(),
    }


def main() -> None:
    records: list[dict[str, object]] = []

    if KNOWLEDGE_BASE_DIR.exists():
        for file_path in sorted(KNOWLEDGE_BASE_DIR.rglob("*.md")):
            if file_path.name == "index.md":
                continue
            records.append(build_manifest_entry(file_path))

    with MANIFEST_PATH.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")

    print(f"Wrote {len(records)} manifest records to {MANIFEST_PATH.name}")


if __name__ == "__main__":
    main()