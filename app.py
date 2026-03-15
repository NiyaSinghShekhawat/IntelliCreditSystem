from datetime import datetime
import os
import tempfile
import streamlit as st
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IntelliCredit — AI Credit Engine",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── GLOBAL CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&family=JetBrains+Mono:wght@400;500&display=swap');
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    /* ── Core palette ── */
    --bg:         #0A0E1A;
    --surface:    #0D1226;
    --surface-2:  #111830;
    --surface-3:  #161E38;
    --border:     #1E2A4A;
    --border-2:   #243052;

    /* ── Brand ── */
    --navy:       #1A237E;
    --navy-light: #283593;
    --blue:       #1565C0;
    --blue-light: #1976D2;
    --steel:      #42A5F5;
    --steel-dim:  #1E88E5;
    --teal:       #00BFA5;
    --teal-dim:   #00897B;
    --gold:       #C9970A;
    --gold-light: #E8B020;

    /* ── Text ── */
    --text:       #F0F2FF;   /* was #E8EAF6 — brighter white */
    --text-sec:   #C5CAE9;   /* was #9FA8DA — much more visible */
    --text-muted: #7986CB;   /* was #5C6BC0 — lifted from near-invisible */
    --text-hint:  #5C6BC0;   /* was #3949AB */
}

    /* ── Semantic ── */
    --approve:    #00E676;
    --approve-bg: #0A2218;
    --approve-bd: #1B5E20;
    --warn:       #FFD740;
    --warn-bg:    #1A1400;
    --warn-bd:    #F57F17;
    --reject:     #FF5252;
    --reject-bg:  #1A0000;
    --reject-bd:  #B71C1C;
    --info:       #40C4FF;
    --info-bg:    #001829;
    --info-bd:    #0277BD;
}

/* ── Base ────────────────────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    color: var(--text) !important;
    background: var(--bg) !important;
}
.stApp { background: var(--bg) !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2.5rem 3rem !important; max-width: 1440px !important; }

/* ── Scrollbar ───────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--surface); }
::-webkit-scrollbar-thumb { background: var(--border-2); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--steel-dim); }

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text-sec) !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: var(--text) !important; }
[data-testid="stSidebar"] label {
    color: var(--text-muted) !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea {
    background: var(--surface-3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
}
[data-testid="stSidebar"] hr { border-color: var(--border) !important; }

/* Sidebar nav buttons */
[data-testid="stSidebar"] .stButton > button {
    background: var(--surface-3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text-sec) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.84rem !important;
    font-weight: 500 !important;
    width: 100% !important;
    padding: 0.55rem 1rem !important;
    transition: all 0.2s !important;
    text-align: left !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--navy) !important;
    border-color: var(--blue-light) !important;
    color: var(--text) !important;
}

/* Sidebar selectbox */
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: var(--surface-3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] span { color: var(--text) !important; }
[data-testid="stSidebar"] .stNumberInput > div {
    background: var(--surface-3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] .stNumberInput input {
    color: var(--text) !important;
    background: transparent !important;
    border: none !important;
}
[data-testid="stSidebar"] .stNumberInput button {
    background: var(--surface-2) !important;
    border: none !important;
    color: var(--text-sec) !important;
}

/* ── Main buttons ─────────────────────────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, var(--navy), var(--blue)) !important;
    color: var(--gold-light) !important;
    border: 1px solid var(--blue-light) !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.04em !important;
    padding: 0.6rem 1.4rem !important;
    box-shadow: 0 4px 12px rgba(26,35,126,0.4) !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, var(--navy-light), var(--blue-light)) !important;
    box-shadow: 0 6px 18px rgba(26,35,126,0.6) !important;
}
.stButton > button:disabled {
    background: var(--surface-3) !important;
    color: var(--text-muted) !important;
    border-color: var(--border) !important;
    box-shadow: none !important;
}

/* ── Tabs ─────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-sec) !important;
    border-radius: 7px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    padding: 0.45rem 1.1rem !important;
    transition: all 0.2s !important;
}
.stTabs [aria-selected="true"] {
    background: var(--navy) !important;
    color: var(--gold-light) !important;
}

/* ── Form inputs ──────────────────────────────────────────────────────────── */
.stTextInput input,
.stTextArea textarea,
.stNumberInput input {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput input:focus,
.stTextArea textarea:focus,
.stNumberInput input:focus {
    border-color: var(--steel) !important;
    box-shadow: 0 0 0 3px rgba(66,165,245,0.15) !important;
}
.stTextInput label, .stTextArea label,
.stSelectbox label, .stNumberInput label,
.stSlider label, .stFileUploader label,
.stCheckbox label {
    color: var(--text-sec) !important;
    font-size: 0.80rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
}

/* Selectbox */
[data-baseweb="select"] > div {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
}
[data-baseweb="select"] span { color: var(--text) !important; }
[data-baseweb="popover"] > div {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
}
[role="option"] {
    background: var(--surface-2) !important;
    color: var(--text-sec) !important;
}
[role="option"]:hover {
    background: var(--navy) !important;
    color: var(--text) !important;
}

/* Slider */
[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
    background: var(--steel) !important;
    border-color: var(--steel) !important;
}

/* Checkbox */
[data-testid="stCheckbox"] span {
    border-color: var(--border) !important;
    border-radius: 4px !important;
}
[data-testid="stCheckbox"] input:checked + span {
    background: var(--blue) !important;
    border-color: var(--steel) !important;
}

/* ── Metrics ──────────────────────────────────────────────────────────────── */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, var(--surface), var(--surface-2)) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 1rem 1.2rem !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.3) !important;
}
[data-testid="metric-container"] label {
    color: var(--text-sec) !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    font-weight: 600 !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: var(--gold-light) !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* ── Alerts ───────────────────────────────────────────────────────────────── */
.stAlert { border-radius: 10px !important; }
div[data-testid="stNotification"] {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
}

/* ── Expanders ────────────────────────────────────────────────────────────── */
.stExpander {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}
.stExpander summary { color: var(--text-sec) !important; font-weight: 500 !important; }
.stExpander summary:hover { color: var(--text) !important; }

/* ── Download buttons ─────────────────────────────────────────────────────── */
.stDownloadButton > button {
    background: var(--surface-2) !important;
    color: var(--steel) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}
.stDownloadButton > button:hover {
    background: var(--surface-3) !important;
    border-color: var(--steel) !important;
    color: var(--text) !important;
}

/* ── File uploader ────────────────────────────────────────────────────────── */
[data-testid="stFileUploader"] { background: transparent !important; }
[data-testid="stFileUploadDropzone"] {
    background: var(--surface-2) !important;
    border: 1.5px dashed var(--border-2) !important;
    border-radius: 10px !important;
    color: var(--text-sec) !important;
}
[data-testid="stFileUploadDropzone"]:hover {
    border-color: var(--steel) !important;
    background: var(--surface-3) !important;
}
[data-testid="stFileUploadDropzone"] span { color: var(--text-sec) !important; }
[data-testid="stFileUploadDropzone"] button {
    background: var(--navy) !important;
    color: var(--gold-light) !important;
    border: 1px solid var(--blue-light) !important;
    border-radius: 6px !important;
    font-size: 0.8rem !important;
}
[data-testid="stFileUploaderFileName"] {
    color: var(--steel) !important;
    font-size: 0.82rem !important;
}

/* ── Data editor ──────────────────────────────────────────────────────────── */
[data-testid="stDataEditor"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}
[data-testid="stDataEditor"] * { color: var(--text) !important; }
[data-testid="stDataEditor"] th {
    background: var(--surface-3) !important;
    color: var(--text-sec) !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
}
[data-testid="stDataEditor"] td {
    color: var(--text) !important;
    background: var(--surface) !important;
    border-color: var(--border) !important;
}
[data-testid="stDataEditor"] input {
    color: var(--text) !important;
    background: var(--surface-2) !important;
}
[data-testid="stDataFrame"] * { color: var(--text) !important; }
[data-testid="stDataFrame"] th {
    background: var(--surface-3) !important;
    color: var(--text-sec) !important;
}

/* ── Caption / spinner ────────────────────────────────────────────────────── */
.stCaption, [data-testid="stCaptionContainer"] p {
    color: var(--text-muted) !important;
    font-size: 0.78rem !important;
}
[data-testid="stSpinner"] p,
div[data-testid="stSpinner"] > div > p {
    color: var(--text-sec) !important;
    font-size: 0.9rem !important;
}

/* ── Custom components ────────────────────────────────────────────────────── */

/* Page header */
.ic-page-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1.4rem 1.8rem;
    background: linear-gradient(135deg, var(--surface), var(--surface-2));
    border: 1px solid var(--border);
    border-radius: 14px;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
}
.ic-logo-mark {
    width: 44px; height: 44px;
    background: var(--navy);
    border: 1px solid var(--blue-light);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.3rem; flex-shrink: 0;
}
.ic-page-header h1 {
    font-family: 'DM Serif Display', serif !important;
    font-size: 1.5rem !important;
    color: var(--text) !important;
    margin: 0 !important;
    line-height: 1.2 !important;
}
.ic-page-header p {
    font-size: 0.82rem !important;
    color: var(--text-muted) !important;
    margin: 2px 0 0 !important;
}
.ic-badge-row { display: flex; gap: 6px; margin-top: 6px; flex-wrap: wrap; }
.ic-badge {
    font-size: 0.68rem; font-weight: 600; letter-spacing: 0.06em;
    text-transform: uppercase; padding: 2px 8px; border-radius: 20px;
    background: var(--surface-3); border: 1px solid var(--border);
    color: var(--text-muted);
}

/* Section title */
.ic-section-title {
    font-size: 0.72rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.1em;
    color: var(--text-muted);
    margin: 0 0 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
}

/* Card */
.ic-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.4rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
}

/* Upload zone */
.ic-upload-zone {
    border: none !important;
    padding: 0 !important;
    margin-bottom: 0.75rem !important;
    background: transparent !important;
}
.ic-upload-label {
    font-size: 0.78rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.07em;
    color: var(--text-sec); margin-bottom: 2px; display: block;
}
.ic-upload-desc {
    font-size: 0.74rem; color: var(--text-muted);
    margin-bottom: 0.5rem; display: block;
}

/* Divider */
.ic-divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: 1.2rem 0;
}

/* Decision blocks */
.decision-approve {
    background: var(--approve-bg);
    border: 1px solid var(--approve-bd);
    border-left: 5px solid var(--approve);
    padding: 1rem 1.4rem; border-radius: 10px;
    font-size: 1.15rem; font-weight: 700;
    color: var(--approve); margin-bottom: 0.75rem;
    font-family: 'DM Sans', sans-serif;
    box-shadow: 0 4px 20px rgba(0,230,118,0.15);
}
.decision-reject {
    background: var(--reject-bg);
    border: 1px solid var(--reject-bd);
    border-left: 5px solid var(--reject);
    padding: 1rem 1.4rem; border-radius: 10px;
    font-size: 1.15rem; font-weight: 700;
    color: var(--reject); margin-bottom: 0.75rem;
    font-family: 'DM Sans', sans-serif;
    box-shadow: 0 4px 20px rgba(255,82,82,0.15);
}
.decision-conditional {
    background: var(--warn-bg);
    border: 1px solid var(--warn-bd);
    border-left: 5px solid var(--warn);
    padding: 1rem 1.4rem; border-radius: 10px;
    font-size: 1.15rem; font-weight: 700;
    color: var(--warn); margin-bottom: 0.75rem;
    font-family: 'DM Sans', sans-serif;
    box-shadow: 0 4px 20px rgba(255,215,64,0.15);
}

/* Decisive factor */
.decisive-factor {
    background: var(--info-bg);
    border-left: 4px solid var(--steel);
    padding: 0.7rem 1.1rem; border-radius: 8px;
    margin: 0 0 1rem; font-size: 0.88rem; color: var(--text);
}
.decisive-factor strong { color: var(--gold-light); font-weight: 700; }

/* Warning / flag boxes */
.warning-box {
    background: var(--warn-bg);
    border-left: 3px solid var(--warn);
    padding: 0.65rem 1rem; border-radius: 6px;
    margin: 0.3rem 0; color: var(--warn); font-size: 0.85rem;
}
.flag-box {
    background: var(--reject-bg);
    border-left: 3px solid var(--reject);
    padding: 0.65rem 1rem; border-radius: 6px;
    margin: 0.3rem 0; color: var(--reject); font-size: 0.85rem;
}

/* News boxes */
.news-negative {
    background: var(--reject-bg);
    border-left: 3px solid var(--reject);
    padding: 0.55rem 0.85rem; border-radius: 6px;
    margin: 0.3rem 0; font-size: 0.83rem; color: var(--reject);
}
.news-positive {
    background: var(--approve-bg);
    border-left: 3px solid var(--approve);
    padding: 0.55rem 0.85rem; border-radius: 6px;
    margin: 0.3rem 0; font-size: 0.83rem; color: var(--approve);
}

/* Dashboard metrics */
.dash-metric {
    background: linear-gradient(135deg, var(--surface), var(--surface-2));
    border: 1px solid var(--border);
    border-radius: 12px; padding: 1rem 1.2rem;
    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
}
.dm-label {
    font-size: 0.68rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.1em;
    color: var(--text-muted); margin-bottom: 4px;
}
.dm-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.6rem; font-weight: 700;
    color: var(--gold-light); line-height: 1.1;
}

/* Dashboard table */
.dash-col-header {
    font-size: 0.68rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.1em;
    color: var(--text-muted); padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border); margin-bottom: 0.5rem;
}

/* Badges */
.badge {
    display: inline-block; font-size: 0.68rem;
    font-weight: 700; letter-spacing: 0.07em;
    text-transform: uppercase; padding: 3px 9px; border-radius: 20px;
}
.badge-approve { background: var(--approve-bg); color: var(--approve); border: 1px solid var(--approve-bd); }
.badge-reject  { background: var(--reject-bg);  color: var(--reject);  border: 1px solid var(--reject-bd); }
.badge-warn    { background: var(--warn-bg);     color: var(--warn);    border: 1px solid var(--warn-bd); }
.badge-progress{ background: var(--info-bg);     color: var(--info);    border: 1px solid var(--info-bd); }

/* Step bar */
.step-bar {
    display: flex; gap: 0; margin-bottom: 1.5rem;
    border-radius: 8px; overflow: hidden;
    border: 1px solid var(--border);
}
.step-item {
    flex: 1; padding: 0.6rem 0.8rem;
    font-size: 0.78rem; font-weight: 500;
    text-align: center;
    background: var(--surface-2); color: var(--text-muted);
    border-right: 1px solid var(--border); letter-spacing: 0.03em;
}
.step-item:last-child { border-right: none; }
.step-item.active { background: var(--navy); color: var(--gold-light); font-weight: 600; }
.step-item.done   { background: var(--approve-bg); color: var(--approve); font-weight: 600; }

/* Sidebar brand */
.sidebar-brand {
    padding: 1.2rem 0 1rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1rem;
}
.brand-name {
    font-family: 'DM Serif Display', serif;
    font-size: 1.3rem; color: var(--gold);
    letter-spacing: 0.02em;
}
.brand-sub {
    font-size: 0.68rem; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.1em; margin-top: 2px;
}

/* Extraction results table */
.ic-extract-table {
    width: 100%; border-collapse: collapse; font-size: 0.85rem;
}
.ic-extract-table th {
    background: var(--surface-3); color: var(--text-sec);
    font-size: 0.72rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.08em;
    padding: 0.6rem 1rem; text-align: left;
    border-bottom: 1px solid var(--border);
}
.ic-extract-table td {
    padding: 0.55rem 1rem; color: var(--text);
    border-bottom: 1px solid var(--border);
}
.ic-extract-table tr:last-child td { border-bottom: none; }
.ic-extract-table td:first-child {
    color: var(--text-sec); font-weight: 500;
    font-family: 'JetBrains Mono', monospace; font-size: 0.78rem;
}
.ic-extract-table td:last-child {
    color: var(--steel); font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
}

/* General text */
.stMarkdown p, .stMarkdown li { color: var(--text) !important; }
h1, h2, h3, h4, h5, h6 { color: var(--text) !important; }
.stExpander p, .stExpander span { color: var(--text-sec) !important; }
[data-testid="stCaptionContainer"] p { color: var(--text-muted) !important; }
.ic-card p, .ic-card span, .ic-card div { color: var(--text) !important; }
            
/* ── High contrast text fixes ─────────────────────────────────────────────── */

/* All markdown and general text */
p, span, li, div, label {
    color: var(--text) !important;
}

/* Section titles — more visible */
.ic-section-title {
    color: #7986CB !important;
}

/* Card inner text */
.ic-card, .ic-card * {
    color: var(--text) !important;
}

/* Dashboard column headers */
.dash-col-header { color: #7986CB !important; }

/* Metric labels */
[data-testid="metric-container"] label {
    color: #C5CAE9 !important;
}

/* Expander headers */
.stExpander summary, .stExpander summary * {
    color: #C5CAE9 !important;
    font-weight: 500 !important;
}

/* Expander content */
details[open] .stExpander > div,
.stExpander [data-testid="stExpanderDetails"] * {
    color: var(--text) !important;
}

/* Sidebar text — all elements visible */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] label {
    color: #C5CAE9 !important;
}

/* Step bar text */
.step-item { color: #7986CB !important; }
.step-item.active { color: var(--gold-light) !important; }
.step-item.done { color: var(--approve) !important; }

/* Badge text */
.ic-badge { color: #C5CAE9 !important; }

/* Review row labels in onboarding */
.ic-card [style*="text-muted"] { color: #7986CB !important; }

/* Captions */
.stCaption p,
[data-testid="stCaptionContainer"] p {
    color: #7986CB !important;
}

/* Info/success/warning/error alert text */
.stAlert p,
.stAlert div,
div[data-testid="stNotification"] p {
    color: var(--text) !important;
}

/* Selectbox selected value */
[data-baseweb="select"] [data-testid="stMarkdown"] p,
[data-baseweb="select"] div {
    color: var(--text) !important;
}

/* Number input text */
.stNumberInput input { color: var(--text) !important; }

/* Slider value labels */
[data-testid="stSlider"] [data-testid="stTickBarMin"],
[data-testid="stSlider"] [data-testid="stTickBarMax"] {
    color: #7986CB !important;
}
                        
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE ────────────────────────────────────────────────────────────
for key, default in {
    "page": "analysis", "entity_id": None, "case_id": None,
    "onboard_step": 1, "demo": {}, "analysis_result": None,
    "switch_to_results": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
demo = st.session_state.get("demo", {})

with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="brand-name">IntelliCredit</div>
        <div class="brand-sub">AI Credit Intelligence · v2.0</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🏠  Officer Dashboard", use_container_width=True):
        st.session_state.page = "dashboard"
        st.rerun()
    if st.button("➕  New Analysis", use_container_width=True):
        st.session_state.page = "analysis"
        st.rerun()
    if st.button("📂  Upload & Classify", use_container_width=True):
        st.session_state.page = "classify"
        st.rerun()
    if st.button("📋  New Case", use_container_width=True):
        st.session_state.page = "onboarding"
        st.session_state.ob_step = 1
        st.session_state.ob_form = {}
        st.rerun()

    st.markdown("---")
    st.markdown("### 📋 Loan Application")

    company_name = st.text_input(
        "Company Name *", value=demo.get("company", ""), placeholder="ABC Private Limited")
    promoter_name = st.text_input(
        "Promoter / Director Name", value=demo.get("promoter", ""), placeholder="Mr. Rajesh Kumar")
    loan_amount_requested = st.number_input("Loan Amount (₹)", min_value=100000, max_value=500_000_000,
                                            value=demo.get("loan", 2500000), step=100000, format="%d")
    purpose_options = ["Working Capital", "Term Loan",
                       "Machinery", "Expansion", "Trade Finance", "Other"]
    default_purpose = demo.get("purpose", "Working Capital")
    purpose_index = purpose_options.index(
        default_purpose) if default_purpose in purpose_options else 0
    loan_purpose = st.selectbox(
        "Loan Purpose", purpose_options, index=purpose_index)

    st.markdown("---")
    st.markdown("### 🎯 Demo Mode")
    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        demo_low = st.button("🟢 Low",  use_container_width=True)
    with col_d2:
        demo_med = st.button("🟡 Med",  use_container_width=True)
    with col_d3:
        demo_high = st.button("🔴 High", use_container_width=True)

    DEMO_SCENARIOS = {
        "low":    {"company": "Safe Industries Pvt Ltd", "promoter": "Rajesh Mehta", "loan": 2500000, "purpose": "Working Capital", "site_visit": "Factory running at full capacity. New orders from Tata Motors. Expanding warehouse. Good condition machinery.", "mgmt": "Promoter has 15 years experience. Clear business plan. Very cooperative during interview.", "de_ratio": 0.8, "collateral": 120, "net_worth": 15000000, "promoter_score": 9, "sector_risk": 3, "mock_level": "low"},
        "medium": {"company": "ABC Manufacturing Pvt Ltd", "promoter": "Suresh Kumar", "loan": 5000000, "purpose": "Machinery", "site_visit": "Factory operational but running at 60% capacity. Some idle machinery observed. Management cooperative.", "mgmt": "Promoter has 8 years experience. Adequate business plan presented.", "de_ratio": 1.8, "collateral": 80, "net_worth": 5000000, "promoter_score": 6, "sector_risk": 5, "mock_level": "medium"},
        "high":   {"company": "XYZ Traders Pvt Ltd", "promoter": "Vikram Shah", "loan": 10000000, "purpose": "Working Capital", "site_visit": "Factory found shut during visit. Idle machinery observed. Poor condition. Workers said no orders since 3 months.", "mgmt": "Promoter was evasive during interview. Could not explain fund utilization.", "de_ratio": 4.2, "collateral": 30, "net_worth": 500000, "promoter_score": 2, "sector_risk": 9, "mock_level": "high"},
    }

    if demo_low:
        st.session_state["demo"] = DEMO_SCENARIOS["low"]
        st.success("🟢 Low risk loaded")
        st.rerun()
    elif demo_med:
        st.session_state["demo"] = DEMO_SCENARIOS["medium"]
        st.warning("🟡 Medium risk loaded")
        st.rerun()
    elif demo_high:
        st.session_state["demo"] = DEMO_SCENARIOS["high"]
        st.error("🔴 High risk loaded")
        st.rerun()

    demo = st.session_state.get("demo", {})

    st.markdown("---")
    st.markdown("### ⚙️ Settings")
    use_mock_research = st.checkbox(
        "Use Mock Research Data", value=True, help="Use when internet is unavailable")
    mock_risk_level = st.select_slider("Mock Risk Level", options=["low", "medium", "high"],
                                       value=demo.get("mock_level", "medium")) if use_mock_research else "medium"

    st.markdown("---")
    st.markdown("<div style='font-size:0.72rem;color:#3A5A7A;line-height:1.7;'><strong style='color:#5A8AAA;'>IntelliCredit v2.0</strong><br>Groq LLaMA 3.3 70B · XGBoost + SHAP<br>Docling · ChromaDB · Supabase<br><span style='color:#2A4A6A;'>Codekarigars · Vivriti Capital</span></div>", unsafe_allow_html=True)


# ─── ENGINE LOADER ────────────────────────────────────────────────────────────
@st.cache_resource
def load_engines():
    from src.parser import DocumentParser
    from src.extractor import FinancialExtractor
    from src.reconciler import GSTReconciler
    from src.researcher import ResearchAgent
    from src.risk_engine import RiskEngine
    from src.five_cs import FiveCsAnalyzer
    from src.agent import CreditAgent
    from src.cam_generator import CAMGenerator
    return {"parser": DocumentParser(), "extractor": FinancialExtractor(), "reconciler": GSTReconciler(),
            "researcher": ResearchAgent(), "risk_engine": RiskEngine(), "five_cs": FiveCsAnalyzer(),
            "agent": CreditAgent(), "cam": CAMGenerator()}


# ─── DASHBOARD ────────────────────────────────────────────────────────────────
def render_dashboard():
    try:
        from src.database import get_all_cases
        cases = get_all_cases()
    except Exception:
        cases = []

    st.markdown("""
    <div class="ic-page-header">
        <div class="ic-logo-mark">🏦</div>
        <div>
            <h1>Officer Dashboard</h1>
            <p>Active and completed credit assessment cases · Codekarigars</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    total = len(cases)
    approved = sum(1 for c in cases if c.get("decision") == "APPROVE")
    conditional = sum(1 for c in cases if c.get("decision") == "CONDITIONAL")
    rejected = sum(1 for c in cases if c.get("decision") == "REJECT")
    in_progress = sum(1 for c in cases if c.get("status") == "IN_PROGRESS")

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, (lbl, val, clr) in zip([c1, c2, c3, c4, c5], [
        ("Total Cases", total, "#2C2C2C"), ("In Progress", in_progress, "#328CC1"),
        ("Approved", approved, "#0E7A4A"), ("Conditional",
                                            conditional, "#B86A00"), ("Rejected", rejected, "#B0001E")
    ]):
        with col:
            st.markdown(
                f"<div class='dash-metric'><div class='dm-label'>{lbl}</div><div class='dm-value' style='color:{clr};'>{val}</div></div>", unsafe_allow_html=True)

    st.markdown("<hr class='ic-divider'>", unsafe_allow_html=True)

    fc1, fc2, fc3 = st.columns([2, 2, 4])
    with fc1:
        filter_dec = st.selectbox("Decision", [
                                  "All", "APPROVE", "CONDITIONAL", "REJECT", "IN PROGRESS"], label_visibility="collapsed")
    with fc2:
        sectors = ["All Sectors"]+sorted(set(c.get("entities", {}).get(
            "sector", "") for c in cases if c.get("entities", {}).get("sector")))
        filter_sec = st.selectbox(
            "Sector", sectors, label_visibility="collapsed")
    with fc3:
        if st.button("➕  Start New Analysis", type="primary"):
            st.session_state.page = "analysis"
            st.rerun()

    filtered = [c for c in cases if
                (filter_dec == "All" or (filter_dec == "IN PROGRESS" and c.get("status") == "IN_PROGRESS") or c.get("decision") == filter_dec) and
                (filter_sec == "All Sectors" or c.get("entities", {}).get("sector") == filter_sec)]

    st.markdown(
        f"<p style='font-size:0.78rem;color:var(--text-muted);margin-bottom:0.6rem;'>{len(filtered)} case(s)</p>", unsafe_allow_html=True)

    if not filtered:
        st.markdown("<div class='ic-card' style='text-align:center;padding:3rem;'><div style='font-size:2.5rem;margin-bottom:0.75rem;'>📂</div><div style='font-weight:600;color:var(--text-sec);'>No cases found</div><div style='font-size:0.85rem;color:var(--text-muted);margin-top:0.3rem;'>Run an analysis to see it appear here</div></div>", unsafe_allow_html=True)
        return

    h1, h2, h3, h4, h5, h6 = st.columns([3, 2, 1.5, 1.5, 1.5, 1.2])
    for col, lbl in zip([h1, h2, h3, h4, h5, h6], ["Company", "Sector", "Loan Amount", "Risk Score", "Decision", "Action"]):
        col.markdown(
            f"<div class='dash-col-header'>{lbl}</div>", unsafe_allow_html=True)

    for case in filtered:
        entity = case.get("entities") or {}
        c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 1.5, 1.5, 1.5, 1.2])
        with c1:
            st.markdown(
                f"<div style='font-weight:600;font-size:0.9rem;color:var(--navy);'>{entity.get('company_name','—')}</div><div style='font-size:0.73rem;color:var(--text-muted);font-family:JetBrains Mono,monospace;'>{entity.get('loan_type','')}</div>", unsafe_allow_html=True)
        with c2:
            st.markdown(
                f"<div style='font-size:0.85rem;color:var(--text-sec);'>{entity.get('sector','—')}</div>", unsafe_allow_html=True)
        with c3:
            amt = entity.get('loan_amount_cr')
            st.markdown(
                f"<div style='font-family:JetBrains Mono,monospace;font-size:0.85rem;'>{'₹'+str(amt)+' Cr' if amt else '—'}</div>", unsafe_allow_html=True)
        with c4:
            score = case.get("risk_score")
            clr = "#0E7A4A" if score and score < 0.35 else "#B86A00" if score and score < 0.65 else "#B0001E" if score else "var(--text-muted)"
            st.markdown(
                f"<div style='font-family:JetBrains Mono,monospace;font-size:0.88rem;font-weight:700;color:{clr};'>{'%.3f'%score if score else '—'}</div>", unsafe_allow_html=True)
        with c5:
            dec = (case.get("decision") or "").upper()
            status = case.get("status", "")
            badge = "<span class='badge badge-progress'>In Progress</span>" if status == "IN_PROGRESS" else "<span class='badge badge-approve'>Approve</span>" if dec == "APPROVE" else "<span class='badge badge-warn'>Conditional</span>" if dec == "CONDITIONAL" else "<span class='badge badge-reject'>Reject</span>" if dec == "REJECT" else "<span class='badge badge-progress'>Pending</span>"
            st.markdown(badge, unsafe_allow_html=True)
        with c6:
            if st.button("Open →", key=f"open_{case['id']}"):
                st.session_state.entity_id = case.get("entity_id")
                st.session_state.case_id = case["id"]
                st.session_state.page = "case_view"  # ← was "analysis", now "case_view"
                st.rerun()
        st.markdown("<hr class='ic-divider' style='margin:0.4rem 0;'>",
                    unsafe_allow_html=True)


# ─── ANALYSIS PAGE ────────────────────────────────────────────────────────────
def render_analysis():
    st.markdown("""
    <div class="ic-page-header">
        <div class="ic-logo-mark">🔍</div>
        <div>
            <h1>Credit Analysis</h1>
            <p>AI-powered appraisal · GST reconciliation · Five Cs · XGBoost + SHAP</p>
            <div class="ic-badge-row">
                <span class="ic-badge">Groq LLaMA 3.3 70B</span>
                <span class="ic-badge">XGBoost + SHAP</span>
                <span class="ic-badge">Docling Parser</span>
                <span class="ic-badge">ChromaDB RAG</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.get("switch_to_results"):
        st.session_state["switch_to_results"] = False
        import streamlit.components.v1 as _c
        _c.html(
            """<script>setTimeout(function(){var t=window.parent.document.querySelectorAll('[data-baseweb="tab"]');if(t.length>=3)t[2].click();},300);</script>""", height=0)

    tab1, tab2, tab3 = st.tabs(
        ["📁  Upload Documents", "👤  Officer Inputs", "📊  Results"])

    # ── Tab 1 ─────────────────────────────────────────────────────────────────
    with tab1:
        st.markdown(
            "<p class='ic-section-title'>Financial Documents</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<div class='ic-upload-zone'><span class='ic-upload-label'>📋 GST Return</span><span class='ic-upload-desc'>GSTR-3B / GSTR-2A — PDF or Excel</span>", unsafe_allow_html=True)
            gst_file = st.file_uploader(
                "GST", type=["pdf", "xlsx", "xls"], key="gst", label_visibility="collapsed")
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<div class='ic-upload-zone'><span class='ic-upload-label'>📝 Income Tax Return</span><span class='ic-upload-desc'>ITR — PDF or Excel</span>", unsafe_allow_html=True)
            itr_file = st.file_uploader(
                "ITR", type=["pdf", "xlsx"], key="itr", label_visibility="collapsed")
            st.markdown("</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("<div class='ic-upload-zone'><span class='ic-upload-label'>🏦 Bank Statement</span><span class='ic-upload-desc'>PDF or Excel format</span>", unsafe_allow_html=True)
            bank_file = st.file_uploader(
                "Bank", type=["pdf", "xlsx"], key="bank", label_visibility="collapsed")
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<div class='ic-upload-zone'><span class='ic-upload-label'>📎 Other Documents</span><span class='ic-upload-desc'>Annual report, projections, etc.</span>", unsafe_allow_html=True)
            other_file = st.file_uploader(
                "Other", type=["pdf", "docx", "xlsx"], key="other", label_visibility="collapsed")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            "<hr class='ic-divider'><p class='ic-section-title'>GST Reconciliation — GSTR-2A vs 3B</p>", unsafe_allow_html=True)
        st.caption(
            "Upload both to detect ITC manipulation and circular trading patterns.")
        col3, col4 = st.columns(2)
        with col3:
            st.markdown("<div class='ic-upload-zone'><span class='ic-upload-label'>GSTR-2A</span><span class='ic-upload-desc'>Auto-populated from suppliers</span>", unsafe_allow_html=True)
            gstr_2a_file = st.file_uploader(
                "2A", type=["pdf", "xlsx"], key="gstr2a", label_visibility="collapsed")
            st.markdown("</div>", unsafe_allow_html=True)
        with col4:
            st.markdown("<div class='ic-upload-zone'><span class='ic-upload-label'>GSTR-3B</span><span class='ic-upload-desc'>Self-declared return</span>", unsafe_allow_html=True)
            gstr_3b_file = st.file_uploader(
                "3B", type=["pdf", "xlsx"], key="gstr3b", label_visibility="collapsed")
            st.markdown("</div>", unsafe_allow_html=True)

        uploaded = [f"✅ {lbl}: {f.name}" for f, lbl in [(gst_file, "GST"), (bank_file, "Bank"), (
            itr_file, "ITR"), (other_file, "Other"), (gstr_2a_file, "GSTR-2A"), (gstr_3b_file, "GSTR-3B")] if f]
        if uploaded:
            st.success("  ·  ".join(uploaded))
        else:
            st.info(
                "No documents uploaded yet — you can still run analysis with manual officer inputs.")

    # ── Tab 2 ─────────────────────────────────────────────────────────────────
    with tab2:
        st.markdown(
            "<p class='ic-section-title'>Primary Due Diligence Inputs</p>", unsafe_allow_html=True)
        st.caption("These inputs adjust the AI risk score (max ±0.25 delta).")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<div class='ic-card'>", unsafe_allow_html=True)
            site_visit_notes = st.text_area("🏭 Site Visit Notes", value=demo.get(
                "site_visit", ""), placeholder="e.g. Factory running at full capacity...", height=150)
            management_notes = st.text_area("👥 Management Interview Notes", value=demo.get(
                "mgmt", ""), placeholder="e.g. Promoter has 15 years experience...", height=150)
            st.markdown("</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("<div class='ic-card'>", unsafe_allow_html=True)
            _derived = st.session_state.get("derived_financials", {})
            _auto_de = _derived.get("debt_equity_ratio")
            _auto_nw = _derived.get("net_worth_inr")
            de_val = float(demo.get("de_ratio", _auto_de or 1.5))
            debt_equity = st.slider(
                "📊 D/E Ratio"+(" 🔒" if _auto_de and not demo else ""), 0.0, 5.0, round(de_val, 1), 0.1)
            collateral_pct = st.slider(
                "🏠 Collateral Coverage (%)", 0, 200, int(demo.get("collateral", 75)), 5)
            _nw_val = int(demo.get("net_worth", _auto_nw or 5000000))
            net_worth = st.number_input("💰 Net Worth (₹)"+(" 🔒" if _auto_nw and not demo else ""),
                                        min_value=0, value=_nw_val, step=100000, format="%d")
            promoter_score = st.slider("⭐ Promoter Integrity Score", 1, 10, int(
                demo.get("promoter_score", 7)), help="1=Very Poor, 10=Excellent")
            sector_risk = st.slider("🏭 Sector Risk Score", 1, 10, int(
                demo.get("sector_risk", 5)), help="1=Very Low Risk, 10=Very High Risk")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            "<hr class='ic-divider'><p class='ic-section-title'>Qualitative Score Preview</p>", unsafe_allow_html=True)
        if site_visit_notes:
            from config import SITE_VISIT_RISK_KEYWORDS, SITE_VISIT_POSITIVE_KEYWORDS
            nl = site_visit_notes.lower()
            rh = sum(1 for kw in SITE_VISIT_RISK_KEYWORDS if kw in nl)
            ph = sum(1 for kw in SITE_VISIT_POSITIVE_KEYWORDS if kw in nl)
            if ph > rh:
                st.success(
                    f"✅ Positive signals ({ph} positive vs {rh} risk). Score will decrease.")
            elif rh > ph:
                st.warning(
                    f"⚠️ Risk signals ({rh} risk vs {ph} positive). Score will increase.")
            else:
                st.info("ℹ️ Neutral notes — no score adjustment.")
        else:
            st.info("Enter site visit notes to see score preview.")

    # ── Run button ────────────────────────────────────────────────────────────
    st.markdown("<hr class='ic-divider'>", unsafe_allow_html=True)
    col_run, _ = st.columns([2, 6])
    with col_run:
        if not company_name:
            st.warning("⚠️ Enter a company name in the sidebar.")
            run_button = st.button(
                "🔍  Run AI Credit Analysis", disabled=True, use_container_width=True)
        else:
            run_button = st.button(
                "🔍  Run AI Credit Analysis", use_container_width=True)

    # ── Tab 3 ─────────────────────────────────────────────────────────────────
    with tab3:
        if not st.session_state.get("analysis_result"):
            st.markdown("<div class='ic-card' style='text-align:center;padding:3rem;'><div style='font-size:2.5rem;margin-bottom:0.75rem;'>📊</div><div style='font-weight:600;font-size:1rem;color:var(--text-sec);'>No analysis run yet</div><div style='font-size:0.85rem;color:var(--text-muted);margin-top:0.3rem;'>Fill in details, upload documents, add officer inputs, then click Run.</div></div>", unsafe_allow_html=True)
        else:
            result = st.session_state["analysis_result"]
            pred = result.risk_prediction
            if pred:
                ds = str(pred.decision).replace("DecisionType.", "")
                cs = str(pred.risk_category).replace("RiskCategory.", "")
                if "APPROVE" in ds.upper():
                    cc, ic = "decision-approve", "✅"
                elif "REJECT" in ds.upper():
                    cc, ic = "decision-reject", "❌"
                else:
                    cc, ic = "decision-conditional", "⚠️"
                st.markdown(
                    f'<div class="{cc}">{ic} AI DECISION: {ds}</div>', unsafe_allow_html=True)
                decisive = getattr(pred, "decisive_factor", "") or ""
                if decisive.strip():
                    st.markdown(
                        f'<div class="decisive-factor"><strong>⚡ DECISIVE FACTOR &nbsp;</strong>{decisive}</div>', unsafe_allow_html=True)

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("Risk Score", f"{pred.risk_score:.3f}")
                with c2:
                    st.metric("Risk Category", cs)
                with c3:
                    st.metric("Loan Limit",
                              f"₹{pred.loan_limit_inr/100000:.1f}L")
                with c4:
                    st.metric("Interest Rate", f"{pred.interest_rate}% p.a.")

                if result.derived_financials:
                    d = result.derived_financials
                    st.markdown(
                        "<hr class='ic-divider'><p class='ic-section-title'>Auto-Derived Financial Ratios</p>", unsafe_allow_html=True)
                    dc1, dc2, dc3, dc4 = st.columns(4)
                    with dc1:
                        if d.debt_equity_ratio is not None:
                            st.metric(
                                "D/E Ratio", f"{d.debt_equity_ratio:.2f}x")
                    with dc2:
                        if d.dscr is not None:
                            st.metric("DSCR", f"{d.dscr:.2f}x")
                    with dc3:
                        if d.net_profit_margin is not None:
                            st.metric("Net Profit Margin",
                                      f"{d.net_profit_margin:.1f}%")
                    with dc4:
                        if d.data_completeness_pct is not None:
                            st.metric("Data Completeness",
                                      f"{d.data_completeness_pct:.0f}%")
                    if d.derivation_notes:
                        for note in d.derivation_notes:
                            st.caption(f"ℹ️ {note}")

                st.markdown("<hr class='ic-divider'>", unsafe_allow_html=True)
                cl, cr = st.columns(2)
                with cl:
                    st.markdown(
                        "<p class='ic-section-title'>Five Cs Scores</p>", unsafe_allow_html=True)
                    if result.five_cs:
                        import plotly.graph_objects as go
                        cs2 = result.five_cs
                        cats = ["Character", "Capacity",
                                "Capital", "Collateral", "Conditions"]
                        scrs = [cs2.character.score, cs2.capacity.score,
                                cs2.capital.score, cs2.collateral.score, cs2.conditions.score]
                        fig = go.Figure()
                        fig.add_trace(go.Scatterpolar(r=scrs+[scrs[0]], theta=cats+[
                                      cats[0]], fill="toself", fillcolor="rgba(11,60,93,0.12)", line=dict(color="#0B3C5D", width=2)))
                        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10], gridcolor="#D6E4EF"), angularaxis=dict(
                            gridcolor="#D6E4EF")), showlegend=False, height=300, margin=dict(l=40, r=40, t=30, b=30), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig, use_container_width=True)
                        st.caption(
                            f"Overall Five Cs: **{result.five_cs.overall_score}/10**")
                with cr:
                    st.markdown(
                        "<p class='ic-section-title'>SHAP Risk Drivers</p>", unsafe_allow_html=True)
                    if pred.top_shap_factors:
                        import plotly.graph_objects as go
                        facs = pred.top_shap_factors
                        nms = [f.display_name for f in facs]
                        vals = [
                            f.shap_value if "increases" in f.direction else -f.shap_value for f in facs]
                        fig2 = go.Figure(go.Bar(x=vals, y=nms, orientation="h", marker_color=[
                                         "#B0001E" if v > 0 else "#0E7A4A" for v in vals]))
                        fig2.update_layout(xaxis_title="Risk Impact", height=300, margin=dict(l=180, r=40, t=20, b=40), xaxis=dict(
                            zeroline=True, zerolinewidth=1.5, zerolinecolor="#D6E4EF"), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig2, use_container_width=True)

                st.markdown("<hr class='ic-divider'>", unsafe_allow_html=True)
                if result.gst_reconciliation:
                    st.markdown(
                        "<p class='ic-section-title'>GST Reconciliation</p>", unsafe_allow_html=True)
                    rec = result.gst_reconciliation
                    if rec.risk_flag:
                        st.markdown(
                            f'<div class="flag-box">🚨 GST Risk Flag: {rec.total_mismatches} mismatch(es). Max variance: {rec.variance_pct}%</div>', unsafe_allow_html=True)
                    else:
                        st.success(
                            f"✅ GST Reconciliation Passed. Variance: {rec.variance_pct}%")
                    if rec.circular_trading_flag:
                        st.markdown(
                            '<div class="flag-box">🚨 CIRCULAR TRADING DETECTED</div>', unsafe_allow_html=True)

                if result.five_cs:
                    st.markdown(
                        "<p class='ic-section-title'>Five Cs Detail</p>", unsafe_allow_html=True)
                    for lbl, obj in [("Character", result.five_cs.character), ("Capacity", result.five_cs.capacity), ("Capital", result.five_cs.capital), ("Collateral", result.five_cs.collateral), ("Conditions", result.five_cs.conditions)]:
                        with st.expander(f"{lbl}: {obj.score}/10 — {obj.summary}"):
                            for f in obj.factors:
                                st.markdown(f"• {f}")

                # SWOT Analysis
                if st.session_state.get("swot_result"):
                    st.markdown("<hr class='ic-divider'>",
                                unsafe_allow_html=True)
                    st.markdown(
                        "<p class='ic-section-title'>SWOT Analysis</p>", unsafe_allow_html=True)
                    from src.swot_generator import render_swot_ui
                    render_swot_ui(st.session_state["swot_result"])

                if pred.early_warning_signals:
                    st.markdown(
                        "<p class='ic-section-title'>Early Warning Signals</p>", unsafe_allow_html=True)
                    for w in pred.early_warning_signals:
                        st.markdown(
                            f'<div class="warning-box">{"" if w.startswith("⚠️") else "⚠️ "}{w}</div>', unsafe_allow_html=True)

                st.markdown("<hr class='ic-divider'>", unsafe_allow_html=True)
                with st.expander("🤖 Full AI Reasoning Chain"):
                    chain = result.reasoning_chain or ""
                    st.text(chain) if chain.strip() else st.info(
                        "AI reasoning chain unavailable — Groq API limit reached.")

                if result.research:
                    with st.expander(f"📰 External Research (News Risk: {result.research.news_risk_score}/10)"):
                        r = result.research
                        st.markdown(r.research_summary)
                        if r.negative_news:
                            st.markdown("**Negative News:**")
                            for item in r.negative_news[:5]:
                                st.markdown(
                                    f'<div class="news-negative">🔴 {item.title}<br><span style="opacity:0.6;font-size:0.75rem">{item.date} — {item.source}</span></div>', unsafe_allow_html=True)
                        if r.positive_news:
                            st.markdown("**Positive News:**")
                            for item in r.positive_news[:3]:
                                st.markdown(
                                    f'<div class="news-positive">🟢 {item.title}<br><span style="opacity:0.6;font-size:0.75rem">{item.date} — {item.source}</span></div>', unsafe_allow_html=True)
                        if r.litigation_details:
                            st.markdown("**Litigation:**")
                            for lcase in r.litigation_details:
                                st.markdown(f"⚖️ {lcase}")

                st.markdown(
                    "<hr class='ic-divider'><p class='ic-section-title'>Reports</p>", unsafe_allow_html=True)
                if "pdf_path" in st.session_state:
                    import base64 as _b64mod
                    with open(st.session_state["pdf_path"], "rb") as _f:
                        _pdf = _f.read()
                    _b64 = _b64mod.b64encode(_pdf).decode()
                    _uri = f"data:application/pdf;base64,{_b64}"
                    import streamlit.components.v1 as _comp
                    _comp.html(
                        f'<div style="margin-bottom:12px;"><button onclick="window.open(\'{_uri}\',\'_blank\')" style="background:#0B3C5D;color:#fff;font-weight:600;padding:10px 22px;border-radius:8px;cursor:pointer;font-size:0.9rem;border:1.5px solid #328CC1;font-family:sans-serif;">&#128196;&nbsp; View PDF Report</button><span style="margin-left:10px;font-size:0.78rem;color:#8FA0B0;font-family:sans-serif;">Opens in new tab</span></div>', height=55)

                dl1, dl2 = st.columns(2)
                if "pdf_path" in st.session_state:
                    with dl1:
                        with open(st.session_state["pdf_path"], "rb") as f:
                            st.download_button("📄 Download PDF CAM", data=f.read(), file_name=Path(
                                st.session_state["pdf_path"]).name, mime="application/pdf", use_container_width=True)
                if "docx_path" in st.session_state:
                    with dl2:
                        with open(st.session_state["docx_path"], "rb") as f:
                            st.download_button("📝 Download DOCX CAM", data=f.read(), file_name=Path(
                                st.session_state["docx_path"]).name, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)

    # ── Pipeline ──────────────────────────────────────────────────────────────
    if run_button and company_name:
        with st.spinner("🔄 Loading AI engines..."):
            engines = load_engines()
        from src.schemas import CreditAppraisalResult, QualitativeInputs
        result = CreditAppraisalResult(company_name=company_name)

        with st.spinner("📄 Parsing documents..."):
            parser = engines["parser"]
            extractor = engines["extractor"]
            rag = engines["agent"].rag
            _tmp = []

            def save_and_parse(uf):
                if not uf:
                    return None
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uf.name).suffix) as t:
                    t.write(uf.read())
                    tp = str(Path(t.name).resolve())
                _tmp.append(tp)
                p = parser.parse(tp)
                p.source_file = tp
                return p

            if gst_file:
                pg = save_and_parse(gst_file)
                if pg and not pg.error:
                    result.gst_data = extractor.extract_gst(pg)
                    rag.ingest(pg, company_name=company_name)
            if bank_file:
                pb = save_and_parse(bank_file)
                if pb and not pb.error:
                    result.bank_data = extractor.extract_bank(pb)
                    rag.ingest(pb, company_name=company_name)
            if itr_file:
                pi = save_and_parse(itr_file)
                if pi and not pi.error:
                    result.itr_data = extractor.extract_itr(pi)
                    rag.ingest(pi, company_name=company_name)
                    if result.itr_data.net_worth == 0:
                        st.warning("⚠️ ITR parsed but net worth is zero.")
                else:
                    st.warning(
                        f"⚠️ ITR could not be parsed: {getattr(pi,'error','unknown') if pi else 'None'}")
            if other_file:
                po = save_and_parse(other_file)
                if po and not po.error:
                    rag.ingest(po, company_name=company_name)
            for _f in _tmp:
                try:
                    os.unlink(_f)
                except OSError:
                    pass
            derived = engines["risk_engine"].derive_from_documents(result)
            result.derived_financials = derived
            st.session_state["derived_financials"] = {
                "debt_equity_ratio": derived.debt_equity_ratio, "net_worth_inr": derived.net_worth_inr}
            if derived.derivation_notes:
                for note in derived.derivation_notes:
                    st.info(f"📊 {note}")

        with st.spinner("🔍 Running GST reconciliation..."):
            if gstr_2a_file and gstr_3b_file:
                p2a = save_and_parse(gstr_2a_file)
                p3b = save_and_parse(gstr_3b_file)
                if p2a and p3b:
                    g2a = extractor.extract_gst(p2a)
                    g3b = extractor.extract_gst(p3b)
                    result.gst_reconciliation = engines["reconciler"].reconcile(
                        g2a, g3b)
                    result.gst_data = g3b
                    if not p2a.error:
                        rag.ingest(p2a, company_name=company_name)
                    if not p3b.error:
                        rag.ingest(p3b, company_name=company_name)
            elif result.gst_data:
                from src.schemas import GSTReconciliationResult
                result.gst_reconciliation = GSTReconciliationResult(
                    total_mismatches=0, risk_flag=False, variance_pct=0.0, summary="Single GST file. Upload both GSTR-2A and 3B for full reconciliation.")

        with st.spinner("🔎 Researching company..."):
            result.research = engines["researcher"].research_with_mock(
                company_name, mock_risk_level) if use_mock_research else engines["researcher"].research(company_name, promoter_name)

        officer_inputs = QualitativeInputs(site_visit_notes=site_visit_notes, management_interview_notes=management_notes,
                                           debt_equity_ratio=debt_equity, collateral_coverage=collateral_pct/100, net_worth_inr=float(net_worth),
                                           sector_risk_score=sector_risk, promoter_score=promoter_score)
        result.qualitative_inputs = engines["risk_engine"].build_qualitative_inputs(
            result.derived_financials, officer_inputs)

        with st.spinner("📊 Running Five Cs analysis..."):
            result.five_cs = engines["five_cs"].analyze(result)
        with st.spinner("🤖 Scoring with XGBoost + SHAP..."):
            result.risk_prediction = engines["risk_engine"].score(
                result, requested_amount_inr=float(loan_amount_requested))
        with st.spinner("🧠 Running AI reasoning (Groq LLaMA)..."):
            result = engines["agent"].analyze(result)
        with st.spinner("📄 Generating reports..."):
            paths = engines["cam"].generate_both(result)
            st.session_state["pdf_path"] = paths["pdf"]
            st.session_state["docx_path"] = paths["docx"]
        with st.spinner("🧩 Generating SWOT analysis..."):
            from src.swot_generator import generate_swot, save_swot_to_case
            swot = generate_swot(result=result)
            st.session_state["swot_result"] = swot
            if st.session_state.get("case_id"):
                save_swot_to_case(st.session_state["case_id"], swot)

        if st.session_state.get("case_id"):
            try:
                from src.database import update_case
                p = result.risk_prediction
                update_case(st.session_state["case_id"], {"status": "COMPLETED", "decision": str(p.decision).replace("DecisionType.", ""), "risk_score": float(
                    p.risk_score), "decisive_factor": getattr(p, "decisive_factor", None), "cam_path": paths.get("pdf", "")})
            except Exception:
                pass

        st.session_state["analysis_result"] = result
        st.session_state["switch_to_results"] = True
        st.success("✅ Analysis complete!")
        st.balloons()
        st.rerun()


# ─── ROUTER ───────────────────────────────────────────────────────────────────
if st.session_state.page == "dashboard":
    render_dashboard()
elif st.session_state.page == "classify":
    from pages.upload_classify import render
    render()
elif st.session_state.page == "onboarding":
    from pages.onboarding import render
    render()
elif st.session_state.page == "case_view":
    from pages.case_view import render
    render()
else:
    render_analysis()
