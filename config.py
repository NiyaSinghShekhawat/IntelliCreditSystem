# config.py
import os
from pathlib import Path

# ─── PROJECT PATHS ───────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR / "src"
SAMPLES_DIR = BASE_DIR / "samples"
OUTPUTS_DIR = BASE_DIR / "outputs"
CHROMA_DIR = BASE_DIR / "chroma_db"

# Create output dir if it doesn't exist
OUTPUTS_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(exist_ok=True)

# ─── LLM SETTINGS ────────────────────────────────────────────────────────────
# Switch between "ollama" and "groq" depending on what's available
LLM_BACKEND = "groq"  # Change to "groq" if Ollama is slow/unavailable

# Ollama settings (local, free, no API key needed)
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "mistral:7b-instruct"
OLLAMA_EMBED_MODEL = "nomic-embed-text"

# Groq settings (cloud, free tier, faster)
# Get your free key at: https://console.groq.com
# NOTE: Do NOT hardcode real keys here. Set GROQ_API_KEY in your environment.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"

# Shared LLM params
LLM_TEMPERATURE = 0.1       # Low = more factual, less creative
LLM_MAX_TOKENS = 2048
LLM_CONTEXT_WINDOW = 4096

# ─── DOCUMENT PARSING ────────────────────────────────────────────────────────
SUPPORTED_FORMATS = [".pdf", ".xlsx", ".xls", ".docx", ".png", ".jpg", ".jpeg"]
MAX_FILE_SIZE_MB = 50
OCR_LANGUAGE = "en"         # Change to "hi" for Hindi-primary docs

# ─── VECTOR DATABASE (ChromaDB) ──────────────────────────────────────────────
CHROMA_COLLECTION_NAME = "intelli_credit_docs"
EMBEDDING_MODEL = "nomic-embed-text"   # Ollama embedding model
TOP_K_RESULTS = 3                       # How many chunks to retrieve for RAG

# ─── CREDIT SCORING THRESHOLDS ───────────────────────────────────────────────
# Risk score is 0.0 to 1.0
RISK_THRESHOLDS = {
    "low":    0.30,   # Below this = Low risk → Approve
    "medium": 0.60,   # Between low and this = Medium → Conditional
    "high":   1.00,   # Above medium = High risk → Reject
}

# Auto-reject if risk score exceeds this
AUTO_REJECT_THRESHOLD = 0.80

# Interest rate calculation: Base rate + risk spread
BASE_INTEREST_RATE = 8.5    # MCLR approximation (%)
MAX_RISK_SPREAD = 8.0       # Added on top of base for highest risk (%)

# Maximum loan limit cap (in INR)
MAX_LOAN_LIMIT_INR = 50_000_000   # 5 Crore

# ─── GST RECONCILIATION ──────────────────────────────────────────────────────
# Flag if GSTR-2A vs GSTR-3B mismatch exceeds this percentage
GST_MISMATCH_THRESHOLD_PCT = 10.0

# Flag if GST turnover vs Bank credits variance exceeds this
CIRCULAR_TRADING_THRESHOLD_PCT = 15.0

# Minimum number of mismatches before raising a risk flag
GST_MISMATCH_MIN_COUNT = 3

# ─── RESEARCH AGENT ──────────────────────────────────────────────────────────
# GDELT news API (free, no key needed)
GDELT_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_MAX_RECORDS = 20
GDELT_TIMESPAN_DAYS = 90    # Look back 90 days for news

# Keywords that trigger a negative news flag
NEGATIVE_KEYWORDS = [
    "fraud", "scam", "default", "bankrupt", "insolvency",
    "investigation", "arrest", "raid", "NPA", "wilful defaulter",
    "money laundering", "SFIO", "ED probe", "RBI penalty",
    "SEBI order", "court case", "litigation", "cheating"
]

# Indian news sources to prioritise
INDIAN_NEWS_DOMAINS = [
    "economictimes.indiatimes.com",
    "livemint.com",
    "business-standard.com",
    "thehindu.com",
    "moneycontrol.com",
    "financialexpress.com"
]

# ─── FIVE Cs SCORING WEIGHTS ─────────────────────────────────────────────────
# How much each C contributes to overall score (must sum to 1.0)
FIVE_CS_WEIGHTS = {
    "character":   0.25,
    "capacity":    0.30,
    "capital":     0.20,
    "collateral":  0.15,
    "conditions":  0.10,
}

# ─── CAM REPORT ──────────────────────────────────────────────────────────────
CAM_BANK_NAME = "Intelli-Credit Bank"
CAM_REPORT_TITLE = "Credit Appraisal Memorandum"
CAM_AUTHOR = "Intelli-Credit AI Engine"

# ─── QUALITATIVE SCORE ADJUSTMENT ────────────────────────────────────────────
# How much a site visit / management note can shift the final risk score
MAX_QUALITATIVE_ADJUSTMENT = 0.25   # Max ±0.25 shift from officer inputs

# Keywords in site visit notes that increase risk
SITE_VISIT_RISK_KEYWORDS = [
    "idle", "shut", "closed", "40%", "low capacity", "empty",
    "poor condition", "dispute", "workers absent", "locked"
]

# Keywords that decrease risk (positive signals)
SITE_VISIT_POSITIVE_KEYWORDS = [
    "full capacity", "expanding", "new orders", "good condition",
    "busy", "export", "growth", "modern equipment"
]

# ─── APP SETTINGS ─────────────────────────────────────────────────────────────
APP_TITLE = "Intelli-Credit: AI-Powered Credit Appraisal"
APP_ICON = "🏦"
DEBUG_MODE = False          # Set True to see extra logs in terminal
DEMO_MODE = False           # Set True to load pre-cached demo outputs
