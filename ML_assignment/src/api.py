"""FastAPI backend for the RAG system."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uvicorn

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import API_HOST, API_PORT
from src.document_processor import DocumentProcessor
from src.vector_store import VectorStore
from src.rag_system import RAGSystem
from src.data_collector import FinancialDataCollector


app = FastAPI(title="SEC 10-K RAG Assistant", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class GenerateRequest(BaseModel):
    company_ticker: str
    fiscal_year: str
    filing_url: Optional[str] = None


class FinancialDataRequest(BaseModel):
    company_ticker: str
    fiscal_year: str
    financial_data: Dict[str, Any]


class GenerateResponse(BaseModel):
    business_section: str
    missing_data_questions: List[str]
    status: str


class MDARequest(BaseModel):
    company_ticker: str
    fiscal_year: str
    financial_data: Dict[str, Any]


class MDAResponse(BaseModel):
    mda_section: str
    status: str


class ProcessDocumentResponse(BaseModel):
    status: str
    message: str
    sections_found: List[str]


class ParseFinancialDataRequest(BaseModel):
    user_input: str
    fiscal_year: Optional[str] = None


# Global state (in production, use proper state management)
vector_stores = {}
rag_systems = {}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "SEC 10-K RAG Assistant API",
        "version": "1.0.0",
        "endpoints": {
            "/generate": "Generate Business section and identify missing data",
            "/generate-mda": "Generate MD&A section with financial data",
            "/health": "Health check"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/process-document", response_model=ProcessDocumentResponse)
async def process_document(request: GenerateRequest):
    """
    Process and index a 10-K document.
    """
    processor = DocumentProcessor()
    
    # Download document if URL provided
    if request.filing_url:
        file_path = processor.download_10k(request.company_ticker, request.filing_url)
        if not file_path:
            raise HTTPException(status_code=400, detail="Failed to download document")
    else:
        # Check if document already exists
        from config import DOCUMENTS_DIR
        file_path = DOCUMENTS_DIR / f"{request.company_ticker}_10k.html"
        if not file_path.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"Document not found. Please provide a filing_url or download the document first."
            )
    
    # Parse document
    sections = processor.parse_html_10k(str(file_path))
    
    # Create vector store and index
    vector_store = VectorStore(request.company_ticker)
    vector_store.clear()  # Clear existing data
    
    # Add sections to vector store
    documents = [sections.get("Item 1. Business", ""), 
                 sections.get("Item 7. MD&A", ""),
                 sections.get("Full Document", "")]
    documents = [d for d in documents if d]  # Filter empty
    
    vector_store.add_documents(documents)
    
    # Create RAG system
    rag_system = RAGSystem(vector_store)
    
    # Store for later use
    vector_stores[request.company_ticker] = vector_store
    rag_systems[request.company_ticker] = rag_system
    
    return ProcessDocumentResponse(
        status="success",
        message=f"Document processed and indexed for {request.company_ticker}",
        sections_found=list(sections.keys())
    )


@app.post("/generate", response_model=GenerateResponse)
async def generate_sections(request: GenerateRequest):
    """
    Generate Business section and identify missing financial data.
    """
    # Check if document is processed
    if request.company_ticker not in rag_systems:
        raise HTTPException(
            status_code=400,
            detail=f"Document not processed. Please call /process-document first."
        )
    
    rag_system = rag_systems[request.company_ticker]
    
    # Generate Business section
    business_section = rag_system.generate_business_section(
        request.company_ticker,
        request.fiscal_year
    )
    
    # Identify missing financial data
    missing_questions = rag_system.identify_missing_financial_data(
        request.company_ticker,
        request.fiscal_year
    )
    
    return GenerateResponse(
        business_section=business_section,
        missing_data_questions=missing_questions,
        status="success"
    )


@app.post("/generate-mda", response_model=MDAResponse)
async def generate_mda(request: MDARequest):
    """
    Generate MD&A section with provided financial data.
    """
    # Check if document is processed
    if request.company_ticker not in rag_systems:
        raise HTTPException(
            status_code=400,
            detail=f"Document not processed. Please call /process-document first."
        )
    
    rag_system = rag_systems[request.company_ticker]
    
    # Generate MD&A section
    mda_section = rag_system.generate_mda_section(
        request.company_ticker,
        request.fiscal_year,
        request.financial_data
    )
    
    return MDAResponse(
        mda_section=mda_section,
        status="success"
    )


@app.post("/parse-financial-data")
async def parse_financial_data(request: ParseFinancialDataRequest):
    """
    Parse financial data from user input text.
    
    Supports multi-year tables. If fiscal_year is provided, it will prioritize
    that year's column when parsing tables with multiple year columns.
    """
    collector = FinancialDataCollector()
    parsed_data = collector.parse_user_input(request.user_input, fiscal_year=request.fiscal_year)
    
    return {
        "parsed_data": parsed_data,
        "status": "success"
    }


def run_server():
    """Run the FastAPI server."""
    uvicorn.run(app, host=API_HOST, port=API_PORT)


if __name__ == "__main__":
    run_server()
