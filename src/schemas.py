# src/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# ─── ENUMS ───────────────────────────────────────────────────────────────────


class RiskCategory(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class DecisionType(str, Enum):
    APPROVE = "Approve"
    CONDITIONAL = "Conditional Approval"
    REJECT = "Reject"


class DocumentType(str, Enum):
    GST_RETURN = "GST_RETURN"
    ITR = "ITR"
    BANK_STATEMENT = "BANK_STATEMENT"
    ANNUAL_REPORT = "ANNUAL_REPORT"
    FINANCIAL_STATEMENT = "FINANCIAL_STATEMENT"
    LEGAL_NOTICE = "LEGAL_NOTICE"
    OTHER = "OTHER"

# ─── DOCUMENT PARSING ────────────────────────────────────────────────────────


class ExtractedTable(BaseModel):
    """A single table extracted from a document"""
    table_index: int
    headers: List[str] = []
    rows: List[List[str]] = []
    raw_text: str = ""


class ParsedDocument(BaseModel):
    """Output of the Docling parser for any document"""
    source_file: str
    document_type: DocumentType = DocumentType.OTHER
    raw_text: str = ""
    markdown: str = ""
    tables: List[ExtractedTable] = []
    page_count: int = 0
    extracted_at: datetime = Field(default_factory=datetime.now)
    error: Optional[str] = None

# ─── GST DATA ────────────────────────────────────────────────────────────────


class GSTData(BaseModel):
    """Extracted GST return data"""
    gstin: Optional[str] = None
    company_name: Optional[str] = None
    tax_period: Optional[str] = None
    turnover: float = 0.0
    igst: float = 0.0
    cgst: float = 0.0
    sgst: float = 0.0
    total_tax: float = 0.0
    itc_claimed: float = 0.0
    filing_date: Optional[str] = None
    filing_regular: bool = True


class GSTReconciliationResult(BaseModel):
    """Result of GSTR-2A vs GSTR-3B reconciliation"""
    total_mismatches: int = 0
    risk_flag: bool = False
    variance_pct: float = 0.0
    circular_trading_flag: bool = False
    mismatches: List[Dict[str, Any]] = []
    summary: str = ""

# ─── BANK STATEMENT DATA ─────────────────────────────────────────────────────


class BankStatementData(BaseModel):
    """Extracted bank statement data"""
    account_number: Optional[str] = None
    account_holder: Optional[str] = None
    bank_name: Optional[str] = None
    period: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    opening_balance: float = 0.0
    closing_balance: float = 0.0
    total_credits: float = 0.0
    total_debits: float = 0.0
    monthly_balances: List[float] = []
    monthly_credits: List[float] = []
    monthly_debits: List[float] = []
    emi_bounce_count: int = 0
    large_unusual_transactions: List[Dict[str, Any]] = []
    average_monthly_balance: float = 0.0

# ─── ITR DATA ────────────────────────────────────────────────────────────────


class ITRData(BaseModel):
    """Extracted ITR data"""
    pan: Optional[str] = None
    assessment_year: Optional[str] = None
    gross_income: float = 0.0
    net_income: float = 0.0
    tax_paid: float = 0.0
    tds: float = 0.0
    depreciation: float = 0.0
    net_worth: float = 0.0
    total_assets: float = 0.0
    total_liabilities: float = 0.0
    # Added: broken-out debt fields needed for accurate D/E ratio calculation.
    # total_liabilities includes trade payables and other non-debt items, so
    # using it directly overstates leverage. These capture borrowings only.
    long_term_debt: float = 0.0     # Term loans, debentures
    short_term_debt: float = 0.0    # CC limits, working capital loans
    revenue: float = 0.0            # Top-line revenue for growth rate calc
    ebitda: float = 0.0             # For DSCR computation
    interest_expense: float = 0.0   # For DSCR computation

# ─── DERIVED FINANCIALS ──────────────────────────────────────────────────────


class DerivedFinancials(BaseModel):
    """
    Auto-computed financial ratios derived from uploaded documents.
    Populated by RiskEngine.derive_from_documents() before the officer
    fills in QualitativeInputs — pre-fills the UI with document-backed values.

    Fields that cannot be derived (collateral, promoter score, site visit)
    remain None so the UI knows to require officer input for those only.
    """
    # Derived from ITR
    debt_equity_ratio: Optional[float] = None      # (LTD + STD) / net_worth
    net_worth_inr: Optional[float] = None          # Direct from ITR
    total_debt_inr: Optional[float] = None         # LTD + STD
    # current_assets / current_liabilities
    current_ratio: Optional[float] = None
    # EBITDA / (interest + principal)
    dscr: Optional[float] = None
    net_profit_margin: Optional[float] = None      # net_income / revenue

    # Derived from Bank Statement
    avg_monthly_balance_inr: Optional[float] = None
    monthly_credit_avg_inr: Optional[float] = None
    credit_utilisation_pct: Optional[float] = None  # debits / credits

    # Derived from GST
    gst_turnover_inr: Optional[float] = None
    itc_claimed_inr: Optional[float] = None
    effective_tax_rate_pct: Optional[float] = None  # total_tax / turnover

    # Flags
    data_completeness_pct: float = 0.0   # % of fields successfully derived
    # Warnings about missing/assumed values
    derivation_notes: List[str] = []
    # Names of fields successfully auto-derived from documents
    auto_filled_fields: List[str] = []

# ─── RESEARCH DATA ───────────────────────────────────────────────────────────


class NewsItem(BaseModel):
    """A single news article"""
    title: str
    url: str = ""
    date: str = ""
    source: str = ""
    is_negative: bool = False
    keywords_found: List[str] = []


class ResearchFindings(BaseModel):
    """Output of the research agent"""
    company_name: str
    negative_news: List[NewsItem] = []
    positive_news: List[NewsItem] = []
    litigation_found: bool = False
    litigation_details: List[str] = []
    mca_charges: List[Dict[str, Any]] = []
    rbi_sebi_actions: List[str] = []
    news_risk_score: float = 0.0   # 0-10
    research_summary: str = ""

# ─── FIVE Cs ─────────────────────────────────────────────────────────────────


class CScore(BaseModel):
    """Score for a single C"""
    score: float        # 0-10
    factors: List[str] = []
    details: Dict[str, Any] = {}
    summary: str = ""


class FiveCsResult(BaseModel):
    """Complete Five Cs assessment"""
    character: CScore
    capacity: CScore
    capital: CScore
    collateral: CScore
    conditions: CScore
    overall_score: float = 0.0   # Weighted average

# ─── RISK SCORING ────────────────────────────────────────────────────────────


class SHAPFactor(BaseModel):
    """A single SHAP explanation factor"""
    feature_name: str
    shap_value: float
    direction: str   # "increases risk" or "decreases risk"
    display_name: str = ""


class RiskPrediction(BaseModel):
    """Output of the risk scoring engine"""
    risk_score: float           # 0.0 to 1.0
    risk_category: RiskCategory
    decision: DecisionType
    loan_limit_inr: float
    interest_rate: float
    top_shap_factors: List[SHAPFactor] = []
    explanation: str = ""
    decisive_factor: str = ""
    early_warning_signals: List[str] = []

# ─── QUALITATIVE INPUTS ──────────────────────────────────────────────────────


class QualitativeInputs(BaseModel):
    """
    Officer's due diligence inputs.

    Fields marked AUTO are pre-filled from DerivedFinancials when documents
    are uploaded — officer can override but doesn't have to type them.
    Fields marked OFFICER must always be entered manually.
    """
    # OFFICER — cannot be derived from any document
    site_visit_notes: str = ""
    management_interview_notes: str = ""
    promoter_score: int = 5             # 1-10, integrity assessment
    sector_risk_score: int = 5          # 1-10, officer's sector view
    collateral_coverage: float = 0.6    # depends on what borrower offers

    # AUTO — pre-filled from ITR/Bank, officer can override
    debt_equity_ratio: float = 1.5      # derived: (LTD+STD) / net_worth
    net_worth_inr: float = 0.0          # derived: from ITR balance sheet

    # Tracks whether auto-fill was applied (for UI to show lock/edit icon)
    auto_filled_fields: List[str] = []


class QualitativeAdjustment(BaseModel):
    """How officer inputs adjusted the base risk score"""
    base_score: float
    adjusted_score: float
    adjustment_delta: float
    adjustment_reason: str

# ─── FINAL CAM OUTPUT ────────────────────────────────────────────────────────


class CreditAppraisalResult(BaseModel):
    """The complete output of the entire pipeline"""
    company_name: str
    cin: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.now)

    # Document data
    gst_data: Optional[GSTData] = None
    bank_data: Optional[BankStatementData] = None
    itr_data: Optional[ITRData] = None
    gst_reconciliation: Optional[GSTReconciliationResult] = None

    # Auto-derived ratios (populated before officer input screen)
    derived_financials: Optional[DerivedFinancials] = None

    # Research
    research: Optional[ResearchFindings] = None

    # Analysis
    five_cs: Optional[FiveCsResult] = None
    qualitative_inputs: Optional[QualitativeInputs] = None
    qualitative_adjustment: Optional[QualitativeAdjustment] = None

    # Final decision
    risk_prediction: Optional[RiskPrediction] = None

    # LLM reasoning
    reasoning_chain: str = ""

    # Report paths
    pdf_report_path: Optional[str] = None
    docx_report_path: Optional[str] = None
