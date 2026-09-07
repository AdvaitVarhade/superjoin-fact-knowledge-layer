import os
import pytest
from src.ingestion.pdf_parser import PDFIngestor

def test_pdf_ingestion_sample():
    sample_pdf = 'starter-datasets/delhivery/03-delhivery-q4-fy24-earnings-presentation.pdf'
    if not os.path.exists(sample_pdf):
        pytest.skip('Sample PDF not found')

    ingestor = PDFIngestor()
    parsed_doc = ingestor.ingest_pdf(sample_pdf, max_pages=3)

    assert parsed_doc.document_id.startswith('03_delhivery')
    assert parsed_doc.total_pages == 27
    assert len(parsed_doc.blocks) > 0
    first_block = parsed_doc.blocks[0]
    assert len(first_block.bbox) == 4
    assert first_block.page_number >= 1
