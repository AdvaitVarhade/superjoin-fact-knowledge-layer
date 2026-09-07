import pytest
from src.normalization.numbers import parse_number, format_inr
from src.normalization.temporal import parse_period
from src.normalization.metrics import canonicalize_metric

def test_parse_number_indian_system():
    # Crores
    val, unit, curr = parse_number("₹ 500 Cr")
    assert val == 5000000000.0
    assert unit == "Cr"
    assert curr == "INR"

    # Lakhs
    val, unit, _ = parse_number("12.5 Lakhs")
    assert val == 1250000.0
    assert unit == "Lakhs"

    # Negative parenthesized
    val, unit, _ = parse_number("(15.4) Cr")
    assert val == -154000000.0

def test_parse_number_percentage_and_millions():
    val, unit, _ = parse_number("8.2%")
    assert val == 8.2
    assert unit == "%"

    val, unit, _ = parse_number("265 million")
    assert val == 265000000.0
    assert unit == "Million"

def test_parse_period():
    p1 = parse_period("FY24")
    assert p1.period_id == "FY24"
    assert p1.start_date == "2023-04-01"
    assert p1.end_date == "2024-03-31"

    p2 = parse_period("Q4 FY24")
    assert p2.period_id == "Q4_FY24"
    assert p2.start_date == "2024-01-01"
    assert p2.end_date == "2024-03-31"

    p3 = parse_period("2024-25")
    assert p3.period_id == "FY25"

def test_canonicalize_metric():
    m1 = canonicalize_metric("Revenue from Operations")
    assert m1.metric_id == "revenue"

    m2 = canonicalize_metric("Adjusted EBITDA")
    assert m2.metric_id == "ebitda"

    m3 = canonicalize_metric("Real GDP Growth")
    assert m3.metric_id == "gdp_growth"
