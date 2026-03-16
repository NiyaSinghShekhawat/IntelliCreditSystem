# 🏦 IntelliCredit v2.0 — AI-Powered Credit Intelligence Engine

> **Vivriti Capital National AI/ML Hackathon** · Codekarigars · Built with Streamlit · Groq LLaMA 3.3 70B · XGBoost · Supabase · ReportLab

IntelliCredit is an end-to-end AI credit underwriting platform for NBFCs and enterprise lenders. It automates the full credit analyst workflow — from entity onboarding through document ingestion, intelligent extraction, secondary research, risk scoring, and professional investment report generation — all accessible from a single hosted web interface.

Visit [this link](https://www.canva.com/design/DAHDRjFsSwE/EMJBZ1IuQkwa49WveTVYaw/view?utm_content=DAHDRjFsSwE&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=hc6361520a4) for prototype presentation and updated mock-ups.
---

## ✨ What's New in v2.0

| Feature | v1.4 | v2.0 |
|---|---|---|
| Case management | None | Full lifecycle — create, track, close |
| Database | None | Supabase (entities + cases + audit trail) |
| Document types | GST / Bank / ITR | + ALM / Shareholding / Borrowing / Annual Report / Portfolio |
| Onboarding | Sidebar form | Dedicated onboarding page → case creation |
| Classification | Manual | Auto-classify with HITL confirmation |
| Schema editor | None | Dynamic per-doc-type schema editor |
| SWOT analysis | None | LLM-generated from Five Cs + research signals |
| Secondary research | News only | News + sector macro + triangulation with financials |
| Investment report | CAM PDF/DOCX | Investment Assessment Report — 5 pages, white cover |
| Officer closure | None | Add collateral, interest rate, notes → close case |
| Uploaded files | Not stored | Stored per case with confidence + date |

---

## 🗺 User Journey

```
📋 New Case          →  Entity onboarding (company, CIN, PAN, sector, loan ask)
         ↓
📂 Upload & Classify →  Upload 5 doc types → auto-classify → HITL confirm
         ↓
🔍 Schema Editor     →  Review/edit extraction schema per document
         ↓
▶  Run Extraction    →  Extract structured data from each doc
         ↓
Continue →           →  Auto-routes to analysis page
         ↓
🤖 AI Analysis       →  Five Cs + XGBoost + SHAP + research + SWOT + report
         ↓
📄 Investment Report →  Download PDF / DOCX (5 pages)
         ↓
✅ Officer Assessment →  Add collateral value, interest rate, notes → Close Case
         ↓
🏠 Dashboard         →  All cases with status, risk score, decision badges
```

Visit [link](https://whimsical.com/niya-s-workspace2/intellicredit-v-2-0-MwBBvpWxKYkYNYV7iz6nRv) to see the full system-architecture workflow diagram.

---

## ✨ Features

### 🗂 Case Lifecycle Management
- **Supabase-backed** entity and case tables with full CRUD
- Case statuses: IN_PROGRESS → UNDER_REVIEW → CLOSED
- Officer closure form — collateral value, final interest rate, due diligence notes, closure remarks
- Re-open closed cases for further review
- All uploaded files, extraction results, analysis output, and reports stored per case

### 📄 Intelligent Data Ingestion (5 Document Types)
- **ALM** — Asset-Liability maturity bucket extraction
- **Shareholding Pattern** — promoter holding, pledge %, FII/DII
- **Borrowing Profile** — total borrowings, NCD, credit rating, lender count
- **Annual Report** — P&L, balance sheet, cashflow (PAT, net worth, D/E)
- **Portfolio / Performance Data** — AUM, GNPA, NIM, collection efficiency, CAR

Each extractor uses a two-tier pipeline:
1. Regex / keyword proximity search (fast, deterministic)
2. Groq LLaMA 3.3 70B fallback if < 3 fields extracted

### 🔬 Auto-Classification with HITL
- **PyMuPDF fast classifier** — scans all pages, scores by financial keyword density
- Per-doc-type keyword scoring — uses Annual Report keywords to score Annual Report pages, Portfolio keywords for Portfolio pages etc.
- LLM fallback via Groq for ambiguous documents
- **Human-in-the-loop confirmation** — confidence badge (HIGH/MED/LOW), editable selectbox, ✓ Confirm / Edit buttons
- **Dynamic schema editor** — `st.data_editor` with default schemas per doc type, fully editable
- 40k chars extracted per document (up from 12k in v1) — covers full financial tables

### 🔍 GST Reconciliation
- Separate GSTR-2A and GSTR-3B upload and extraction
- GSTR-2A ITC extracted by summing supplier ITC column (skips embedded reconciliation note rows)
- Variance analysis with configurable thresholds
- Circular trading detection via bank credit vs GST turnover ratio
- Hard policy rule: ITC variance ≥ 50% → minimum CONDITIONAL decision

### 📊 Risk Scoring Engine
- **XGBoost + SHAP** — explainable risk score 0.0–1.0
- **Extraction enrichment** — D/E ratio from Annual Report / Borrowing Profile auto-fills officer inputs; promoter pledge > 50% reduces promoter score
- Hard policy overrides — GST fraud signal floors score regardless of financials
- Decisive factor surfaced prominently below AI decision banner
- Loan limit calculated relative to requested amount

### 🤖 AI Reasoning Chain
- Groq LLaMA 3.3 70B — 4-step narrative (GST → Bank → Research → Inputs)
- ChromaDB RAG context from ingested documents
- Decisive factor and early warning signal extraction
- Graceful fallback when rate-limited

### 🧩 SWOT Analysis
- Generated from Five Cs scores + risk signals + research findings
- 2×2 grid rendered in UI and embedded in Investment Report
- Rule-based fallback when LLM unavailable
- Saved to Supabase `swot_json` column per case

### 🔎 Secondary Research & Macro Triangulation
- Google News RSS + GDELT with accent-normalised relevance filtering
- Per-entity risk queries: fraud, GST notice, defaulter, FIR, court case
- **Sector macro research** — RBI sectoral data, industry trends via Google News
- **Triangulation** — LLM synthesises news + legal + extracted financials into unified risk narrative with red flags, positives, recommended checks
- MCA charge check · e-Courts · RBI/SEBI regulatory actions

### 📋 Investment Assessment Report (PDF + DOCX)
- **5-page PDF** — white cover with entity + loan details, navy/gold branding
- Sections: Executive Summary · Financial Analysis · Five Cs · SHAP · Reasoning · SWOT · Research & Macro · Early Warnings · Conditions · Recommendation
- Semi-circular risk gauge · decision colour-coded banner · 4-column sign-off block
- DOCX version mirrors PDF structure
- Downloadable from both Results tab and Case View
- Branding: **IntelliCredit** (AI engine), not bank-specific

### 🖥 Officer Dashboard
- Default landing page — all cases with status badges, risk scores, loan amounts
- Filter by decision and sector
- One-click open → Case View with full audit trail
- Metrics row: Total / In Progress / Approved / Conditional / Rejected

---

## 🗂 Project Structure

```
IntelliCredit/
├── app.py                          # Streamlit router + CSS + analysis pipeline
├── config.py                       # API keys, thresholds, constants
├── requirements.txt
├── pages/
│   ├── dashboard.py                # Officer dashboard (all cases)
│   ├── onboarding.py               # Entity onboarding → case creation
│   ├── upload_classify.py          # HITL classification + schema editor + extraction
│   └── case_view.py                # Full case detail + officer closure form
└── src/
    ├── schemas.py                  # Pydantic models (all data structures)
    ├── parser.py                   # Docling parser (OCR disabled for speed)
    ├── extractor.py                # GST / Bank / ITR extraction (Groq + regex + openpyxl)
    ├── extractors_v2.py            # 5 new doc type extractors + QualitativeInputs enrichment
    ├── classifier.py               # PyMuPDF classifier + doc-type-aware page scoring
    ├── reconciler.py               # GSTR-2A vs 3B reconciliation
    ├── researcher.py               # News + sector macro + triangulation
    ├── risk_engine.py              # XGBoost + SHAP + hard policy rules
    ├── five_cs.py                  # Five Cs credit analysis
    ├── agent.py                    # Groq LLM reasoning agent + RAG
    ├── swot_generator.py           # SWOT from Five Cs + research signals
    ├── database.py                 # Supabase client + CRUD helpers
    └── cam_generator.py            # Investment Assessment Report — PDF + DOCX
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.11+
- Groq API key — [console.groq.com](https://console.groq.com)
- Supabase project — [supabase.com](https://supabase.com)
- Google Gemini API key — optional ([aistudio.google.com](https://aistudio.google.com))

### Install

```bash
git clone https://github.com/NiyaSinghShekhawat/IntelliCreditSystem.git
cd IntelliCreditSystem
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

### Configure

Create a `.env` file in the project root:

```env
# Groq — multi-key rotation (up to 4 keys from separate accounts)
GROQ_API_KEY=your_primary_groq_key
GROQ_API_KEY_2=your_backup_groq_key
GROQ_API_KEY_3=your_third_groq_key

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key

# Gemini — optional fallback
GEMINI_API_KEY=your_gemini_api_key
```

### Supabase Setup

Run this SQL in your Supabase SQL Editor:

```sql
-- Entities table
CREATE TABLE IF NOT EXISTS entities (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  company_name TEXT NOT NULL,
  cin TEXT, pan TEXT, sector TEXT,
  loan_type TEXT, loan_amount_cr NUMERIC,
  loan_tenure_months INTEGER, loan_purpose TEXT,
  turnover_cr NUMERIC, gstin TEXT,
  promoter_name TEXT, promoter_phone TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cases table
CREATE TABLE IF NOT EXISTS cases (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  entity_id UUID REFERENCES entities(id),
  status TEXT DEFAULT 'IN_PROGRESS',
  decision TEXT, risk_score NUMERIC,
  five_cs_json JSONB, research_json JSONB,
  swot_json JSONB, uploaded_files JSONB,
  cam_path TEXT, decisive_factor TEXT,
  officer_notes TEXT, collateral_value_cr NUMERIC,
  final_interest_rate NUMERIC, officer_decision TEXT,
  closure_remarks TEXT, closed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Disable RLS for development
ALTER TABLE entities DISABLE ROW LEVEL SECURITY;
ALTER TABLE cases    DISABLE ROW LEVEL SECURITY;
```

### Run

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501).

---

## 📋 How to Use

### 1. Create a Case
Click **📋 New Case** → fill company name, CIN, sector, loan type, amount → **Create Case →**

### 2. Upload & Classify
Click **📂 Upload & Classify** → upload up to 5 documents → AI auto-classifies each → confirm or correct → review schema → **▶ Run Extraction & Analysis**

### 3. Continue to Analysis
Click **Continue to Analysis →** — analysis runs automatically with all extracted data pre-loaded.

### 4. Review Results
- AI decision · decisive factor · risk score · Five Cs radar · SHAP chart
- SWOT analysis · external research · early warning signals
- Download **Investment Assessment Report** (PDF + DOCX)

### 5. Close Case
Open case from Dashboard → **✅ Officer Assessment** tab → add collateral value, interest rate, due diligence notes → **🔒 Close Case**

---

## 🧪 Demo Test Data

Use the included synthetic demo files based on **Tata Capital Limited FY 2024-25** real annual report data:

| File | Type | Key Values |
|---|---|---|
| `TCL_Bank_Statement_FY25.pdf` | Bank Statement | Avg balance ₹1,185 Cr · 0 bounces |
| `TCL_ITR_AY2025-26.pdf` | ITR | Gross income ₹21,940 Cr · PAT ₹2,594 Cr · Net worth ₹20,559 Cr |
| `TCL_GSTR2A_FY25.xlsx` | GSTR-2A | 45 supplier invoices · ITC ₹1.68 Cr |
| `TCL_GSTR3B_FY25.xlsx` | GSTR-3B | ITC claimed ₹1.62 Cr · **3.88% variance** (timing difference) |
| `tata-capital-limited.pdf` | Annual Report | AUM ₹2,21,950 Cr · GNPA 1.87% · CAR 16.9% |

Expected result: **CONDITIONAL APPROVAL** · Risk Score ~0.350 · Five Cs ~7.7/10

---

## 🏗 Architecture

```
New Case (Supabase entity + case)
         ↓
Upload → PyMuPDF classifier (doc-type-aware page scoring, 40k chars)
         ↓
HITL confirmation → Dynamic schema editor
         ↓
Extraction: Regex → Groq LLM (8k chars, first+last) → fallback
         ↓
Enrichment: D/E from Annual Report / pledge from Shareholding → QualitativeInputs
         ↓
GST Reconciliation (supplier ITC sum vs 3B claimed)
         ↓
derive_from_documents() → DerivedFinancials
         ↓
five_cs.analyze() → Five Cs scores
         ↓
risk_engine.score() → XGBoost + SHAP + hard policy rules
         ↓
agent.analyze() → narrative + decisive factor (Groq + RAG)
         ↓
researcher.research_full() → news + sector macro + triangulation
         ↓
swot_generator.generate_swot() → SWOT from Five Cs + research
         ↓
cam_generator.generate_both() → Investment Assessment Report (PDF + DOCX)
         ↓
Save to Supabase → case_view shows full audit trail
         ↓
Officer: collateral + interest rate + notes → Close Case
```

---

## 🎨 Design

| Colour | Hex | Usage |
|---|---|---|
| Deep Navy | `#0A0E1A` | App background |
| Steel Blue | `#42A5F5` | Accents, links |
| Gold | `#E8B020` | Decisive factor, brand |
| Green | `#00E676` | APPROVE, positive signals |
| Amber | `#FFD740` | CONDITIONAL, warnings |
| Red | `#FF5252` | REJECT, risk flags |

Font stack: DM Serif Display (headings) · DM Sans (body) · JetBrains Mono (numbers)

---

## 📦 Dependencies

```
streamlit
groq>=0.9.0
supabase
google-generativeai
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
plotly
pymupdf
beautifulsoup4
```

---

## 📝 Changelog

### v2.0 (Current — Vivriti Capital Hackathon)
- **Full case lifecycle** — Supabase-backed entity/case management with officer closure
- **5 new document types** — ALM, Shareholding, Borrowing Profile, Annual Report, Portfolio
- **HITL classification pipeline** — auto-classify + confirm + dynamic schema editor
- **SWOT generation** — LLM-powered from Five Cs + research, saved to DB
- **Secondary research triangulation** — sector macro + LLM synthesis of all signals
- **Investment Assessment Report** — 5-page white cover, renamed from CAM
- **Officer Dashboard** as default landing page
- **Case View** — full audit trail: uploaded files, extractions, analysis, report
- **Continue → button** — seamless Upload & Classify → Analysis flow
- **Extraction confidence improved** — 40k char window, doc-type-aware page scoring
- **IntelliCredit branding** — removed bank name, positioned as AI engine

### v1.4
- Dual LLM backend (Gemini fallback + multi-key Groq rotation)
- GST reconciliation fix — supplier ITC column sum, skip embedded rows
- Hard policy rule — GST variance ≥ 50% floors to CONDITIONAL
- Decisive factor gold accent banner
- Auto tab switch to Results on analysis completion

### v1.3
- Bank-grade CAM PDF redesign — 10 sections, cover page, signature block
- Semi-circular risk gauge · decision colour coding

### v1.2
- Groq LLaMA 3.3 70B primary extractor · three-tier ITR extraction
- Loan limit respects requested amount · news relevance filtering

### v1.1
- Auto-fill pipeline · RAG ingestion · SHAP · Five Cs engine

### v1.0
- Initial release — document upload to CAM generation

---

## 🔮 Roadmap

### Multi-Client Portfolio Dashboard
Aggregate bank exposure by sector, risk category, geography. Track borrower financial health over successive applications. Flag deteriorating trends automatically.

### Government Scheme Recommendation Engine
Based on borrower sector, loan amount, and risk profile — surface applicable MUDRA, CGTMSE, SIDBI, PM Vishwakarma schemes with eligibility criteria, subsidy amounts, and direct application links.

---

## 👩‍💻 Author

**Niya Singh Shekhawat** — Team Codekarigars
GitHub: [@NiyaSinghShekhawat](https://github.com/NiyaSinghShekhawat)

---

*Built for the Vivriti Capital National AI/ML Hackathon. Not intended for production credit decisioning.*
