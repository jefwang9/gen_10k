"""Interactive financial data collection."""
import re
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
import pandas as pd


class FinancialDataCollector:
    """Collects and parses financial data from user input."""
    
    def __init__(self):
        self.collected_data = {}
    
    def parse_user_input(self, user_input: str, fiscal_year: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse user input to extract financial data.
        
        Supports:
        - Standalone numbers (e.g., "Revenue: $50B")
        - Markdown tables
        - HTML tables (with multi-year support)
        - Natural language descriptions
        
        Args:
            user_input: User input text
            fiscal_year: Optional fiscal year (e.g., "2024") to prioritize when parsing multi-year tables
        """
        parsed_data = {}
        
        # Try to parse as table first
        table_data = self._parse_table(user_input, fiscal_year)
        if table_data:
            parsed_data.update(table_data)
        
        # Parse standalone key-value pairs
        kv_pairs = self._parse_key_value_pairs(user_input)
        parsed_data.update(kv_pairs)
        
        # Parse numbers with context
        numbers = self._parse_numbers(user_input)
        parsed_data.update(numbers)
        
        return parsed_data
    
    def _parse_table(self, text: str, fiscal_year: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse markdown or HTML tables.
        
        For multi-year tables, if fiscal_year is provided, prioritizes that year's column.
        Otherwise, uses the first data column or the most recent year found.
        """
        parsed = {}
        
        # Try markdown table
        if "|" in text:
            lines = [line.strip() for line in text.split("\n") if "|" in line]
            if len(lines) > 1:
                # Skip header separator line
                data_lines = [l for l in lines if not re.match(r'^\|[\s\-:]+\|', l)]
                if data_lines:
                    headers = [h.strip() for h in data_lines[0].split("|")[1:-1]]
                    
                    # Find the best column index for fiscal_year
                    col_idx = self._find_year_column(headers, fiscal_year)
                    
                    for line in data_lines[1:]:
                        values = [v.strip() for v in line.split("|")[1:-1]]
                        if len(values) > 0:
                            # First column is usually the metric name
                            if len(values) > 1:
                                key = values[0]
                                # Use the selected column, or first data column if no match
                                value = values[col_idx] if col_idx < len(values) else values[1]
                            else:
                                # Single column table
                                key = headers[0] if headers else "Value"
                                value = values[0]
                            
                            if key and value and key.lower() not in ['metric', 'item', '']:
                                parsed[key] = self._parse_value(value)
        
        # Try HTML table
        if "<table" in text.lower():
            try:
                soup = BeautifulSoup(text, 'html.parser')
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    if not rows:
                        continue
                    
                    # Parse header row to find year columns
                    header_row = rows[0]
                    header_cells = header_row.find_all(['th', 'td'])
                    headers = [cell.get_text().strip() for cell in header_cells]
                    
                    # Find the best column index for fiscal_year
                    col_idx = self._find_year_column(headers, fiscal_year)
                    
                    # Parse data rows
                    for row in rows[1:]:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) < 2:
                            continue
                        
                        # First cell is usually the metric name
                        key = cells[0].get_text().strip()
                        
                        # Skip if key is empty or looks like a header
                        if not key or key.lower() in ['metric', 'item', '']:
                            continue
                        
                        # Use the selected column, or second column if no match
                        if col_idx < len(cells):
                            value = cells[col_idx].get_text().strip()
                        elif len(cells) > 1:
                            value = cells[1].get_text().strip()
                        else:
                            continue
                        
                        if value:
                            parsed[key] = self._parse_value(value)
            except Exception:
                pass
        
        return parsed
    
    def _find_year_column(self, headers: List[str], fiscal_year: Optional[str] = None) -> int:
        """
        Find the best column index based on fiscal_year.
        
        Returns:
            Column index (0-based). Returns 1 by default (first data column).
        """
        if not headers or len(headers) < 2:
            return 1
        
        # If no fiscal_year specified, return first data column (index 1)
        if not fiscal_year:
            return 1
        
        # Extract year from fiscal_year (e.g., "2024" from "2024" or "FY 2024")
        year_match = re.search(r'(\d{4})', fiscal_year)
        if not year_match:
            return 1
        
        target_year = year_match.group(1)
        
        # Look for columns matching the fiscal year
        for i, header in enumerate(headers):
            header_lower = header.lower()
            # Check for patterns like "FY 2024", "2024", "FY2024", etc.
            if (target_year in header or 
                f"fy {target_year}" in header_lower or 
                f"fy{target_year}" in header_lower or
                f"fiscal year {target_year}" in header_lower):
                return i
        
        # If no exact match, look for the most recent year
        years_found = []
        for i, header in enumerate(headers):
            year_matches = re.findall(r'(\d{4})', header)
            for year_str in year_matches:
                try:
                    years_found.append((i, int(year_str)))
                except ValueError:
                    pass
        
        if years_found:
            # Sort by year descending and return the most recent
            years_found.sort(key=lambda x: x[1], reverse=True)
            return years_found[0][0]
        
        # Default to first data column
        return 1
    
    def _parse_key_value_pairs(self, text: str) -> Dict[str, Any]:
        """Parse key-value pairs from text."""
        parsed = {}
        
        # Patterns like "Revenue: $50B" or "Revenue = 50 billion"
        patterns = [
            r'([A-Za-z\s]+):\s*\$?([\d,\.]+)\s*([BMKbmk]?)\s*(?:billion|million|thousand)?',
            r'([A-Za-z\s]+)\s*=\s*\$?([\d,\.]+)\s*([BMKbmk]?)\s*(?:billion|million|thousand)?',
            r'([A-Za-z\s]+)\s+of\s+\$?([\d,\.]+)\s*([BMKbmk]?)\s*(?:billion|million|thousand)?',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                key = match.group(1).strip()
                value_str = match.group(2).replace(',', '')
                multiplier = match.group(3).upper() if match.group(3) else ''
                
                try:
                    value = float(value_str)
                    if multiplier == 'B' or 'billion' in text[match.start():match.end()].lower():
                        value *= 1e9
                    elif multiplier == 'M' or 'million' in text[match.start():match.end()].lower():
                        value *= 1e6
                    elif multiplier == 'K' or 'thousand' in text[match.start():match.end()].lower():
                        value *= 1e3
                    
                    parsed[key] = value
                except ValueError:
                    pass
        
        return parsed
    
    def _parse_numbers(self, text: str) -> Dict[str, Any]:
        """Extract numbers with context."""
        parsed = {}
        
        # Look for percentage changes
        pct_pattern = r'([A-Za-z\s]+)\s+(?:growth|change|increase|decrease)\s+(?:of|by)?\s*([\d,\.\-]+)\s*%'
        matches = re.finditer(pct_pattern, text, re.IGNORECASE)
        for match in matches:
            key = f"{match.group(1).strip()} YoY Change (%)"
            try:
                parsed[key] = float(match.group(2).replace(',', ''))
            except ValueError:
                pass
        
        return parsed
    
    def _parse_value(self, value_str: str) -> Any:
        """Parse a single value string."""
        value_str = value_str.strip()
        
        # Remove currency symbols and commas
        clean_value = re.sub(r'[\$,\s]', '', value_str)
        
        # Check for percentages
        if '%' in value_str:
            try:
                return float(clean_value.replace('%', ''))
            except:
                return value_str
        
        # Check for multipliers
        multiplier = 1
        if 'B' in value_str.upper() or 'billion' in value_str.lower():
            multiplier = 1e9
        elif 'M' in value_str.upper() or 'million' in value_str.lower():
            multiplier = 1e6
        elif 'K' in value_str.upper() or 'thousand' in value_str.lower():
            multiplier = 1e3
        
        # Try to parse as number
        try:
            return float(clean_value.replace('B', '').replace('b', '').replace('M', '').replace('m', '').replace('K', '').replace('k', '')) * multiplier
        except:
            return value_str
    
    def format_questions(self, missing_items: List[str]) -> str:
        """Format missing data items as user-friendly questions."""
        if not missing_items:
            return ""
        
        formatted = "To complete the MD&A section, I need the following information:\n\n"
        for i, item in enumerate(missing_items, 1):
            formatted += f"{i}. {item}\n"
        
        formatted += "\nYou can provide this data in any format:\n"
        formatted += "- Standalone numbers (e.g., 'Revenue: $50B')\n"
        formatted += "- Markdown tables\n"
        formatted += "- HTML tables\n"
        formatted += "- Natural language descriptions\n"
        
        return formatted
    
    def merge_data(self, existing_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge new data into existing data."""
        merged = existing_data.copy()
        merged.update(new_data)
        return merged

