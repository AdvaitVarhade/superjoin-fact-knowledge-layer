import os
import pytest
from src.ingestion.pdf_parser import PDFIngestor
from src.extraction.extractor import FactExtractor

def test_fact_extraction_sample():
    sample_pdf = "starter-datasets/delhivery/03-delhivery-q4-fy24-earnings-presentation.pdf"
    if not os.path.exists(sample_pdf):
        pytest.skip("Sample PDF not found")

    ingestor = PDFIngestor()
    parsed_doc = ingestor.ingest_pdf(sample_pdf, max_pages=10)

    extractor = FactExtractor()
    facts = extractor.extract_from_document(parsed_doc)

    assert len(facts) > 0
    # Check that each fact has valid provenance evidence
    for f in facts:
        assert f.entity_id is not None
        assert f.metric_id is not None
        assert f.period_id is not None
        assert f.normalized_value is not None
        assert len(f.evidence) > 0
        assert f.evidence[0].page_number >= 1
        assert len(f.evidence[0].bbox) == 4
