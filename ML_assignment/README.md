# SEC 10-K RAG Assistant

A Retrieval-Augmented Generation (RAG) system for assisting securities lawyers and finance professionals in drafting and reviewing SEC 10-K disclosure filings.

## Quick Links

- 🚀 [Quick Start Guide](QUICKSTART.md) - Get started in 5 minutes
- 📦 [Installation Guide](INSTALL.md) - Troubleshooting installation issues
- 📖 [Usage](#usage) - CLI and API documentation
- 🔧 [Configuration](#configuration) - Customize models and settings

## Overview

This system generates two key sections of SEC Form 10-K filings:
- **Item 1. Business**: Business description based on prior year filings
- **Item 7. MD&A**: Management's Discussion and Analysis with interactive financial data collection

## Features

- 📄 Document ingestion from SEC EDGAR 10-K HTML filings
- 🔍 RAG-based retrieval and generation
- 💬 Interactive clarification of missing financial inputs
- 🎯 Clean API and CLI interfaces
- ✅ Grounded generation (no hallucinations)
- 📊 Support for multiple data input formats (numbers, tables, natural language)

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd ML_assignment
   ```

2. **Install dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```
   
   **Note:** If you encounter import errors related to `langchain.text_splitter` or `langchain_text_splitters`, 
   see [INSTALL.md](INSTALL.md) for troubleshooting.

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```
   
   Or create `.env` manually:
   ```
   OPENAI_API_KEY=sk-your-key-here
   ```

## Configuration

Edit `config.py` to customize:
- LLM model (default: `gpt-4-turbo-preview`)
- Embedding model (default: `text-embedding-3-small`)
- Vector database settings
- Chunk size and overlap

## Usage

### CLI Interface

#### Basic Usage

Process a document and generate both sections:
```bash
python3 run_cli.py --company NVDA --fiscal-year 2024 --filing-url "https://www.sec.gov/ix?doc=/Archives/edgar/data/..."
```

Or using the module directly:
```bash
python3 -m src.cli --company NVDA --fiscal-year 2024 --filing-url "https://www.sec.gov/ix?doc=/Archives/edgar/data/..."
```

#### Generate Only Business Section
```bash
python3 run_cli.py --company NVDA --fiscal-year 2024 --filing-url "..." --skip-mda
```

#### Generate Only MD&A Section
```bash
python3 run_cli.py --company NVDA --fiscal-year 2024 --filing-url "..." --skip-business
```

#### Using Local Document
If you already have the HTML file in `data/10k_filings/`, you can omit `--filing-url`:
```bash
python3 run_cli.py --company NVDA --fiscal-year 2024
```

### API Interface

1. Start the FastAPI server:
```bash
python3 run_api.py
```

Or using the module directly:
```bash
python3 -m src.api
```

2. The API will be available at `http://localhost:8000`

#### API Endpoints

**Root Endpoint**
```bash
GET http://localhost:8000/
```
Returns API information and available endpoints.

**Health Check**
```bash
GET http://localhost:8000/health
```
Returns `{"status": "healthy"}`.

**Process Document**
```bash
POST http://localhost:8000/process-document
Content-Type: application/json

{
  "company_ticker": "NVDA",
  "fiscal_year": "2024",
  "filing_url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/..."
}
```

Or using curl:
```bash
curl -X POST "http://localhost:8000/process-document" \
  -H "Content-Type: application/json" \
  -d '{
    "company_ticker": "NVDA",
    "fiscal_year": "2024",
    "filing_url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/..."
  }'
```

**Generate Business Section**
```bash
POST http://localhost:8000/generate
Content-Type: application/json

{
  "company_ticker": "NVDA",
  "fiscal_year": "2024"
}
```

Or using curl:
```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "company_ticker": "NVDA",
    "fiscal_year": "2024"
  }'
```

**Generate MD&A Section**
```bash
POST http://localhost:8000/generate-mda
Content-Type: application/json

{
  "company_ticker": "NVDA",
  "fiscal_year": "2024",
  "financial_data": {
    "Revenue": 50000000000,
    "Revenue YoY Change (%)": 15.5,
    "Operating Income": 20000000000
  }
}
```

Or using curl:
```bash
curl -X POST "http://localhost:8000/generate-mda" \
  -H "Content-Type: application/json" \
  -d '{
    "company_ticker": "NVDA",
    "fiscal_year": "2024",
    "financial_data": {
      "Revenue": 50000000000,
      "Revenue YoY Change (%)": 15.5,
      "Operating Income": 20000000000
    }
  }'
```

**Parse Financial Data**
```bash
POST http://localhost:8000/parse-financial-data
Content-Type: application/json

"Revenue: $50B, Operating Income: $20B, Revenue growth: 15.5%"
```

Or using curl:
```bash
curl -X POST "http://localhost:8000/parse-financial-data" \
  -H "Content-Type: application/json" \
  -d '"Revenue: $50B, Operating Income: $20B, Revenue growth: 15.5%"'
```

Response:
```json
{
  "parsed_data": {
    "Revenue": 50000000000,
    "Operating Income": 20000000000,
    "Revenue YoY Change (%)": 15.5
  },
  "status": "success"
}
```

**Note:** You must call `/process-document` before using `/generate` or `/generate-mda` endpoints.

## Supported Companies

The following companies are pre-configured in `config.py`:

- **NVDA** - NVIDIA Corporation
- **MSFT** - Microsoft Corporation
- **KO** - The Coca-Cola Company
- **NKE** - Nike, Inc.
- **AMZN** - Amazon.com, Inc.
- **DASH** - DoorDash, Inc.
- **TJX** - The TJX Companies, Inc.
- **DRI** - Darden Restaurants, Inc.
- **UBER** - UBER TECHNOLOGIES, INC.

You can add more companies by editing the `COMPANIES` dictionary in `config.py`.

## Financial Data Input Formats

The system accepts financial data in multiple formats:

1. **Standalone numbers**: `Revenue: $50B`
2. **Markdown tables**:
   ```
   | Metric | Value |
   |--------|-------|
   | Revenue | $50B |
   | Operating Income | $20B |
   ```
3. **HTML tables**: Any HTML table structure
4. **Natural language**: `Revenue increased by 15.5% year-over-year to $50 billion`

## Project Structure

```
ML_assignment/
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── .env                     # Your API keys (create this file)
├── README.md                # This file
├── QUICKSTART.md            # Quick start guide
├── INSTALL.md               # Installation troubleshooting
├── run_api.py              # API server entry point
├── run_cli.py              # CLI entry point
├── src/
│   ├── __init__.py
│   ├── document_processor.py  # SEC 10-K HTML parsing
│   ├── vector_store.py        # Vector database management
│   ├── rag_system.py          # RAG generation logic
│   ├── data_collector.py      # Financial data parsing
│   ├── api.py                 # FastAPI backend
│   └── cli.py                 # CLI interface
└── data/                    # Created automatically
    ├── 10k_filings/          # Downloaded 10-K HTML files
    └── vector_db/            # Vector database storage
```

## Workflow

The system follows this workflow:

1. **Document Processing**: Download and parse SEC 10-K HTML filing from SEC EDGAR
2. **Indexing**: Extract key sections (Item 1. Business, Item 7. MD&A) and create vector embeddings
3. **Business Section Generation**: Generate Item 1. Business using RAG based on prior year filings
4. **Financial Data Collection**: Identify missing financial data needed for MD&A and collect from user
5. **MD&A Generation**: Generate Item 7. MD&A incorporating user-provided financial data and retrieved context

### Typical Usage Flow

**CLI:**
```bash
# 1. Process document and generate both sections
python3 run_cli.py --company NVDA --fiscal-year 2024 --filing-url "..."

# 2. Or generate sections separately
python3 run_cli.py --company NVDA --fiscal-year 2024 --skip-mda  # Business only
python3 run_cli.py --company NVDA --fiscal-year 2024 --skip-business  # MD&A only
```

**API:**
```bash
# 1. Process document
POST /process-document

# 2. Generate Business section
POST /generate

# 3. Generate MD&A with financial data
POST /generate-mda
```

## Evaluation Criteria

The system is designed to meet:
- ✅ **Correctness**: Grounded in retrieved documents, no hallucinations
- ✅ **Usability**: Clear, business-friendly interface
- ✅ **Domain Awareness**: Appropriate legal/financial tone and structure
- ✅ **Interactive Data Collection**: Identifies and collects missing financial inputs

## Technical Stack

- **Python 3.8+**
- **LangChain**: LLM framework and prompt management
- **OpenAI**: LLM (GPT-4) and embeddings (text-embedding-3-small)
- **ChromaDB**: Persistent vector database for document embeddings
- **FastAPI**: RESTful API backend with automatic OpenAPI documentation
- **BeautifulSoup4**: HTML parsing for SEC 10-K filings
- **html2text**: HTML to text conversion
- **Pydantic**: Data validation and settings management

### Default Configuration

- **LLM Model**: `gpt-4-turbo-preview` (configurable in `config.py`)
- **Embedding Model**: `text-embedding-3-small`
- **Chunk Size**: 1000 characters
- **Chunk Overlap**: 200 characters
- **Top K Retrieval**: 5 documents
- **API Host**: `0.0.0.0` (all interfaces)
- **API Port**: `8000`

## Important Notes

- **Prior Year Context**: The system uses prior year 10-K filings to generate current year narratives
- **Data Validation**: Financial data validation is optional (assumes user-provided data is accurate)
- **No Frontend**: No frontend UI required - CLI and API interfaces provided
- **Rate Limiting**: Be respectful to SEC servers (rate limiting included in download function)
- **State Management**: API uses in-memory storage (global dictionaries). For production, consider Redis or database
- **CORS**: API allows all origins by default. Restrict in production environments

## Example Output

### CLI Output

The CLI generates structured output files in the project root:
```
NVDA_2024_10k_draft.txt
```

File contents:
```
SEC Form 10-K Draft
Company: NVDA (NVIDIA Corporation)
Fiscal Year: 2024
============================================================

Item 1. Business
------------------------------------------------------------
[Generated Business section text...]

Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations
------------------------------------------------------------
[Generated MD&A section text...]
```

### API Output

API endpoints return JSON responses:

**Generate Response:**
```json
{
  "business_section": "[Generated text...]",
  "missing_data_questions": [
    "What was the total revenue for fiscal year 2024?",
    "What was the operating income?",
    "What was the cash flow from operations?"
  ],
  "status": "success"
}
```

**MD&A Response:**
```json
{
  "mda_section": "[Generated MD&A text...]",
  "status": "success"
}
```

Both sections are grounded in retrieved context from prior year filings and incorporate user-provided financial data.

## Troubleshooting

See [INSTALL.md](INSTALL.md) for installation issues and [QUICKSTART.md](QUICKSTART.md) for a quick start guide.

Common issues:
- **Import errors**: Run `pip3 install -r requirements.txt` or see INSTALL.md
- **API key not found**: Create `.env` file with `OPENAI_API_KEY=sk-...`
- **Document not found**: Provide `--filing-url` or ensure file exists in `data/10k_filings/`
- **Connection errors**: Check internet connection and SEC URL validity

## License

This is a take-home assignment project.

