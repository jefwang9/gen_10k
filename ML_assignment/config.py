"""Configuration settings for the RAG system."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
DOCUMENTS_DIR = DATA_DIR / "10k_filings"
VECTOR_DB_DIR = DATA_DIR / "vector_db"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
DOCUMENTS_DIR.mkdir(exist_ok=True)
VECTOR_DB_DIR.mkdir(exist_ok=True)

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Model settings
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4-turbo-preview"  # or "gpt-3.5-turbo" for cost savings

# RAG settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RETRIEVAL = 5

# SEC EDGAR settings
SEC_BASE_URL = "https://www.sec.gov"
EDGAR_SEARCH_URL = "https://www.sec.gov/search-filings"

# Companies to process
COMPANIES = {
    "NVDA": "NVIDIA Corporation",
    "MSFT": "Microsoft Corporation",
    "KO": "The Coca-Cola Company",
    "NKE": "Nike, Inc.",
    "AMZN": "Amazon.com, Inc.",
    "DASH": "DoorDash, Inc.",
    "TJX": "The TJX Companies, Inc.",
    "DRI": "Darden Restaurants, Inc.",
    "UBER": "UBER TECHNOLOGIES, INC."
}

# FastAPI settings
API_HOST = "0.0.0.0"
API_PORT = 8000

