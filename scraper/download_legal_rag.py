"""
Download WangchanX Legal RAG dataset from Hugging Face.
11,953 Q&A pairs with law contexts from 35 legislations - MIT License.

Output: data/knowledge/legal_rag/qa/*.json (Q&A pairs)
        data/knowledge/legal_rag/contexts/*.md (unique law sections)
"""
import json
import re
import sys
from pathlib import Path
from tqdm import tqdm

from config import HF_DATASETS


def sanitize_filename(text: str, max_len: int = 60) -> str:
    clean = re.sub(r'[^\u0E00-\u0E7Fa-zA-Z0-9\s\-]', '', text)
    clean = re.sub(r'\s+', '-', clean.strip())
    return clean[:max_len] if clean else "unnamed"


def main():
    from datasets import load_dataset

    cfg = HF_DATASETS["legal_rag"]
    output_dir = Path(cfg["output_dir"])
    qa_dir = output_dir / "qa"
    ctx_dir = output_dir / "contexts"
    qa_dir.mkdir(parents=True, exist_ok=True)
    ctx_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading dataset: {cfg['repo']}")
    ds = load_dataset(cfg["repo"])

    seen_contexts = {}

    for split_name in ds:
        split = ds[split_name]
        limit = int(sys.argv[1]) if len(sys.argv) > 1 else len(split)

        print(f"\nProcessing split: {split_name} ({min(limit, len(split))} rows)")

        for i, row in enumerate(tqdm(split.select(range(min(limit, len(split)))))):
            question = row.get("question", "")
            positive_answer = row.get("positive_answer", "")
            positive_contexts = row.get("positive_contexts", [])
            hard_negative_contexts = row.get("hard_negative_contexts", [])

            # Save Q&A pair
            qa_record = {
                "split": split_name,
                "index": i,
                "question": question,
                "answer": positive_answer,
                "contexts": [],
            }

            # Extract and save unique law contexts
            for ctx in positive_contexts:
                if not isinstance(ctx, dict):
                    continue
                context_text = ctx.get("context", "")
                metadata = ctx.get("metadata", {})
                unique_key = ctx.get("unique_key", "")

                if unique_key and unique_key not in seen_contexts:
                    law_title = metadata.get("law_title", "unknown")
                    section = metadata.get("section", "")
                    law_code = metadata.get("law_code", "")

                    md_content = f"""---
type: statute
law_code: "{law_code}"
law_title: "{law_title.replace('"', '\\"')}"
section: "{section}"
source: WangchanX-Legal-ThaiCCL-RAG
license: MIT
---

# {law_title} - {section}

{context_text}
"""
                    safe_key = sanitize_filename(unique_key)
                    (ctx_dir / f"{safe_key}.md").write_text(
                        md_content, encoding="utf-8"
                    )
                    seen_contexts[unique_key] = True

                qa_record["contexts"].append({
                    "law_code": metadata.get("law_code", ""),
                    "law_title": metadata.get("law_title", ""),
                    "section": metadata.get("section", ""),
                })

            qa_file = qa_dir / f"{split_name}-{i:05d}.json"
            qa_file.write_text(
                json.dumps(qa_record, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    print(f"\nDone!")
    print(f"  Q&A pairs: {qa_dir}")
    print(f"  Unique contexts: {len(seen_contexts)} files in {ctx_dir}")


if __name__ == "__main__":
    main()
