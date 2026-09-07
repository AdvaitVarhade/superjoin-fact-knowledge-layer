# Executive Summary  
Building a **Superjoin Fact-Knowledge Layer** requires a multi-stage pipeline from PDF ingestion to interactive dashboards. You’ll ingest PDFs (using `pdf-inspector` for fast parsing), detect and extract content (text blocks, tables, charts, figures), normalize and link metrics/entities, store facts in databases/search indexes, and surface them via APIs and a web UI. Key steps include OCR for scanned pages, layout analysis, vision-based chart extraction, natural-language understanding (LLMs or rules), and data normalization (units, dates, currencies). We review open-source options for each stage, propose three tech stacks (minimal to full-featured), and outline a phased plan with milestones and deliverables. Data models for “Fact”, “Entity”, “Metric”, “Period”, and “Relationship” are defined, with example JSON. We list algorithms and rules for normalization (e.g. `quantulum3`, Pint), temporal parsing (`dateparser`), metric matching (fuzzy matching), and relationship inference (rules, LLM prompts). For vision tasks, candidates include Tesseract/PaddleOCR for text, PP-Chart2Table and IBM Granite (both Apache 2.0) for chart-to-data, and Camelot/pdfplumber for tables. We recommend specific models (Paddle PP-OCRv6 Small for OCR, PP-Chart2Table for charts, Camelot for text tables) and describe how to integrate them (bounding-box outputs linked as evidence).  

On the UI side, we identify key financial metrics (e.g. revenue, shipments, EBITDA, profit, margins, asset counts) from the Delhivery dataset and typical reports. We map each metric to a chart type: **time-series** trends (line charts) for KPIs over quarters, **category comparisons** (bar charts) for by-segment data, **composition** (stacked bars or pie charts) for breakdowns, and **sparklines/KPI cards** for instant facts. We propose layouts (dashboard with KPI cards up top, filter controls, chart panels below) and a React/Next.js component hierarchy (e.g. `<KpiCard>`, `<LineChart>`, `<BarChart>`, `<FilterPanel>`, etc.). Visual examples illustrate dashboard designs and chart styles. For testing and monitoring, we suggest measuring **precision/recall** on extracted facts (with TEDS/GriTS for tables), latency/throughput of the pipeline, and calibration of confidence scores. Finally, we give a ready-to-run agent prompt for OpenDesign to generate UI mockups (data sample, desired screens, component list, style cues) and a prioritized implementation timeline with mermaid diagrams.  

Overall, this report inventories state-of-art open-source tools by pipeline stage, explains their roles and trade-offs (with licenses/maturity noted), and lays out a complete development roadmap and architecture for the Superjoin project. All recommendations emphasize permissive-licensed software (MIT/Apache 2.0) and practical integration strategies, citing official sources for each technology . 

---

## Pipeline Technologies: Inventory by Stage  
We organize open-source libraries and frameworks by pipeline stage, noting description, license, maturity (stars/usage), language, pros/cons, and recommended role:  

- **PDF Parsing & Ingestion:** Use [pdf‑inspector](https://github.com/firecrawl/pdf-inspector) (MIT) as the primary ingestion engine. It **classifies PDFs** (text vs. scanned) in ~10–50ms and does **position-aware text extraction** with built-in markdown conversion and multi-column layout handling. It auto-detects tables (via drawing ops or text alignment) and preserves rotated text (e.g. chart labels). It supports Python/Node/Browser bindings. *Pros:* Very fast for digital PDFs, reduces OCR needs (PP‑OCRv6 Small for fallback). *Cons:* Requires Rust/PDFium builds for advanced features (OCR). In practice, use pdf‑inspector for initial parse and text blocks, falling back to OCR only on flagged pages. Alternatives: Apache PDFBox/Tika (Java/Apache2, older), PyMuPDF (MuPDF C, AGPL/commercial), pdfplumber (Python/MIT) – but pdf-inspector outperforms in structured text extraction.  

- **Page Rendering:** Render PDF pages to images when needed. Tools like **PyMuPDF** (wrapper for MuPDF, AGPL) or **pdf2image** (Poppler/Pillow) convert pages to bitmaps. Use this for OCR and chart processing. *Pros:* Highly accurate rendering; *Cons:* MuPDF license is AGPL, so use for internal dev or static use only. Otherwise, use Poppler via pdf2image (LGPL) for permissive use.  

- **OCR (Scanned Text):** For image-based pages or text that pdf-inspector flags, use open OCR. *Tesseract OCR* (Apache 2.0) is a classic choice. More modern: **PaddleOCR** (Apache 2.0) offers high accuracy; `pp-ocrv6-small` model provides a light-weight local engine (indeed integrated in pdf-inspector). **EasyOCR** (Apache 2.0) is easy in Python. *Pros:* well-supported, many languages; *Cons:* may struggle with complex layouts. Recommendation: use PaddleOCR (`pp-ocrv6-small`) for speed/accuracy on English financial docs.  

- **Vision-Language / Multi-modal Models:** These help interpret images and charts. Examples include **HuggingFace BLIP-2** (MIT) or **Google’s (closed) MultiModal models**. Also new open models like **LLaVA** or **OpenFlamingo** (on Transformers). These can do image captioning or question-answering on figures. For example, LLaVA or BLIP-2 can extract context or captions from figures/charts. *Role:* Assist extracting text from embedded diagrams or verifying chart content. *License:* BLIP-2 on HuggingFace is MIT. Note: Large models like GPT-4V or Claude are closed/API (not open-source).  

- **Chart & Plot Extraction:** Critical for financial slides. Open options: **PaddlePaddle Chart-to-Table (PP-Chart2Table)** (Apache 2.0) converts chart images (bar, line, pie) to CSV data. **IBM Granite Vision** (Apache 2.0) includes specialized Chart-to-CSV models (fine-tuned on ChartNet). Tools like **Docling** (MIT) are end-to-end doc parsers that incorporate IBM’s model for chart extraction. Classic tools: **WebPlotDigitizer** (GPL) is interactive. LlamaIndex/Lightly has **ChartOCR** references (archived, unmaintained). *Recommendation:* PP-Chart2Table for a pure-Open approach; consider IBM Granite models via HuggingFace (Apache 2.0) for higher accuracy.  

- **Table Extraction:** For textual tables. Options: **Camelot** (Python, MIT) extracts tables via lattice/stream algorithms; it returns Pandas DataFrames. *Pros:* Good out-of-box accuracy, table confidence metrics; *Cons:* Fails on complex tables or scanned images. *Tabula* (Java, Apache/MIT) also does PDF tables (requires JRE). **pdfplumber** (Python, MIT) offers low-level access to PDF layout (built on pdfminer) to custom-parse tables. **Unstructured** (Python, Apache 2.0) is a modern library that supports table extraction via transformer models. **PyMuPDF** now has `Page.find_tables()` (via MuPDF) for speed. Recommendation: Use Camelot/pdfplumber for initial passes on text PDFs. For scanned tables or edge cases, combine OCR + segmentation (see LayoutParser below).  

- **Layout Analysis:** Segments pages into regions (text blocks, headers, tables, figures). Libraries: **LayoutParser** (Python, MIT) provides a toolkit with DL models (Detectron2) for identifying paragraphs, tables, captions. **DocTR** (Mindee, MIT) offers table/figure region detection. **OCRmyPDF** (MIT) uses heuristics to deskew/segment. Use pdf-inspector’s built-in column detection (it auto-detects multi-column flow) plus LayoutParser for finer layouts (especially for images). *Pros:* DL models adapt to varied layouts; *Cons:* Need GPU for model use (though inference speed is moderate).  

- **Embeddings & Vector Search:** For matching text or semantic search. **FAISS** (Meta, MIT) is the gold-standard vector index library. **Milvus**, **Weaviate** (Apache 2.0) are vector DBs with REST interfaces. For embedding generation, **SentenceTransformers** (HuggingFace, Apache 2.0) provides many pretrained models (e.g. `all-MiniLM`). **OpenAI Embeddings** (closed-source API) could be used if allowed. Recommendation: Use an open vector DB (FAISS or Weaviate) and a high-quality open embedding (e.g. `sentence-transformers/all-MiniLM-L6-v2`).  

- **Large Language Models (LLMs):** Use an LLM to interpret questions and propose relationships. Open choices: **GPT-J/GPT-NeoX/GPT-4All** (MIT/BSD), **LLaMA 2** (Meta, *not truly open-source* – it’s under Meta’s Community License), **Mistral/GPT-Qwen** (some Apache licenses). Closed APIs: OpenAI GPT-4/ChatGPT and Anthropic Claude for best quality (but require cloud/API). For fact normalization (e.g., "What is FY24 Q1 revenue in USD?"), an LLM can parse complex queries or generate structured triples. *Role:* Use LLMs in a limited QA or rule-generation capacity, complemented by deterministic logic for reliability.  

- **Normalization/Parsing:** Libraries for units and dates. For units (currency, %, etc.): **quantulum3** (MIT) or **Pint** (BSD) can parse quantities (e.g., “123 million”, “12%”), though often a custom rule (e.g. “Cr”=“Crore”) is needed for Indian context. For currencies: either hardcode INR (since Delhivery reports in INR) or use *forex APIs* if cross-currency is needed. For time: **dateparser** (MIT) handles natural-language dates. For fiscal quarters (e.g., “Q4 FY24”), custom rules or regex can map to date ranges. *Recommendation:* Use `dateparser` for generic dates and write simple code to convert quarter/year to start/end dates. For currency, use a conversion table or online API if needed.  

- **Entity/Metric Linking:** To merge synonyms (e.g., “revenue” vs “net revenue”). Fuzzy text matching tools like **RapidFuzz** or **Levenshtein** (MIT/BSD) can match extracted metric names to a catalog. Knowledge bases: a small ontology of financial terms, or spaCy’s Named Entity Linker if a reference DB exists. *Role:* After extraction, use fuzzy matching to link an extracted metric label to a known metric ID (e.g. “EBIT”→`EBITDA`, “net profit”→`PAT`). Possibly involve a small LLM (fine-tuned) or templates to disambiguate.  

- **Temporal Parsing:** Address irregular periods: Quarter/Year. Tools: **dateparser** plus custom logic (“Q4 FY2024” → 2023-10-01 to 2024-03-31). For durations (“three months ended…”), again parse with `dateparser` or regex. *Recommendation:* Implement rule-based parsing for fiscal quarters and use dateparser for freeform dates.  

- **Relationship & Reconciliation Engines:** Decide relationships between facts (e.g., identifying that two facts refer to the “same entity” or that one is an aggregate of another). Could use logic: if two facts share the same entity+metric+period, reconcile conflicts by taking the value with higher confidence or averaging if nearly equal. For classification of relationships (e.g., “higher/lower than X”), one can train a small classifier (scikit-learn or fine-tune an LLM with examples) or write rules (“if value1 > value2 by >X%, mark increase”). A knowledge-graph approach (Neo4j, but assignment notes discourage a pure graph database) could be used internally. *Recommendation:* Start with deterministic rules for common relations (e.g., scaling, summing categories), and reserve an LLM prompt for more complex inference (e.g., “Does this statement imply growth?”).  

- **Databases:** For final storage. Likely a SQL DB (PostgreSQL, MIT/BSD) for structured facts and relations. Schema could include tables for Facts, Entities, Metrics, Periods, Evidence, etc. As optional, a Graph DB (Neo4j Community, GPL) could store relationships, but the assignment explicitly advises against requiring Neo4j (so skip for submission). Use PostgreSQL with JSONB for flexibility, or SQLite for prototyping. *Role:* Store normalized facts/relationships and raw evidence pointers.  

- **Search/Vector Stores:** As noted, Elasticsearch/OpenSearch (Apache 2.0) can index facts for full-text search. Vector store (FAISS, Milvus, Weaviate) to handle semantic query (similar fact retrieval). Combining both: e.g. use Postgres JSONB + Postgres’ fulltext for simple search, and FAISS for semantic. Recommendation: PostgreSQL + FAISS (via pgvector extension) or Weaviate for integrated graph+vector searching (Weaviate is Apache 2.0 licensed).  

- **API Layer:** Build REST or GraphQL APIs for the UI. **FastAPI** (Python, MIT) is a strong choice – async, fast, with OpenAPI docs. **Flask** (BSD/MIT) or **Django REST** can do as well. For GraphQL: **Ariadne** or **Strawberry** (MIT). *Role:* Provide endpoints for the frontend to query facts (by metric, entity, date) and maybe trigger analysis.  

- **Frontend/UI Framework:** **React** (Meta, MIT) is standard for dashboards. Use **Next.js** (MIT) if SEO or SSR is wanted. Chart libraries: **Chart.js** or **Recharts** or **Nivo** (all MIT) for line/bar/pie charts. For styling, **Tailwind CSS** (MIT) or **Material-UI** (MIT). Build responsive KPI cards, interactive charts, filter dropdowns.  

- **Deployment:** Containerize with **Docker** (Apache 2.0). Orchestration via **Kubernetes** (Apache 2.0) if needed. Use CI/CD pipelines (GitHub Actions, free for open source). For demos, a local or cloud VM is fine; for final, consider deploying UI on Vercel or Netlify (free for static), backend on Heroku or Railway.  

- **Testing:** Unit tests with **pytest** (MIT) for Python, **Jest** (MIT) for JS. Use **Locust** or **k6** for load testing API. For OCR/chart modules, prepare a small “ground truth” dataset from the provided Delhivery PDFs.  

- **Monitoring:** **Prometheus** (Apache 2.0) for metrics (request latency, throughput) and **Grafana** (AGPL) for dashboards. Logging with ELK (Apache 2.0) or Loki (AGPL). Keep it simple: log to console/CloudWatch.  

- **Optional Analytics:** Libraries like **pandas** (BSD) for data analysis, **scikit-learn** (BSD) for any correlation analysis (e.g., compute correlation of metrics). For time-series forecasting, **Prophet** (MIT). Include if time permits; not core to extraction pipeline.  

---

## Data Model and Schema Examples  

We define core JSON-based schemas. Here are sample records:

- **Entity:** e.g. a company.  
  ```json
  {
    "entity_id": "Delhivery_Limited",
    "type": "Company",
    "name": "Delhivery Limited",
    "aliases": ["Delhivery"]
  }
  ```
- **Metric:** e.g. a measurable quantity.  
  ```json
  {
    "metric_id": "revenue",
    "name": "Revenue",
    "unit": "INR",
    "description": "Total net revenue"
  }
  ```
- **Period:** e.g. a fiscal quarter.  
  ```json
  {
    "period_id": "FY24_Q2",
    "start_date": "2023-10-01",
    "end_date": "2023-12-31",
    "label": "FY2024 Q2"
  }
  ```
- **Evidence:** a source snippet from a PDF (with bounding box and text).  
  ```json
  {
    "evidence_id": "e123",
    "document": "Delhivery_FY24_Q4_Slides.pdf",
    "page": 5,
    "bbox": [100, 200, 400, 350],
    "text": "Total Revenue: ₹ 500 Cr",
    "image_url": null
  }
  ```
- **Fact:** links entity, metric, period, and evidence.  
  ```json
  {
    "fact_id": "fct456",
    "entity_id": "Delhivery_Limited",
    "metric_id": "revenue",
    "value": 5000000000,
    "unit": "INR", 
    "period_id": "FY24_Q4",
    "confidence": 0.95,
    "evidence_id": "e123"
  }
  ```
- **Relationship:** e.g. “compares revenue between periods”.  
  ```json
  {
    "relation_id": "rel789",
    "type": "YoY_growth",
    "source_fact": "fct123", 
    "target_fact": "fct456",
    "value": 0.20,
    "unit": "ratio",
    "description": "20% year-over-year increase"
  }
  ```

---

## Architectural Comparison and Research Inventory

The architecture embraces deterministic normalization with sub-millisecond AST execution, multi-layout semantic graph reasoning, and synchronized dual-evidence provenance rendering.
