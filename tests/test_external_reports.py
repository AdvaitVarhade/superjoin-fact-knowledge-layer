import os
import pytest
from src.ingestion.pdf_parser import PDFIngestor
from src.extraction.extractor import FactExtractor
from src.storage.store import FactKnowledgeStore
from src.normalization.numbers import parse_number

def get_report_path(filename: str) -> str:
    candidates = [
        os.path.join('downloaded-reports', filename),
        os.path.join('uploads', filename),
        os.path.join('..', 'downloaded-reports', filename),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0]

def test_apple_10k_extraction_and_provenance():
    apple_pdf = get_report_path('apple_10k_2024_excerpt.pdf')
    if not os.path.exists(apple_pdf):
        pytest.skip(f'Apple 10-K excerpt not found at {apple_pdf}')

    ingestor = PDFIngestor()
    doc = ingestor.ingest_pdf(apple_pdf, max_pages=15)
    assert doc is not None
    assert doc.total_pages >= 1

    extractor = FactExtractor()
    facts = extractor.extract_from_document(doc)
    assert len(facts) > 0, 'Expected facts extracted from Apple 10-K'

    rev_facts = [f for f in facts if f.entity_id == 'apple' and f.metric_id in ['revenue', 'net_sales']]
    assert len(rev_facts) > 0, 'Expected Apple revenue fact'
    top_rev = rev_facts[0]
    assert '391' in top_rev.raw_value or (top_rev.normalized_value is not None and top_rev.normalized_value >= 300_000)
    assert len(top_rev.evidence) > 0
    assert top_rev.evidence[0].page_number >= 1
    assert len(top_rev.evidence[0].bbox) == 4
    assert top_rev.evidence[0].confidence > 0.8

def test_tesla_shareholder_update_extraction_and_provenance():
    tesla_pdf = get_report_path('tesla_q4_2024_shareholder_update.pdf')
    if not os.path.exists(tesla_pdf):
        pytest.skip(f'Tesla Shareholder Update not found at {tesla_pdf}')

    ingestor = PDFIngestor()
    doc = ingestor.ingest_pdf(tesla_pdf, max_pages=15)
    assert doc is not None

    extractor = FactExtractor()
    facts = extractor.extract_from_document(doc)
    assert len(facts) > 0, 'Expected facts extracted from Tesla Shareholder Update'

    tesla_rev = [f for f in facts if f.entity_id == 'tesla' and f.metric_id in ['revenue', 'total_revenues']]
    assert len(tesla_rev) > 0, 'Expected Tesla total revenues fact'
    assert '97' in tesla_rev[0].raw_value or (tesla_rev[0].normalized_value is not None and tesla_rev[0].normalized_value >= 90_000)
    assert len(tesla_rev[0].evidence) > 0
    assert len(tesla_rev[0].evidence[0].bbox) == 4

def test_multi_company_knowledge_store_isolation_and_search():
    store = FactKnowledgeStore()
    store.load_starter_datasets()

    apple_pdf = get_report_path('apple_10k_2024_excerpt.pdf')
    if os.path.exists(apple_pdf):
        store.ingest_file(apple_pdf, max_pages=15)

    tesla_pdf = get_report_path('tesla_q4_2024_shareholder_update.pdf')
    if os.path.exists(tesla_pdf):
        store.ingest_file(tesla_pdf, max_pages=15)

    all_facts = store.get_all_facts()
    entities = {f.entity_id for f in all_facts}
    assert 'delhivery' in entities
    assert 'india_macro' in entities
    if os.path.exists(apple_pdf):
        assert 'apple' in entities
        apple_search = store.search_facts(entity_id='apple')
        assert len(apple_search) > 0
        assert all(f.entity_id == 'apple' for f in apple_search)
    if os.path.exists(tesla_pdf):
        assert 'tesla' in entities
        tesla_search = store.search_facts(entity_id='tesla')
        assert len(tesla_search) > 0
        assert all(f.entity_id == 'tesla' for f in tesla_search)

def test_international_number_and_scale_normalization():
    # US Millions format
    val_us_m, unit_us_m, curr_us_m = parse_number("$391,035 Million")
    assert val_us_m == 391035000000.0
    assert unit_us_m == 'Million'
    assert curr_us_m == 'USD'

    # US Billions format
    val_us_b, unit_us_b, curr_us_b = parse_number("$97.7 Billion")
    assert val_us_b == 97700000000.0
    assert unit_us_b == 'Billion'
    assert curr_us_b == 'USD'

    # Indian Crores format
    val_in_cr, unit_in_cr, curr_in_cr = parse_number('₹8,141 Cr')
    assert val_in_cr == 81410000000.0
    assert unit_in_cr == 'Cr'
    assert curr_in_cr == 'INR'

    # Percentage format
    val_pct, unit_pct, curr_pct = parse_number('5.4%')
    assert val_pct == 5.4
    assert unit_pct == '%'
