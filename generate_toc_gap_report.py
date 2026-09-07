from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
TOC_DIR = ROOT / "toc"
INDEX_PATH = ROOT / "KnowledgeBase" / "index.md"
SKIPPED_PATH = ROOT / "skipped_urls.txt"
ERRORS_PATH = ROOT / "errors.txt"
REPORT_PATH = ROOT / "toc_gap_report.md"

TOC_FILES = {
    "common": "Common",
    "onprem": "On-Premises Products",
    "online_services": "Online Services",
    "azure": "Azure",
}


def canonicalize_url(url: str) -> str:
    cleaned = url.strip().lstrip("\ufeff")
    cleaned = re.sub(r"\s+", "", cleaned)
    if cleaned.endswith("/"):
        cleaned = cleaned.rstrip("/")
    return cleaned


def read_expected_urls() -> dict[str, list[str]]:
    expected: dict[str, list[str]] = {}
    for stem in TOC_FILES:
        path = TOC_DIR / f"toc_{stem}.txt"
        if not path.exists():
            expected[stem] = []
            continue
        urls = []
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            cleaned = line.strip()
            if not cleaned or cleaned.startswith("#"):
                continue
            urls.append(canonicalize_url(cleaned))
        expected[stem] = urls
    return expected


def read_included_urls() -> set[str]:
    if not INDEX_PATH.exists():
        return set()
    content = INDEX_PATH.read_text(encoding="utf-8", errors="ignore")
    return {
        canonicalize_url(url)
        for url in re.findall(r"^  - Source: (https?://\S+)\s*$", content, flags=re.MULTILINE)
    }


def read_skipped_urls() -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    if not SKIPPED_PATH.exists():
        return result
    lines = SKIPPED_PATH.read_text(encoding="utf-8", errors="ignore").splitlines()[1:]
    for line in lines:
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        reason, url, details = parts
        result[canonicalize_url(url)] = (reason, details)
    return result


def read_error_urls() -> dict[str, str]:
    result: dict[str, str] = {}
    if not ERRORS_PATH.exists():
        return result
    lines = ERRORS_PATH.read_text(encoding="utf-8", errors="ignore").splitlines()[1:]
    for line in lines:
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        url, error = parts
        result[canonicalize_url(url)] = error
    return result


def build_status_rows(
    expected: dict[str, list[str]],
    included_urls: set[str],
    skipped_urls: dict[str, tuple[str, str]],
    error_urls: dict[str, str],
) -> tuple[list[str], dict[str, dict[str, int]]]:
    lines: list[str] = ["# TOC Gap Report", ""]
    summary: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for stem, label in TOC_FILES.items():
        urls = expected.get(stem, [])
        lines.append(f"## {label}")
        lines.append("")

        if not urls:
            lines.append("No TOC input file found or file is empty.")
            lines.append("")
            continue

        deviation_rows: list[str] = []

        for url in urls:
            if url in included_urls:
                status = "INCLUDED"
                notes = "Found in KnowledgeBase/index.md source list"
            elif url in error_urls:
                status = "ERROR"
                notes = error_urls[url]
            elif url in skipped_urls:
                reason, details = skipped_urls[url]
                status = "SKIPPED"
                notes = f"{reason}: {details}"
            else:
                status = "MISSING"
                notes = "Not found in index, skipped list, or error log"

            summary[label][status] += 1

            if status != "INCLUDED":
                deviation_rows.append(f"| {status} | {url} | {notes} |")

        if deviation_rows:
            lines.append("| Status | URL | Notes |")
            lines.append("|---|---|---|")
            lines.extend(deviation_rows)
        else:
            lines.append("No deviations. All expected URLs are included.")

        lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append("| Category | Skipped | Error | Missing |")
    lines.append("|---|---:|---:|---:|")
    for label in TOC_FILES.values():
        counts = summary[label]
        lines.append(
            f"| {label} | {counts['SKIPPED']} | {counts['ERROR']} | {counts['MISSING']} |"
        )

    return lines, summary


def main() -> None:
    expected = read_expected_urls()
    included_urls = read_included_urls()
    skipped_urls = read_skipped_urls()
    error_urls = read_error_urls()

    lines, _ = build_status_rows(expected, included_urls, skipped_urls, error_urls)
    REPORT_PATH.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"Wrote TOC gap report to {REPORT_PATH.name}")


if __name__ == "__main__":
    main()