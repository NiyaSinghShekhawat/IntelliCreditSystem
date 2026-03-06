from datetime import datetime
import os
import tempfile
import streamlit as st
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))


#  ─ PAGE CONFIG                               ─

st.set_page_config(
    page_title="IntelliCredit — AI Credit Engine",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

#  ─ CUSTOM CSS
st.markdown("""
<style>
    .stApp { background: rgb(10,14,26); color: rgb(232,234,246); }
    section[data-testid="stSidebar"] {
        background: rgb(13,18,38);
        border-right: 1px solid rgb(30,42,74);
    }
    .main-header {
        background: linear-gradient(135deg, rgb(13,18,38), rgb(26,35,126), rgb(13,18,38));
        padding: 2.5rem 2rem;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        border: 1px solid rgb(30,42,74);
        box-shadow: 0 8px 32px rgba(26,35,126,0.4);
    }
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 800;
        color: gold;
        margin: 0;
    }
    .main-header p { color: rgb(159,168,218); margin: 0.3rem 0 0 0; }
    .decision-approve {
        background: linear-gradient(135deg, rgb(10,46,10), rgb(27,94,32));
        border: 1px solid rgb(76,175,80);
        border-left: 6px solid rgb(76,175,80);
        padding: 1.2rem 1.5rem;
        border-radius: 12px;
        font-size: 1.4rem;
        font-weight: 800;
        color: rgb(165,214,167);
        box-shadow: 0 4px 20px rgba(76,175,80,0.2);
    }
    .decision-reject {
        background: linear-gradient(135deg, rgb(46,10,10), rgb(94,27,27));
        border: 1px solid rgb(244,67,54);
        border-left: 6px solid rgb(244,67,54);
        padding: 1.2rem 1.5rem;
        border-radius: 12px;
        font-size: 1.4rem;
        font-weight: 800;
        color: rgb(239,154,154);
        box-shadow: 0 4px 20px rgba(244,67,54,0.2);
    }
    .decision-conditional {
        background: linear-gradient(135deg, rgb(46,31,10), rgb(94,60,10));
        border: 1px solid rgb(255,193,7);
        border-left: 6px solid rgb(255,193,7);
        padding: 1.2rem 1.5rem;
        border-radius: 12px;
        font-size: 1.4rem;
        font-weight: 800;
        color: rgb(255,224,130);
        box-shadow: 0 4px 20px rgba(255,193,7,0.2);
    }
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, rgb(13,18,38), rgb(20,29,53));
        border: 1px solid rgb(30,42,74);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 16px rgba(0,0,0,0.3);
    }
    [data-testid="metric-container"] label {
        color: rgb(159,168,218) !important;
        font-size: 0.8rem !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: gold !important;
        font-size: 1.8rem !important;
        font-weight: 800 !important;
    }
    .warning-box {
        background: linear-gradient(135deg, rgb(26,20,0), rgb(42,32,0));
        border-left: 4px solid rgb(255,193,7);
        padding: 0.8rem 1rem;
        border-radius: 8px;
        margin: 0.4rem 0;
        color: rgb(255,224,130);
        font-size: 0.9rem;
    }
    .flag-box {
        background: linear-gradient(135deg, rgb(26,0,0), rgb(42,0,0));
        border-left: 4px solid rgb(244,67,54);
        padding: 0.8rem 1rem;
        border-radius: 8px;
        margin: 0.4rem 0;
        color: rgb(239,154,154);
        font-size: 0.9rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        background: rgb(13,18,38);
        border-radius: 10px;
        padding: 4px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: rgb(159,168,218);
        border-radius: 8px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: rgb(26,35,126) !important;
        color: gold !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, rgb(26,35,126), rgb(40,53,147));
        color: gold;
        border: 1px solid rgb(57,73,171);
        border-radius: 10px;
        font-weight: 700;
        font-size: 1rem;
        letter-spacing: 0.05em;
        padding: 0.6rem 1rem;
        box-shadow: 0 4px 12px rgba(26,35,126,0.4);
    }
    .news-negative {
        background: rgb(26,5,5);
        border-left: 3px solid rgb(244,67,54);
        padding: 0.6rem 0.8rem;
        border-radius: 6px;
        margin: 0.3rem 0;
        font-size: 0.85rem;
        color: rgb(239,154,154);
    }
    .news-positive {
        background: rgb(5,26,5);
        border-left: 3px solid rgb(76,175,80);
        padding: 0.6rem 0.8rem;
        border-radius: 6px;
        margin: 0.3rem 0;
        font-size: 0.85rem;
        color: rgb(165,214,167);
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

#  ─ HEADER
st.markdown("""
<div class="main-header">
    <h1>🏦 IntelliCredit</h1>
    <p style="font-size:1.1rem;">
        AI-Powered Credit Appraisal Engine for Indian Banks
    </p>
    <p style="font-size:0.8rem; color:rgb(121,134,203); margin-top:0.5rem;">
        GST Reconciliation &nbsp;•&nbsp;
        XGBoost + SHAP Scoring &nbsp;•&nbsp;
        Five Cs Analysis &nbsp;•&nbsp;
        CAM Generation &nbsp;•&nbsp;
        Live News Research
    </p>
</div>
""", unsafe_allow_html=True)

#  ─ IMPORTS (lazy to speed up startup)


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
    return {
        "parser": DocumentParser(),
        "extractor": FinancialExtractor(),
        "reconciler": GSTReconciler(),
        "researcher": ResearchAgent(),
        "risk_engine": RiskEngine(),
        "five_cs": FiveCsAnalyzer(),
        "agent": CreditAgent(),
        "cam": CAMGenerator()
    }


#  ─ SIDEBAR                                 ─
    # Make demo available outside sidebar
global demo
demo = st.session_state.get("demo", {})

with st.sidebar:
    st.markdown("### 📋 Loan Application")
    st.markdown("---")

    # company_name = st.text_input(
    #     "Company Name *",
    #     placeholder="ABC Private Limited"
    # )
    # promoter_name = st.text_input(
    #     "Promoter / Director Name",
    #     placeholder="Mr. Rajesh Kumar"
    # )
    # loan_amount_requested = st.number_input(
    #     "Loan Amount Requested (Rs.)",
    #     min_value=100000,
    #     max_value=50000000,
    #     value=2500000,
    #     step=100000,
    #     format="%d"
    # )
    # loan_purpose = st.selectbox(
    #     "Loan Purpose",
    #     ["Working Capital", "Term Loan", "Machinery",
    #      "Expansion", "Trade Finance", "Other"]
    # )
    company_name = st.text_input(
        "Company Name *",
        value=demo.get("company", ""),
        placeholder="ABC Private Limited"
    )
    promoter_name = st.text_input(
        "Promoter / Director Name",
        value=demo.get("promoter", ""),
        placeholder="Mr. Rajesh Kumar"
    )
    loan_amount_requested = st.number_input(
        "Loan Amount Requested (Rs.)",
        min_value=100000,
        max_value=50000000,
        value=demo.get("loan", 2500000),
        step=100000,
        format="%d"
    )
    purpose_options = ["Working Capital", "Term Loan", "Machinery",
                       "Expansion", "Trade Finance", "Other"]
    default_purpose = demo.get("purpose", "Working Capital")
    purpose_index = purpose_options.index(default_purpose) \
        if default_purpose in purpose_options else 0
    loan_purpose = st.selectbox(
        "Loan Purpose",
        purpose_options,
        index=purpose_index
    )

    # st.markdown("---")
    # st.markdown("### ⚙️ Settings")
    st.markdown("---")
    st.markdown("### 🎯 Demo Mode")
    st.markdown("Auto-fill inputs for judges:")

    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        demo_low = st.button("🟢 Low\nRisk", use_container_width=True)
    with col_d2:
        demo_med = st.button("🟡 Med\nRisk", use_container_width=True)
    with col_d3:
        demo_high = st.button("🔴 High\nRisk", use_container_width=True)

    # Demo scenario definitions
    DEMO_SCENARIOS = {
        "low": {
            "company": "Safe Industries Pvt Ltd",
            "promoter": "Rajesh Mehta",
            "loan": 2500000,
            "purpose": "Working Capital",
            "site_visit": "Factory running at full capacity. New orders from Tata Motors. Expanding warehouse. Good condition machinery.",
            "mgmt": "Promoter has 15 years experience. Clear business plan. Very cooperative during interview.",
            "de_ratio": 0.8,
            "collateral": 120,
            "net_worth": 15000000,
            "promoter_score": 9,
            "sector_risk": 3,
            "mock_level": "low"
        },
        "medium": {
            "company": "ABC Manufacturing Pvt Ltd",
            "promoter": "Suresh Kumar",
            "loan": 5000000,
            "purpose": "Machinery",
            "site_visit": "Factory operational but running at 60% capacity. Some idle machinery observed. Management cooperative.",
            "mgmt": "Promoter has 8 years experience. Adequate business plan presented.",
            "de_ratio": 1.8,
            "collateral": 80,
            "net_worth": 5000000,
            "promoter_score": 6,
            "sector_risk": 5,
            "mock_level": "medium"
        },
        "high": {
            "company": "XYZ Traders Pvt Ltd",
            "promoter": "Vikram Shah",
            "loan": 10000000,
            "purpose": "Working Capital",
            "site_visit": "Factory found shut during visit. Idle machinery observed. Poor condition. Workers said no orders since 3 months.",
            "mgmt": "Promoter was evasive during interview. Could not explain fund utilization.",
            "de_ratio": 4.2,
            "collateral": 30,
            "net_worth": 500000,
            "promoter_score": 2,
            "sector_risk": 9,
            "mock_level": "high"
        }
    }

    # Set demo scenario in session state
    if demo_low:
        st.session_state["demo"] = DEMO_SCENARIOS["low"]
        st.success("🟢 Low Risk scenario loaded!")
    elif demo_med:
        st.session_state["demo"] = DEMO_SCENARIOS["medium"]
        st.warning("🟡 Medium Risk scenario loaded!")
    elif demo_high:
        st.session_state["demo"] = DEMO_SCENARIOS["high"]
        st.error("🔴 High Risk scenario loaded!")

    # Load demo values if set
    demo = st.session_state.get("demo", {})

    st.markdown("---")
    st.markdown("### ⚙️ Settings")

    # use_mock_research = st.checkbox(
    #     "Use Mock Research Data",
    #     value=True,
    #     help="Use when internet is unavailable"
    # )
    # mock_risk_level = st.select_slider(
    #     "Mock Risk Level",
    #     options=["low", "medium", "high"],
    #     value="medium"
    # ) if use_mock_research else "medium"
    use_mock_research = st.checkbox(
        "Use Mock Research Data",
        value=True,
        help="Use when internet is unavailable"
    )
    if use_mock_research:
        mock_risk_level = st.select_slider(
            "Mock Risk Level (auto-set in Demo Mode)",
            options=["low", "medium", "high"],
            value=demo.get("mock_level", "medium")
        )
    else:
        mock_risk_level = "medium"

    st.markdown("---")
    st.markdown("### 📊 About")
    st.markdown("""
    ** IntelliCredit v1.0 **
    - 🤖 LLM: Groq LLaMA 3.3 70B
    - 📊 ML: XGBoost + SHAP
    - 📄 Parser: Docling
    - 🗄️ RAG: ChromaDB
    """)


#  ─ MAIN CONTENT

tab1, tab2, tab3 = st.tabs([
    "📁 Upload Documents",
    "👤 Officer Inputs",
    "📊 Results"
])

#   TAB 1: Document Upload                          ─

with tab1:
    st.markdown("### Upload Financial Documents")
    st.markdown(
        "Upload any combination of GST returns, "
        "bank statements, and ITR documents."
    )

    col1, col2 = st.columns(2)

    with col1:
        gst_file = st.file_uploader(
            "📋 GST Return (GSTR-3B / GSTR-2A)",
            type=["pdf", "xlsx", "xls"],
            key="gst"
        )
        itr_file = st.file_uploader(
            "📝 Income Tax Return (ITR)",
            type=["pdf", "xlsx"],
            key="itr"
        )

    with col2:
        bank_file = st.file_uploader(
            "🏦 Bank Statement",
            type=["pdf", "xlsx"],
            key="bank"
        )
        other_file = st.file_uploader(
            "📎 Other Documents (Annual Report, etc.)",
            type=["pdf", "docx", "xlsx"],
            key="other"
        )

    # GST Reconciliation section
    st.markdown("---")
    st.markdown("### 🔍 GST Reconciliation (GSTR-2A vs 3B)")
    st.markdown(
        "Upload both GSTR-2A and GSTR-3B to detect "
        "ITC manipulation and circular trading."
    )

    col3, col4 = st.columns(2)
    with col3:
        gstr_2a_file = st.file_uploader(
            "GSTR-2A (Auto-populated from suppliers)",
            type=["pdf", "xlsx"],
            key="gstr2a"
        )
    with col4:
        gstr_3b_file = st.file_uploader(
            "GSTR-3B (Self-declared)",
            type=["pdf", "xlsx"],
            key="gstr3b"
        )

    # Show upload status
    uploaded = []
    if gst_file:
        uploaded.append(f"✅ GST Return: {gst_file.name}")
    if bank_file:
        uploaded.append(f"✅ Bank Statement: {bank_file.name}")
    if itr_file:
        uploaded.append(f"✅ ITR: {itr_file.name}")
    if other_file:
        uploaded.append(f"✅ Other: {other_file.name}")
    if gstr_2a_file:
        uploaded.append(f"✅ GSTR-2A: {gstr_2a_file.name}")
    if gstr_3b_file:
        uploaded.append(f"✅ GSTR-3B: {gstr_3b_file.name}")

    if uploaded:
        st.success("\n".join(uploaded))
    else:
        st.info(
            "No documents uploaded yet. "
            "You can still run analysis with manual inputs below."
        )

#   TAB 2: Officer Inputs
with tab2:
    st.markdown("### 👤 Primary Due Diligence Inputs")
    st.markdown(
        "These inputs from the credit officer adjust "
        "the AI risk score (max ±0.25 delta)."
    )

    col1, col2 = st.columns(2)

    with col1:
        site_visit_notes = st.text_area(
            "🏭 Site Visit Notes",
            value=demo.get("site_visit", ""),
            placeholder="e.g. Factory running at full capacity...",
            height=150
        )
        management_notes = st.text_area(
            "👥 Management Interview Notes",
            value=demo.get("mgmt", ""),
            placeholder="e.g. Promoter has 15 years experience...",
            height=150
        )

    with col2:
        de_val = float(demo.get("de_ratio", 1.5))
        debt_equity = st.slider(
            "📊 Debt / Equity Ratio",
            min_value=0.0,
            max_value=5.0,
            value=round(de_val, 1),
            step=0.1
        )
        collateral_pct = st.slider(
            "🏠 Collateral Coverage (%)",
            min_value=0,
            max_value=200,
            value=int(demo.get("collateral", 75)),
            step=5
        )
        net_worth = st.number_input(
            "💰 Net Worth (Rs.)",
            min_value=0,
            value=int(demo.get("net_worth", 5000000)),
            step=100000,
            format="%d"
        )
        promoter_score = st.slider(
            "⭐ Promoter Integrity Score",
            min_value=1,
            max_value=10,
            value=int(demo.get("promoter_score", 7)),
            help="1=Very Poor, 10=Excellent"
        )
        sector_risk = st.slider(
            "🏭 Sector Risk Score",
            min_value=1,
            max_value=10,
            value=int(demo.get("sector_risk", 5)),
            help="1=Very Low Risk, 10=Very High Risk"
        )

    st.markdown("---")
    st.markdown("### 📋 Qualitative Score Preview")
    if site_visit_notes:
        from config import (
            SITE_VISIT_RISK_KEYWORDS,
            SITE_VISIT_POSITIVE_KEYWORDS
        )
        notes_lower = site_visit_notes.lower()
        risk_hits = sum(
            1 for kw in SITE_VISIT_RISK_KEYWORDS
            if kw in notes_lower
        )
        pos_hits = sum(
            1 for kw in SITE_VISIT_POSITIVE_KEYWORDS
            if kw in notes_lower
        )
        if pos_hits > risk_hits:
            st.success(
                f"✅ Positive signals detected "
                f"({pos_hits} positive vs {risk_hits} risk keywords). "
                f"Risk score will decrease."
            )
        elif risk_hits > pos_hits:
            st.warning(
                f"⚠️ Risk signals detected "
                f"({risk_hits} risk vs {pos_hits} positive keywords). "
                f"Risk score will increase."
            )
        else:
            st.info("ℹ️ Neutral site visit notes. No score adjustment.")
    else:
        st.info("Enter site visit notes above to see score preview.")


#   RUN ANALYSIS BUTTON

st.markdown("---")

if not company_name:
    st.warning("⚠️ Please enter a Company Name in the sidebar to proceed.")
    run_button = st.button("🔍 Run AI Credit Analysis", disabled=True)
else:
    run_button = st.button("🔍 Run AI Credit Analysis")

#   TAB 3: Results                              ─

with tab3:
    if "analysis_result" not in st.session_state:
        st.info(
            "👈 Fill in company details, upload documents, "
            "add officer inputs, then click "
            "**Run AI Credit Analysis**"
        )
    else:
        result = st.session_state["analysis_result"]
        pred = result.risk_prediction

        if pred:
            #   Decision Banner                      ─
            decision_str = str(pred.decision).replace(
                "DecisionType.", ""
            )
            category_str = str(pred.risk_category).replace(
                "RiskCategory.", ""
            )

            if "APPROVE" in decision_str.upper():
                css_class = "decision-approve"
                icon = "✅"
            elif "REJECT" in decision_str.upper():
                css_class = "decision-reject"
                icon = "❌"
            else:
                css_class = "decision-conditional"
                icon = "⚠️"

            st.markdown(
                f'<div class="{css_class}">'
                f'{icon} AI DECISION: {decision_str}'
                f'</div>',
                unsafe_allow_html=True
            )
            st.markdown("")

            #   Key Metrics                        ─
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(
                    "Risk Score",
                    f"{pred.risk_score:.3f}",
                    help="0=No Risk, 1=Maximum Risk"
                )
            with col2:
                st.metric(
                    "Risk Category",
                    category_str
                )
            with col3:
                st.metric(
                    "Loan Limit",
                    f"Rs.{pred.loan_limit_inr/100000:.1f}L"
                )
            with col4:
                st.metric(
                    "Interest Rate",
                    f"{pred.interest_rate}% p.a."
                )

            st.markdown("---")

            #   Charts Row
            col_left, col_right = st.columns(2)

            with col_left:
                st.markdown("#### 📊 Five Cs Scores")
                if result.five_cs:
                    import plotly.graph_objects as go
                    cs = result.five_cs
                    categories = [
                        "Character", "Capacity",
                        "Capital", "Collateral", "Conditions"
                    ]
                    scores = [
                        cs.character.score,
                        cs.capacity.score,
                        cs.capital.score,
                        cs.collateral.score,
                        cs.conditions.score
                    ]
                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(
                        r=scores + [scores[0]],
                        theta=categories + [categories[0]],
                        fill="toself",
                        fillcolor="rgba(26,35,126,0.2)",
                        line=dict(color="#1a237e", width=2),
                        name="Five Cs"
                    ))
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 10]
                            )
                        ),
                        showlegend=False,
                        height=350,
                        margin=dict(l=40, r=40, t=40, b=40)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown(
                        f"**Overall Five Cs Score: "
                        f"{result.five_cs.overall_score}/10**"
                    )

            with col_right:
                st.markdown("#### 🔍 SHAP Risk Drivers")
                if pred.top_shap_factors:
                    import plotly.graph_objects as go
                    factors = pred.top_shap_factors
                    names = [f.display_name for f in factors]
                    import plotly.graph_objects as go
                    factors = pred.top_shap_factors
                    names = [f.display_name for f in factors]
                    values = [
                        f.shap_value if "increases" in f.direction
                        else -f.shap_value
                        for f in factors
                    ]
                    colors_list = [
                        "#c62828" if v > 0 else "#2e7d32"
                        for v in values
                    ]
                    fig2 = go.Figure(go.Bar(
                        x=values,
                        y=names,
                        orientation="h",
                        marker_color=colors_list,
                    ))
                    fig2.update_layout(
                        xaxis_title="Risk Impact (Red=Increases Risk, Green=Decreases)",
                        height=350,
                        margin=dict(l=180, r=40, t=40, b=40),
                        xaxis=dict(zeroline=True, zerolinewidth=2)
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                    colors_list = [
                        "#c62828" if v > 0 else "#2e7d32"
                        for v in values
                    ]
                    # fig2 = go.Figure(go.Bar(
                    #     x=values,
                    #     y=names,
                    #     orientation="h",
                    #     marker_color=colors_list,
                    #     text=[
                    #         f.direction for f in factors
                    #     ],
                    #     textposition="outside"
                    # ))
                    # fig2.update_layout(
                    #     xaxis_title="Risk Impact",
                    #     height=350,
                    #     margin=dict(l=10, r=10, t=40, b=40),
                    #     xaxis=dict(zeroline=True)
                    # )
                    # st.plotly_chart(fig2, use_container_width=True)

            st.markdown("---")

            #   GST Reconciliation
            if result.gst_reconciliation:
                st.markdown("#### 🔍 GST Reconciliation")
                rec = result.gst_reconciliation
                if rec.risk_flag:
                    st.markdown(
                        f'<div class="flag-box">'
                        f'🚨 GST Risk Flag: {rec.total_mismatches} '
                        f'mismatch(es) detected. '
                        f'Max variance: {rec.variance_pct}%'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.success(
                        f"✅ GST Reconciliation Passed. "
                        f"Variance: {rec.variance_pct}%"
                    )
                if rec.circular_trading_flag:
                    st.markdown(
                        '<div class="flag-box">'
                        '🚨 CIRCULAR TRADING DETECTED'
                        '</div>',
                        unsafe_allow_html=True
                    )

            #   Five Cs Detail
            if result.five_cs:
                st.markdown("#### 📋 Five Cs Detail")
                cs = result.five_cs
                for label, obj in [
                    ("Character", cs.character),
                    ("Capacity", cs.capacity),
                    ("Capital", cs.capital),
                    ("Collateral", cs.collateral),
                    ("Conditions", cs.conditions),
                ]:
                    with st.expander(
                        f"{label}: {obj.score}/10 — {obj.summary}"
                    ):
                        for f in obj.factors:
                            st.markdown(f"• {f}")

            #   Early Warnings
            if pred.early_warning_signals:
                st.markdown("#### ⚠️ Early Warning Signals")
                for w in pred.early_warning_signals:
                    st.markdown(
                        f'<div class="warning-box">⚠️ {w}</div>',
                        unsafe_allow_html=True
                    )

            #   Reasoning Chain                      ─
            st.markdown("---")
            with st.expander("🤖 View Full AI Reasoning Chain"):
                st.text(result.reasoning_chain)

            #   Research
            if result.research:
                with st.expander(
                    f"📰 External Research "
                    f"(News Risk: {result.research.news_risk_score}/10)"
                ):
                    r = result.research
                    st.markdown(r.research_summary)
                    if r.negative_news:
                        st.markdown("**Negative News:**")
                        for item in r.negative_news[:5]:
                            st.markdown(
                                f'<div class="news-negative">'
                                f'🔴 {item.title}<br>'
                                f'<span style="opacity:0.6;font-size:0.75rem">'
                                f'{item.date} — {item.source}</span>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                    if r.positive_news:
                        st.markdown("**Positive News:**")
                        for item in r.positive_news[:3]:
                            st.markdown(
                                f'<div class="news-positive">'
                                f'🟢 {item.title}<br>'
                                f'<span style="opacity:0.6;font-size:0.75rem">'
                                f'{item.date} — {item.source}</span>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                    if r.litigation_details:
                        st.markdown("**Litigation:**")
                        for case in r.litigation_details:
                            st.markdown(f"⚖️ {case}")

            #   Download Reports
            st.markdown("---")
            st.markdown("#### 📥 Download Reports")
            col_dl1, col_dl2 = st.columns(2)

            if "pdf_path" in st.session_state:
                with col_dl1:
                    with open(
                        st.session_state["pdf_path"], "rb"
                    ) as f:
                        st.download_button(
                            "📄 Download PDF CAM",
                            data=f.read(),
                            file_name=Path(
                                st.session_state["pdf_path"]
                            ).name,
                            mime="application/pdf"
                        )
            if "docx_path" in st.session_state:
                with col_dl2:
                    with open(
                        st.session_state["docx_path"], "rb"
                    ) as f:
                        st.download_button(
                            "📝 Download DOCX CAM",
                            data=f.read(),
                            file_name=Path(
                                st.session_state["docx_path"]
                            ).name,
                            mime=(
                                "application/vnd.openxmlformats-"
                                "officedocument.wordprocessingml.document"
                            )
                        )

#  ─ RUN ANALYSIS PIPELINE                          ─

if run_button and company_name:
    with st.spinner("🔄 Loading AI engines..."):
        engines = load_engines()

    from src.schemas import (
        CreditAppraisalResult, QualitativeInputs
    )

    result = CreditAppraisalResult(company_name=company_name)

    #   Parse & Extract Documents                     ─
    with st.spinner("📄 Parsing documents..."):
        parser = engines["parser"]
        extractor = engines["extractor"]

        def save_and_parse(uploaded_file):
            if not uploaded_file:
                return None
            suffix = Path(uploaded_file.name).suffix
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=suffix
            ) as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name
            parsed = parser.parse(tmp_path)
            os.unlink(tmp_path)
            return parsed

        # Parse uploaded files
        if gst_file:
            parsed_gst = save_and_parse(gst_file)
            if parsed_gst and not parsed_gst.error:
                result.gst_data = extractor.extract_gst(parsed_gst)

        if bank_file:
            parsed_bank = save_and_parse(bank_file)
            if parsed_bank and not parsed_bank.error:
                result.bank_data = extractor.extract_bank(parsed_bank)

        if itr_file:
            parsed_itr = save_and_parse(itr_file)
            if parsed_itr and not parsed_itr.error:
                result.itr_data = extractor.extract_itr(parsed_itr)

    #   GST Reconciliation
    with st.spinner("🔍 Running GST reconciliation..."):
        if gstr_2a_file and gstr_3b_file:
            parsed_2a = save_and_parse(gstr_2a_file)
            parsed_3b = save_and_parse(gstr_3b_file)
            if parsed_2a and parsed_3b:
                gst_2a = extractor.extract_gst(parsed_2a)
                gst_3b = extractor.extract_gst(parsed_3b)
                result.gst_reconciliation = (
                    engines["reconciler"].reconcile(gst_2a, gst_3b)
                )
        elif result.gst_data:
            # Single GST file — create dummy reconciliation
            from src.schemas import GSTReconciliationResult
            result.gst_reconciliation = GSTReconciliationResult(
                total_mismatches=0,
                risk_flag=False,
                variance_pct=0.0,
                summary="Single GST file uploaded. Upload both "
                        "GSTR-2A and 3B for full reconciliation."
            )

    #   Research
    with st.spinner("🔎 Researching company..."):
        if use_mock_research:
            result.research = engines["researcher"].research_with_mock(
                company_name, mock_risk_level
            )
        else:
            result.research = engines["researcher"].research(
                company_name, promoter_name
            )

    #   Qualitative Inputs
    result.qualitative_inputs = QualitativeInputs(
        site_visit_notes=site_visit_notes,
        management_interview_notes=management_notes,
        debt_equity_ratio=debt_equity,
        collateral_coverage=collateral_pct / 100,
        net_worth_inr=float(net_worth),
        sector_risk_score=sector_risk,
        promoter_score=promoter_score
    )

    #   Five Cs                              ─
    with st.spinner("📊 Running Five Cs analysis..."):
        result.five_cs = engines["five_cs"].analyze(result)

    #   XGBoost Risk Score
    with st.spinner("🤖 Scoring with XGBoost + SHAP..."):
        result.risk_prediction = engines["risk_engine"].score(result)

    #   LLM Reasoning                           ─
    with st.spinner("🧠 Running AI reasoning (Groq LLaMA)..."):
        result = engines["agent"].analyze(result)

    #   Generate Reports
    with st.spinner("📄 Generating PDF and DOCX reports..."):
        paths = engines["cam"].generate_both(result)
        st.session_state["pdf_path"] = paths["pdf"]
        st.session_state["docx_path"] = paths["docx"]

    # Save result to session
    st.session_state["analysis_result"] = result

    st.success("✅ Analysis complete! Switch to the Results tab.")
    st.balloons()
