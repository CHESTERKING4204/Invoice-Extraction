"""
PDF extraction module - extracts structured data from invoice/order PDFs
Supports German B2B documents (Bestellung/Rechnung)
"""
import pdfplumber
import re
from pathlib import Path
from typing import List, Optional
from .models import Invoice, LineItem
from .utils import parse_date, extract_amount


class InvoiceExtractor:
    """Extract structured invoice data from PDFs"""
    
    def extract_from_pdf(self, pdf_path: str) -> Invoice:
        """Extract invoice data from a single PDF"""
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
            
            # Extract fields based on German document format
            invoice_data = {
                "invoice_number": self._extract_order_number(full_text),
                "invoice_date": self._extract_date(full_text),
                "due_date": None,  # Not in these documents
                "seller_name": self._extract_seller_name(full_text),
                "seller_address": self._extract_seller_address(full_text),
                "seller_tax_id": self._extract_customer_number(full_text),
                "buyer_name": self._extract_buyer_name(full_text),
                "buyer_address": self._extract_buyer_address(full_text),
                "buyer_tax_id": self._extract_end_customer_number(full_text),
                "currency": "EUR",
                "net_total": self._extract_net_total(full_text),
                "tax_amount": self._extract_tax_amount(full_text),
                "gross_total": self._extract_gross_total(full_text),
                "payment_terms": self._extract_payment_terms(full_text),
                "external_reference": self._extract_external_reference(full_text),
            }
            
            # Extract line items
            line_items = self._extract_line_items(full_text)
            invoice_data["line_items"] = line_items
            
            return Invoice(**invoice_data)
    
    def extract_from_directory(self, pdf_dir: str) -> List[Invoice]:
        """Extract invoices from all PDFs in a directory"""
        pdf_path = Path(pdf_dir)
        invoices = []
        
        for pdf_file in sorted(pdf_path.glob("*.pdf")):
            try:
                invoice = self.extract_from_pdf(str(pdf_file))
                invoices.append(invoice)
            except Exception as e:
                print(f"Error processing {pdf_file}: {e}")
        
        return invoices
    
    def _extract_order_number(self, text: str) -> Optional[str]:
        """Extract order/invoice number (AUFNR...)"""
        patterns = [
            r"Bestellung\s+(AUFNR\d+)",
            r"(AUFNR\d+)",
            r"Rechnung\s*(?:Nr\.?|Number|#)?[:\s]*([A-Z0-9-]+)",
            r"Invoice\s*(?:No\.?|Number|#)?[:\s]*([A-Z0-9-]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract document date"""
        patterns = [
            r"vom\s+(\d{2}\.\d{2}\.\d{4})",
            r"Datum[:\s]*(\d{2}\.\d{2}\.\d{4})",
            r"Date[:\s]*(\d{2}[./-]\d{2}[./-]\d{4})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return parse_date(match.group(1))
        return None
    
    def _extract_seller_name(self, text: str) -> Optional[str]:
        """Extract seller/supplier name (first company in header)"""
        patterns = [
            r"^([A-Z][A-Za-z\s]+Corporation)",
            r"^([A-Z][A-Za-z\s]+GmbH)",
            r"Kundenanschrift\s*\n([^\n]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                return match.group(1).strip()
        
        # Fallback: get first line that looks like a company
        lines = text.split('\n')
        for line in lines[1:10]:
            if 'Corporation' in line or 'GmbH' in line or 'Unternehmen' in line:
                return line.strip()
        return None
    
    def _extract_seller_address(self, text: str) -> Optional[str]:
        """Extract seller address"""
        # Look for address after Kundenanschrift
        match = re.search(r"Kundenanschrift\s*\n[^\n]+\n([^\n]+(?:GmbH|AG|Ltd)?)\s*\n([^\n]+)", text)
        if match:
            return f"{match.group(1).strip()}, {match.group(2).strip()}"
        
        # Look for Industriestraße pattern
        match = re.search(r"Industriestraße\s+\d+[^\n]*\n([^\n]+)", text)
        if match:
            return f"Industriestraße, {match.group(1).strip()}"
        
        # Look for postal code + city + Deutschland
        match = re.search(r"(\d{5}\s+[A-Za-zäöüÄÖÜß]+)\s*\n?\s*Deutschland", text)
        if match:
            return match.group(1).strip()
        
        # Look for any address with postal code
        match = re.search(r"([A-Za-zäöüÄÖÜß\-]+(?:str\.|straße|weg|platz)[^\n]*\d{5}[^\n]+)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Fallback: look for city with postal code
        match = re.search(r"([A-Z]{2}\s+\d{5})", text)
        if match:
            return match.group(1).strip()
        
        return "Germany"  # Default fallback
    
    def _extract_buyer_name(self, text: str) -> Optional[str]:
        """Extract buyer name"""
        patterns = [
            r"Kundenanschrift\s*\n([^\n]+)",
            r"im Auftrag von\s+\d+\s*\n([^\n]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                if name and len(name) > 3:
                    return name
        return None
    
    def _extract_buyer_address(self, text: str) -> Optional[str]:
        """Extract buyer address"""
        match = re.search(r"·\s*([^·\n]+,\s*[A-Za-zäöüÄÖÜß\s]+,\s*[A-Z]{2}\s+\d+)", text)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_customer_number(self, text: str) -> Optional[str]:
        """Extract customer number"""
        match = re.search(r"Kundennummer\s*\n(\d+)", text)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_end_customer_number(self, text: str) -> Optional[str]:
        """Extract end customer number"""
        match = re.search(r"Endkundennummer\s*\n(\d+)", text)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_net_total(self, text: str) -> Optional[float]:
        """Extract net total (before tax)"""
        patterns = [
            r"Gesamtwert\s+EUR\s+([\d.,]+)",
            r"Netto[:\s]*([\d.,]+)",
            r"Subtotal[:\s]*([\d.,]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return extract_amount(match.group(1))
        return None
    
    def _extract_tax_amount(self, text: str) -> Optional[float]:
        """Extract tax amount (MwSt)"""
        patterns = [
            r"MwSt\.\s+[\d,]+%\s+EUR\s+([\d.,]+)",
            r"VAT[:\s]*([\d.,]+)",
            r"Tax[:\s]*([\d.,]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return extract_amount(match.group(1))
        return None
    
    def _extract_gross_total(self, text: str) -> Optional[float]:
        """Extract gross total (including tax)"""
        patterns = [
            r"Gesamtwert\s+inkl\.\s+MwSt\.\s+EUR\s+([\d.,]+)",
            r"Total\s+inkl[:\s]*([\d.,]+)",
            r"Brutto[:\s]*([\d.,]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return extract_amount(match.group(1))
        return None
    
    def _extract_payment_terms(self, text: str) -> Optional[str]:
        """Extract payment terms"""
        match = re.search(r"Zahlungsbedingungen\s*\n([^\n]+)", text)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_external_reference(self, text: str) -> Optional[str]:
        """Extract external reference (Auftrag number)"""
        match = re.search(r"im Auftrag von\s+(\d+)", text)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_line_items(self, text: str) -> List[LineItem]:
        """Extract line items from the document"""
        items = []
        
        # Pattern for line items: Pos number, description, quantity, unit, price
        pattern = r"(\d+)\s+([A-Za-zäöüÄÖÜß\s\-\'\"]+?)\s+(\d+)\s+VE\s+.*?([\d.,]+)\s*$"
        
        lines = text.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            # Look for position number at start
            pos_match = re.match(r"^(\d+)\s+(.+?)\s+(\d+)\s+VE", line)
            if pos_match:
                pos = pos_match.group(1)
                desc = pos_match.group(2).strip()
                qty = int(pos_match.group(3))
                
                # Find the price at end of line
                price_match = re.search(r"([\d.,]+)\s*$", line)
                if price_match:
                    total = extract_amount(price_match.group(1))
                    if total and qty > 0:
                        unit_price = total / qty
                        items.append(LineItem(
                            description=desc,
                            quantity=float(qty),
                            unit_price=unit_price,
                            line_total=total
                        ))
            i += 1
        
        return items
