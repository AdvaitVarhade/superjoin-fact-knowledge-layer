import os
import json
import glob
from typing import List, Dict, Any, Optional
from src.models.evidence import Evidence
from src.models.fact import Fact
from src.models.relationship import Relationship, RelationType
from src.models.case_study import CaseStudy
from src.ingestion.pdf_parser import PDFIngestor, ParsedDocument
from src.extraction.extractor import FactExtractor
from src.reconciliation.engine import ReconciliationEngine

import threading
from collections import defaultdict

class FactKnowledgeStore:
    def __init__(self):
        self._lock = threading.Lock()
        self.documents: Dict[str, ParsedDocument] = {}
        self.facts: Dict[str, Fact] = {}
        self.relationships: List[Relationship] = []
        self.case_studies: List[CaseStudy] = []
        # Inverted indexes for sub-millisecond filtering
        self._entity_index: Dict[str, set] = defaultdict(set)
        self._metric_index: Dict[str, set] = defaultdict(set)
        self._period_index: Dict[str, set] = defaultdict(set)
        self.ingestor = PDFIngestor()
        self.extractor = FactExtractor()
        self.reconciliation_engine = ReconciliationEngine()
        # Initialize canonical showcase case studies immediately
        self.recompute_relationships()

    def _index_fact(self, f: Fact):
        """Indexes a fact into the inverted hash maps for high-speed multi-attribute filtering."""
        fid = f.fact_id
        if f.entity_id:
            self._entity_index[f.entity_id.lower().strip()].add(fid)
        if f.metric_id:
            self._metric_index[f.metric_id.lower().strip()].add(fid)
        if f.period_id:
            p_clean = f.period_id.lower().replace(" ", "_").replace("-", "_").strip()
            self._period_index[p_clean].add(fid)

    def add_document(self, doc: ParsedDocument, facts: List[Fact]):
        self.documents[doc.document_id] = doc
        for f in facts:
            self.facts[f.fact_id] = f
            self._index_fact(f)

    def ingest_file(self, file_path: str, max_pages: Optional[int] = 20) -> List[Fact]:
        parsed_doc = self.ingestor.ingest_pdf(file_path, max_pages=max_pages)
        extracted_facts = self.extractor.extract_from_document(parsed_doc)
        self.add_document(parsed_doc, extracted_facts)
        self.recompute_relationships()
        return extracted_facts

    def recompute_relationships(self) -> List[Relationship]:
        all_facts = list(self.facts.values())
        self.relationships = self.reconciliation_engine.reconcile_facts(all_facts)
        self.case_studies = self.reconciliation_engine.generate_showcase_cases(all_facts, self.relationships)
        for cs in self.case_studies:
            if cs.source_fact and cs.source_fact.fact_id not in self.facts:
                self.facts[cs.source_fact.fact_id] = cs.source_fact
                self._index_fact(cs.source_fact)
            if cs.target_fact and cs.target_fact.fact_id not in self.facts:
                self.facts[cs.target_fact.fact_id] = cs.target_fact
                self._index_fact(cs.target_fact)
            if cs.relationship and cs.relationship not in self.relationships:
                self.relationships.append(cs.relationship)
        return self.relationships

    def get_case_studies(self, entity_id: Optional[str] = None) -> List[CaseStudy]:
        """Returns the 4 canonical reconciliation cases dynamically tailored for any entity or uploaded document."""
        all_facts = list(self.facts.values())
        return self.reconciliation_engine.generate_showcase_cases(all_facts, self.relationships, entity_id=entity_id)

    def get_all_facts(self) -> List[Fact]:
        return list(self.facts.values())

    def get_all_documents(self) -> List[Dict[str, Any]]:
        return [
            {
                "document_id": doc.document_id,
                "document_name": doc.document_name,
                "total_pages": doc.total_pages,
                "blocks_count": len(doc.blocks),
                "tables_count": len(doc.tables),
                "facts_count": sum(1 for f in self.facts.values() if any(e.document_id == doc.document_id for e in f.evidence))
            }
            for doc in self.documents.values()
        ]

    def search_facts(
        self,
        query: Optional[str] = None,
        entity_id: Optional[str] = None,
        metric_id: Optional[str] = None,
        period_id: Optional[str] = None
    ) -> List[Fact]:
        # Fast-path: If no filters applied, return all facts
        if not entity_id and not metric_id and not period_id and not query:
            return list(self.facts.values())

        candidate_ids: Optional[set] = None

        if entity_id:
            e_lower = entity_id.lower().strip()
            matched_ids = set()
            for key, fids in self._entity_index.items():
                if e_lower in key:
                    matched_ids.update(fids)
            candidate_ids = matched_ids if candidate_ids is None else candidate_ids.intersection(matched_ids)

        if metric_id:
            m_lower = metric_id.lower().strip()
            metric_aliases = {
                "revenue": ["revenue", "revenue_from_operations", "revenue_operations", "income"],
                "revenue_operations": ["revenue", "revenue_from_operations", "revenue_operations", "income"],
                "express_shipments": ["express_shipments", "express_parcel_volume", "volume", "shipments"],
                "express_parcel_volume": ["express_shipments", "express_parcel_volume", "volume", "shipments"],
                "ebitda": ["ebitda", "adjusted_ebitda"],
                "adjusted_ebitda": ["ebitda", "adjusted_ebitda"],
                "gdp": ["gdp", "gdp_growth", "real_gdp_growth", "real_gdp", "growth"],
                "gdp_growth": ["gdp", "gdp_growth", "real_gdp_growth", "real_gdp", "growth"],
                "inflation": ["inflation", "cpi", "cpi_inflation", "headline_inflation"],
                "cpi_inflation": ["inflation", "cpi", "cpi_inflation", "headline_inflation"],
                "pin_codes": ["pin_codes_covered", "pin_codes"]
            }
            target_aliases = metric_aliases.get(m_lower, [m_lower])
            matched_ids = set()
            for key, fids in self._metric_index.items():
                if any(alias in key or key in alias for alias in target_aliases):
                    matched_ids.update(fids)
            candidate_ids = matched_ids if candidate_ids is None else candidate_ids.intersection(matched_ids)

        if period_id:
            p_clean = period_id.lower().replace(" ", "_").replace("-", "_").strip()
            matched_ids = set()
            for key, fids in self._period_index.items():
                if (p_clean in key or key in p_clean or (p_clean.startswith("fy") and p_clean[2:] in key)):
                    matched_ids.update(fids)
            candidate_ids = matched_ids if candidate_ids is None else candidate_ids.intersection(matched_ids)

        if candidate_ids is not None:
            results = [self.facts[fid] for fid in candidate_ids if fid in self.facts]
        else:
            results = list(self.facts.values())

        if query:
            q_raw = query.lower().strip()
            q_clean = q_raw.replace(",", "").replace("₹", "").replace("$", "").replace("%", "").strip()
            filtered = []
            for f in results:
                raw_clean = f.raw_value.lower().replace(",", "").replace("₹", "").replace("$", "").replace("%", "").strip()
                norm_str = str(f.normalized_value or "")
                norm_cr = str(round((f.normalized_value or 0) / 1e7, 2)) if f.normalized_value else ""
                
                match = (
                    q_raw in f.metric_id.lower()
                    or q_raw in f.entity_id.lower()
                    or q_raw in f.period_id.lower()
                    or q_raw in (f.scope or "").lower()
                    or q_clean in raw_clean
                    or (q_clean and q_clean in norm_str)
                    or (q_clean and q_clean in norm_cr)
                    or any(q_raw in (ev.text_snippet or "").lower() for ev in f.evidence)
                )
                if match:
                    filtered.append(f)
            results = filtered

        return results

    def load_starter_datasets(self, base_dir: str = "."):
        """Pre-indexes available starter PDFs from starter-datasets/, uploads/, and downloaded-reports/."""
        with self._lock:
            patterns = [
                os.path.join(base_dir, "starter-datasets", "*", "*.pdf"),
                os.path.join(base_dir, "starter-datasets", "*.pdf"),
                os.path.join(base_dir, "uploads", "*.pdf"),
                os.path.join(base_dir, "downloaded-reports", "*.pdf"),
                os.path.join(base_dir, "downloaded-reports", "*", "*.pdf")
            ]
            seen_docs = set()
            for pattern in patterns:
                for pdf_file in glob.glob(pattern):
                    fname = os.path.basename(pdf_file)
                    if fname in seen_docs:
                        continue
                    seen_docs.add(fname)
                    try:
                        # Fast ingest for starter filings to ensure sub-second startup
                        max_p = 30
                        parsed_doc = self.ingestor.ingest_pdf(pdf_file, max_pages=max_p)
                        extracted_facts = self.extractor.extract_from_document(parsed_doc)
                        self.add_document(parsed_doc, extracted_facts)
                    except Exception as e:
                        print(f"Error loading {pdf_file}: {e}")

            # Recompute all cross-document links once
            self.recompute_relationships()
