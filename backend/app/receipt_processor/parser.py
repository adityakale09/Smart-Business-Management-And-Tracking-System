"""
Receipt parser for extracting structured data from OCR text
"""

import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone


class ReceiptParser:
    """Parser for extracting product information from receipt text"""
    
    def __init__(self):
        """Initialize parser with common patterns"""
        # Common patterns for receipts
        self.price_pattern = re.compile(r'\$?\s*(\d+\.?\d{0,2})', re.IGNORECASE)
        self.quantity_pattern = re.compile(r'(\d+)\s*(?:x|×|@|ea|each|units?|pcs?|pieces?)', re.IGNORECASE)
        self.item_pattern = re.compile(r'^(.+?)\s+\$?\s*(\d+\.?\d{0,2})$', re.IGNORECASE | re.MULTILINE)
        self.item_row_pattern = re.compile(
            r'^\s*(\d+)\s+(.+?)\s+(\d+(?:\.\d{1,2})?)\s+(\d+(?:\.\d{1,2})?)\s*$',
            re.IGNORECASE,
        )
        self.item_row_name_first_pattern = re.compile(
            r'^\s*(.+?)\s+(\d+)\s+\$?\s*(\d+(?:\.\d{1,2})?)\s+\$?\s*(\d+(?:\.\d{1,2})?)\s*$',
            re.IGNORECASE,
        )
        self.item_row_prices_only_pattern = re.compile(
            r'^\s*(\d+)\s+\$?\s*(\d+(?:\.\d{1,2})?)\s+\$?\s*(\d+(?:\.\d{1,2})?)\s*$',
            re.IGNORECASE,
        )
        self.item_row_single_amount_pattern = re.compile(
            r'^\s*(\d+)\s+(.+?)\s+(\d+(?:\.\d{1,2})?)\s*$',
            re.IGNORECASE,
        )
        self.inline_name_with_prices_pattern = re.compile(
            r'^\s*(.+?)\s+\$?\s*(\d+(?:\.\d{1,2})?)\s+\$?\s*(\d+(?:\.\d{1,2})?)\s*$',
            re.IGNORECASE,
        )
        # Common retail layout: SrNo Item Qty MRP Rate Value
        self.retail_row_with_mrp_pattern = re.compile(
            r'^\s*(\d{1,3})\s+(.+?)\s+(\d{1,3})\s+(\d+(?:\.\d{1,2})?)\s+(\d+(?:\.\d{1,2})?)\s+(\d+(?:\.\d{1,2})?)\s*$',
            re.IGNORECASE,
        )
        # Common retail layout: SrNo Item Qty Rate Value
        self.retail_row_pattern = re.compile(
            r'^\s*(\d{1,3})\s+(.+?)\s+(\d{1,3})\s+(\d+(?:\.\d{1,2})?)\s+(\d+(?:\.\d{1,2})?)\s*$',
            re.IGNORECASE,
        )
        # Variant without explicit serial number at row start
        self.retail_row_no_sr_pattern = re.compile(
            r'^\s*(.+?)\s+(\d{1,3})\s+(\d+(?:\.\d{1,2})?)\s+(\d+(?:\.\d{1,2})?)\s*$',
            re.IGNORECASE,
        )
        
    def is_valid_receipt(self, text: str) -> bool:
        """
        Validate whether OCR text actually represents a receipt.
        Checks for key receipt indicators like prices, quantities, dates, and totals.
        
        Args:
            text: OCR extracted text
            
        Returns:
            True if the text appears to be a valid receipt, False otherwise
        """
        if not text or len(text.strip()) < 15:
            return False

        text_lower = text.lower()

        # Count receipt-like indicators
        score = 0

        # Must have price-like patterns (numbers with decimal points)
        price_matches = re.findall(r'\d+\.\d{2}', text)
        if len(price_matches) >= 2:
            score += 3
        elif len(price_matches) >= 1:
            score += 1

        # Check for receipt/invoice/bill keywords
        receipt_keywords = ['receipt', 'invoice', 'bill', 'purchase', 'total', 'subtotal', 'store', 'shop', 'mart', 'bought', 'item', 'qty', 'quantity', 'price', 'amount', 'payment', 'cash', 'change']
        keyword_count = sum(1 for kw in receipt_keywords if kw in text_lower)
        if keyword_count >= 3:
            score += 3
        elif keyword_count >= 1:
            score += 1

        # Check for date patterns
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}',
            r'\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*'
        ]
        if any(re.search(p, text, re.IGNORECASE) for p in date_patterns):
            score += 2

        # Check for currency symbols
        currency_symbols = ['₹', '$', '€', '£', '¥']
        if any(sym in text for sym in currency_symbols):
            score += 1

        # Check for numeric lines with product-like content (alphanumeric + numbers)
        lines = text.split('\n')
        data_lines = sum(1 for line in lines if re.search(r'[A-Za-z]', line) and re.search(r'\d', line))
        if data_lines >= 3:
            score += 2
        elif data_lines >= 1:
            score += 1

        # Minimum score threshold: 4 (requires at least a few indicators)
        return score >= 4

    def categorize_receipt(self, text: str, items: List[Dict]) -> str:
        """
        Auto-categorize a receipt based on OCR text content and extracted items.
        
        Args:
            text: OCR extracted text
            items: Extracted item dictionaries
            
        Returns:
            Category string (grocery, electronics, restaurant, etc.) or None
        """
        text_lower = text.lower()
        product_names = ' '.join(item.get('product_name', '') for item in items).lower()
        combined = text_lower + ' ' + product_names

        # Grocery
        grocery_kw = ['grocery', 'supermarket', 'food', 'vegetables', 'fruits', 'milk', 'bread', 'rice', 'sugar', 'oil', 'spices', 'snacks', 'beverages', 'groceries']
        if any(kw in combined for kw in grocery_kw):
            return 'grocery'

        # Electronics
        electronics_kw = ['electronics', 'electric', 'battery', 'charger', 'cable', 'phone', 'computer', 'laptop', 'accessories', 'digital', 'camera', 'headphone']
        if any(kw in combined for kw in electronics_kw):
            return 'electronics'

        # Restaurant
        restaurant_kw = ['restaurant', 'cafe', 'dining', 'food', 'meal', 'lunch', 'dinner', 'breakfast', 'pizza', 'burger', 'coffee', 'tea', 'snack', 'bakery']
        if any(kw in combined for kw in restaurant_kw):
            return 'restaurant'

        # Office Supplies
        office_kw = ['office', 'stationery', 'paper', 'printer', 'pen', 'pencil', 'notebook', 'desk', 'supplies', 'folder', 'file']
        if any(kw in combined for kw in office_kw):
            return 'office_supplies'

        # Transportation
        transport_kw = ['fuel', 'gas', 'petrol', 'diesel', 'transport', 'taxi', 'parking', 'toll', 'travel', 'mileage']
        if any(kw in combined for kw in transport_kw):
            return 'transportation'

        # Utilities
        utilities_kw = ['utility', 'electricity', 'water', 'gas', 'internet', 'phone bill', 'mobile', 'broadband', 'subscription']
        if any(kw in combined for kw in utilities_kw):
            return 'utilities'

        # Medical
        medical_kw = ['medical', 'pharmacy', 'medicine', 'drug', 'hospital', 'clinic', 'doctor', 'health', 'prescription', 'diagnostic', 'lab']
        if any(kw in combined for kw in medical_kw):
            return 'medical'

        # Default to None (uncategorized)
        return None

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

        # Detect currency used in receipt values
        currency_code = self._detect_currency(text)
        
        # Auto-categorize if possible
        category = self.categorize_receipt(text, items)
        
        return {
            'receipt_type': receipt_type,
            'receipt_date': receipt_date,
            'source': source,
            'items': items,
            'total_amount': total,
            'currency_code': currency_code,
            'category': category,
        }

    def _detect_currency(self, text: str) -> str:
        """Detect currency code from symbols or currency keywords in OCR text."""
        text_upper = (text or '').upper()

        if '₹' in text or ' INR' in text_upper or 'RUPEE' in text_upper:
            return 'INR'
        if '$' in text or ' USD' in text_upper or 'DOLLAR' in text_upper:
            return 'USD'
        if '€' in text or ' EUR' in text_upper:
            return 'EUR'
        if '£' in text or ' GBP' in text_upper or 'POUND' in text_upper:
            return 'GBP'
        if ' AED' in text_upper:
            return 'AED'
        if ' CAD' in text_upper:
            return 'CAD'
        if ' AUD' in text_upper:
            return 'AUD'
        if ' JPY' in text_upper or '¥' in text:
            return 'JPY'

        # Keep existing behavior for local usage when symbol is unclear.
        return 'INR'
    
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
        return datetime.now(timezone.utc)
    
    def _extract_items(self, lines: List[str]) -> List[Dict]:
        """
        Extract product items from receipt lines
        
        Args:
            lines: List of text lines
            
        Returns:
            List of item dictionaries
        """
        normalized_lines = [self._normalize_line(line) for line in lines]
        normalized_lines = [line for line in normalized_lines if line]

        items = []
        seen = set()
        start_index = self._find_item_table_start(normalized_lines)
        in_table_lines = []

        for line in normalized_lines[start_index:]:
            if self._is_table_end_line(line) and in_table_lines:
                break
            if self._is_noise_line(line):
                continue
            in_table_lines.append(line)

        if not in_table_lines:
            in_table_lines = [line for line in normalized_lines if not self._is_noise_line(line)]

        pending_name_parts = []
        pending_qty: Optional[int] = None
        pending_unit_price: Optional[float] = None

        for line in in_table_lines:
            item = self._parse_complete_item_line(line)
            if item:
                self._append_item_if_new(items, seen, item)
                pending_name_parts = []
                pending_qty = None
                pending_unit_price = None
                continue

            prices_only_match = self.item_row_prices_only_pattern.match(line)
            if prices_only_match and pending_name_parts:
                quantity = int(prices_only_match.group(1))
                unit_price = self._to_amount(prices_only_match.group(2))
                total_price = self._to_amount(prices_only_match.group(3))
                product_name = self._clean_product_name(' '.join(pending_name_parts))
                item = {
                    'product_name': product_name,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_price': total_price,
                }
                if self._is_valid_item(**item):
                    self._append_item_if_new(items, seen, item)
                pending_name_parts = []
                pending_qty = None
                pending_unit_price = None
                continue

            if self._looks_like_product_text(line):
                pending_name_parts.append(line)
                if len(pending_name_parts) > 3:
                    pending_name_parts = pending_name_parts[-2:]
                continue

            if pending_name_parts:
                numeric_tokens = self._extract_amount_tokens(line)

                # Pattern: qty only (e.g., "2")
                if pending_qty is None and re.match(r'^\s*\d{1,4}\s*$', line):
                    pending_qty = int(line.strip())
                    continue

                # Pattern: qty + one amount (e.g., "2 30.00")
                if len(numeric_tokens) == 2 and pending_qty is None and re.match(r'^\s*\d{1,4}\s+[\$₹]?\s*\d+(?:[\.,]\d{1,2})\s*$', line):
                    pending_qty = int(float(numeric_tokens[0]))
                    pending_unit_price = self._to_amount(numeric_tokens[1])
                    continue

                # Pattern: qty + unit + total already in one line (defensive fallback)
                if len(numeric_tokens) >= 3 and pending_qty is None and re.match(r'^\s*\d{1,4}\s+', line):
                    qty = int(float(numeric_tokens[0]))
                    unit = self._to_amount(numeric_tokens[1])
                    total = self._to_amount(numeric_tokens[2])
                    item = {
                        'product_name': self._clean_product_name(' '.join(pending_name_parts)),
                        'quantity': qty,
                        'unit_price': unit,
                        'total_price': total,
                    }
                    if self._is_valid_item(**item):
                        self._append_item_if_new(items, seen, item)
                    pending_name_parts = []
                    pending_qty = None
                    pending_unit_price = None
                    continue

                # Pattern: amount only line(s), combined with previous qty/unit context.
                if len(numeric_tokens) == 1 and re.match(r'^\s*[\$₹]?\s*\d+(?:[\.,]\d{1,2})\s*$', line):
                    amount = self._to_amount(numeric_tokens[0])

                    if pending_qty is not None and pending_unit_price is None:
                        pending_unit_price = amount
                        continue

                    if pending_qty is not None and pending_unit_price is not None:
                        item = {
                            'product_name': self._clean_product_name(' '.join(pending_name_parts)),
                            'quantity': pending_qty,
                            'unit_price': pending_unit_price,
                            'total_price': amount,
                        }
                        if self._is_valid_item(**item):
                            self._append_item_if_new(items, seen, item)
                        pending_name_parts = []
                        pending_qty = None
                        pending_unit_price = None
                        continue

                    # If quantity missing, infer from two amount lines.
                    if pending_qty is None and pending_unit_price is None:
                        pending_unit_price = amount
                        continue

                    if pending_qty is None and pending_unit_price is not None:
                        inferred_qty = int(round(amount / pending_unit_price)) if pending_unit_price > 0 else 1
                        inferred_qty = max(inferred_qty, 1)
                        item = {
                            'product_name': self._clean_product_name(' '.join(pending_name_parts)),
                            'quantity': inferred_qty,
                            'unit_price': pending_unit_price,
                            'total_price': amount,
                        }
                        if self._is_valid_item(**item):
                            self._append_item_if_new(items, seen, item)
                        pending_name_parts = []
                        pending_qty = None
                        pending_unit_price = None
                        continue

            if pending_name_parts and self._looks_like_price_line_without_qty(line):
                amounts = re.findall(r'\d+(?:\.\d{1,2})', line)
                if len(amounts) >= 2:
                    unit_price = self._to_amount(amounts[-2])
                    total_price = self._to_amount(amounts[-1])
                    quantity = int(round(total_price / unit_price)) if unit_price > 0 else 1
                    quantity = max(quantity, 1)
                    product_name = self._clean_product_name(' '.join(pending_name_parts))
                    item = {
                        'product_name': product_name,
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'total_price': total_price,
                    }
                    if self._is_valid_item(**item):
                        self._append_item_if_new(items, seen, item)
                pending_name_parts = []
                pending_qty = None
                pending_unit_price = None

        return items

    def _find_item_table_start(self, lines: List[str]) -> int:
        """Find the first line likely to be the beginning of the item table."""
        for index, line in enumerate(lines):
            line_lower = line.lower()
            if (
                ('qty' in line_lower or 'quantity' in line_lower)
                and ('description' in line_lower or 'item' in line_lower or 'particular' in line_lower)
                and ('amount' in line_lower or 'price' in line_lower or 'rate' in line_lower or 'value' in line_lower)
            ):
                return index + 1
        return 0

    def _is_table_end_line(self, line: str) -> bool:
        """Detect footer lines that usually appear after item rows."""
        line_lower = line.lower()
        end_keywords = [
            'subtotal', 'grand total', 'total', 'sales tax', 'tax',
            'terms', 'thank you', 'payment', 'balance due', 'for any inquiries'
        ]
        return any(keyword in line_lower for keyword in end_keywords)

    def _is_noise_line(self, line: str) -> bool:
        """Filter out non-item lines commonly found in headers and addresses."""
        line_lower = line.lower()

        noise_keywords = [
            'receipt', 'invoice', 'sold to', 'ship to', 'receipt #', 'p.o.#',
            'due date', 'invoice date', 'invoice number', 'date', 'logo',
            'phone', 'email', 'website', 'contact us', 'address', 'terms',
            'item description quantity unit price amount'
        ]
        if any(keyword in line_lower for keyword in noise_keywords):
            return True

        # Drop lines that look like addresses or IDs and not item rows
        if re.search(r'\b\d{5}\b', line) and not re.search(r'\d+\.\d{1,2}', line):
            return True

        # Item rows should contain alphabetic product text and at least one amount-like value.
        if not re.search(r'[A-Za-z]', line) and not re.search(r'\d+\.\d{1,2}', line):
            return True

        return False

    def _normalize_line(self, line: str) -> str:
        """Normalize OCR artifacts while preserving item semantics."""
        normalized = re.sub(r'\s+', ' ', (line or '').strip())
        normalized = normalized.replace('₹', '$')
        normalized = re.sub(r'\$\s+', '$', normalized)
        normalized = re.sub(r'(?<=\d),(?=\d{2}\b)', '.', normalized)
        return normalized

    def _to_amount(self, value: str) -> float:
        """Convert OCR numeric token into float amount."""
        cleaned = (value or '').replace('$', '').replace(',', '.').strip()
        return float(cleaned)

    def _extract_amount_tokens(self, line: str) -> List[str]:
        """Extract numeric amount-like tokens from a line."""
        return re.findall(r'\d+(?:[\.,]\d{1,2})?', line)

    def _parse_complete_item_line(self, line: str) -> Optional[Dict]:
        """Parse one-line item formats where all values exist in the same line."""
        retail_item = self._parse_tabular_retail_row(line)
        if retail_item:
            return retail_item

        match = self.item_row_pattern.match(line)
        if match:
            item = {
                'product_name': self._clean_product_name(match.group(2)),
                'quantity': int(match.group(1)),
                'unit_price': self._to_amount(match.group(3)),
                'total_price': self._to_amount(match.group(4)),
            }
            return item if self._is_valid_item(**item) else None

        match = self.item_row_name_first_pattern.match(line)
        if match:
            item = {
                'product_name': self._clean_product_name(match.group(1)),
                'quantity': int(match.group(2)),
                'unit_price': self._to_amount(match.group(3)),
                'total_price': self._to_amount(match.group(4)),
            }
            return item if self._is_valid_item(**item) else None

        match = self.item_row_single_amount_pattern.match(line)
        if match:
            quantity = int(match.group(1))
            total_price = self._to_amount(match.group(3))
            unit_price = total_price / quantity if quantity > 0 else total_price
            item = {
                'product_name': self._clean_product_name(match.group(2)),
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': total_price,
            }
            return item if self._is_valid_item(**item) else None

        match = self.inline_name_with_prices_pattern.match(line)
        if match:
            product_name = self._clean_product_name(match.group(1))
            unit_price = self._to_amount(match.group(2))
            total_price = self._to_amount(match.group(3))
            quantity = int(round(total_price / unit_price)) if unit_price > 0 else 1
            quantity = max(quantity, 1)
            item = {
                'product_name': product_name,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': total_price,
            }
            return item if self._is_valid_item(**item) else None

        return None

    def _parse_tabular_retail_row(self, line: str) -> Optional[Dict]:
        """Parse common Indian retail rows like '11 ITEM NAME 1 95.00 95.00'."""
        match = self.retail_row_with_mrp_pattern.match(line)
        if match:
            product_name = self._clean_product_name(match.group(2))
            quantity = int(match.group(3))
            mrp = self._to_amount(match.group(4))
            rate = self._to_amount(match.group(5))
            total = self._to_amount(match.group(6))
            unit_price = rate if rate > 0 else mrp

            item = {
                'product_name': product_name,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': total,
            }
            return item if self._is_valid_item(**item) else None

        match = self.retail_row_pattern.match(line)
        if match:
            product_name = self._clean_product_name(match.group(2))
            quantity = int(match.group(3))
            unit_price = self._to_amount(match.group(4))
            total = self._to_amount(match.group(5))
            item = {
                'product_name': product_name,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': total,
            }
            return item if self._is_valid_item(**item) else None

        match = self.retail_row_no_sr_pattern.match(line)
        if match:
            product_name = self._clean_product_name(match.group(1))
            quantity = int(match.group(2))
            unit_price = self._to_amount(match.group(3))
            total = self._to_amount(match.group(4))
            item = {
                'product_name': product_name,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': total,
            }
            return item if self._is_valid_item(**item) else None

        return None

    def _looks_like_product_text(self, line: str) -> bool:
        """Detect candidate product name/description lines."""
        line_lower = line.lower()
        if any(k in line_lower for k in ['subtotal', 'total', 'tax', 'invoice', 'receipt']):
            return False
        if re.search(r'\d+\.\d{1,2}', line):
            return False
        return bool(re.search(r'[A-Za-z]', line)) and len(line) >= 3

    def _looks_like_price_line_without_qty(self, line: str) -> bool:
        """Detect lines that contain two amounts but may miss explicit quantity token."""
        amounts = re.findall(r'\d+(?:\.\d{1,2})', line)
        if len(amounts) < 2:
            return False
        return not bool(re.search(r'[A-Za-z]{3,}', line))

    def _append_item_if_new(self, items: List[Dict], seen: set, item: Dict):
        """Append item only when it's not a duplicate OCR artifact."""
        key = (item['product_name'].lower(), item['quantity'], round(item['total_price'], 2))
        if key not in seen:
            seen.add(key)
            items.append(item)

    def _clean_product_name(self, product_name: str) -> str:
        """Normalize OCR product text into a clean inventory item name."""
        cleaned = re.sub(r'\s+', ' ', (product_name or '').strip())
        cleaned = re.sub(r'^[\-:;,]+', '', cleaned).strip()
        cleaned = re.sub(r'^\d{1,3}\s+', '', cleaned)
        cleaned = cleaned.replace('•', ' ')
        cleaned = re.sub(r'\b(qty|amount|price|unit)\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.replace('¢', '').replace('`', '').replace('|', ' ')
        cleaned = re.sub(r'[^A-Za-z0-9\s\-./()]+', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    def _is_valid_item(self, product_name: str, quantity: int, unit_price: float, total_price: float) -> bool:
        """Validate parsed item values before storing them."""
        if not product_name or len(product_name) < 2:
            return False
        # Prevent malformed OCR rows like "2 30.00 60.00" from using numeric token as name.
        if not re.search(r'[A-Za-z]', product_name):
            return False
        # Drop header-like rows that OCR mixes into table data.
        blocked_keywords = {'particulars', 'amount', 'value', 'qty', 'rate', 'total'}
        if product_name.strip().lower() in blocked_keywords:
            return False
        if quantity <= 0:
            return False
        if quantity > 250:
            return False
        if unit_price <= 0 or total_price <= 0:
            return False
        if len(product_name) > 120:
            return False
        return True
    
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

