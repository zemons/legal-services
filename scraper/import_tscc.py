"""
Import TSCC (Thai Supreme Court Cases) dataset into data/knowledge/dika/

Source: https://github.com/KevinMercury/tscc-dataset
1,207 criminal case issues from 1,000 Supreme Court judgements.
Academic use - public domain court decisions.

Output: data/knowledge/dika/tscc-{dekaid}.md
"""
import csv
import re
import sys
from pathlib import Path
from collections import defaultdict

from config import DIKA_DIR

TSCC_JUDGEMENT_URL = "https://raw.githubusercontent.com/KevinMercury/tscc-dataset/master/tscc_v0.1-judgement.csv"
TSCC_LAW_URL = "https://raw.githubusercontent.com/KevinMercury/tscc-dataset/master/tscc_v0.1-law.csv"

CATEGORY_MAP = {
    "LB": "ความผิดต่อชีวิตและร่างกาย",
    "P": "ความผิดต่อทรัพย์",
    "D": "ความผิดต่อชื่อเสียง",
}

GUILTY_MAP = {
    "1": "มีความผิด",
    "0": "ไม่มีความผิด",
    "-1": "ไม่ระบุ",
}


def download_csv(url: str) -> list[dict]:
    """Download CSV from URL and return as list of dicts."""
    import requests
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    lines = resp.text.splitlines()
    reader = csv.DictReader(lines)
    return list(reader)


def clean_fact(text: str) -> str:
    """Remove <discr> tags from fact text."""
    return re.sub(r'</?discr>', '', text).strip()


def main():
    import requests

    DIKA_DIR.mkdir(parents=True, exist_ok=True)

    print("Downloading TSCC dataset...")
    judgements = download_csv(TSCC_JUDGEMENT_URL)
    laws = download_csv(TSCC_LAW_URL)

    print(f"  Judgements: {len(judgements)} issues")
    print(f"  Laws: {len(laws)} provisions")

    # Build law lookup
    law_lookup = {row["lawid"]: row for row in laws}

    # Group issues by dekaid (case number)
    cases = defaultdict(list)
    for row in judgements:
        cases[row["dekaid"]].append(row)

    print(f"  Unique cases: {len(cases)}")

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else len(cases)
    count = 0

    for dekaid, issues in list(cases.items())[:limit]:
        first = issues[0]
        year = first.get("year", "")
        category_code = first.get("category", "")
        category = CATEGORY_MAP.get(category_code, category_code)

        # Collect all facts and decisions
        facts = []
        decisions = []
        related_laws = []

        for issue in issues:
            fact = clean_fact(issue.get("fact", ""))
            decision = issue.get("decision", "").strip()
            guilty = GUILTY_MAP.get(issue.get("isguilty", "-1"), "ไม่ระบุ")

            if fact:
                facts.append(fact)
            if decision:
                decisions.append(f"{decision} ({guilty})")

            # Resolve law references
            law_ids = issue.get("lawids", "").split(",")
            for lid in law_ids:
                lid = lid.strip()
                if lid and lid in law_lookup:
                    law = law_lookup[lid]
                    section = law.get("lawsection", "")
                    content = law.get("content", "").strip()
                    entry = f"- มาตรา {section}: {content}"
                    if entry not in related_laws:
                        related_laws.append(entry)

        # Determine topics
        topics = []
        if category_code == "LB":
            topics = ["อาญา", "ชีวิตและร่างกาย"]
        elif category_code == "P":
            topics = ["อาญา", "ทรัพย์"]
        elif category_code == "D":
            topics = ["อาญา", "ชื่อเสียง"]

        safe_id = dekaid.replace("/", "-")
        content = f"""---
type: dika
case_no: "{dekaid}"
court: ศาลฎีกา
year: {year}
category: อาญา
subcategory: {category}
topic: [{', '.join(topics)}]
source: TSCC-dataset
summary: "{decisions[0].replace('"', '\\"') if decisions else ''}"
---

# ฎีกาที่ {dekaid}

## ข้อเท็จจริง

{chr(10).join(facts)}

## คำวินิจฉัย

{chr(10).join('- ' + d for d in decisions)}

## หลักกฎหมายที่เกี่ยวข้อง

{chr(10).join(related_laws) if related_laws else 'ไม่ระบุ'}
"""

        filepath = DIKA_DIR / f"tscc-{safe_id}.md"
        filepath.write_text(content, encoding="utf-8")
        count += 1

    print(f"\nDone! {count} cases saved to {DIKA_DIR}")


if __name__ == "__main__":
    main()
