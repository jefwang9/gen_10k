"""CLI interface for the RAG system."""
import argparse
import sys
from pathlib import Path
from typing import Dict, Any

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import DOCUMENTS_DIR, COMPANIES
from src.document_processor import DocumentProcessor
from src.vector_store import VectorStore
from src.rag_system import RAGSystem
from src.data_collector import FinancialDataCollector


def process_document(company_ticker: str, filing_url: str = None):
    """Process and index a 10-K document."""
    print(f"\n{'='*60}")
    print(f"Processing 10-K document for {company_ticker}")
    print(f"{'='*60}\n")
    
    processor = DocumentProcessor()
    
    # Check if document exists locally
    file_path = DOCUMENTS_DIR / f"{company_ticker}_10k.html"
    
    if not file_path.exists() and not filing_url:
        print(f"Document not found locally. Please provide a filing URL.")
        print(f"Example: https://www.sec.gov/ix?doc=/Archives/edgar/data/...")
        filing_url = input("Enter 10-K filing URL (or press Enter to skip): ").strip()
        if not filing_url:
            return None, None
    
    # Download if URL provided
    if filing_url:
        print(f"Downloading document from: {filing_url}")
        file_path = processor.download_10k(company_ticker, filing_url)
        if not file_path:
            print("Error: Failed to download document")
            return None, None
        print(f"Document saved to: {file_path}")
    
    # Parse document
    print("\nParsing document sections...")
    sections = processor.parse_html_10k(str(file_path))
    print(f"Found sections: {list(sections.keys())}")
    
    # Create vector store
    print("\nCreating vector embeddings...")
    vector_store = VectorStore(company_ticker)
    vector_store.clear()
    
    documents = [
        sections.get("Item 1. Business", ""),
        sections.get("Item 7. MD&A", ""),
        sections.get("Full Document", "")
    ]
    documents = [d for d in documents if d]
    
    vector_store.add_documents(documents)
    print("Document indexed successfully!")
    
    # Create RAG system
    rag_system = RAGSystem(vector_store)
    
    return vector_store, rag_system


def generate_business_section(rag_system: RAGSystem, company_ticker: str, fiscal_year: str):
    """Generate Business section."""
    print(f"\n{'='*60}")
    print(f"Generating Item 1. Business section for {company_ticker} {fiscal_year}")
    print(f"{'='*60}\n")
    
    business_section = rag_system.generate_business_section(company_ticker, fiscal_year)
    
    print("Item 1. Business")
    print("-" * 60)
    print(business_section)
    print("-" * 60)
    
    return business_section


def collect_financial_data(rag_system: RAGSystem, company_ticker: str, fiscal_year: str) -> Dict[str, Any]:
    """Interactive financial data collection."""
    print(f"\n{'='*60}")
    print(f"Collecting Financial Data for MD&A")
    print(f"{'='*60}\n")
    
    # Identify missing data
    missing_questions = rag_system.identify_missing_financial_data(company_ticker, fiscal_year)
    
    collector = FinancialDataCollector()
    print(collector.format_questions(missing_questions))
    
    financial_data = {}
    
    print("\nPlease provide financial data. You can:")
    print("- Enter data line by line (e.g., 'Revenue: $50B')")
    print("- Paste a table (markdown or HTML)")
    print("- Type 'done' when finished")
    print("- Type 'skip' to proceed with available data\n")
    
    while True:
        user_input = input("Enter financial data (or 'done'/'skip'): ").strip()
        
        if user_input.lower() == 'done':
            break
        if user_input.lower() == 'skip':
            break
        
        if user_input:
            parsed = collector.parse_user_input(user_input, fiscal_year=fiscal_year)
            if parsed:
                financial_data = collector.merge_data(financial_data, parsed)
                print(f"\nParsed data: {parsed}")
                print(f"Total collected: {list(financial_data.keys())}\n")
            else:
                print("Could not parse data. Please try again or type 'done'/'skip'.\n")
    
    return financial_data


def generate_mda_section(rag_system: RAGSystem, company_ticker: str, fiscal_year: str, financial_data: Dict[str, Any]):
    """Generate MD&A section."""
    print(f"\n{'='*60}")
    print(f"Generating Item 7. MD&A section for {company_ticker} {fiscal_year}")
    print(f"{'='*60}\n")
    
    if financial_data:
        print(f"Using financial data: {list(financial_data.keys())}\n")
    else:
        print("Warning: No financial data provided. Generating based on context only.\n")
    
    mda_section = rag_system.generate_mda_section(company_ticker, fiscal_year, financial_data)
    
    print("Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations")
    print("-" * 60)
    print(mda_section)
    print("-" * 60)
    
    return mda_section


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SEC 10-K RAG Assistant - Generate Business and MD&A sections"
    )
    parser.add_argument(
        "--company",
        type=str,
        required=True,
        choices=list(COMPANIES.keys()),
        help="Company ticker symbol"
    )
    parser.add_argument(
        "--fiscal-year",
        type=str,
        required=True,
        help="Fiscal year for the filing (e.g., 2024)"
    )
    parser.add_argument(
        "--filing-url",
        type=str,
        default=None,
        help="URL to the 10-K filing HTML page"
    )
    parser.add_argument(
        "--skip-business",
        action="store_true",
        help="Skip Business section generation"
    )
    parser.add_argument(
        "--skip-mda",
        action="store_true",
        help="Skip MD&A section generation"
    )
    
    args = parser.parse_args()
    
    company_ticker = args.company.upper()
    fiscal_year = args.fiscal_year
    
    print(f"\n{'='*60}")
    print(f"SEC 10-K RAG Assistant")
    print(f"Company: {company_ticker} ({COMPANIES.get(company_ticker, 'Unknown')})")
    print(f"Fiscal Year: {fiscal_year}")
    print(f"{'='*60}\n")
    
    # Process document
    vector_store, rag_system = process_document(company_ticker, args.filing_url)
    
    if not rag_system:
        print("Error: Failed to process document. Exiting.")
        sys.exit(1)
    
    # Generate Business section
    business_section = None
    if not args.skip_business:
        business_section = generate_business_section(rag_system, company_ticker, fiscal_year)
    
    # Collect financial data and generate MD&A
    mda_section = None
    if not args.skip_mda:
        financial_data = collect_financial_data(rag_system, company_ticker, fiscal_year)
        mda_section = generate_mda_section(rag_system, company_ticker, fiscal_year, financial_data)
    
    # Save output
    output_file = Path(f"{company_ticker}_{fiscal_year}_10k_draft.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"SEC Form 10-K Draft\n")
        f.write(f"Company: {company_ticker} ({COMPANIES.get(company_ticker, 'Unknown')})\n")
        f.write(f"Fiscal Year: {fiscal_year}\n")
        f.write(f"{'='*60}\n\n")
        
        if business_section:
            f.write("Item 1. Business\n")
            f.write("-" * 60 + "\n")
            f.write(business_section + "\n\n")
        
        if mda_section:
            f.write("Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations\n")
            f.write("-" * 60 + "\n")
            f.write(mda_section + "\n")
    
    print(f"\n{'='*60}")
    print(f"Output saved to: {output_file}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()

