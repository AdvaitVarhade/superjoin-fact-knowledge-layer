import os
import re
from typing import List, Dict, Any, Optional, Tuple
from src.models.evidence import Evidence
from src.models.fact import Fact
from src.models.entity import Entity
from src.models.metric import Metric
from src.models.period import Period
from src.ingestion.pdf_parser import ParsedDocument, ParsedBlock, ParsedTable
from src.normalization.numbers import parse_number
from src.normalization.temporal import parse_period
from src.normalization.metrics import canonicalize_metric

class FactExtractor:
    def __init__(self, default_entity_name: str = "Delhivery Limited"):
        self.default_entity_name = default_entity_name

    def infer_entity(self, text: str, doc_name: str) -> Entity:
        text_lower = (doc_name + " " + text[:1000]).lower()
        
        known_entities = [
            ("apple", "apple", "Apple Inc."),
            ("tesla", "tesla", "Tesla, Inc."),
            ("alphabet", "alphabet", "Alphabet Inc."),
            ("google", "alphabet", "Alphabet Inc."),
            ("microsoft", "microsoft", "Microsoft Corporation"),
            ("nvidia", "nvidia", "NVIDIA Corporation"),
            ("amazon", "amazon", "Amazon.com, Inc."),
            ("infosys", "infosys", "Infosys Limited"),
            ("tcs", "tcs", "Tata Consultancy Services"),
            ("wipro", "wipro", "Wipro Limited"),
            ("zomato", "zomato", "Zomato Limited"),
            ("tata motors", "tata_motors", "Tata Motors Limited"),
            ("tatamotors", "tata_motors", "Tata Motors Limited"),
            ("reliance", "reliance", "Reliance Industries Limited"),
            ("hdfc", "hdfc_bank", "HDFC Bank Limited"),
            ("delhivery", "delhivery", "Delhivery Limited"),
            ("economic-survey", "india_macro", "Indian Macroeconomy"),
            ("economic survey", "india_macro", "Indian Macroeconomy"),
            ("rbi", "india_macro", "Indian Macroeconomy"),
            ("imf", "india_macro", "Indian Macroeconomy")
        ]
        
        for key, eid, name in known_entities:
            if key in text_lower:
                return Entity(entity_id=eid, name=name, entity_type="Economy" if eid == "india_macro" else "Company")
        
        clean_id = os.path.splitext(doc_name)[0].split('_')[0].split('-')[0].lower()
        return Entity(entity_id=clean_id, name=clean_id.title(), entity_type="Company")

    def detect_page_scale(self, blocks: List[ParsedBlock]) -> Tuple[float, Optional[str]]:
        multiplier = 1.0
        currency = None
        for b in blocks:
            t = b.text.lower()
            if "in millions" in t or "(in millions" in t or "millions of" in t:
                multiplier = 1e6
            elif "in thousands" in t or "(in thousands" in t:
                multiplier = 1e3
            elif "in crores" in t or "in crore" in t or "rs. in crore" in t:
                multiplier = 1e7
            elif "in lakhs" in t or "in lakh" in t:
                multiplier = 1e5
            
            if "$" in t or re.search(r'\busd\b|\bdollars?\b', t):
                currency = "USD"
            elif "₹" in t or re.search(r'\b(?:rs\.?|inr|rupees?)\b', t):
                currency = "INR"
            elif "€" in t or re.search(r'\beur\b|\beuros?\b', t):
                currency = "EUR"
        return multiplier, currency

    def extract_from_document(self, parsed_doc: ParsedDocument) -> List[Fact]:
        facts: List[Fact] = []
        sample_text = " ".join(b.text for b in parsed_doc.blocks[:10])
        entity = self.infer_entity(sample_text, parsed_doc.document_name)

        table_facts = self.extract_table_facts(parsed_doc, entity)
        facts.extend(table_facts)

        text_facts = self.extract_text_facts(parsed_doc, entity)
        facts.extend(text_facts)

        unique_facts: Dict[str, Fact] = {}
        for f in facts:
            key = f"{f.entity_id}_{f.metric_id}_{f.period_id}_{round(f.normalized_value, 2)}_{f.scope}"
            if key not in unique_facts:
                unique_facts[key] = f
            else:
                unique_facts[key].evidence.extend(f.evidence)

        return list(unique_facts.values())

    def extract_table_facts(self, parsed_doc: ParsedDocument, entity: Entity) -> List[Fact]:
        facts: List[Fact] = []
        for tab in parsed_doc.tables:
            if not tab.rows and not tab.headers:
                continue

            p_blocks = [b for b in parsed_doc.blocks if b.page_number == tab.page_number]
            page_mult, page_curr = self.detect_page_scale(p_blocks)

            period_cols: Dict[int, Period] = {}
            for col_idx, h in enumerate(tab.headers):
                if any(k in h.lower() for k in ["fy", "202", "q1", "q2", "q3", "q4", "quarter", "year", "september", "december", "march", "june"]):
                    period_cols[col_idx] = parse_period(h)

            all_rows = list(tab.rows)

            # If headers contained data (common in borderless tables) or had no periods, search row 0 and preceding blocks
            if not period_cols:
                if tab.rows and any(any(k in cell.lower() for k in ["202", "fy", "q1", "q2", "q3", "q4", "september", "ended"]) for cell in tab.rows[0]):
                    for col_idx, cell in enumerate(tab.rows[0]):
                        if any(k in cell.lower() for k in ["202", "fy", "q1", "q2", "q3", "q4", "september", "ended"]):
                            period_cols[col_idx] = parse_period(cell)
                    all_rows = tab.rows[1:]
                else:
                    header_candidates = []
                    for b in p_blocks:
                        if b.bbox[3] <= tab.bbox[1] + 60 and any(k in b.text.lower() for k in ["2024", "2023", "2022", "ended"]):
                            header_candidates.append(b.text.strip())

                    num_cols = [c_idx for c_idx, cell in enumerate(tab.headers) if parse_number(cell)[0] is not None]
                    if not num_cols and tab.rows:
                        num_cols = [c_idx for c_idx, cell in enumerate(tab.rows[0]) if parse_number(cell)[0] is not None]

                    if num_cols and header_candidates:
                        date_matches = []
                        for hc in header_candidates:
                            for dm in re.finditer(r'(?:(?:three|twelve)\s+months\s+ended\s+)?(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+20\d{2}|\b20\d{2}\b', hc, re.IGNORECASE):
                                date_matches.append(dm.group(0))

                        for idx, c_idx in enumerate(num_cols):
                            if idx < len(date_matches):
                                period_cols[c_idx] = parse_period(date_matches[idx])
                            else:
                                period_cols[c_idx] = parse_period(f"FY24" if idx % 2 == 0 else "FY23")

                    if len(tab.headers) > 1 and parse_number(tab.headers[1])[0] is not None:
                        all_rows = [tab.headers] + all_rows

            if not period_cols:
                continue

            for row in all_rows:
                if not row or len(row) < 2:
                    continue
                row_label = row[0].strip()
                if not row_label or len(row_label) < 2:
                    continue

                canonical_metric = canonicalize_metric(row_label)
                scope = "Standalone" if "standalone" in row_label.lower() else "Consolidated"

                for col_idx, period in period_cols.items():
                    if col_idx >= len(row):
                        continue
                    cell_val = row[col_idx].strip()
                    if not cell_val or cell_val in ["-", "—", "NA", "N/A", ""]:
                        continue

                    norm_val, unit, curr = parse_number(cell_val, default_multiplier=page_mult, default_currency=page_curr)
                    if norm_val is None:
                        continue

                    header_label = tab.headers[col_idx] if col_idx < len(tab.headers) else f"Col_{col_idx}"
                    ev_id = f"ev_{parsed_doc.document_id}_p{tab.page_number}_tab_{len(facts)}"
                    evidence = Evidence(
                        evidence_id=ev_id,
                        document_id=parsed_doc.document_id,
                        document_name=parsed_doc.document_name,
                        page_number=tab.page_number,
                        bbox=tab.bbox,
                        text_snippet=f"Table Row: {row_label} | Column: {header_label} -> {cell_val}",
                        extraction_method="table_structure",
                        confidence=0.95
                    )

                    fact_id = f"fact_{parsed_doc.document_id}_{tab.page_number}_{len(facts)}"
                    facts.append(Fact(
                        fact_id=fact_id,
                        entity_id=entity.entity_id,
                        metric_id=canonical_metric.metric_id,
                        period_id=period.period_id,
                        raw_value=cell_val,
                        normalized_value=norm_val,
                        unit=unit or canonical_metric.default_unit,
                        scope=scope,
                        confidence=0.95,
                        evidence=[evidence],
                        metadata={"row_label": row_label, "header": header_label}
                    ))

        return facts

    def extract_text_facts(self, parsed_doc: ParsedDocument, entity: Entity) -> List[Fact]:
        facts: List[Fact] = []
        for block in parsed_doc.blocks:
            text = block.text
            
            # Revenue statements (supports ₹ Cr, ₹ Mn, ₹ Million, Rs.)
            if "revenue" in text.lower() and any(u in text.lower() for u in ["cr", "crore", "mn", "million", "₹", "rs"]):
                # Case A: Crores
                rev_matches_cr = re.finditer(r'(?:₹|rs\.?)\s*([\d\,]+(?:\.\d+)?)\s*(?:cr|crore)', text, re.IGNORECASE)
                for m in rev_matches_cr:
                    val_str = m.group(1).replace(",", "")
                    norm_val, unit, _ = parse_number(f"₹ {val_str} Cr")
                    if norm_val and norm_val > 1e6:
                        period_str = "FY24" if "fy24" in text.lower() or "2024" in text else "FY23"
                        period = parse_period(period_str)
                        ev = Evidence(
                            evidence_id=f"ev_{parsed_doc.document_id}_p{block.page_number}_txt_{len(facts)}",
                            document_id=parsed_doc.document_id,
                            document_name=parsed_doc.document_name,
                            page_number=block.page_number,
                            bbox=block.bbox,
                            text_snippet=text[:250],
                            extraction_method="narrative_text",
                            confidence=0.95
                        )
                        facts.append(Fact(
                            fact_id=f"fact_{parsed_doc.document_id}_{block.page_number}_{len(facts)}",
                            entity_id=entity.entity_id,
                            metric_id="revenue",
                            period_id=period.period_id,
                            raw_value=f"₹{m.group(1)} Cr",
                            normalized_value=norm_val,
                            unit="Cr",
                            scope="Consolidated",
                            confidence=0.95,
                            evidence=[ev]
                        ))
                
                # Case B: Millions (e.g. ₹81,415Mn or ₹81,415 Million)
                rev_matches_mn = re.finditer(r'(?:₹|rs\.?)\s*([\d\,]+(?:\.\d+)?)\s*(?:mn|million)', text, re.IGNORECASE)
                for m in rev_matches_mn:
                    val_str = m.group(1).replace(",", "")
                    try:
                        val_mn = float(val_str)
                        if val_mn > 1000:  # In millions, e.g. 81,415 Mn = 8,141.5 Cr
                            val_cr = round(val_mn / 10.0, 1)
                            norm_val = val_mn * 1e6
                            period_str = "FY24" if "fy24" in text.lower() or "2024" in text else "FY23"
                            period = parse_period(period_str)
                            ev = Evidence(
                                evidence_id=f"ev_{parsed_doc.document_id}_p{block.page_number}_txt_{len(facts)}",
                                document_id=parsed_doc.document_id,
                                document_name=parsed_doc.document_name,
                                page_number=block.page_number,
                                bbox=block.bbox,
                                text_snippet=text[:250],
                                extraction_method="narrative_text",
                                confidence=0.95
                            )
                            facts.append(Fact(
                                fact_id=f"fact_{parsed_doc.document_id}_{block.page_number}_{len(facts)}",
                                entity_id=entity.entity_id,
                                metric_id="revenue",
                                period_id=period.period_id,
                                raw_value=f"₹{val_cr:,.0f} Cr (₹{m.group(1)} Mn)",
                                normalized_value=norm_val,
                                unit="Cr",
                                scope="Consolidated",
                                confidence=0.95,
                                evidence=[ev]
                            ))
                    except ValueError:
                        pass

            # Shipments volume (supports Mn, Million, packages)
            if any(k in text.lower() for k in ["parcel", "shipment", "express", "package"]) and any(u in text.lower() for u in ["mn", "million", "cr"]):
                m = re.search(r'(\d+[\,\.]?\d*)\s*(?:mn|million)\b', text, re.IGNORECASE)
                if m:
                    val_str = m.group(1).replace(",", "")
                    try:
                        val_f = float(val_str)
                        if 50 <= val_f <= 2000:  # typical parcel volumes in millions (e.g. 740Mn)
                            period_str = "FY24" if "fy24" in text.lower() or "2024" in text else "FY23"
                            period = parse_period(period_str)
                            norm_val = val_f * 1e6
                            ev = Evidence(
                                evidence_id=f"ev_{parsed_doc.document_id}_p{block.page_number}_shp_{len(facts)}",
                                document_id=parsed_doc.document_id,
                                document_name=parsed_doc.document_name,
                                page_number=block.page_number,
                                bbox=block.bbox,
                                text_snippet=text[:250],
                                extraction_method="narrative_text",
                                confidence=0.95
                            )
                            facts.append(Fact(
                                fact_id=f"fact_{parsed_doc.document_id}_{block.page_number}_{len(facts)}",
                                entity_id=entity.entity_id,
                                metric_id="express_shipments",
                                period_id=period.period_id,
                                raw_value=f"{int(val_f)} Million Packages",
                                normalized_value=norm_val,
                                unit="Million Packages",
                                scope="Consolidated",
                                confidence=0.95,
                                evidence=[ev]
                            ))
                    except ValueError:
                        pass

            # PIN codes
            if "pin" in text.lower() and "code" in text.lower():
                m = re.search(r'(\d{2,3}[\,\.]?\d{3})\s*(?:pin\s*codes|active\s*pin\s*codes)', text, re.IGNORECASE)
                if m:
                    num_str = m.group(1).replace(",", "").replace(".", "")
                    try:
                        val = float(num_str)
                        if 10000 <= val <= 30000:
                            period_str = "FY24" if "2024" in text or "fy24" in text.lower() else "FY22"
                            period = parse_period(period_str)
                            ev = Evidence(
                                evidence_id=f"ev_{parsed_doc.document_id}_p{block.page_number}_pin_{len(facts)}",
                                document_id=parsed_doc.document_id,
                                document_name=parsed_doc.document_name,
                                page_number=block.page_number,
                                bbox=block.bbox,
                                text_snippet=text[:250],
                                extraction_method="narrative_text",
                                confidence=0.95
                            )
                            facts.append(Fact(
                                fact_id=f"fact_{parsed_doc.document_id}_{block.page_number}_{len(facts)}",
                                entity_id=entity.entity_id,
                                metric_id="pin_codes_covered",
                                period_id=period.period_id,
                                raw_value=str(int(val)),
                                normalized_value=val,
                                unit="Count",
                                scope="Consolidated",
                                confidence=0.95,
                                evidence=[ev]
                            ))
                    except ValueError:
                        pass

            # Macro Inflation & GDP Statements
            if "inflation" in text.lower() and ("%" in text or "percent" in text.lower()):
                m = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
                if m:
                    val = float(m.group(1))
                    if 2.0 <= val <= 12.0:
                        period_str = "FY25" if "2024-25" in text or "2025" in text else "FY24"
                        period = parse_period(period_str)
                        ev = Evidence(
                            evidence_id=f"ev_{parsed_doc.document_id}_p{block.page_number}_inf_{len(facts)}",
                            document_id=parsed_doc.document_id,
                            document_name=parsed_doc.document_name,
                            page_number=block.page_number,
                            bbox=block.bbox,
                            text_snippet=text[:250],
                            extraction_method="narrative_text",
                            confidence=0.88
                        )
                        facts.append(Fact(
                            fact_id=f"fact_{parsed_doc.document_id}_{block.page_number}_{len(facts)}",
                            entity_id="india_macro",
                            metric_id="cpi_inflation",
                            period_id=period.period_id,
                            raw_value=f"{val}%",
                            normalized_value=val,
                            unit="%",
                            scope="Headline",
                            confidence=0.88,
                            evidence=[ev]
                        ))

            if "gdp" in text.lower() and ("growth" in text.lower() or "percent" in text.lower() or "%" in text):
                m = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
                if m:
                    val = float(m.group(1))
                    if 4.0 <= val <= 10.0:
                        period_str = "FY25" if "2024-25" in text or "2025" in text else "FY24"
                        period = parse_period(period_str)
                        ev = Evidence(
                            evidence_id=f"ev_{parsed_doc.document_id}_p{block.page_number}_gdp_{len(facts)}",
                            document_id=parsed_doc.document_id,
                            document_name=parsed_doc.document_name,
                            page_number=block.page_number,
                            bbox=block.bbox,
                            text_snippet=text[:250],
                            extraction_method="narrative_text",
                            confidence=0.90
                        )
                        facts.append(Fact(
                            fact_id=f"fact_{parsed_doc.document_id}_{block.page_number}_{len(facts)}",
                            entity_id="india_macro",
                            metric_id="gdp_growth",
                            period_id=period.period_id,
                            raw_value=f"{val}%",
                            normalized_value=val,
                            unit="%",
                            scope="Headline",
                            confidence=0.90,
                            evidence=[ev]
                        ))

        return facts
