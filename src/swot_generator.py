# src/swot_generator.py
"""
SWOT Analysis Generator for IntelliCredit v2.0

Generates a structured SWOT analysis by combining:
  - Five Cs scores and factors
  - Extracted financial data (AUM, NPA, borrowings, etc.)
  - Secondary research signals (news, legal, macro)
  - Risk prediction output

Output is a typed Pydantic model stored in cases.swot_json
"""

import json
import re
from typing import Optional
from pydantic import BaseModel


# ─── SCHEMA ───────────────────────────────────────────────────────────────────

class SWOTAnalysis(BaseModel):
    strengths:     list[str] = []
    weaknesses:    list[str] = []
    opportunities: list[str] = []
    threats:       list[str] = []
    summary:       str = ""
    generated_from: str = ""   # what data was used


# ─── BUILDER ──────────────────────────────────────────────────────────────────

def _build_context(result) -> str:
    """
    Flatten CreditAppraisalResult into a text context string for the LLM.
    Handles missing fields gracefully.
    """
    lines = []
    company = getattr(result, "company_name", "the company")
    lines.append(f"Company: {company}")

    # Five Cs
    fcs = getattr(result, "five_cs", None)
    if fcs:
        lines.append("\n--- FIVE CS SCORES ---")
        for label, obj in [
            ("Character",  fcs.character),
            ("Capacity",   fcs.capacity),
            ("Capital",    fcs.capital),
            ("Collateral", fcs.collateral),
            ("Conditions", fcs.conditions),
        ]:
            lines.append(f"{label}: {obj.score}/10 — {obj.summary}")
            for f in obj.factors[:3]:
                lines.append(f"  • {f}")
        lines.append(f"Overall Five Cs: {fcs.overall_score}/10")

    # Risk prediction
    pred = getattr(result, "risk_prediction", None)
    if pred:
        lines.append("\n--- RISK ASSESSMENT ---")
        lines.append(f"Risk Score: {pred.risk_score:.3f}")
        lines.append(
            f"Decision: {str(pred.decision).replace('DecisionType.','')}")
        lines.append(
            f"Risk Category: {str(pred.risk_category).replace('RiskCategory.','')}")
        if getattr(pred, "decisive_factor", ""):
            lines.append(f"Decisive Factor: {pred.decisive_factor}")
        for w in (pred.early_warning_signals or [])[:5]:
            lines.append(f"Warning: {w}")

    # Derived financials
    derived = getattr(result, "derived_financials", None)
    if derived:
        lines.append("\n--- FINANCIAL RATIOS ---")
        if derived.debt_equity_ratio:
            lines.append(f"D/E Ratio: {derived.debt_equity_ratio:.2f}x")
        if derived.dscr:
            lines.append(f"DSCR: {derived.dscr:.2f}x")
        if derived.net_profit_margin:
            lines.append(
                f"Net Profit Margin: {derived.net_profit_margin:.1f}%")
        if derived.avg_monthly_balance_inr:
            lines.append(
                f"Avg Monthly Balance: ₹{derived.avg_monthly_balance_inr/1e7:.2f} Cr")

    # GST reconciliation
    gst_rec = getattr(result, "gst_reconciliation", None)
    if gst_rec:
        lines.append("\n--- GST RECONCILIATION ---")
        lines.append(f"Risk Flag: {gst_rec.risk_flag}")
        lines.append(f"Variance: {gst_rec.variance_pct}%")
        if gst_rec.circular_trading_flag:
            lines.append("CIRCULAR TRADING DETECTED")

    # Research
    research = getattr(result, "research", None)
    if research:
        lines.append("\n--- EXTERNAL RESEARCH ---")
        lines.append(f"News Risk Score: {research.news_risk_score}/10")
        lines.append(
            research.research_summary[:400] if research.research_summary else "")
        for item in (research.negative_news or [])[:3]:
            lines.append(f"Negative: {item.title}")
        for item in (research.positive_news or [])[:3]:
            lines.append(f"Positive: {item.title}")
        for detail in (research.litigation_details or [])[:2]:
            lines.append(f"Litigation: {detail}")

    return "\n".join(lines)


def _build_context_from_dict(data: dict) -> str:
    """
    Build context from raw dict (used when loading from Supabase,
    where result is already serialized).
    """
    lines = []

    if data.get("company_name"):
        lines.append(f"Company: {data['company_name']}")

    if data.get("risk_score"):
        lines.append(f"\nRisk Score: {data['risk_score']:.3f}")
    if data.get("decision"):
        lines.append(f"Decision: {data['decision']}")
    if data.get("decisive_factor"):
        lines.append(f"Decisive Factor: {data['decisive_factor']}")

    fcs = data.get("five_cs_json")
    if fcs and isinstance(fcs, dict):
        lines.append("\n--- FIVE CS ---")
        for key in ["character", "capacity", "capital", "collateral", "conditions"]:
            obj = fcs.get(key, {})
            if isinstance(obj, dict):
                lines.append(
                    f"{key.title()}: {obj.get('score','?')}/10 — {obj.get('summary','')}")

    research = data.get("research_json")
    if research and isinstance(research, dict):
        lines.append("\n--- RESEARCH ---")
        lines.append(f"News Risk: {research.get('news_risk_score','?')}/10")
        lines.append(research.get("research_summary", "")[:300])

    return "\n".join(lines)


# ─── LLM CALL ─────────────────────────────────────────────────────────────────

def _call_llm(context: str, company: str) -> SWOTAnalysis:
    from config import get_groq_client
    client = get_groq_client()

    prompt = f"""You are a senior credit analyst at an NBFC performing SWOT analysis for a loan application.

Generate a comprehensive SWOT analysis for {company} based on the credit assessment data below.

Rules:
- Each quadrant: 3-5 specific, data-backed bullet points
- Be specific — reference actual numbers and signals from the data
- Strengths/Weaknesses = internal factors
- Opportunities/Threats = external factors
- Summary = 2-sentence overall assessment
- Do NOT invent data not present in the context

Context:
{context}

Respond ONLY with valid JSON, no markdown fences:
{{
  "strengths": ["point 1", "point 2", "point 3"],
  "weaknesses": ["point 1", "point 2", "point 3"],
  "opportunities": ["point 1", "point 2", "point 3"],
  "threats": ["point 1", "point 2", "point 3"],
  "summary": "Two sentence overall assessment."
}}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"```(?:json)?|```", "", raw).strip()
    data = json.loads(raw)

    return SWOTAnalysis(
        strengths=data.get("strengths", []),
        weaknesses=data.get("weaknesses", []),
        opportunities=data.get("opportunities", []),
        threats=data.get("threats", []),
        summary=data.get("summary", ""),
        generated_from="Five Cs + Risk Engine + Research"
    )


def _rule_based_fallback(context: str, company: str) -> SWOTAnalysis:
    """
    Simple rule-based SWOT when LLM is unavailable.
    Scans context for key signals.
    """
    ctx = context.lower()

    strengths, weaknesses, opportunities, threats = [], [], [], []

    # Strengths
    if "dscr: 1" in ctx or "dscr: 2" in ctx:
        strengths.append(
            "Adequate debt service coverage ratio indicates manageable debt burden")
    if "character: " in ctx and any(f"character: {i}" in ctx for i in ["7", "8", "9", "10"]):
        strengths.append(
            "Strong promoter integrity and management track record")
    if "positive news" in ctx or "new orders" in ctx:
        strengths.append(
            "Positive external news signals and business momentum")
    if "collateral: " in ctx and any(f"collateral: {i}" in ctx for i in ["7", "8", "9", "10"]):
        strengths.append("Strong collateral coverage reduces lender risk")
    if not strengths:
        strengths.append(
            "Business operations ongoing with active revenue generation")

    # Weaknesses
    if "risk flag: true" in ctx or "circular trading" in ctx:
        weaknesses.append(
            "GST reconciliation flags indicate potential ITC irregularities")
    if "d/e ratio: " in ctx:
        for ratio in ["3.", "4.", "5."]:
            if f"d/e ratio: {ratio}" in ctx:
                weaknesses.append(
                    "Elevated debt-equity ratio signals high financial leverage")
                break
    if "negative news" in ctx or "litigation" in ctx:
        weaknesses.append(
            "Adverse news or litigation signals reputational risk")
    if not weaknesses:
        weaknesses.append(
            "Limited financial history available for comprehensive assessment")

    # Opportunities
    opportunities.append(
        "India's growing MSME sector presents strong demand potential")
    opportunities.append(
        "Improving digital lending infrastructure reduces operational costs")
    if "nbfc" in ctx or "fintech" in ctx:
        opportunities.append(
            "Co-lending partnerships with banks can expand funding access")

    # Threats
    threats.append(
        "Rising interest rate environment may pressure debt servicing capacity")
    threats.append(
        "Regulatory tightening in NBFC/lending sector could impact operations")
    if "npa" in ctx or "par 30" in ctx:
        threats.append(
            "Portfolio quality risks may impact future borrowing capacity")

    return SWOTAnalysis(
        strengths=strengths,
        weaknesses=weaknesses,
        opportunities=opportunities,
        threats=threats,
        summary=f"Assessment for {company} based on available financial and qualitative data. "
                f"Further due diligence recommended for complete risk evaluation.",
        generated_from="Rule-based fallback (LLM unavailable)"
    )


# ─── PUBLIC API ───────────────────────────────────────────────────────────────

def generate_swot(result=None, case_dict: dict = None) -> SWOTAnalysis:
    """
    Generate SWOT analysis.

    Pass either:
      result     — a CreditAppraisalResult object (from live pipeline)
      case_dict  — a dict loaded from Supabase (for case_view)
    """
    if result is not None:
        company = getattr(result, "company_name", "the company")
        context = _build_context(result)
    elif case_dict is not None:
        entity = case_dict.get("entities") or {}
        company = entity.get("company_name") or case_dict.get(
            "company_name") or "the company"
        context = _build_context_from_dict({
            **case_dict,
            "company_name": company,
        })
    else:
        return SWOTAnalysis(summary="No data provided for SWOT generation.")

    try:
        swot = _call_llm(context, company)
        return swot
    except Exception as e:
        print(f"[SWOT] LLM failed: {e} — using rule-based fallback")
        return _rule_based_fallback(context, company)


def save_swot_to_case(case_id: str, swot: SWOTAnalysis):
    """Persist SWOT JSON to Supabase cases table."""
    from src.database import update_case
    update_case(case_id, {"swot_json": swot.model_dump()})


def render_swot_ui(swot: SWOTAnalysis):
    """
    Render SWOT as a 2x2 grid in Streamlit.
    Call this from case_view.py or the analysis results tab.
    """
    import streamlit as st

    st.markdown(f"""
    <div style='font-size:0.78rem;color:var(--text-muted);
                margin-bottom:1rem;font-style:italic;'>
        {swot.summary}
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        # Strengths
        st.markdown("""
        <div style='background:var(--approve-bg);border:1px solid var(--approve-bd);
                    border-radius:10px;padding:1rem 1.2rem;margin-bottom:0.75rem;'>
            <div style='font-size:0.72rem;font-weight:700;text-transform:uppercase;
                        letter-spacing:0.1em;color:var(--approve);margin-bottom:0.6rem;'>
                💪 Strengths
            </div>
        """, unsafe_allow_html=True)
        for s in swot.strengths:
            st.markdown(f"<div style='font-size:0.84rem;color:var(--text);padding:3px 0;'>• {s}</div>",
                        unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Opportunities
        st.markdown("""
        <div style='background:var(--info-bg);border:1px solid var(--info-bd);
                    border-radius:10px;padding:1rem 1.2rem;'>
            <div style='font-size:0.72rem;font-weight:700;text-transform:uppercase;
                        letter-spacing:0.1em;color:var(--info);margin-bottom:0.6rem;'>
                🚀 Opportunities
            </div>
        """, unsafe_allow_html=True)
        for o in swot.opportunities:
            st.markdown(f"<div style='font-size:0.84rem;color:var(--text);padding:3px 0;'>• {o}</div>",
                        unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        # Weaknesses
        st.markdown("""
        <div style='background:var(--warn-bg);border:1px solid var(--warn-bd);
                    border-radius:10px;padding:1rem 1.2rem;margin-bottom:0.75rem;'>
            <div style='font-size:0.72rem;font-weight:700;text-transform:uppercase;
                        letter-spacing:0.1em;color:var(--warn);margin-bottom:0.6rem;'>
                ⚠️ Weaknesses
            </div>
        """, unsafe_allow_html=True)
        for w in swot.weaknesses:
            st.markdown(f"<div style='font-size:0.84rem;color:var(--text);padding:3px 0;'>• {w}</div>",
                        unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Threats
        st.markdown("""
        <div style='background:var(--reject-bg);border:1px solid var(--reject-bd);
                    border-radius:10px;padding:1rem 1.2rem;'>
            <div style='font-size:0.72rem;font-weight:700;text-transform:uppercase;
                        letter-spacing:0.1em;color:var(--reject);margin-bottom:0.6rem;'>
                ⚡ Threats
            </div>
        """, unsafe_allow_html=True)
        for t in swot.threats:
            st.markdown(f"<div style='font-size:0.84rem;color:var(--text);padding:3px 0;'>• {t}</div>",
                        unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if swot.generated_from:
        st.caption(f"Generated from: {swot.generated_from}")
