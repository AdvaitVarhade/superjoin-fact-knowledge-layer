# Superjoin — Fact Knowledge Layer & Cross-Document Reconciliation Engine

An end-to-end Fact Knowledge Layer and deterministic cross-document reconciliation system for financial filings, investor decks, and macroeconomic reports. Built for the **Superjoin AI Engineer Assignment (VIT 2026)**.

---

## 🚀 1. Setup and Run Instructions

### Prerequisites
- Python 3.10+ (tested on Python 3.11)
- Google Chrome / Chromium (optional, for automated Playwright verification)

### Installation
```bash
# 1. Clone the repository
git clone https://github.com/AdvaitVarhade/superjoin-fact-knowledge-layer.git
cd superjoin-fact-knowledge-layer

# 2. Create and activate a virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux / macOS:
source venv/bin/activate

# 3. Install required dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Start the FastAPI backend and interactive UI server
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```

Navigate to **`http://127.0.0.1:8000`** in your browser.

---

## 🧪 2. Automated Test Suite
```bash
# Run all 23 automated evaluation and unit tests
python -m pytest -v
```

---

## 📋 3. Assignment Four Core Cases

1. **Delhivery FY24 Revenue Restatement / Scope Variance**: Annual Report FY24 Note 34 (₹4,766.19 Cr standalone vs ₹4,896.11 Cr consolidated).
2. **Delhivery Express Parcel Volume Corroboration**: 740 Million Express parcel shipments corroborated across Annual Report and Investor Presentation.
3. **Delhivery FY23 Growth Rate Divergence**: 8.16% vs 7.94% cross-period restatement.
4. **India Macroeconomic CPI Inflation Spread**: Economic Survey (4.5%) vs IMF Article IV Report (4.8%).
