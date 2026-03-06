"""
Scrape Supreme Court decisions (ฎีกา) from deka.supremecourt.or.th

This scraper uses the court's search system to download decisions.
Note: The site may be slow or have rate limits.

Output: data/knowledge/dika/*.md (with YAML frontmatter)
"""
import re
import time
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from config import DIKA_DIR, REQUEST_DELAY, REQUEST_TIMEOUT, USER_AGENT

BASE_URL = "https://deka.supremecourt.or.th"
SEARCH_URL = f"{BASE_URL}/search"

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT})


def search_deka(keyword: str, page: int = 1) -> list[dict]:
    """Search for court decisions by keyword."""
    try:
        resp = SESSION.get(
            SEARCH_URL,
            params={"q": keyword, "page": page},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  Search failed: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    # Parse search results - structure may vary
    for item in soup.select("article, .result-item, .search-result, tr"):
        link = item.find("a", href=True)
        if not link:
            continue

        href = link.get("href", "")
        if not href or href == "#":
            continue

        title = link.get_text(strip=True)
        if not title:
            continue

        # Build full URL
        if href.startswith("/"):
            href = BASE_URL + href

        summary_el = item.find("p") or item.find(".summary") or item.find("td")
        summary = summary_el.get_text(strip=True) if summary_el else ""

        results.append({
            "title": title,
            "url": href,
            "summary": summary,
        })

    return results


def fetch_deka_detail(url: str) -> dict | None:
    """Fetch full text of a court decision."""
    try:
        resp = SESSION.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  Fetch failed: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Extract content - adapt selectors to actual page structure
    title_el = soup.find("h1") or soup.find("h2") or soup.find("title")
    title = title_el.get_text(strip=True) if title_el else ""

    # Try common content containers
    content_el = (
        soup.find("article")
        or soup.find(".content")
        or soup.find(".detail")
        or soup.find("#content")
        or soup.find("main")
    )
    content = content_el.get_text("\n", strip=True) if content_el else ""

    if not content:
        # Fallback: get all paragraphs
        paragraphs = soup.find_all("p")
        content = "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

    return {"title": title, "content": content, "url": url}


def extract_case_no(title: str) -> str:
    """Extract case number from title."""
    match = re.search(r'(\d+/\d{4})', title)
    return match.group(1) if match else ""


def extract_year(title: str) -> str:
    """Extract year from case number or title."""
    match = re.search(r'/(\d{4})', title)
    return match.group(1) if match else ""


def save_deka(detail: dict, case_no: str) -> Path:
    """Save court decision as markdown."""
    DIKA_DIR.mkdir(parents=True, exist_ok=True)

    title = detail["title"]
    year = extract_year(title)
    safe_case = re.sub(r'[/\\]', '-', case_no) if case_no else "unknown"
    filename = f"dika-{safe_case}.md"

    content = f"""---
type: dika
case_no: "{case_no}"
title: "{title.replace('"', '\\"')}"
year: {year}
source: deka.supremecourt.or.th
url: "{detail['url']}"
---

# {title}

{detail['content']}
"""

    filepath = DIKA_DIR / filename
    filepath.write_text(content, encoding="utf-8")
    return filepath


def main():
    keywords = sys.argv[1:] if len(sys.argv) > 1 else ["สัญญาเช่า", "ผิดสัญญา", "ละเมิด"]

    print("Supreme Court Decision Scraper")
    print(f"Keywords: {keywords}")
    print(f"Output: {DIKA_DIR}")
    print(f"Delay: {REQUEST_DELAY}s between requests")
    print()

    total_saved = 0

    for keyword in keywords:
        print(f"\nSearching: {keyword}")
        results = search_deka(keyword)

        if not results:
            print(f"  No results found (site may be unavailable)")
            continue

        print(f"  Found {len(results)} results")

        for result in tqdm(results, desc=f"  Downloading"):
            time.sleep(REQUEST_DELAY)

            detail = fetch_deka_detail(result["url"])
            if not detail or not detail["content"]:
                continue

            case_no = extract_case_no(result["title"]) or extract_case_no(detail["title"])
            filepath = save_deka(detail, case_no)
            total_saved += 1

    print(f"\nDone! {total_saved} decisions saved to {DIKA_DIR}")


if __name__ == "__main__":
    main()
