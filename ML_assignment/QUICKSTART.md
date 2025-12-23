# Quick Start Guide

## Prerequisites

1. **Python 3.8+** installed
2. **OpenAI API Key** - Get one from https://platform.openai.com/api-keys

## Setup (5 minutes)

1. **Install dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Set up API key:**
   ```bash
   cp .env.example .env
   # Edit .env and add: OPENAI_API_KEY=sk-your-key-here
   ```

## Quick Test

### Option 1: Using CLI (Recommended for first-time users)

1. **Get a 10-K filing URL:**
   - Go to https://www.sec.gov/search-filings
   - Search for a company (e.g., "NVIDIA" or "NVDA")
   - Find a recent 10-K filing
   - Copy the HTML document URL (looks like: `https://www.sec.gov/ix?doc=/Archives/edgar/data/...`)

2. **Run the CLI:**
   ```bash
   python3 run_cli.py --company NVDA --fiscal-year 2024 --filing-url "YOUR_URL_HERE"
   ```

3. **Follow the prompts:**
   - The system will download and process the document
   - Generate the Business section
   - Ask for financial data
   - Generate the MD&A section
   - Save output to a file

### Option 2: Using API

1. **Start the server:**
   ```bash
   python3 run_api.py
   ```

2. **In another terminal, process a document:**
   ```bash
   curl -X POST "http://localhost:8000/process-document" \
     -H "Content-Type: application/json" \
     -d '{
       "company_ticker": "NVDA",
       "fiscal_year": "2024",
       "filing_url": "YOUR_URL_HERE"
     }'
   ```

3. **Generate Business section:**
   ```bash
   curl -X POST "http://localhost:8000/generate" \
     -H "Content-Type: application/json" \
     -d '{
       "company_ticker": "NVDA",
       "fiscal_year": "2024"
     }'
   ```

4. **Generate MD&A with financial data:**
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

## Example Financial Data Input

When prompted for financial data, you can provide it in various formats:

**Format 1: Simple key-value**
```
Revenue: $50B
Operating Income: $20B
Revenue growth: 15.5%
```

**Format 2: Markdown table**
```
| Metric | Value |
|--------|-------|
| Revenue | $50B |
| Operating Income | $20B |
| Revenue Growth | 15.5% |
```

**Format 3: Natural language**
```
Revenue increased by 15.5% year-over-year to $50 billion. Operating income was $20 billion, up from $18 billion last year.
```

## Output

The system generates a file like `NVDA_2024_10k_draft.txt` containing:
- Item 1. Business section
- Item 7. MD&A section

Both sections are grounded in the retrieved 10-K context and incorporate your provided financial data.

## Troubleshooting

**Error: "OPENAI_API_KEY not found"**
- Make sure you created `.env` file with your API key
- Check that `python-dotenv` is installed

**Error: "Module not found"**
- Run `pip3 install -r requirements.txt` again
- Make sure you're in the project root directory

**Error: "Failed to download document"**
- Check your internet connection
- Verify the SEC URL is correct
- SEC servers may have rate limiting - wait a moment and try again

**Error: "Document not processed"**
- Make sure you called `/process-document` endpoint first (for API)
- Or provide `--filing-url` when running CLI

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Customize `config.py` for different models or settings
- Add more companies to the `COMPANIES` dictionary in `config.py`

