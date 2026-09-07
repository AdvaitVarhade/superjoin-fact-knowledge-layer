# src/storage/store.py

- FactKnowledgeStore · class · L13-L156 — class FactKnowledgeStore:
- __init__ · method · L14-L21 — def __init__(self):
- add_document · method · L23-L26 — def add_document(self, doc: ParsedDocument, facts: List[Fact]):
- ingest_file · method · L28-L33 — def ingest_file(self, file_path: str, max_pages: Optional[int] = 20) -> List[Fact]:
- recompute_relationships · method · L35-L46 — def recompute_relationships(self) -> List[Relationship]:
- get_all_facts · method · L48-L49 — def get_all_facts(self) -> List[Fact]:
- get_all_documents · method · L51-L62 — def get_all_documents(self) -> List[Dict[str, Any]]:
- search_facts · method · L64-L130 — def search_facts(
- load_starter_datasets · method · L132-L156 — def load_starter_datasets(self, base_dir: str = "."):
