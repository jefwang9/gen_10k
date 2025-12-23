"""Document processing for SEC 10-K filings."""
import re
import requests
from pathlib import Path
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import html2text
from urllib.parse import urljoin
import time

from config import DOCUMENTS_DIR, SEC_BASE_URL


class DocumentProcessor:
    """Processes SEC 10-K HTML filings."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
        
    def download_10k(self, company_ticker: str, filing_url: Optional[str] = None) -> Optional[str]:
        """
        Download a 10-K filing from SEC EDGAR.
        
        Args:
            company_ticker: Company ticker symbol
            filing_url: Direct URL to the 10-K filing HTML page
            
        Returns:
            Path to saved file or None if download failed
        """
        if filing_url:
            url = filing_url
        else:
            # For now, we'll need the user to provide URLs or implement SEC search
            # This is a placeholder - in production, you'd search EDGAR
            print(f"Please provide a 10-K filing URL for {company_ticker}")
            return None
            
        try:
            time.sleep(0.1)  # Be respectful to SEC servers
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Save the HTML file
            output_path = DOCUMENTS_DIR / f"{company_ticker}_10k.html"
            output_path.write_text(response.text, encoding='utf-8')
            
            return str(output_path)
        except Exception as e:
            print(f"Error downloading 10-K for {company_ticker}: {e}")
            return None
    
    def parse_html_10k(self, file_path: str) -> Dict[str, str]:
        """
        Parse HTML 10-K filing and extract key sections.
        
        Args:
            file_path: Path to HTML file
            
        Returns:
            Dictionary with section names as keys and content as values
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Extract text content
        sections = {}
        
        # Find Item 1. Business
        business_section = self._extract_section(soup, "1", "Business")
        if business_section:
            sections["Item 1. Business"] = business_section
        
        # Find Item 7. MD&A
        mda_section = self._extract_section(soup, "7", "Management")
        if mda_section:
            sections["Item 7. MD&A"] = mda_section
        
        # Extract full document for context
        full_text = self.html_converter.handle(html_content)
        sections["Full Document"] = full_text
        
        return sections
    
    def _extract_section(self, soup: BeautifulSoup, item_num: str, keyword: str) -> Optional[str]:
        """Extract a specific section from the 10-K."""
        # Extract just the number from the item string if it's passed in formats like "Item 1"
        item_number_str = re.search(r'\d+', item_num).group(0)
        item_number_int = int(item_number_str)

        # Look for section headers
        patterns = [
            rf"Item\s+{item_num}.*?{keyword}",
            rf"ITEM\s+{item_num}.*?{keyword}",
            rf"{item_num}\.\s*{keyword}",
        ]
        
        text_content = soup.get_text()
        
        for pattern in patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                start_pos = match.start()
                # Find the next Item or end of document
                next_item_pattern = rf"Item\s+{item_number_int + 1}|ITEM\s+{item_number_int + 1}"
                next_item = re.search(next_item_pattern, text_content[start_pos:], re.IGNORECASE)
                
                if next_item:
                    section_text = text_content[start_pos:start_pos + next_item.start()]
                else:
                    section_text = text_content[start_pos:start_pos + 50000]  # Limit length
                
                # Clean up the text
                section_text = re.sub(r'\s+', ' ', section_text)
                section_text = section_text.strip()
                
                return section_text[:50000]  # Limit to reasonable size
        
        return None
    
    def chunk_document(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split document into chunks for vector storage.
        
        Args:
            text: Document text
            chunk_size: Size of each chunk
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        # Simple sentence-aware chunking
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > chunk_size and current_chunk:
                # Save current chunk
                chunks.append(' '.join(current_chunk))
                
                # Start new chunk with overlap
                overlap_words = ' '.join(current_chunk).split()[-overlap//10:]
                current_chunk = overlap_words + [sentence]
                current_length = sum(len(s) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
