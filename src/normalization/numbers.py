import re
from typing import Tuple, Optional

CURRENCY_PATTERNS = {
    'INR': [r'₹', r'rs\.?', r'inr', r'rupees?'],
    'USD': [r'\$', r'usd', r'dollars?'],
    'EUR': [r'€', r'eur', r'euros?'],
}

MULTIPLIERS = {
    'lakh': 1e5,
    'lakhs': 1e5,
    'lac': 1e5,
    'lacs': 1e5,
    'cr': 1e7,
    'crore': 1e7,
    'crores': 1e7,
    'k': 1e3,
    'thousand': 1e3,
    'thousands': 1e3,
    'm': 1e6,
    'mn': 1e6,
    'million': 1e6,
    'millions': 1e6,
    'b': 1e9,
    'bn': 1e9,
    'billion': 1e9,
    'billions': 1e9,
    't': 1e12,
    'tn': 1e12,
    'trillion': 1e12,
    'trillions': 1e12,
}

def clean_number_string(text: str) -> str:
    cleaned = text.strip().replace(',', '')
    paren_match = re.match(r'^\s*\(([\d\.]+)\)\s*$', cleaned)
    if paren_match:
        cleaned = f'-{paren_match.group(1)}'
    return cleaned

def extract_currency(text: str) -> Optional[str]:
    text_lower = text.lower()
    for curr, patterns in CURRENCY_PATTERNS.items():
        for p in patterns:
            if re.search(r'\b' + p + r'\b', text_lower) or (p in ['₹', r'\$', '€'] and re.search(p, text_lower)):
                return curr
    return None

def parse_number(
    text: str,
    default_multiplier: float = 1.0,
    default_currency: Optional[str] = None
) -> Tuple[Optional[float], Optional[str], Optional[str]]:
    if not text:
        return None, None, None
    
    raw = text.strip()
    currency = extract_currency(raw) or default_currency
    
    if '%' in raw:
        m = re.search(r'([-\+]?\d+(?:\.\d+)?)\s*%', raw)
        if m:
            val = float(m.group(1))
            return val, '%', None
            
    if 'bps' in raw.lower():
        m = re.search(r'([-\+]?\d+(?:\.\d+)?)\s*bps', raw, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            return val, 'bps', None

    multiplier_val = default_multiplier
    detected_unit = None
    
    for word, mult in MULTIPLIERS.items():
        if re.search(r'(?:\b|(?<=\d))' + word + r'\b', raw, re.IGNORECASE):
            multiplier_val = mult
            detected_unit = word.capitalize()
            break

    num_match = re.search(r'(\((?:[\d\.\,]+)\)|[-\+]?[\d\,]+(?:\.\d+)?)', raw)
    if not num_match:
        return None, detected_unit, currency
        
    num_str = clean_number_string(num_match.group(1))
    try:
        base_num = float(num_str)
        normalized = base_num * multiplier_val
        unit_label = detected_unit or ('USD' if currency == 'USD' else ('INR' if currency == 'INR' else ('Million' if default_multiplier == 1e6 else 'units')))
        return normalized, unit_label, currency
    except ValueError:
        return None, detected_unit, currency

def format_inr(value: float) -> str:
    abs_val = abs(value)
    sign = '-' if value < 0 else ''
    if abs_val >= 1e7:
        return f'{sign}₹{abs_val / 1e7:.2f} Cr'
    elif abs_val >= 1e5:
        return f'{sign}₹{abs_val / 1e5:.2f} Lakh'
    elif abs_val >= 1e3:
        return f'{sign}₹{abs_val:,.0f}'
    else:
        return f'{sign}₹{abs_val:.2f}'
