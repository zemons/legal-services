#!/usr/bin/env python3
"""
Legal Data Scraper - Main runner

Usage:
    python run.py thailaw          # Download Thai Law dataset (42K acts)
    python run.py thailaw 100      # Download first 100 only (test)
    python run.py legal_rag        # Download Legal RAG Q&A dataset
    python run.py legal_rag 50     # Download first 50 only (test)
    python run.py ratchakitcha     # Download Royal Gazette metadata (2020s)
    python run.py ratchakitcha 2024           # Specific year
    python run.py ratchakitcha 2024 --with-ocr  # With OCR text
    python run.py deka             # Scrape Supreme Court decisions
    python run.py deka สัญญาเช่า ละเมิด     # With specific keywords
    python run.py all              # Download all datasets
    python run.py status           # Show current data status
"""
import subprocess
import sys
from pathlib import Path

SCRAPER_DIR = Path(__file__).parent
DATA_DIR = SCRAPER_DIR.parent / "data" / "knowledge"


def show_status():
    """Show current data download status."""
    dirs = {
        "statute (thailaw)": DATA_DIR / "statute",
        "legal_rag (Q&A)": DATA_DIR / "legal_rag",
        "regulation (ratchakitcha)": DATA_DIR / "regulation" / "ratchakitcha",
        "dika (court decisions)": DATA_DIR / "dika",
    }

    print("=== Legal Data Status ===\n")
    for name, path in dirs.items():
        if path.exists():
            files = list(path.rglob("*"))
            file_count = sum(1 for f in files if f.is_file())
            size_mb = sum(f.stat().st_size for f in files if f.is_file()) / (1024 * 1024)
            print(f"  {name}: {file_count} files ({size_mb:.1f} MB)")
        else:
            print(f"  {name}: not downloaded")
    print()


def run_script(script: str, args: list[str] = None):
    """Run a scraper script."""
    cmd = [sys.executable, str(SCRAPER_DIR / script)] + (args or [])
    subprocess.run(cmd, cwd=str(SCRAPER_DIR))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        show_status()
        return

    command = sys.argv[1]
    extra_args = sys.argv[2:]

    if command == "status":
        show_status()
    elif command == "thailaw":
        run_script("download_thailaw.py", extra_args)
    elif command == "legal_rag":
        run_script("download_legal_rag.py", extra_args)
    elif command == "ratchakitcha":
        run_script("download_ratchakitcha.py", extra_args)
    elif command == "deka":
        run_script("scrape_deka.py", extra_args)
    elif command == "all":
        print("=== Downloading all datasets ===\n")
        run_script("download_thailaw.py", extra_args)
        run_script("download_legal_rag.py", extra_args)
        run_script("download_ratchakitcha.py", extra_args)
        print("\nNote: deka (court scraping) not included in 'all' - run separately")
    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
