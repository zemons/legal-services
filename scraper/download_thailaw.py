"""
Download Thai Law dataset from Hugging Face (pythainlp/thailaw).
42,755 Acts of Parliament from krisdika.go.th - Public Domain.

Output: data/knowledge/statute/*.md (with YAML frontmatter)
"""
import re
import sys
from pathlib import Path
from tqdm import tqdm

from config import HF_DATASETS


def sanitize_filename(title: str, sysid: str) -> str:
    """Create safe filename from title."""
    clean = re.sub(r'[^\u0E00-\u0E7Fa-zA-Z0-9\s\-]', '', title)
    clean = re.sub(r'\s+', '-', clean.strip())
    if len(clean) > 80:
        clean = clean[:80]
    return f"{sysid}-{clean}.md" if clean else f"{sysid}.md"


def extract_category(title: str) -> str:
    """Guess category from title."""
    categories = {
        "พระราชบัญญัติ": "พระราชบัญญัติ",
        "พระราชกำหนด": "พระราชกำหนด",
        "พระราชกฤษฎีกา": "พระราชกฤษฎีกา",
        "กฎกระทรวง": "กฎกระทรวง",
        "ประมวลกฎหมาย": "ประมวลกฎหมาย",
        "รัฐธรรมนูญ": "รัฐธรรมนูญ",
        "ประกาศ": "ประกาศ",
        "ระเบียบ": "ระเบียบ",
        "คำสั่ง": "คำสั่ง",
    }
    for keyword, cat in categories.items():
        if keyword in title:
            return cat
    return "อื่นๆ"


def extract_year(title: str) -> str:
    """Extract Buddhist year from title."""
    match = re.search(r'พ\.ศ\.\s*(\d{4})', title)
    if match:
        return match.group(1)
    match = re.search(r'(\d{4})', title)
    if match and int(match.group(1)) > 2400:
        return match.group(1)
    return ""


def to_markdown(row: dict) -> str:
    """Convert a dataset row to markdown with YAML frontmatter."""
    sysid = str(row.get("sysid", ""))
    title = str(row.get("title", "")).strip()
    text = str(row.get("txt", "")).strip()
    category = extract_category(title)
    year = extract_year(title)

    frontmatter = f"""---
type: statute
sysid: "{sysid}"
title: "{title.replace('"', '\\"')}"
category: {category}
year: {year}
source: krisdika.go.th
license: public-domain
---"""

    return f"{frontmatter}\n\n# {title}\n\n{text}\n"


def main():
    from datasets import load_dataset

    cfg = HF_DATASETS["thailaw"]
    output_dir = Path(cfg["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading dataset: {cfg['repo']}")
    print(f"Description: {cfg['description']}")
    ds = load_dataset(cfg["repo"], split="train")

    limit = None
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])
        print(f"Limiting to {limit} rows")

    count = 0
    skipped = 0
    data = ds.select(range(limit)) if limit else ds

    for row in tqdm(data, desc="Converting to markdown"):
        text = str(row.get("txt", "")).strip()
        if not text:
            skipped += 1
            continue

        title = str(row.get("title", "")).strip()
        sysid = str(row.get("sysid", ""))
        filename = sanitize_filename(title, sysid)
        filepath = output_dir / filename

        content = to_markdown(row)
        filepath.write_text(content, encoding="utf-8")
        count += 1

    print(f"\nDone! {count} files saved to {output_dir}")
    if skipped:
        print(f"Skipped {skipped} empty records")


if __name__ == "__main__":
    main()
