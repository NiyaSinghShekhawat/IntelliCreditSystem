# config.py
import os
from pathlib import Path
from google import genai
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

# ─── PROJECT PATHS ───────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR / "src"
SAMPLES_DIR = BASE_DIR / "samples"
OUTPUTS_DIR = BASE_DIR / "outputs"
CHROMA_DIR = BASE_DIR / "chroma_db"

OUTPUTS_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(exist_ok=True)

# ─── LLM SETTINGS ────────────────────────────────────────────────────────────
LLM_BACKEND = "groq"

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "mistral:7b-instruct"
OLLAMA_EMBED_MODEL = "nomic-embed-text"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"

# ── Gemini fallback (secondary LLM when all Groq keys exhausted) ─────────────
GEMINI_API_KEY = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

# ── Multi-key rotation (add backup keys to .env as GROQ_API_KEY_2, _3 etc.) ──
# Automatically falls through to next key on rate limit (429) errors.
GROQ_API_KEYS = [
    k for k in [
        os.getenv("GROQ_API_KEY"),
        os.getenv("GROQ_API_KEY_2"),
        os.getenv("GROQ_API_KEY_3"),
        os.getenv("GROQ_API_KEY_4"),
    ]
    if k  # only include keys that are actually set
]

LLM_TEMPERATURE = 0.1
LLM_MAX_TOKENS = 2048
LLM_CONTEXT_WINDOW = 4096

# ─── DOCUMENT PARSING ────────────────────────────────────────────────────────
SUPPORTED_FORMATS = [".pdf", ".xlsx", ".xls", ".docx", ".png", ".jpg", ".jpeg"]
MAX_FILE_SIZE_MB = 50
OCR_LANGUAGE = "en"

# ─── VECTOR DATABASE (ChromaDB) ──────────────────────────────────────────────
CHROMA_COLLECTION_NAME = "intelli_credit_docs"
# FIX Note 3: use ChromaDB default, not Ollama
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K_RESULTS = 3

# ─── CREDIT SCORING THRESHOLDS ───────────────────────────────────────────────
RISK_THRESHOLDS = {
    "low":    0.30,
    "medium": 0.60,
    "high":   1.00,
}
AUTO_REJECT_THRESHOLD = 0.80
BASE_INTEREST_RATE = 8.5
MAX_RISK_SPREAD = 8.0
MAX_LOAN_LIMIT_INR = 500_000_000  # ₹50 Cr hard cap

# ─── GST RECONCILIATION ──────────────────────────────────────────────────────
GST_MISMATCH_THRESHOLD_PCT = 10.0
CIRCULAR_TRADING_THRESHOLD_PCT = 15.0
# FIX Note 1: lowered from 3 to 2 — with only 3 fields checked (ITC/turnover/tax),
# requiring 3 mismatches meant a 15% ITC + 12% turnover gap would pass unflagged.
GST_MISMATCH_MIN_COUNT = 2

# ─── RESEARCH AGENT ──────────────────────────────────────────────────────────
GDELT_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_MAX_RECORDS = 20
GDELT_TIMESPAN_DAYS = 90

NEGATIVE_KEYWORDS = [
    "fraud", "scam", "default", "bankrupt", "insolvency",
    "investigation", "arrest", "raid", "NPA", "wilful defaulter",
    "money laundering", "SFIO", "ED probe", "RBI penalty",
    "SEBI order", "court case", "litigation", "cheating"
]

INDIAN_NEWS_DOMAINS = [
    "economictimes.indiatimes.com",
    "livemint.com",
    "business-standard.com",
    "thehindu.com",
    "moneycontrol.com",
    "financialexpress.com",
    "ndtv.com",
    "hindustantimes.com",
    "timesofindia.com",
    "indiatoday.in",
    "businesstoday.in",
    "inc42.com",
    "vccircle.com",
    "cnbctv18.com",
    "reuters.com",
    "bloomberg.com",
]

# ─── FIVE Cs SCORING WEIGHTS ─────────────────────────────────────────────────
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
MAX_QUALITATIVE_ADJUSTMENT = 0.25

SITE_VISIT_RISK_KEYWORDS = [
    "idle", "shut", "closed", "40%", "low capacity", "empty",
    "poor condition", "dispute", "workers absent", "locked"
]
SITE_VISIT_POSITIVE_KEYWORDS = [
    "full capacity", "expanding", "new orders", "good condition",
    "busy", "export", "growth", "modern equipment"
]

# ─── APP SETTINGS ─────────────────────────────────────────────────────────────
APP_TITLE = "Intelli-Credit: AI-Powered Credit Appraisal"
APP_ICON = "🏦"
DEBUG_MODE = False
DEMO_MODE = False
