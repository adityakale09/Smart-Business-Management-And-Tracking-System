"""
Receipt parser for extracting structured data from OCR text
"""

import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class ReceiptParser:
    """Parser for extracting product information from receipt text"""
    
    def __init__(self):
        """Initialize parser with common patterns"""
        # Common patterns for receipts
        self.price_pattern = re.compile(r'\$?\s*(\d+\.?\d{0,2})', re.IGNORECASE)
        self.quantity_pattern = re.compile(r'(\d+)\s*(?:x|×|@|ea|each|units?|pcs?|pieces?)', re.IGNORECASE)
        self.item_pattern = re.compile(r'^(.+?)\s+\$?\s*(\d+\.?\d{0,2})$', re.IGNORECASE | re.MULTILINE)
        
    def parse_receipt(self, text: str) -> Dict:
        """
        Parse receipt text to extract structured data
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary with parsed receipt data
        """
        lines = text.split('\n')
        
        # Extract receipt type (purchase or sale)
        receipt_type = self._detect_receipt_type(text)
        
        # Extract date
        receipt_date = self._extract_date(text)
        
        # Extract items
        items = self._extract_items(lines)
        
        # Calculate total
        total = self._extract_total(text, items)
        
        # Extract source/store name
        source = self._extract_source(text)
        
        return {
            'receipt_type': receipt_type,
            'receipt_date': receipt_date,
            'source': source,
            'items': items,
            'total_amount': total
        }
    
    def _detect_receipt_type(self, text: str) -> str:
        """
        Detect if receipt is a purchase or sale
        
        Args:
            text: Receipt text
            
        Returns:
            'purchase' or 'sale'
        """
        text_lower = text.lower()
        
        # Keywords that indicate a purchase (buying inventory)
        purchase_keywords = ['supplier', 'vendor', 'wholesale', 'purchase', 'buy', 'order', 'invoice']
        
        # Keywords that indicate a sale (selling to customer)
        sale_keywords = ['customer', 'retail', 'sale', 'total', 'subtotal', 'tax', 'receipt']
        
        purchase_score = sum(1 for keyword in purchase_keywords if keyword in text_lower)
        sale_score = sum(1 for keyword in sale_keywords if keyword in text_lower)
        
        # Default to sale if ambiguous
        return 'purchase' if purchase_score > sale_score else 'sale'
    
    def _extract_date(self, text: str) -> Optional[datetime]:
        """
        Extract date from receipt text
        
        Args:
            text: Receipt text
            
        Returns:
            Parsed datetime or None
        """
        # Common date patterns
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',
            r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{2,4})',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2}),?\s+(\d{2,4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    # Try to parse the date
                    date_str = match.group(0)
                    for fmt in ['%m/%d/%Y', '%m-%d-%Y', '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%b %d, %Y', '%d %b %Y']:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
                except:
                    continue
        
        # Return current date if no date found
        return datetime.now()
    
    def _extract_items(self, lines: List[str]) -> List[Dict]:
        """
        Extract product items from receipt lines
        
        Args:
            lines: List of text lines
            
        Returns:
            List of item dictionaries
        """
        items = []
        current_item = None
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Skip header/footer lines
            if any(keyword in line.lower() for keyword in ['receipt', 'invoice', 'total', 'subtotal', 'tax', 'change', 'thank you']):
                continue
            
            # Try to match item with price pattern: "Item Name $XX.XX"
            item_match = re.match(r'^(.+?)\s+(\d+\.?\d{0,2})\s*$', line)
            if item_match:
                product_name = item_match.group(1).strip()
                price = float(item_match.group(2))
                
                # Extract quantity if present
                qty_match = self.quantity_pattern.search(line)
                quantity = int(qty_match.group(1)) if qty_match else 1
                
                # Calculate unit price
                unit_price = price / quantity if quantity > 0 else price
                
                items.append({
                    'product_name': product_name,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_price': price
                })
                continue
            
            # Try to match item with quantity and price: "Qty x Item Name $XX.XX"
            qty_item_match = re.match(r'^(\d+)\s*(?:x|×|@)\s*(.+?)\s+(\d+\.?\d{0,2})\s*$', line)
            if qty_item_match:
                quantity = int(qty_item_match.group(1))
                product_name = qty_item_match.group(2).strip()
                price = float(qty_item_match.group(3))
                unit_price = price / quantity if quantity > 0 else price
                
                items.append({
                    'product_name': product_name,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_price': price
                })
        
        return items
    
    def _extract_total(self, text: str, items: List[Dict]) -> float:
        """
        Extract total amount from receipt
        
        Args:
            text: Receipt text
            items: Extracted items
            
        Returns:
            Total amount
        """
        # Try to find explicit total
        total_patterns = [
            r'total[:\s]+\$?\s*(\d+\.?\d{0,2})',
            r'amount[:\s]+\$?\s*(\d+\.?\d{0,2})',
            r'grand\s+total[:\s]+\$?\s*(\d+\.?\d{0,2})',
            r'^\s*\$?\s*(\d+\.?\d{0,2})\s*$',
        ]
        
        for pattern in total_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                try:
                    # Take the largest number as total
                    totals = [float(m) for m in matches]
                    if totals:
                        return max(totals)
                except:
                    continue
        
        # Calculate from items if no explicit total found
        if items:
            return sum(item.get('total_price', 0) for item in items)
        
        return 0.0
    
    def _extract_source(self, text: str) -> str:
        """
        Extract store/source name from receipt
        
        Args:
            text: Receipt text
            
        Returns:
            Source/store name
        """
        lines = text.split('\n')
        
        # Usually the first few non-empty lines contain store name
        for i, line in enumerate(lines[:5]):
            line = line.strip()
            if line and len(line) > 2:
                # Skip common header words
                if not any(keyword in line.lower() for keyword in ['receipt', 'invoice', 'date', 'time']):
                    return line[:100]  # Limit length
        
        return "Unknown"


# Singleton instance
receipt_parser = ReceiptParser()

