# 🏦 IntelliCredit — AI-Powered Credit Appraisal System

> **Hackathon Project** · Built with Streamlit · Groq LLaMA 3.3 70B · XGBoost · ReportLab · ChromaDB

IntelliCredit is an end-to-end AI-assisted credit appraisal platform for Indian SME lending. It automates document parsing, financial ratio derivation, GST reconciliation, risk scoring, Five Cs analysis, external due diligence, and professional CAM report generation — all from a single web interface.

---

## ✨ Features

### 📄 Document Intelligence
- **Multi-format parser** — Docling-powered parsing for XLSX, PDF, and text documents
- **Groq LLaMA 3.3 70B primary extractor** — LLM-based structured extraction for GST returns, bank statements, and ITR/balance sheets
- **Three-tier ITR extraction chain** — Groq LLM → dual-strategy regex (colon-style + whitespace-style) → openpyxl direct cell scan fallback
- **Auto-fill pipeline** — financial ratios derived automatically from uploaded documents and pre-populated in the officer input form with 🔒 lock icons

### 🔍 GST Reconciliation
- GSTR-2A vs GSTR-3B mismatch detection
- ITC variance analysis with fraud signal flagging
- Circular trading detection
- Configurable mismatch thresholds

### 📊 Risk Scoring Engine
- **XGBoost model** with SHAP explainability
- Accepts officer-requested loan amount as scoring input
- Loan limit calculated relative to requested amount (not a fixed formula)
- `MAX_LOAN_LIMIT_INR` = ₹50 Cr (configurable in `config.py`)
- Three risk categories: LOW / MEDIUM / HIGH
- Three decisions: APPROVE / CONDITIONAL / REJECT

### 🤖 AI Agent (Groq LLaMA 3.3 70B)
- Full reasoning chain generation
- Narrative decision (supplementary to XGBoost — never overrides model score)
- Early warning signal extraction
- RAG-backed context using ChromaDB + `all-MiniLM-L6-v2` embeddings

### 🏅 Five Cs Credit Analysis
- Character, Capacity, Capital, Collateral, Conditions
- Scored 0–10 with qualitative summaries
- Feeds into the risk engine as qualitative features

### 🔎 External Research & Due Diligence
- Google News + GDELT news search
- Relevance filtering — only articles mentioning the specific company are included
- MCA charge check
- e-Courts litigation search
- RBI / SEBI regulatory action check
- News risk score 0–10

### 📋 Bank-Grade CAM Report (PDF + DOCX)
- **PDF** — 10-section Credit Appraisal Memorandum with:
  - Full-bleed navy letterhead cover page with gold rule, CONFIDENTIAL watermark, and credit committee approval block
  - Running navy header bar + gold hairline on every body page
  - Confidentiality footer with timestamp on every page
  - Semi-circular risk gauge (green / amber / red zones, navy needle)
  - Decision colour-coded badge: 🟢 APPROVED · 🟡 CONDITIONAL · 🔴 REJECTED
  - 10 formal sections with navy left-bar rules and decimal numbering
  - Standard credit conditions & covenants table
  - Recommendation banner + 4-column signature/approval block
  - Legal disclaimer referencing RBI guidelines
- **DOCX** — matching structure with Arial font, navy section headers, and footer reference number
- **Auto-reference number** — format `CAM/YYYY/COMP/DDHHMM`

### 👁 Inline PDF Viewer
- PDF viewer opens automatically as a modal overlay when analysis completes
- Navy + gold styled dialog matching the CAM design language
- Close via ✕ button, Escape key, or clicking the backdrop
- "View PDF" button in Results tab to re-open at any time

---

## 🗂 Project Structure

```
IntelliCredit/
├── app.py                      # Streamlit UI + analysis pipeline
├── config.py                   # Constants: bank name, limits, model paths
├── requirements.txt
└── src/
    ├── schemas.py              # Pydantic models (all data structures)
    ├── parser.py               # Docling document parser
    ├── extractor.py            # Groq + regex + openpyxl extraction
    ├── reconciler.py           # GSTR-2A vs 3B reconciliation
    ├── researcher.py           # External news + MCA + court research
    ├── risk_engine.py          # XGBoost scoring + SHAP + loan limit
    ├── five_cs.py              # Five Cs credit analysis
    ├── agent.py                # Groq LLM reasoning agent
    ├── prompts.py              # All LLM prompt templates
    └── cam_generator.py        # PDF + DOCX CAM report generator
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.11+
- Groq API key ([get one free at console.groq.com](https://console.groq.com))

### Install

```bash
git clone https://github.com/NiyaSinghShekhawat/IntelliCreditSystem.git
cd IntelliCreditSystem
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### Configure

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Or set it as an environment variable:

```bash
# Windows PowerShell
$env:GROQ_API_KEY = "your_key_here"

# macOS / Linux
export GROQ_API_KEY="your_key_here"
```

### Run

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 📋 How to Use

### Tab 1 — Upload Documents

| Field | Document | Format |
|---|---|---|
| GSTIN / Company Name | Manual entry | Text |
| GSTR-3B | GST return (filed) | XLSX |
| GSTR-2A | Auto-drafted ITC statement | XLSX |
| Bank Statement | 6-month statement | XLSX |
| ITR / Balance Sheet | ITR-6 or financial statements | XLSX |
| Loan Amount Requested | Officer input | Number (₹) |

Click **Run Analysis** — all subsequent steps are fully automated.

### Tab 2 — Officer Inputs

Financial ratios auto-derived from uploaded documents are shown with 🔒 lock icons. The officer can override any field or fill in missing values manually before the risk score is computed.

### Tab 3 — Results

- AI decision with colour-coded badge
- Risk score, loan limit, interest rate
- SHAP risk drivers chart
- Five Cs detail
- GST reconciliation summary
- External research findings
- Full AI reasoning chain
- **PDF viewer opens automatically** — scroll through the full CAM report inline
- Download PDF and DOCX buttons

---

## 🎨 Design Palette

| Colour | Hex | Usage |
|---|---|---|
| Deep Navy | `#0d1f5c` | All structural chrome — headers, table headers, borders |
| Mid Navy | `#1a3080` | Section headings, inner borders |
| Gold | `#c9970a` | Cover accent rule only |
| Pale Blue | `#e8edf8` | Label column background in all tables |
| Green | `#1a6b2a` | APPROVE decision |
| Amber | `#b85c00` | CONDITIONAL decision + early warning |
| Red | `#b71c1c` | REJECT decision + adverse items |

---

## 🧪 Mock Test Data

Two test companies are included in `/outputs/` for local testing:

### Sunrise Apparels (SME — moderate risk)
- Turnover: ₹13.2 Cr · Net Worth: ₹3.25 Cr · D/E: 0.82x
- ITC gap: 62.5% → fraud signal
- Expected decision: APPROVE or CONDITIONAL

### Lakme Lever Pvt Ltd (large company — low risk)
- Turnover: ₹168.5 Cr · Net Worth: ₹74.5 Cr · D/E: 0.54x · DSCR: 4.2x
- Directors: Prabha Narasimhan, Sanjeev Mehta
- GSTIN: 27AABCL9876R1ZX · PAN: AABCL2345M
- Expected decision: APPROVE

---

## 🔧 Key Configuration (`config.py`)

| Parameter | Default | Description |
|---|---|---|
| `MAX_LOAN_LIMIT_INR` | `500,000,000` | Maximum sanctionable limit (₹50 Cr) |
| `GST_MISMATCH_MIN_COUNT` | `2` | Minimum mismatches to raise a GST flag |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | ChromaDB embedding model |
| `CAM_BANK_NAME` | `IntelliCredit Bank Ltd.` | Bank name on CAM letterhead |
| `CAM_AUTHOR` | `IntelliCredit AI v1.3` | Author field on CAM |

---

## 🏗 Architecture

```
Upload Docs → Parse (Docling) → Extract (Groq → Regex → openpyxl)
                                        ↓
                              RAG Ingest (ChromaDB)
                                        ↓
                           derive_from_documents()
                        session_state["derived_financials"]
                                        ↓
                        build_qualitative_inputs(derived, officer)
                                        ↓
                              five_cs.analyze()
                                        ↓
                    risk_engine.score(result, requested_amount_inr)
                         XGBoost + SHAP explainability
                                        ↓
                    agent.analyze()  ← narrative only, score unchanged
                                        ↓
                    cam.generate_both()  ← PDF (ReportLab) + DOCX
                                        ↓
                         Inline PDF Modal Viewer (Streamlit)
```

---

## 📦 Dependencies

```
streamlit
groq>=0.9.0
xgboost
shap
chromadb
sentence-transformers
docling
openpyxl
reportlab
python-docx
pandas
requests
pydantic
python-dotenv
```

---

## 📝 Changelog

### v1.3 (Current)
- Full bank-grade CAM redesign — 10 sections, cover page, running headers/footers, signature block
- Semi-circular risk gauge with colour zones in PDF
- Inline PDF modal viewer — auto-opens on analysis completion
- Decision colour coding: green / amber / red throughout PDF and UI
- Temp file lifecycle fix — openpyxl ITR fallback now works correctly
- `cheque_returns` and other optional bank fields use `getattr` fallback
- Gauge repositioned: small, centred, table starts on next line

### v1.2
- Groq LLaMA 3.3 70B as primary extractor (replaces regex-first approach)
- Three-tier ITR extraction: Groq → dual-strategy regex → openpyxl cell scan
- Loan limit respects officer-requested amount
- `MAX_LOAN_LIMIT_INR` raised to ₹50 Cr
- News relevance filtering — multi-token company name matching
- Risk gauge added to PDF

### v1.1
- Auto-fill pipeline with 🔒 lock icons on derived fields
- RAG ingestion after each document parse
- SHAP explainability integration
- GST circular trading detection
- Five Cs scoring engine

### v1.0
- Initial release — end-to-end pipeline from document upload to CAM generation

---

## 👩‍💻 Author

**Niya Singh Shekhawat**
GitHub: [@NiyaSinghShekhawat](https://github.com/NiyaSinghShekhawat)

---

*Built for a hackathon. Not intended for production credit decisioning.*