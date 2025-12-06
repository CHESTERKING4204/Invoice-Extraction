"""
Utility functions for invoice processing
"""
import re
from datetime import datetime
from typing import Optional


def parse_date(date_str: Optional[str]) -> Optional[str]:
    """
    Parse various date formats to ISO format (YYYY-MM-DD)
    """
    if not date_str:
        return None
    
    date_str = date_str.strip()
    
    date_formats = [
        "%d.%m.%Y",  # German: 22.05.2024
        "%Y-%m-%d",  # ISO
        "%d/%m/%Y",  # European
        "%m/%d/%Y",  # US
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%B %d, %Y",
        "%d %B %Y",
    ]
    
    for fmt in date_formats:
        try:
            parsed = datetime.strptime(date_str, fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    return None


def extract_amount(text: str) -> Optional[float]:
    """
    Extract monetary amount from text
    Handles formats like: 1,234.56 or 1.234,56 or 1234.56
    """
    if not text:
        return None
    
    # Remove currency symbols and whitespace
    cleaned = re.sub(r'[€$£¥₹\s]', '', str(text))
    
    # Handle German format (1.234,56) - dot as thousand separator, comma as decimal
    if ',' in cleaned and '.' in cleaned:
        if cleaned.rindex(',') > cleaned.rindex('.'):
            # German format: 1.234,56
            cleaned = cleaned.replace('.', '').replace(',', '.')
        else:
            # US format: 1,234.56
            cleaned = cleaned.replace(',', '')
    elif ',' in cleaned:
        # Check if comma is decimal separator (German) or thousand separator
        parts = cleaned.split(',')
        if len(parts) == 2 and len(parts[1]) <= 2:
            # Decimal separator: 123,45
            cleaned = cleaned.replace(',', '.')
        else:
            # Thousand separator: 1,234
            cleaned = cleaned.replace(',', '')
    
    try:
        return float(cleaned)
    except ValueError:
        return None


def normalize_currency(currency: Optional[str]) -> Optional[str]:
    """
    Normalize currency code
    """
    if not currency:
        return None
    
    currency_map = {
        '€': 'EUR',
        '$': 'USD',
        '£': 'GBP',
        '¥': 'JPY',
        '₹': 'INR',
    }
    
    currency = currency.strip().upper()
    return currency_map.get(currency, currency)


def is_valid_currency(currency: Optional[str]) -> bool:
    """
    Check if currency is in known set
    """
    valid_currencies = {
        'EUR', 'USD', 'GBP', 'INR', 'JPY', 'CHF', 'CAD', 'AUD', 'CNY', 'SEK'
    }
    return currency in valid_currencies if currency else False


def calculate_tolerance_match(value1: Optional[float], value2: Optional[float], tolerance: float = 0.02) -> bool:
    """
    Check if two values match within tolerance
    """
    if value1 is None or value2 is None:
        return False
    return abs(value1 - value2) <= tolerance
