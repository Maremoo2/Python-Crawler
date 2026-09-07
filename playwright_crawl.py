from collections import deque
from datetime import date
from pathlib import Path
import json
import re
import random
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from playwright.sync_api import sync_playwright

ROOT_URL = "https://www.licensingschool.co.uk/licenseverse/on-premises/"
LICENSEVERSE_ROOT = "https://www.licensingschool.co.uk/licenseverse/"
ROOT_URLS = {
    "on-premises": "https://www.licensingschool.co.uk/licenseverse/on-premises/",
    "azure": "https://www.licensingschool.co.uk/licenseverse/azure/",
    "online-services": "https://www.licensingschool.co.uk/licenseverse/ols/",
    "common": "https://www.licensingschool.co.uk/licenseverse/common-info/",
    "licensing-guides": "https://www.licensingschool.co.uk/licenseverse/licensing-guides/",
}
DOMAIN_FILTER = "licensingschool.co.uk/licenseverse/"
CRAWL_SCOPE = "all"  # Options: "onprem", "all"
# Optional: run only selected On-Prem headings by slug token(s) from TOC URLs.
# Example: ("windows-server", "sql-server")
ONPREM_HEADING_TOKENS: tuple[str, ...] = ()
STATE_FILE = Path("licenseverse_state.json")
PROFILE_DIR = Path("browser_profile")
OUTPUT_TEXT = Path("LicenseVerse_clean.txt")
OUTPUT_URLS = Path("visited_urls.txt")
OUTPUT_SKIPPED = Path("skipped_urls.txt")
OUTPUT_ERRORS = Path("errors.txt")
COVERAGE_REPORT = Path("coverage_report.md")
TOC_COVERAGE_REPORT = Path("onprem_toc_coverage.md")
CATEGORY_MAP_FILE = Path("category_map.json")
UNMAPPED_URLS_FILE = Path("unmapped_urls.txt")
KNOWLEDGE_BASE_DIR = Path("KnowledgeBase")
INDEX_FILE = KNOWLEDGE_BASE_DIR / "index.md"
TOC_DIR = Path("toc")

SESSION_HEALTH_CHECK_MIN_PAGES = 5
SESSION_HEALTH_CHECK_MAX_PAGES = 10

MAX_ARTICLES_PER_FILE = 40
MAX_CHARS_PER_FILE = 120000

EXCLUDE_KEYWORDS = (
    "dashboard",
    "login",
    "account",
    "wp-login",
    "logout",
    "about",
    "blog",
    "school-reports",
    "body-of-knowledge",
    "profile",
    "search",
    "checkout",
    "cart",
    "admin",
    "author",
    "free-resources",
    "category/",
    "books/",
    "world-class-licensing-training-for-free",
)

TOP_NAV_LINES = {
    "licensing guides",
    "dashboard",
    "common",
    "azure",
    "online services",
    "on-premises products",
    "account",
    "logout",
}

FOOTER_MARKERS = (
    "about licensing school",
    "facebook | linkedin | rss | x",
    "copyright (c) licensing school",
)

CATEGORY_FOLDERS = {
    "Common": "Common",
    "On-Premises Products": "On-Premises Products",
    "Online Services": "Online Services",
    "Azure": "Azure",
    "Licensing Guides": "Licensing Guides",
    "GLR Handouts": "GLR Handouts",
}

TARGET_CATEGORIES = tuple(CATEGORY_FOLDERS.keys())

QUALITY_WARN_PHRASES = (
    "Table of contents",
    "Collapse all",
    "Dashboard",
    "Login",
    "Account",
    "About Licensing School",
)

# Known thin landing pages that should be retained even when text is short.
STUB_INCLUDE_SLUGS = {
    "sql-server-2019",
    "sql-server-2017",
    "dynamics-365-business-central-on-premises",
    "buying-on-premises-products-mca-e",
    "dynamics-365-intelligent-order-management",
    "dynamics-365-electronic-invoicing",
    "buying-online-services-select-plus",
    "buying-online-services-mca-e",
    "esus-windows-7",
    "esus-sql-server-2016",
    "product-terms-cautionary-notes",
    "buying-azure-services-mpsa",
    "buying-azure-services-select-plus",
}

STUB_FORCE_CONTENT_SLUGS = {
    "sql-server-2017",
    "sql-server-2019",
}

SCOPE_EXCLUDED_SEGMENTS = {
    "dashboard",
    "common-info",
    "azure",
    "ols",
    "public",
    "licensing-exams",
    "find-what-you-need-fwyn",
    "licenseverse-updates",
    "high-school-resources",
    "hs-resources",
    "promotions-playground",
    "licensing-school-toolbox",
}

GENERIC_PRODUCT_LABELS = {
    "common",
    "azure",
    "online services",
    "on-premises products",
    "licensing guides",
    "glr handouts",
    "licensing on-premises products",
    "licensing online services",
    "licensing azure",
}

DEFAULT_CATEGORY_MAP = {
    "common-info": "Common",
    "azure": "Azure",
    "buying-azure-services": "Azure",
    "ols": "Online Services",
    "online-services": "Online Services",
    "on-premises": "On-Premises Products",
    "on-premises-products": "On-Premises Products",
    "licensing-guides": "Licensing Guides",
    "glr-handouts": "GLR Handouts",
    "glr": "GLR Handouts",
}

VALID_OUTPUT_CATEGORIES = set(TARGET_CATEGORIES)
VALID_MAP_CATEGORIES = VALID_OUTPUT_CATEGORIES | {"_meta"}

CORE_COMPLETENESS_CATEGORIES = {
    "Azure",
    "Online Services",
    "On-Premises Products",
    "Common",
}

BREADCRUMB_CATEGORY_MAP = {
    "common": "Common",
    "on-premises products": "On-Premises Products",
    "online services": "Online Services",
    "azure": "Azure",
    "licensing guides": "Licensing Guides",
    "glr handouts": "GLR Handouts",
}

ONPREM_HINT_PREFIXES = (
    "windows-server",
    "sql-server",
    "biztalk",
    "project-server",
    "exchange-server",
    "sharepoint-server",
    "skype-for-business-server",
    "office-ltsc",
    "visio-",
    "project-",
    "software-assurance",
    "spla",
    "buying-on-premises-products",
    "licensing-on-premises-products",
    "system-center",
    "host-integration-server",
    "dynamics-365-server",
    "dynamics-365-for-operations-server",
    "windows-11-device",
    "the-cal-suites",
)

ONLINE_HINT_PREFIXES = (
    "microsoft-365",
    "office-365",
    "ems-",
    "teams",
    "windows-365",
    "copilot",
    "power-",
    "dynamics-365-",
    "standalone-online-services",
    "visio-online",
    "microsoft-entra",
    "microsoft-intune",
    "microsoft-defender",
    "microsoft-purview",
    "microsoft-priva",
    "microsoft-project",
    "dataverse",
    "ai-builder",
    "buying-online-services",
    "licensing-online-services",
    "viva",
    "frontline-worker",
)

AZURE_HINT_PREFIXES = (
    "azure",
    "capacity-reservations",
    "licensing-azure",
    "licensing-sql-server-paas-solutions",
    "licensing-sql-server-virtual-machines",
    "licensing-windows-server-virtual-machines",
    "microsoft-fabric",
    "buying-azure-services",
    "multiple-azure-savings-plans",
    "using-a-capacity-reservation",
)

COMMON_HINT_PREFIXES = (
    "introduction-to-microsoft-licensing",
    "azure-hybrid-benefit",
    "flexible-virtualization-benefit",
    "license-mobility-through-sa",
    "licensing-csp-hoster-solutions",
    "license-deployment-options",
    "lifecycle-policies",
    "esus-",
    "licensing-the-developer-tools",
    "pricing",
    "partner-center-announcements",
    "product-terms-cautionary-notes",
    "servicing-channels",
    "cal-equivalent-licenses",
    "extended-security-updates",
)


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def slugify_for_file(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9 _\-]", "", name).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or "Unknown"


def humanize_slug(value: str) -> str:
    value = value.strip().strip("/")
    value = re.sub(r"[-_]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.title().strip()


def canonicalize_url(url: str) -> str:
    parts = urlsplit(url)
    path = unquote(parts.path or "")
    path = re.sub(r"\s+", "", path)
    path = re.sub(r"/+", "/", path)
    if path and path != "/":
        path = path.rstrip("/")
    path = quote(path or "/", safe="/-._~()")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, "", ""))


def get_licenseverse_parts(url: str) -> list[str]:
    lower = canonicalize_url(url).lower()
    if "/licenseverse/" not in lower:
        return []
    tail = lower.split("/licenseverse/", 1)[1].strip("/")
    if not tail:
        return []
    return [part for part in tail.split("/") if part]


def load_category_map() -> dict[str, str]:
    category_map = dict(DEFAULT_CATEGORY_MAP)

    if not CATEGORY_MAP_FILE.exists():
        return category_map

    try:
        loaded = json.loads(CATEGORY_MAP_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Warning: failed to parse {CATEGORY_MAP_FILE}: {exc}")
        return category_map

    if not isinstance(loaded, dict):
        print(f"Warning: {CATEGORY_MAP_FILE} must be a JSON object of slug -> category")
        return category_map

    raw_map = loaded.get("map") if isinstance(loaded.get("map"), dict) else loaded

    for slug, category in raw_map.items():
        if not isinstance(slug, str) or not isinstance(category, str):
            continue

        normalized_slug = slug.strip().lower()
        normalized_category = category.strip()
        if normalized_category not in VALID_MAP_CATEGORIES:
            continue

        category_map[normalized_slug] = normalized_category

    return category_map


def infer_category(url: str, category_map: dict[str, str]) -> str:
    parts = get_licenseverse_parts(url)
    if not parts:
        return "_UNMAPPED"

    first = parts[0].lower()
    if first == "lessons":
        if len(parts) < 2:
            return "_UNMAPPED"
        lesson_root = parts[1].lower()
        return category_map.get(lesson_root, "_UNMAPPED")

    return category_map.get(first, "_UNMAPPED")


def url_is_stub_whitelisted(url: str) -> bool:
    parts = get_licenseverse_parts(url)
    if not parts:
        return False

    first = parts[0].lower()
    key = parts[1].lower() if first == "lessons" and len(parts) >= 2 else first
    return key in STUB_INCLUDE_SLUGS


def get_primary_slug(url: str) -> str:
    parts = get_licenseverse_parts(url)
    if not parts:
        return ""

    first = parts[0].lower()
    if first == "lessons" and len(parts) >= 2:
        return parts[1].lower()
    return first


def should_force_stub_materialization(url: str) -> bool:
    return get_primary_slug(url) in STUB_FORCE_CONTENT_SLUGS


def should_force_category_completeness(category: str) -> bool:
    return category in CORE_COMPLETENESS_CATEGORIES


def infer_category_from_breadcrumb(breadcrumb_parts: list[str]) -> str:
    for part in breadcrumb_parts:
        normalized = normalize_whitespace(part).lower()
        if normalized in BREADCRUMB_CATEGORY_MAP:
            return BREADCRUMB_CATEGORY_MAP[normalized]
    return "_UNMAPPED"


def infer_category_from_url_hints(url: str) -> str:
    parts = get_licenseverse_parts(url)
    if not parts:
        return "_UNMAPPED"

    first = parts[0].lower()
    if first == "lessons" and len(parts) >= 2:
        first = parts[1].lower()

    if any(first.startswith(prefix) for prefix in ONPREM_HINT_PREFIXES):
        return "On-Premises Products"

    if any(first.startswith(prefix) for prefix in ONLINE_HINT_PREFIXES):
        return "Online Services"

    if any(first.startswith(prefix) for prefix in AZURE_HINT_PREFIXES):
        return "Azure"

    if any(first.startswith(prefix) for prefix in COMMON_HINT_PREFIXES):
        return "Common"

    return "_UNMAPPED"


def resolve_category(url: str, category_map: dict[str, str], breadcrumb_parts: list[str]) -> str:
    category = infer_category(url, category_map)
    if category not in {"_UNMAPPED", "_meta"}:
        return category

    breadcrumb_category = infer_category_from_breadcrumb(breadcrumb_parts)
    if breadcrumb_category in VALID_OUTPUT_CATEGORIES:
        return breadcrumb_category

    hint_category = infer_category_from_url_hints(url)
    if hint_category in VALID_OUTPUT_CATEGORIES:
        return hint_category

    return category


def build_forced_stub_text(url: str) -> str:
    slug = get_primary_slug(url)

    if slug == "sql-server-2017":
        return (
            "No standalone licensing content is published on the source page for SQL Server 2017. "
            "This page primarily redirects to newer SQL Server licensing guidance. "
            "Use SQL Server 2022 and SQL Server 2025 chapters for current licensing details."
        )

    if slug == "sql-server-2019":
        return (
            "No standalone licensing content is published on the source page for SQL Server 2019. "
            "This page primarily redirects to newer SQL Server licensing guidance. "
            "Use SQL Server 2022 and SQL Server 2025 chapters for current licensing details."
        )

    return "No standalone licensing content is published on the source page."


def should_skip_content_page(url: str, title: str, text: str) -> bool:
    lower_url = url.lower()
    lower_title = title.lower()
    if any(token in lower_url for token in EXCLUDE_KEYWORDS):
        return True
    if any(token in lower_title for token in EXCLUDE_KEYWORDS):
        return True
    if len(text.split()) < 60 and not url_is_stub_whitelisted(url):
        return True
    if lower_url.rstrip("/").endswith("/licenseverse"):
        return True
    if any(marker in lower_url for marker in ("/author/", "/books/", "/category/")):
        return True
    return False


def parse_breadcrumb(page) -> list[str]:
    selectors = [
        "nav[aria-label='breadcrumb']",
        ".breadcrumb",
        ".yoast-breadcrumb",
        ".aioseo-breadcrumbs",
    ]

    for selector in selectors:
        loc = page.locator(selector)
        if loc.count() == 0:
            continue

        breadcrumb_text = loc.first.inner_text().strip()
        if not breadcrumb_text:
            continue

        parts = [normalize_whitespace(part) for part in breadcrumb_text.split("»")]
        parts = [part for part in parts if part and part.lower() != "home"]
        if parts:
            return parts

    return []


def clean_article_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]

    cleaned = []
    skip_next_nav_block = False

    for line in lines:
        lower_line = line.lower()

        if any(marker in lower_line for marker in FOOTER_MARKERS):
            break

        if lower_line in {"table of contents", "collapse all"}:
            skip_next_nav_block = True
            continue

        if "home »" in lower_line:
            continue

        if lower_line in TOP_NAV_LINES:
            continue

        if skip_next_nav_block:
            has_lower = any(ch.islower() for ch in line)
            likely_sentence = has_lower and (line.endswith(".") or len(line) > 100)
            if likely_sentence:
                skip_next_nav_block = False
            else:
                continue

        if lower_line in {
            "show instructions",
            "generating document…",
            "generating document...",
            "contact us",
        }:
            continue

        if line.isupper() and len(line) < 70:
            continue

        cleaned.append(line)

    return "\n".join(cleaned).strip()


def extract_page_title(page) -> str:
    h1 = page.locator("h1")
    if h1.count() > 0:
        title = normalize_whitespace(h1.first.inner_text())
        if title:
            return title

    title = normalize_whitespace(page.title())
    if title.lower().endswith(" - licenseverse"):
        title = title[: -len(" - licenseverse")].strip()
    return title or "Untitled"


def has_valid_licenseverse_session(page) -> bool:
    current_url = page.url.lower()
    if "login" in current_url or "account" in current_url:
        return False

    body_text = normalize_whitespace(page.locator("body").inner_text()).lower()
    invalid_markers = (
        "sign in",
        "log in",
        "you do not have access",
        "visit our dashboard",
    )
    if any(marker in body_text for marker in invalid_markers):
        return False

    return "/licenseverse/" in current_url


def page_shows_logged_in_nav(page) -> bool:
    body_text = normalize_whitespace(page.locator("body").inner_text()).lower()
    return "logout" in body_text or "log out" in body_text


def probe_licenseverse_session(context) -> bool:
    probe_page = context.new_page()
    try:
        probe_page.goto(ROOT_URL, wait_until="domcontentloaded", timeout=60000)

        try:
            probe_page.wait_for_load_state("networkidle", timeout=60000)
        except Exception:
            pass

        return has_valid_licenseverse_session(probe_page) and page_shows_logged_in_nav(probe_page)
    finally:
        probe_page.close()


def create_authenticated_context(context):
    page = context.new_page()

    if probe_licenseverse_session(context):
        print("Loaded existing login session from the persistent browser profile.")
        return context, page

    print("No confirmed LicenseVerse session was found in the persistent browser profile.")
    page.goto("https://www.licensingschool.co.uk/licenseverse/", wait_until="domcontentloaded", timeout=60000)
    input("Log in to LicenseVerse in the opened browser, then press Enter here...")

    if not probe_licenseverse_session(context):
        input("LicenseVerse still looks logged out. Log in again in the browser, then press Enter here...")
        if not probe_licenseverse_session(context):
            raise RuntimeError("LicenseVerse login was not confirmed after manual sign-in.")

    context.storage_state(path=str(STATE_FILE))
    print(f"Saved login state to {STATE_FILE}")
    return context, page


def refresh_authenticated_session(context) -> None:
    if probe_licenseverse_session(context):
        context.storage_state(path=str(STATE_FILE))
        print(f"Saved login state to {STATE_FILE}")
        return

    login_page = context.new_page()
    try:
        login_page.goto("https://www.licensingschool.co.uk/licenseverse/", wait_until="domcontentloaded", timeout=60000)
        print("LicenseVerse session looks logged out. Re-log in in the browser, then press Enter here...")
        input()
    finally:
        login_page.close()

    if not probe_licenseverse_session(context):
        raise RuntimeError("LicenseVerse login was not confirmed after session refresh.")

    context.storage_state(path=str(STATE_FILE))
    print(f"Saved login state to {STATE_FILE}")


def should_visit(url: str, scope_state: dict | None = None) -> bool:
    lower_url = url.lower()
    if DOMAIN_FILTER not in lower_url:
        return False
    if any(word in lower_url for word in EXCLUDE_KEYWORDS):
        return False

    if not scope_state or scope_state.get("scope") == "all":
        return True

    parts = get_licenseverse_parts(url)
    if not parts:
        return False

    first = parts[0]
    allowed_segments = scope_state.get("allowed_segments", set())
    allowed_lessons = scope_state.get("allowed_lessons", set())

    if first == "lessons":
        if len(parts) < 2:
            return False
        return parts[1] in allowed_lessons

    return first in allowed_segments


def get_seed_urls(scope: str) -> list[str]:
    if scope == "onprem":
        return [ROOT_URL]

    return [LICENSEVERSE_ROOT] + list(ROOT_URLS.values())


def load_toc_seed_urls(scope: str) -> list[str]:
    if scope != "all" or not TOC_DIR.exists():
        return []

    toc_paths = (
        TOC_DIR / "toc_common.txt",
        TOC_DIR / "toc_onprem.txt",
        TOC_DIR / "toc_online_services.txt",
        TOC_DIR / "toc_azure.txt",
    )

    toc_urls: list[str] = []
    for toc_path in toc_paths:
        if not toc_path.exists():
            continue

        for line in toc_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            cleaned = line.strip().lstrip("\ufeff")
            if not cleaned or cleaned.startswith("#"):
                continue
            if "/licenseverse/" not in cleaned.lower():
                continue
            toc_urls.append(canonicalize_url(cleaned))

    return sorted(set(toc_urls))


def matches_onprem_heading_filter(parts: list[str], heading_tokens: tuple[str, ...]) -> bool:
    if not heading_tokens:
        return True
    lowered = [part.lower() for part in parts]
    return any(token.lower() in part for token in heading_tokens for part in lowered)


def collect_onprem_scope(page, root_url: str) -> dict:
    page.goto(root_url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_load_state("networkidle", timeout=60000)

    raw_links = page.eval_on_selector_all(
        "a[href]",
        "elements => elements.map(a => a.href)",
    )

    allowed_segments: set[str] = set()
    allowed_lessons: set[str] = set()
    toc_urls: set[str] = set()

    for href in raw_links:
        if not isinstance(href, str):
            continue
        canonical = canonicalize_url(href)
        if "/licenseverse/" not in canonical.lower():
            continue
        if any(word in canonical.lower() for word in EXCLUDE_KEYWORDS):
            continue

        parts = get_licenseverse_parts(canonical)
        if not parts:
            continue
        if not matches_onprem_heading_filter(parts, ONPREM_HEADING_TOKENS):
            continue

        first = parts[0]
        if first in SCOPE_EXCLUDED_SEGMENTS:
            continue

        if first == "lessons":
            if len(parts) >= 2:
                allowed_lessons.add(parts[1])
                toc_urls.add(canonical)
            continue

        allowed_segments.add(first)
        toc_urls.add(canonical)

    # Always keep the root path segment in scope.
    allowed_segments.add("on-premises")

    return {
        "scope": "onprem",
        "allowed_segments": allowed_segments,
        "allowed_lessons": allowed_lessons,
        "toc_urls": sorted(toc_urls),
    }


def write_onprem_toc_coverage_report(toc_urls: list[str], visited_urls: set[str]) -> None:
    lines = [
        "# On-Prem TOC Coverage",
        "",
        f"- TOC links discovered: {len(toc_urls)}",
        f"- TOC links visited: {sum(1 for url in toc_urls if url in visited_urls)}",
        "",
        "## Link Status",
        "",
    ]

    for url in toc_urls:
        status = "VISITED" if url in visited_urls else "MISSING"
        lines.append(f"- {status}: {url}")

    TOC_COVERAGE_REPORT.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return True


def navigate_to_licenseverse_page(page, url: str) -> None:
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_load_state("networkidle", timeout=60000)
        return
    except Exception as exc:
        current_url = canonicalize_url(page.url) if page.url else ""
        if "ERR_ABORTED" in str(exc) and should_visit(current_url):
            try:
                page.wait_for_load_state("networkidle", timeout=60000)
            except Exception:
                pass
            return
        raise


def extract_page_text(page) -> str:
    selectors = [
        "main article",
        "main .entry-content",
        "main .content",
        "article .entry-content",
        "article",
        "[role='main']",
        "main",
        ".entry-content",
        ".content",
    ]

    for selector in selectors:
        loc = page.locator(selector)
        if loc.count() == 0:
            continue

        text = loc.first.inner_text().strip()
        cleaned = clean_article_text(text)
        if len(cleaned.split()) >= 60:
            return cleaned

    return clean_article_text(page.locator("body").inner_text().strip())


def is_navigation_only_page(url: str, title: str, text: str) -> bool:
    lower_url = url.lower().rstrip("/")
    if lower_url.endswith("/licenseverse"):
        return True
    if len(text.split()) < 60 and not url_is_stub_whitelisted(url):
        return True
    if title.lower() in {"dashboard", "account", "login"}:
        return True
    return False


def infer_product_from_url(url: str, category: str, breadcrumb_parts: list[str]) -> str:
    if len(breadcrumb_parts) >= 2:
        second = normalize_whitespace(breadcrumb_parts[1])
        if second and second.lower() not in GENERIC_PRODUCT_LABELS:
            return second

    path = url.split("/licenseverse/", 1)[-1].strip("/")
    parts = [part for part in path.split("/") if part]

    if not parts:
        return category

    if parts[0] == "lessons" and len(parts) >= 2:
        return humanize_slug(parts[1])

    return humanize_slug(parts[0])


def chunk_articles(article_blocks: list[dict[str, str]]) -> list[list[dict[str, str]]]:
    chunks: list[list[dict[str, str]]] = []
    current_chunk: list[dict[str, str]] = []
    current_chars = 0

    for article in article_blocks:
        article_chars = len(article["text"]) + len(article["title"]) + 200
        exceeds_count = len(current_chunk) >= MAX_ARTICLES_PER_FILE
        exceeds_chars = current_chars + article_chars > MAX_CHARS_PER_FILE

        if current_chunk and (exceeds_count or exceeds_chars):
            chunks.append(current_chunk)
            current_chunk = []
            current_chars = 0

        current_chunk.append(article)
        current_chars += article_chars

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def write_index_file(file_manifest: dict[str, dict[str, list[dict[str, object]]]]) -> None:
    KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)

    lines = ["# LicenseVerse Knowledge Base", ""]
    for category in TARGET_CATEGORIES:
        lines.append(f"## {category}")
        lines.append("")
        for product in sorted(file_manifest.get(category, {}).keys()):
            lines.append(f"### {product}")
            for file_info in file_manifest[category][product]:
                lines.append(f"- [{file_info['label']}]({file_info['relative_path']})")
                for source_url in file_info["source_urls"]:
                    lines.append(f"  - Source: {source_url}")
            lines.append("")

    index_content = "\n".join(lines).strip() + "\n"
    INDEX_FILE.write_text(index_content, encoding="utf-8")
    INDEX_FILE.with_suffix(".txt").write_text(index_content, encoding="utf-8")


def quality_check_markdown_files(base_dir: Path) -> list[str]:
    warnings: list[str] = []
    if not base_dir.exists():
        return warnings

    for md_file in base_dir.rglob("*.md"):
        if md_file.name == "index.md":
            continue

        content = md_file.read_text(encoding="utf-8", errors="ignore")
        for phrase in QUALITY_WARN_PHRASES:
            if phrase.lower() in content.lower():
                warnings.append(f"{md_file}: contains '{phrase}'")

    return warnings


def write_coverage_report(
    file_manifest: dict[str, dict[str, list[dict[str, object]]]],
    category_counts: dict[str, int],
    visited_count: int,
    skipped_count: int,
    error_count: int,
) -> None:
    lines = [
        "# Coverage Report",
        "",
        f"- Crawled URLs: {visited_count}",
        f"- Skipped URLs: {skipped_count}",
        f"- Errors: {error_count}",
        "",
        "## Categories",
        "",
    ]

    for category in TARGET_CATEGORIES:
        products = file_manifest.get(category, {})
        product_names = sorted(products.keys())
        lines.append(f"### {category}")
        lines.append(f"- Articles: {category_counts.get(category, 0)}")
        lines.append(f"- Product files: {sum(len(items) for items in products.values())}")
        lines.append(f"- Product areas: {len(product_names)}")
        if product_names:
            lines.append("- Product areas covered:")
            for product in product_names:
                lines.append(f"  - {product}")
        lines.append("")

    COVERAGE_REPORT.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def main() -> None:
    visited = set()
    knowledge_map: dict[str, dict[str, list[dict[str, str]]]] = {}
    file_manifest: dict[str, dict[str, list[dict[str, object]]]] = {}
    skipped_urls = 0
    skipped_by_filter = 0
    skipped_nav_only = 0
    skipped_meta = 0
    category_counts = {category: 0 for category in TARGET_CATEGORIES}
    skipped_entries: list[str] = []
    error_entries: list[str] = []
    unmapped_entries: list[str] = []
    category_map = load_category_map()

    with sync_playwright() as p:
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        context = p.chromium.launch_persistent_context(
            str(PROFILE_DIR),
            headless=False,
            args=["--start-maximized"],
        )
        try:
            context, page = create_authenticated_context(context)
            pages_since_session_check = 0
            next_session_check_at = random.randint(SESSION_HEALTH_CHECK_MIN_PAGES, SESSION_HEALTH_CHECK_MAX_PAGES)

            if CRAWL_SCOPE == "onprem":
                root_url = canonicalize_url(ROOT_URL)
                scope_state = collect_onprem_scope(page, root_url)
                print(
                    "On-Prem scope initialized: "
                    f"{len(scope_state['allowed_segments'])} top-level segments, "
                    f"{len(scope_state['allowed_lessons'])} lessons roots, "
                    f"{len(scope_state.get('toc_urls', []))} TOC links."
                )
            else:
                scope_state = {"scope": "all"}

            seed_urls = [canonicalize_url(url) for url in get_seed_urls(CRAWL_SCOPE)]
            seed_urls.extend(load_toc_seed_urls(CRAWL_SCOPE))
            seed_urls = sorted(set(seed_urls))
            queued = set(seed_urls)
            to_visit = deque(seed_urls)
            print(f"Seeded crawl with {len(seed_urls)} URL roots.")

            with OUTPUT_TEXT.open("w", encoding="utf-8") as outfile:
                while to_visit:
                    url = to_visit.popleft()
                    queued.discard(url)

                    if url in visited:
                        continue

                    print(f"Visiting: {url}")
                    visited.add(url)

                    try:
                        navigate_to_licenseverse_page(page, url)

                        title = extract_page_title(page)
                        breadcrumb_parts = parse_breadcrumb(page)
                        text = extract_page_text(page)
                        force_stub = should_force_stub_materialization(url)
                        category = resolve_category(url, category_map, breadcrumb_parts)
                        force_category_keep = should_force_category_completeness(category)

                        if force_stub and not text:
                            text = build_forced_stub_text(url)

                        if force_category_keep and not text:
                            text = (
                                "No extractable article body was found on the source page. "
                                "The chapter URL has been retained for completeness."
                            )

                        if not text and not force_stub and not force_category_keep:
                            skipped_urls += 1
                            skipped_nav_only += 1
                            skipped_entries.append(f"NAV_ONLY\t{url}\tNo extracted text")
                        elif should_skip_content_page(url, title, text) and not force_stub and not force_category_keep:
                            skipped_urls += 1
                            skipped_by_filter += 1
                            skipped_entries.append(f"FILTER\t{url}\tFiltered by URL/title/text rule")
                        elif is_navigation_only_page(url, title, text) and not force_stub and not force_category_keep:
                            skipped_urls += 1
                            skipped_nav_only += 1
                            skipped_entries.append(f"NAV_ONLY\t{url}\tNavigation-only page")
                        else:
                            skip_reason = ""

                            if category == "_UNMAPPED":
                                skipped_urls += 1
                                skipped_by_filter += 1
                                skip_reason = "Category unmapped"
                                skipped_entries.append(f"FILTER\t{url}\t{skip_reason}")
                                parts = get_licenseverse_parts(url)
                                root = parts[1] if len(parts) >= 2 and parts[0] == "lessons" else (parts[0] if parts else "")
                                unmapped_entries.append(f"{root}\t{url}")
                            elif category == "_meta":
                                skipped_urls += 1
                                skipped_meta += 1
                                skip_reason = "Mapped as _meta"
                                skipped_entries.append(f"FILTER\t{url}\t{skip_reason}")
                            elif scope_state.get("scope") == "onprem" and category != "On-Premises Products":
                                skipped_urls += 1
                                skipped_by_filter += 1
                                skip_reason = "Outside On-Premises scope"
                                skipped_entries.append(f"FILTER\t{url}\t{skip_reason}")
                            elif category not in TARGET_CATEGORIES:
                                skipped_urls += 1
                                skipped_by_filter += 1
                                skip_reason = "Category outside target scope"
                                skipped_entries.append(f"FILTER\t{url}\t{skip_reason}")

                            if not skip_reason:
                                product = slugify_for_file(infer_product_from_url(url, category, breadcrumb_parts))
                                category_counts[category] += 1

                                outfile.write("\n\n")
                                outfile.write("=" * 100)
                                outfile.write("\n")
                                outfile.write(f"URL: {url}\n")
                                outfile.write(f"Title: {title}\n")
                                outfile.write("=" * 100)
                                outfile.write("\n\n")
                                outfile.write(text)

                                article_block = {
                                    "title": title,
                                    "url": url,
                                    "category": category,
                                    "product": product,
                                    "text": text,
                                }

                                knowledge_map.setdefault(category, {}).setdefault(product, []).append(article_block)

                        links = page.eval_on_selector_all(
                            "a[href]",
                            "elements => elements.map(a => a.href)",
                        )

                        for href in links:
                            if not isinstance(href, str):
                                continue
                            canonical_href = canonicalize_url(href)
                            if should_visit(canonical_href, scope_state) and canonical_href not in visited and canonical_href not in queued:
                                to_visit.append(canonical_href)
                                queued.add(canonical_href)

                    except Exception as exc:
                        error_entries.append(f"{url}\t{exc}")
                        print(f"Error: {exc}")

                    pages_since_session_check += 1
                    if pages_since_session_check >= next_session_check_at:
                        refresh_authenticated_session(context)
                        pages_since_session_check = 0
                        next_session_check_at = random.randint(SESSION_HEALTH_CHECK_MIN_PAGES, SESSION_HEALTH_CHECK_MAX_PAGES)
                        print(f"Next session health check in {next_session_check_at} pages.")

            KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
            # Avoid full directory deletion on Windows; folders may be locked by editor/indexer.
            for pattern in ("*.md", "*.txt"):
                for existing_file in KNOWLEDGE_BASE_DIR.rglob(pattern):
                    try:
                        existing_file.unlink()
                    except PermissionError:
                        pass

            files_created = 0
            today_str = str(date.today())

            for category in TARGET_CATEGORIES:
                products = knowledge_map.get(category, {})
                folder = KNOWLEDGE_BASE_DIR / CATEGORY_FOLDERS[category]
                folder.mkdir(parents=True, exist_ok=True)

                for product, article_blocks in sorted(products.items()):
                    chunks = chunk_articles(article_blocks)

                    for chunk_index, chunk in enumerate(chunks, start=1):
                        is_chunked = len(chunks) > 1
                        file_name = f"{slugify_for_file(product)}.md"
                        label = product
                        if is_chunked:
                            file_name = f"{slugify_for_file(product)} - Part {chunk_index}.md"
                            label = f"{product} - Part {chunk_index}"

                        file_path = folder / file_name
                        relative_path = file_path.relative_to(KNOWLEDGE_BASE_DIR).as_posix()

                        frontmatter = [
                            "---",
                            "source: LicenseVerse",
                            f"category: {category}",
                            f"product_area: {product}",
                            f"last_crawled: {today_str}",
                            "content_type: licensing_reference",
                            "---",
                            "",
                            f"# {product}",
                            "",
                        ]

                        content_parts = []
                        for article in chunk:
                            content_parts.append(
                                "\n".join(
                                    [
                                        f"## {article['title']}",
                                        "",
                                        f"Category: {article['category']}",
                                        f"Product: {article['product']}",
                                        f"Title: {article['title']}",
                                        f"URL: {article['url']}",
                                        "",
                                        article["text"],
                                    ]
                                )
                            )

                        file_content = "\n\n".join(frontmatter + content_parts).strip() + "\n"
                        file_path.write_text(file_content, encoding="utf-8")
                        file_path.with_suffix(".txt").write_text(file_content, encoding="utf-8")
                        files_created += 1

                        file_manifest.setdefault(category, {}).setdefault(product, []).append(
                            {
                                "label": label,
                                "relative_path": relative_path,
                                "source_urls": sorted({article["url"] for article in chunk}),
                            }
                        )

            write_index_file(file_manifest)
            write_coverage_report(file_manifest, category_counts, len(visited), skipped_urls, len(error_entries))

            with OUTPUT_URLS.open("w", encoding="utf-8") as urls_file:
                for visited_url in sorted(visited):
                    urls_file.write(visited_url)
                    urls_file.write("\n")

            with OUTPUT_SKIPPED.open("w", encoding="utf-8") as skipped_file:
                skipped_file.write("Reason\tURL\tDetails\n")
                for entry in skipped_entries:
                    skipped_file.write(entry + "\n")

            with OUTPUT_ERRORS.open("w", encoding="utf-8") as errors_file:
                errors_file.write("URL\tError\n")
                for entry in error_entries:
                    errors_file.write(entry + "\n")

            with UNMAPPED_URLS_FILE.open("w", encoding="utf-8") as unmapped_file:
                unmapped_file.write("Slug\tURL\n")
                for entry in sorted(set(unmapped_entries)):
                    unmapped_file.write(entry + "\n")

            if scope_state.get("scope") == "onprem":
                write_onprem_toc_coverage_report(scope_state.get("toc_urls", []), visited)

            quality_warnings = quality_check_markdown_files(KNOWLEDGE_BASE_DIR)

            print(f"Done! Crawled {len(visited)} pages.")
            print(f"Skipped URLs: {skipped_urls}")
            print(f"Skipped by filter: {skipped_by_filter}")
            print(f"Skipped as navigation-only: {skipped_nav_only}")
            print(f"Skipped as _meta: {skipped_meta}")
            print(f"Files created: {files_created}")
            print("Count by category:")
            for category in TARGET_CATEGORIES:
                print(f"- {category}: {category_counts[category]}")
            print(f"Saved text to {OUTPUT_TEXT}")
            print(f"Saved URLs to {OUTPUT_URLS}")
            print(f"Saved skipped URLs to {OUTPUT_SKIPPED}")
            print(f"Saved errors to {OUTPUT_ERRORS}")
            print(f"Saved unmapped URLs to {UNMAPPED_URLS_FILE}")
            print(f"Saved coverage report to {COVERAGE_REPORT}")
            if scope_state.get("scope") == "onprem":
                print(f"Saved TOC coverage report to {TOC_COVERAGE_REPORT}")
            print(f"Saved knowledge base to {KNOWLEDGE_BASE_DIR}")

            if quality_warnings:
                print("Quality warnings:")
                for warning in quality_warnings:
                    print(f"- {warning}")
            else:
                print("Quality check: no known navigation phrases found.")
        finally:
            context.close()


if __name__ == "__main__":
    main()
