"""Configuration for legal data scraper."""
from pathlib import Path

# Base data directory
DATA_DIR = Path(__file__).parent.parent / "data"

# Output directories
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
DIKA_DIR = KNOWLEDGE_DIR / "dika"
STATUTE_DIR = KNOWLEDGE_DIR / "statute"
REGULATION_DIR = KNOWLEDGE_DIR / "regulation"

# Hugging Face datasets
HF_DATASETS = {
    "thailaw": {
        "repo": "pythainlp/thailaw",
        "description": "Thai Law (Act of Parliament) - 42,755 rows",
        "output_dir": STATUTE_DIR,
    },
    "legal_rag": {
        "repo": "airesearch/WangchanX-Legal-ThaiCCL-RAG",
        "description": "Legal RAG Q&A - 11,953 rows (35 legislations)",
        "output_dir": KNOWLEDGE_DIR / "legal_rag",
    },
    "ratchakitcha": {
        "repo": "obbzung/soc-ratchakitcha",
        "description": "Royal Gazette - 1M+ docs (metadata + OCR)",
        "output_dir": REGULATION_DIR,
    },
}

# Scraping settings
REQUEST_DELAY = 2  # seconds between requests
REQUEST_TIMEOUT = 30
USER_AGENT = "LegalServices-Scraper/1.0 (educational/research)"
