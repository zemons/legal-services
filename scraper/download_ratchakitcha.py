"""
Download Royal Gazette (ราชกิจจานุเบกษา) metadata from Hugging Face.
Dataset: obbzung/soc-ratchakitcha - CC-BY-4.0

This downloads metadata only (not full PDFs/OCR) to keep size manageable.
Use --with-ocr flag to also download OCR text for recent years.
"""
import sys
from pathlib import Path

from config import HF_DATASETS


def main():
    from huggingface_hub import snapshot_download

    cfg = HF_DATASETS["ratchakitcha"]
    output_dir = Path(cfg["output_dir"]) / "ratchakitcha"
    output_dir.mkdir(parents=True, exist_ok=True)

    with_ocr = "--with-ocr" in sys.argv
    year = None
    for arg in sys.argv[1:]:
        if arg.isdigit() and len(arg) == 4:
            year = arg

    # Build include patterns
    patterns = []
    if year:
        patterns.append(f"meta/{year}/*")
        if with_ocr:
            patterns.append(f"ocr/*/{year}/*")
        print(f"Downloading year: {year}")
    else:
        patterns.append("meta/202?/*")  # 2020s decade only
        if with_ocr:
            patterns.append("ocr/*/202?/*")
        print("Downloading decade: 2020s (use `python download_ratchakitcha.py 2024` for specific year)")

    if with_ocr:
        print("Including OCR text")
    else:
        print("Metadata only (add --with-ocr for OCR text)")

    print(f"Dataset: {cfg['repo']}")
    print(f"Output: {output_dir}")
    print()

    snapshot_download(
        repo_id="open-law-data-thailand/soc-ratchakitcha",
        repo_type="dataset",
        allow_patterns=patterns,
        local_dir=str(output_dir),
    )

    print(f"\nDone! Files saved to {output_dir}")


if __name__ == "__main__":
    main()
