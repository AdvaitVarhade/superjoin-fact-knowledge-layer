# src/ingestion/pdf_parser.py

- ParsedBlock · class · L8-L12 — class ParsedBlock(BaseModel):
- ParsedTable · class · L14-L19 — class ParsedTable(BaseModel):
- ParsedDocument · class · L21-L27 — class ParsedDocument(BaseModel):
- PDFIngestor · class · L29-L96 — class PDFIngestor:
- __init__ · method · L30-L31 — def __init__(self):
- generate_doc_id · method · L34-L36 — def generate_doc_id(file_path: str) -> str:
- ingest_pdf · method · L38-L96 — def ingest_pdf(self, file_path: str, max_pages: Optional[int] = None) -> ParsedDocument:
