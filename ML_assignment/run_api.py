#!/usr/bin/env python3
"""API server entry point for the RAG system."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.api import run_server

if __name__ == "__main__":
    run_server()

