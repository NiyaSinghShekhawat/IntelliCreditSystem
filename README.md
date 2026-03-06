# 🏦 IntelliCredit — AI-Powered Credit Appraisal Engine

### Version 1.1 | Hackathon Build | March 2026


> An end-to-end AI credit decisioning system for Indian banks — combining document parsing, GST reconciliation, XGBoost risk scoring, LLM reasoning, and automated CAM generation.


---


## 📌 Overview


IntelliCredit automates the credit appraisal process for Indian SME lending. It ingests financial documents (GST returns, bank statements, ITR), reconciles GSTR-2A vs 3B for ITC manipulation detection, scores risk using XGBoost + SHAP, runs Five Cs analysis, researches external news and litigation, and generates a complete Credit Appraisal Memorandum (CAM) in both PDF and DOCX formats — all in under 60 seconds.


---


## ✅ Current Status (v1.1)


| Module | File | Status |
|--------|------|--------|
| Data Schemas | `src/schemas.py` | ✅ Complete |
| Document Parser | `src/parser.py` | ✅ Complete |
| Financial Extractor | `src/extractor.py` | ✅ Complete |
| GST Reconciler | `src/reconciler.py` | ✅ Complete |
| Prompt Templates | `src/prompts.py` | ✅ Complete |
| RAG Engine | `src/rag.py` | ✅ Complete |
| Credit Agent (LLM) | `src/agent.py` | ✅ Complete |
| Risk Engine | `src/risk_engine.py` | ✅ Complete |
| Five Cs Analyzer | `src/five_cs.py` | ✅ Complete |
| Research Agent | `src/researcher.py` | ✅ Complete |
| CAM Generator | `src/cam_generator.py` | ✅ Complete |
| Streamlit UI | `app.py` | ✅ Complete |
| Test Pipeline | `tests/test_pipeline.py` | 🔜 Pending |
| Google News Scraper | `src/researcher.py` upgrade | 🔜 Pending |


---


## 🏗️ Project Structure


```
IntelliCredit/
├── app.py                  # Streamlit UI — main entry point
├── config.py               # All settings, thresholds, API keys
├── src/
│   ├── schemas.py          # Pydantic data models
│   ├── parser.py           # Docling PDF/Excel/image parser
│   ├── extractor.py        # GST/ITR/bank data extraction
│   ├── reconciler.py       # GSTR-2A vs 3B mismatch detection
│   ├── agent.py            # LangChain + LLM orchestration
│   ├── prompts.py          # All prompt templates
│   ├── rag.py              # ChromaDB vector store
│   ├── risk_engine.py      # XGBoost + SHAP scoring
│   ├── five_cs.py          # Five Cs credit assessment
│   ├── researcher.py       # News + MCA + e-Courts scraper
│   └── cam_generator.py    # PDF + DOCX report builder
├── samples/
│   ├── low_risk/
│   ├── medium_risk/
│   └── high_risk/
├── outputs/                # Generated CAM reports
└── tests/
    └── test_pipeline.py    # End-to-end integration tests
```


---


## 🔧 Tech Stack


| Layer | Technology |
|-------|-----------|
| **LLM (Primary)** | Groq — LLaMA 3.3 70B (`llama-3.3-70b-versatile`) |
| **LLM (Offline Backup)** | Ollama — Mistral 7B Instruct (local) |
| **ML Scoring** | XGBoost + SHAP (synthetic training data) |
| **Document Parsing** | Docling (PDF, XLSX, DOCX, images) |
| **Vector Database** | ChromaDB (persistent, local) |
| **Embeddings** | all-MiniLM-L6-v2 (via ChromaDB) |
| **OCR** | RapidOCR + ONNX runtime |
| **LLM Framework** | LangChain (langchain-groq, langchain-ollama) |
| **UI** | Streamlit |
| **PDF Generation** | ReportLab |
| **DOCX Generation** | python-docx |
| **News Research** | GDELT API (free, no key) |
| **Charts** | Plotly |


---


## 🚀 Setup & Installation


### Prerequisites

- Python 3.11+
- Windows 10/11
- Ollama installed (for offline backup)
- Groq API key (free at console.groq.com)


### Installation


```bash
# Clone or create project folder
cd C:\Niya\Code\IntelliCredit

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install docling langchain langchain-community langchain-ollama
pip install langchain-groq chromadb xgboost scikit-learn shap
pip install numpy pandas reportlab python-docx streamlit plotly
pip install requests beautifulsoup4 paddleocr opencv-python-headless

# Pull Ollama models (offline backup)
ollama pull mistral:7b-instruct
ollama pull nomic-embed-text
```


### Configuration


Open `config.py` and set:

```python
LLM_BACKEND = "groq"           # or "ollama" for offline
GROQ_API_KEY = "gsk_xxxx..."   # your Groq API key
GROQ_MODEL = "llama-3.3-70b-versatile"
```


### Run


```bash
streamlit run app.py
# Opens at http://localhost:8501
```


---


## 🎯 Core Features


### 1. Document Parsing (Docling)

- Supports PDF, XLSX, DOCX, PNG, JPG
- Auto-detects document type (GST/Bank/ITR)
- Extracts tables and text including Hindi/bilingual documents
- OCR via RapidOCR for scanned documents


### 2. Financial Data Extraction

- **GST Returns** — GSTIN, turnover, IGST/CGST/SGST, ITC claimed, filing date
- **Bank Statements** — credits, debits, average balance, EMI bounces, large transactions
- **ITR** — PAN, gross income, net income, tax paid, net worth
- Indian number format support (1,00,000 / 10L / 2Cr)


### 3. GST Reconciliation (GSTR-2A vs 3B)

- Compares supplier-declared ITC (2A) vs company-claimed ITC (3B)
- Flags mismatches above 10% threshold
- Detects circular trading via bank credit vs GST turnover ratio
- Generates detailed mismatch report with variance percentages


### 4. XGBoost Risk Scoring + SHAP

- 12 financial features extracted from documents
- Trained on 500 synthetic Indian credit samples
- SHAP explainability — top 4 risk drivers shown
- Risk score: 0.0 (no risk) to 1.0 (maximum risk)
- Auto-thresholds: Low (<0.30), Medium (0.30-0.60), High (>0.60)


### 5. Five Cs Analysis

| C | Weight | Based On |
|---|--------|----------|
| Character | 25% | GST compliance, litigation, promoter score |
| Capacity | 30% | Cash flow, DSCR, EMI history |
| Capital | 20% | D/E ratio, net worth, ITR income |
| Collateral | 15% | Coverage ratio |
| Conditions | 10% | Sector risk, regulatory environment |


### 6. LLM Credit Reasoning (Groq LLaMA 3.3 70B)

- Structured reasoning chain across all data sources
- Extracts: Decision, Loan Limit, Interest Rate, Decisive Factor
|- Early warning signals for post-disbursement monitoring
- Qualitative score adjustment based on officer site visit notes (±0.25 max)
- RAG context injection from ChromaDB


### 7. External Research Agent

- **GDELT** — global news search (free, no key)
- **MCA21** — company charges and director info
- **e-Courts** — litigation detection
- **RBI/SEBI** — enforcement actions
- Mock research mode for offline/demo use
- Risk levels: low / medium / high


### 8. CAM Report Generation

- Professional bank-grade PDF via ReportLab
- DOCX version via python-docx
- Sections: Executive Summary, Reasoning Chain, Five Cs, SHAP Factors, Early Warnings, Research, Recommendation
- Auto-named: `CAM_{Company}_{Timestamp}.pdf`


---


## 📊 Risk Decision Logic


```
Risk Score → Category → Decision → Loan Limit
─────────────────────────────────────────────────
< 0.30     → LOW      → APPROVE      → Up to Rs.5 Cr
0.30-0.60  → MEDIUM   → CONDITIONAL  → Reduced limit
> 0.60     → HIGH     → REJECT       → No loan
> 0.80     → HIGH     → AUTO-REJECT  → Immediate reject

Interest Rate = 8.5% base + (risk_score × 8%) spread
```


---


## 🧪 Test Scenarios


### Scenario 1 — Low Risk (Expected: APPROVE)

```
Company: Safe Industries Pvt Ltd
D/E Ratio: 0.8 | Collateral: 120% | Promoter Score: 9
Site Visit: "Full capacity, new Tata Motors orders"
Mock Research: low
Expected: Score ~0.15-0.25, APPROVE, Rate ~8.5-9.5%
```


### Scenario 2 — Medium Risk (Expected: CONDITIONAL)

```
Company: ABC Manufacturing Pvt Ltd
D/E Ratio: 1.8 | Collateral: 80% | Promoter Score: 6
Site Visit: "60% capacity, some idle machinery"
Mock Research: medium
Expected: Score ~0.35-0.50, CONDITIONAL, Rate ~11-13%
```


### Scenario 3 — High Risk (Expected: REJECT)

```
Company: XYZ Traders Pvt Ltd
D/E Ratio: 4.2 | Collateral: 30% | Promoter Score: 2
Site Visit: "Factory shut, idle machinery, no orders"
Mock Research: high
Expected: Score ~0.75-0.90, REJECT, Rate 14%+
```


---


## 🔜 Roadmap (v1.2)


- [ ] Google News RSS scraper for real-time Indian news
- [ ] Economic Times + Moneycontrol BeautifulSoup scraper
- [ ] End-to-end test pipeline (`tests/test_pipeline.py`)
- [ ] Demo mode button (auto-fill scenarios)
- [ ] SHAP waterfall chart
- [ ] Loan condition generator
- [ ] Multi-year trend analysis from ITR


---


## 👤 Team


**Project:** IntelliCredit  
**Version:** 1.1  
**Build Date:** March 2026  
**Stack:** Python 3.11 + Streamlit + Groq + XGBoost + Docling + ChromaDB


---


## ⚠️ Disclaimer


This system is a prototype built for hackathon demonstration purposes.

All credit decisions are AI-generated and must be reviewed by a qualified

credit officer before any actual loan disbursement.

Mock research data is used for demonstration when live scraping is unavailable.

