import os
import hashlib
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF
from pydantic import BaseModel, Field
from src.models.evidence import Evidence

class ParsedBlock(BaseModel):
    page_number: int
    bbox: List[float]  # [x0, y0, x1, y1]
    text: str
    is_table: bool = False

class ParsedTable(BaseModel):
    page_number: int
    bbox: List[float]
    headers: List[str]
    rows: List[List[str]]
    title: Optional[str] = None

class ParsedDocument(BaseModel):
    document_id: str
    document_name: str
    file_path: str
    total_pages: int
    blocks: List[ParsedBlock] = Field(default_factory=list)
    tables: List[ParsedTable] = Field(default_factory=list)

class PDFIngestor:
    def __init__(self):
        pass

    @staticmethod
    def generate_doc_id(file_path: str) -> str:
        basename = os.path.basename(file_path)
        return basename.replace(' ', '_').replace('-', '_').replace('.pdf', '')

    def ingest_pdf(self, file_path: str, max_pages: Optional[int] = None) -> ParsedDocument:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f'PDF not found at {file_path}')

        doc_name = os.path.basename(file_path)
        doc_id = self.generate_doc_id(file_path)
        
        doc = fitz.open(file_path)
        total_pages = len(doc)
        pages_to_process = min(total_pages, max_pages) if max_pages else total_pages

        blocks: List[ParsedBlock] = []
        tables: List[ParsedTable] = []

        for page_idx in range(pages_to_process):
            page_num = page_idx + 1
            page = doc[page_idx]

            # 1. Extract text blocks with coordinates
            raw_blocks = page.get_text('blocks')
            for b in raw_blocks:
                x0, y0, x1, y1, text, block_no, block_type = b
                cleaned_text = text.strip()
                if cleaned_text:
                    blocks.append(ParsedBlock(
                        page_number=page_num,
                        bbox=[round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)],
                        text=cleaned_text,
                        is_table=False
                    ))

            # 2. Extract tables via PyMuPDF native table finder if available
            try:
                table_finder = page.find_tables()
                for tab in table_finder.tables:
                    df = tab.extract()
                    if df and len(df) > 1:
                        headers = [str(c or '').strip() for c in df[0]]
                        rows = [[str(c or '').strip() for c in r] for r in df[1:]]\n                        tab_bbox = [round(c, 2) for c in tab.bbox]
                        tables.append(ParsedTable(
                            page_number=page_num,
                            bbox=tab_bbox,
                            headers=headers,
                            rows=rows
                        ))
            except Exception:
                pass

        doc.close()

        return ParsedDocument(
            document_id=doc_id,
            document_name=doc_name,
            file_path=file_path,
            total_pages=total_pages,
            blocks=blocks,
            tables=tables
        )
