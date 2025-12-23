"""RAG system for generating 10-K sections."""
from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import LLM_MODEL, OPENAI_API_KEY, TOP_K_RETRIEVAL
from src.vector_store import VectorStore


class RAGSystem:
    """RAG system for generating 10-K narratives."""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.llm = ChatOpenAI(
            model=LLM_MODEL,
            temperature=0.3,
            openai_api_key=OPENAI_API_KEY
        )
    
    def retrieve_context(self, query: str, k: int = TOP_K_RETRIEVAL) -> str:
        """Retrieve relevant context from vector store."""
        results = self.vector_store.similarity_search(query, k=k)
        
        context_parts = []
        for result in results:
            context_parts.append(result["content"])
        
        return "\n\n".join(context_parts)
    
    def generate_business_section(self, company_ticker: str, fiscal_year: str) -> str:
        """
        Generate Item 1. Business section.
        
        Args:
            company_ticker: Company ticker symbol
            fiscal_year: Fiscal year for the filing
            
        Returns:
            Generated Business section text
        """
        query = f"Item 1 Business description operations products services {company_ticker}"
        context = self.retrieve_context(query)
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                """You are a securities lawyer helping draft a SEC Form 10-K filing. 
Generate the Item 1. Business section based on the retrieved context from prior year filings.

Requirements:
- Use only information from the retrieved context
- Do not hallucinate or make up information
- Write in the formal, professional tone of a 10-K filing
- Be concise but comprehensive
- Focus on business operations, products, services, and markets
- Use the fiscal year {fiscal_year} in your narrative"""
            ),
            HumanMessagePromptTemplate.from_template(
                """Company: {company_ticker}
Fiscal Year: {fiscal_year}

Retrieved Context from Prior Year Filing:
{context}

Generate the Item 1. Business section for {company_ticker}'s {fiscal_year} Form 10-K.
Ensure the narrative is grounded in the retrieved context and does not include unsupported claims."""
            )
        ])
        
        messages = prompt.format_messages(
            company_ticker=company_ticker,
            fiscal_year=fiscal_year,
            context=context
        )
        
        response = self.llm.invoke(messages)
        return response.content
    
    def identify_missing_financial_data(self, company_ticker: str, fiscal_year: str) -> List[str]:
        """
        Identify what financial data is needed for MD&A.
        
        Args:
            company_ticker: Company ticker symbol
            fiscal_year: Fiscal year for the filing
            
        Returns:
            List of missing data items
        """
        query = f"Item 7 MD&A financial data revenue operating income cash flow {company_ticker}"
        context = self.retrieve_context(query, k=3)
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                """You are analyzing a 10-K filing to identify what financial data is needed 
to complete the MD&A section. Based on the structure and content of prior year filings, 
identify the key financial metrics that would typically be required."""
            ),
            HumanMessagePromptTemplate.from_template(
                """Company: {company_ticker}
Fiscal Year: {fiscal_year}

Prior Year MD&A Context:
{context}

Based on this context, what are the top 3-5 most critical financial data points 
needed to generate the MD&A section for {fiscal_year}? Focus on high-level metrics 
like Total Revenue, Net Income, and Cash Flow from Operations.

List them as clear, business-friendly questions that a finance professional would understand.

Format as a bulleted list of questions."""
            )
        ])
        
        messages = prompt.format_messages(
            company_ticker=company_ticker,
            fiscal_year=fiscal_year,
            context=context
        )
        
        response = self.llm.invoke(messages)
        
        # Parse the response into a list
        questions = [
            q.strip().lstrip("- •*")
            for q in response.content.split("\n")
            if q.strip() and (q.strip().startswith("-") or q.strip().startswith("•") or q.strip().startswith("*"))
        ]
        
        return questions if questions else [response.content]
    
    def generate_mda_section(
        self, 
        company_ticker: str, 
        fiscal_year: str, 
        financial_data: Dict[str, any]
    ) -> str:
        """
        Generate Item 7. MD&A section with user-provided financial data.
        
        Args:
            company_ticker: Company ticker symbol
            fiscal_year: Fiscal year for the filing
            financial_data: Dictionary of financial data provided by user
            
        Returns:
            Generated MD&A section text
        """
        query = f"Item 7 MD&A management discussion analysis financial results {company_ticker}"
        context = self.retrieve_context(query)
        
        # Format financial data for the prompt
        financial_summary = self._format_financial_data(financial_data)
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                """You are a securities lawyer helping draft a SEC Form 10-K filing. 
Generate the Item 7. Management's Discussion and Analysis (MD&A) section.

Requirements:
- Explicitly incorporate the user-provided financial data
- Explain drivers of performance changes
- Compare to prior year when data allows
- Use the formal, professional tone of a 10-K filing
- Ground explanations in the retrieved context from prior filings
- Do not hallucinate information not provided or in context
- Write for fiscal year {fiscal_year}"""
            ),
            HumanMessagePromptTemplate.from_template(
                """Company: {company_ticker}
Fiscal Year: {fiscal_year}

Retrieved Context from Prior Year Filing:
{context}

User-Provided Financial Data for {fiscal_year}:
{financial_data}

Generate the Item 7. MD&A section that:
1. Explicitly references the provided financial data
2. Explains the drivers of performance
3. Compares to prior periods where applicable
4. Matches the tone and structure of a real 10-K MD&A
5. Is grounded in the retrieved context"""
            )
        ])
        
        messages = prompt.format_messages(
            company_ticker=company_ticker,
            fiscal_year=fiscal_year,
            context=context,
            financial_data=financial_summary
        )
        
        response = self.llm.invoke(messages)
        return response.content
    
    def _format_financial_data(self, financial_data: Dict[str, any]) -> str:
        """Format financial data dictionary into a readable string."""
        if not financial_data:
            return "No financial data provided."
        
        formatted = []
        for key, value in financial_data.items():
            if isinstance(value, (int, float)):
                formatted.append(f"{key}: {value:,.2f}")
            elif isinstance(value, dict):
                formatted.append(f"{key}:")
                for sub_key, sub_value in value.items():
                    formatted.append(f"  {sub_key}: {sub_value}")
            else:
                formatted.append(f"{key}: {value}")
        
        return "\n".join(formatted)
