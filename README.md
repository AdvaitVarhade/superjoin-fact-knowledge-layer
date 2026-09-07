# Superjoin Fact Knowledge Layer

An evidence-first **Fact Knowledge Layer** that ingests PDF documents, extracts grounded numerical and semantic facts with exact bounding boxes, normalizes units/temporal ranges/metric synonyms, and reconciles facts across documents to detect:
1. **Corroborations** (facts corroborated across documents, even if expressed differently)
2. **Genuine Contradictions** (unreconciled conflicting estimates/figures across publishers)
3. **Context-Reconciled Contradictions** (discrepancies explained by scope, temporal restatement, or units)
4. **Handled Extraction/Reasoning Edge Cases** (accounting bracket losses, multi-year fiscal ranges)

---

## 1. Setup and Run Instructions

### Prerequisites
- Python 3.10+
- Virtual environment (optional, but recommended)

### Quickstart
1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd "Super Join"
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *(Core requirements: `fastapi`, `uvicorn`, `pymupdf`, `pydantic`, `pytest`)*

3. Run the interactive server:
   ```bash
   uvicorn src.api.main:app --reload --port 8000
   ```

4. Open the Web Dashboard:
   - Navigate to `http://localhost:8000` for the interactive dashboard.
   - Interactive API Swagger docs available at `http://localhost:8000/docs`.

5. Run Automated Tests:
   ```bash
   pytest -q
   ```

---

## 2. Video Demo
- **Demo Link**: `[Video Demo Link (<= 3 mins)]` (e.g. YouTube / Loom)
- **Demonstration Coverage**:
  - Live PDF processing & fact extraction with bounding box evidence provenance.
  - Interactive walkthrough of the 4 required cases (Corroboration, Contradiction, Scope/Temporal Reconciliation, Edge-case mitigation).
  - Dynamic file upload and real-time reconciliation.

---

## 3. Approach & Architecture

```
PDF Ingestion (PyMuPDF) ➔ Layout & BBox Parsing ➔ Normalization (Numbers, Fiscal Dates, Metrics)
       ➔ Grounded Fact Extractor ➔ Cross-Document Reconciliation Engine ➔ FastAPI & OpenDesign UI
```

### Key Architectural Decisions:
1. **Evidence-First Grounding**: Every fact retains strict provenance: `document_id`, `document_name`, `page_number`, `bbox [x0, y0, x1, y1]`, `text_snippet`, and `extraction_method`.
2. **Deterministic Normalization Layer (`src/normalization/`)**:
   - **Indian & International Scale Parsing**: Translates `₹ 500 Cr`, `12.5 Lakhs`, `265 million`, `8.2%`, and accounting parentheses `(15.4) Cr` to base numeric values.
   - **Temporal Engine**: Standardizes fiscal quarters (`Q4 FY24`), fiscal years (`FY2023-24`), and multi-year ranges (`2024-25`) to ISO date spans (`start_date`, `end_date`).
   - **Metric Canonicalization**: Maps synonyms (`Revenue from Operations`, `Net Revenue`, `Turnover`) to canonical metric IDs.
3. **Cross-Document Reconciliation Engine (`src/reconciliation/`)**:
   - Computes normalized variance $\Delta\% = |v_1 - v_2| / \max(|v_1|, |v_2|)$.
   - Classifies cross-document relationships:
     - `CORROBORATION`: $\Delta\% \le 1.0\%$ across independent documents.
     - `CONTRADICTION`: Same metric & period with $\Delta\% > 1.0\%$ without scope qualification.
     - `RECONCILED_SCOPE` & `RECONCILED_TEMPORAL`: Discrepancies explained by Standalone vs Consolidated scope or differing fiscal periods.
4. **Graft Repository Memory**: Indexed with Graft (`graft build`) for token-efficient development and blast-radius reasoning.

---

## 4. Demonstration of the Four Required Cases

### Case 1: Corroboration Across Documents
- **Fact**: Delhivery FY24 Consolidated Revenue reported at **₹8,141 Cr** and Express Parcel Volume at **740 Million Packages**.
- **Source A**: `02-delhivery-annual-report-fy24-excerpt.pdf` (Page 6, Consolidated P&L)
- **Source B**: `03-delhivery-q4-fy24-earnings-presentation.pdf` (Slide 4, FY24 Key Metrics)
- **System Reasoning**: Identical normalized values with 0.00% variance across distinct disclosure formats.

### Case 2: Genuine Contradiction
- **Fact**: Conflicting FY25 headline CPI inflation baseline projections.
- **Source A**: `01-india-economic-survey-2024-25-excerpt.pdf` (Headline CPI projection 4.5%)
- **Source B**: `03-imf-india-2025-article-iv-excerpt.pdf` (Staff baseline estimate 4.8%)
- **System Reasoning**: Unreconciled 30 bps institutional divergence for the same fiscal period without revision notes.

### Case 3: Apparent Contradiction Reconciled by Context
- **Fact**: Delhivery FY24 revenue appears as **₹7,542 Cr** vs **₹8,141 Cr**.
- **Context**: Standalone reporting (excluding subsidiaries like Spoton Logistics and Delhivery USA) vs Consolidated accounts.
- **System Reasoning**: Discrepancy fully reconciled by Entity Scope metadata (`Standalone` vs `Consolidated`).

### Case 4: Handled Extraction / Reasoning Edge Case
- **Challenge**: Naive regex/OCR parses accounting loss in parentheses `(15.4) Cr` as positive `+15.4 Cr` and conflates `2024-25` with single year 2024.
- **Handling**: `src/normalization/numbers.py` automatically converts bracketed accounting notation to negative integers (`-154,000,000 INR`), preventing inverted margin calculations.

---

## 5. Limitations and Next Steps
- **Vision Chart-to-Table Model Integration**: Integrate Docling / PP-Chart2Table for scanned image charts.
- **Dynamic Incremental Graph Sync**: Stream new document deltas directly into pgvector/SQLite without full store reload.
- **Multi-lingual PDF Ingestion**: Extend normalization to Hindi and regional language financial statements.

---

## 6. Additional Notes & Brownie Points Addressed

### Brownie Points Accomplished:
1. **Handling Large PDFs Without Performance Degradation**:
   - PyMuPDF streaming parser extracts blocks with minimal memory footprint.
   - 150 DPI page rendering and bounding box calculations are computed lazily on-demand per page request.
2. **Many PDFs in the Same Knowledge Layer**:
   - Successfully ingests and indexes multi-company corpora (Delhivery, Apple Inc. SEC 10-K, Tesla Inc. Q4 Update, and India Macroeconomy) with isolated workspaces and unified cross-entity search.
3. **Dynamic Schema Evolution**:
   - New kinds of facts, units, currencies (`$`, `₹`), and metadata properties are extracted without requiring database migrations or static schema changes.
4. **Incremental Ingestion**:
   - Uploading new PDFs via `/api/upload` or the UI dynamically updates the knowledge store and recomputes relationships without rebuilding existing indexed facts.

### Zero Credentials / 100% Local & Reproducible:
- The system runs completely self-contained without paid API keys, cloud subscriptions, or external network dependencies.

---

## 7. Project Structure
```
Super Join/
├── src/
│   ├── api/              # FastAPI endpoints (upload, facts, query, cases, graph, canvas)
│   ├── extraction/       # Grounded Fact Extractor & table parsing
│   ├── ingestion/        # PyMuPDF fast layout, text block, and table extractor
│   ├── models/           # Pydantic data schemas (Fact, Evidence, Relationship, CaseStudy)
│   ├── normalization/    # Indian/international scale, temporal, and metric canonicalizers
│   ├── reconciliation/   # Cross-Document Relationship & Case Studies Engine
│   ├── storage/          # Multi-company Fact Knowledge Store & hybrid search
│   └── ui/               # Obsidian-themed UI with Canvas Studio & D3 Knowledge Graph
├── tests/
│   ├── evals/            # Automated verification for the 4 required cases
│   ├── test_api.py       # Comprehensive FastAPI endpoint test suite
│   ├── test_external_reports.py # Multi-company SEC & international report tests
│   └── test_normalization.py   # Currency, scale, and period normalization tests
├── starter-datasets/     # Delhivery & Indian Macroeconomy PDF filings
├── requirements.txt      # Minimal, pinned Python dependencies
└── README.md             # Project documentation & run guide
```
