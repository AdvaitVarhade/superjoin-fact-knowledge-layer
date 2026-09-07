# src/extraction/extractor.py

- FactExtractor · class · L14-L402 — class FactExtractor:
- __init__ · method · L15-L16 — def __init__(self, default_entity_name: str = "Delhivery Limited"):
- infer_entity · method · L18-L49 — def infer_entity(self, text: str, doc_name: str) -> Entity:
- detect_page_scale · method · L51-L71 — def detect_page_scale(self, blocks: List[ParsedBlock]) -> Tuple[float, Optional[str]]:
- extract_from_document · method · L73-L92 — def extract_from_document(self, parsed_doc: ParsedDocument) -> List[Fact]:
- extract_table_facts · method · L94-L194 — def extract_table_facts(self, parsed_doc: ParsedDocument, entity: Entity) -> List[Fact]:
- extract_text_facts · method · L196-L402 — def extract_text_facts(self, parsed_doc: ParsedDocument, entity: Entity) -> List[Fact]:
