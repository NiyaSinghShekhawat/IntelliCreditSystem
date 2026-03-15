# pages/case_view.py
"""
Case detail view — opened when officer clicks "Open →" on the dashboard.

Tabs:
  1. Extraction Results — all fields extracted from uploaded docs
  2. Analysis — risk score, AI decision, Five Cs
  3. CAM Report — download PDF / DOCX
  4. Officer Assessment — final values + close case
"""
import streamlit as st
import json
from src.database import get_case, update_case


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _status_badge(status: str, decision: str) -> str:
    s = (status or "").upper()
    d = (decision or "").upper()
    if s in ("CLOSED", "COMPLETED"):
        if "APPROVE" in d:
            return "<span class='badge badge-approve'>Approved</span>"
        elif "REJECT" in d:
            return "<span class='badge badge-reject'>Rejected</span>"
        elif "CONDITIONAL" in d:
            return "<span class='badge badge-warn'>Conditional</span>"
        return "<span class='badge badge-approve'>Closed</span>"
    elif s == "UNDER_REVIEW":
        return "<span class='badge badge-warn'>Under Review</span>"
    elif s == "IN_PROGRESS":
        return "<span class='badge badge-progress'>In Progress</span>"
    return "<span class='badge badge-progress'>Pending</span>"


def _info_row(label: str, value: str, mono: bool = False):
    font = "font-family:JetBrains Mono,monospace;" if mono else ""
    st.markdown(f"""
    <div style='display:flex;justify-content:space-between;align-items:center;
                padding:0.5rem 0;border-bottom:1px solid var(--border);'>
        <div style='font-size:0.75rem;color:var(--text-muted);font-weight:500;
                    text-transform:uppercase;letter-spacing:0.07em;'>{label}</div>
        <div style='font-size:0.88rem;color:var(--text);font-weight:600;{font}'>{value or "—"}</div>
    </div>
    """, unsafe_allow_html=True)


def _section(title: str):
    st.markdown(
        f"<p class='ic-section-title'>{title}</p>", unsafe_allow_html=True)


# ─── HEADER ───────────────────────────────────────────────────────────────────

def _render_header(case: dict):
    entity = case.get("entities") or {}
    status = case.get("status", "IN_PROGRESS")
    decision = case.get("decision", "")
    created = (case.get("created_at") or "")[:10] or "—"
    risk = case.get("risk_score")

    risk_color = "#00E676" if risk and risk < 0.35 else \
                 "#FFD740" if risk and risk < 0.65 else \
                 "#FF5252" if risk else "var(--text-muted)"

    st.markdown(f"""
    <div class='ic-page-header'>
        <div class='ic-logo-mark'>🏢</div>
        <div style='flex:1;'>
            <div style='display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap;'>
                <h1 style='margin:0;'>{entity.get('company_name','Unknown Entity')}</h1>
                {_status_badge(status, decision)}
            </div>
            <p style='margin:4px 0 0;'>
                {entity.get('sector','—')} &nbsp;·&nbsp;
                {entity.get('loan_type','—')} &nbsp;·&nbsp;
                ₹ {entity.get('loan_amount_cr','—')} Cr &nbsp;·&nbsp;
                Opened {created}
            </p>
        </div>
        <div style='text-align:right;flex-shrink:0;'>
            <div style='font-family:JetBrains Mono,monospace;font-size:1.8rem;
                        font-weight:700;color:{risk_color};line-height:1;'>
                {'%.3f' % risk if risk else '—'}
            </div>
            <div style='font-size:0.68rem;color:var(--text-muted);
                        text-transform:uppercase;letter-spacing:0.08em;margin-top:4px;'>
                Risk Score
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── TAB 1: EXTRACTION RESULTS ───────────────────────────────────────────────

def _render_extractions(case: dict):
    import pandas as pd

    raw = case.get("five_cs_json")
    if not raw:
        st.info("No extraction results yet — upload and classify documents first.")
        col_btn, _ = st.columns([2, 6])
        with col_btn:
            if st.button("📂 Upload & Classify Documents", type="primary", use_container_width=True):
                st.session_state.page = "classify"
                st.rerun()
        return

    data = raw if isinstance(raw, dict) else {}
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except Exception:
            st.warning("Could not parse extraction results.")
            return

    skip = {"extraction_confidence", "extraction_notes"}

    for filename, fields in data.items():
        if not isinstance(fields, dict):
            continue

        conf = fields.get("extraction_confidence", 0)
        notes = fields.get("extraction_notes", [])
        conf_color = "#00E676" if conf >= 0.7 else "#FFD740" if conf >= 0.4 else "#FF5252"
        border_color = "#1B5E20" if conf >= 0.7 else "#F57F17" if conf >= 0.4 else "#B71C1C"

        with st.expander(f"📄 {filename}  —  {conf:.0%} confidence", expanded=True):
            rows = []
            for field, value in fields.items():
                if field in skip or value is None:
                    continue
                label = (field.replace("_", " ")
                         .replace(" cr", " (₹ Cr)")
                         .replace(" pct", " (%)")
                         .title())
                if isinstance(value, float):
                    formatted = f"{value:,.2f}"
                elif isinstance(value, list):
                    formatted = ", ".join(str(x)
                                          for x in value) if value else "—"
                else:
                    formatted = str(value)
                rows.append({"Field": label, "Value": formatted})

            if rows:
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True, hide_index=True,
                             column_config={
                                 "Field": st.column_config.TextColumn(width="medium"),
                                 "Value": st.column_config.TextColumn(width="medium"),
                             })
            else:
                st.caption("No fields extracted.")

            for note in notes:
                st.caption(f"ℹ️ {note}")


# ─── TAB 2: ANALYSIS ─────────────────────────────────────────────────────────

def _render_analysis(case: dict):
    risk_score = case.get("risk_score")
    decision = case.get("decision", "")
    decisive = case.get("decisive_factor", "")
    research = case.get("research_json")
    fcs_raw = case.get("five_cs_json")

    if not risk_score and not decision:
        st.info("No analysis results yet — run AI credit analysis first.")
        col_btn, _ = st.columns([2, 6])
        with col_btn:
            if st.button("🔍 Run Analysis", type="primary", use_container_width=True):
                st.session_state.page = "analysis"
                st.rerun()
        return

    # Decision block
    d = (decision or "").upper()
    if "APPROVE" in d:
        css, icon = "decision-approve", "✅"
    elif "REJECT" in d:
        css, icon = "decision-reject", "❌"
    elif "CONDITIONAL" in d:
        css, icon = "decision-conditional", "⚠️"
    else:
        css, icon = "decision-conditional", "🔍"

    st.markdown(f'<div class="{css}">{icon} AI DECISION: {decision}</div>',
                unsafe_allow_html=True)

    if decisive:
        st.markdown(f"""
        <div class='decisive-factor'>
            <strong>⚡ DECISIVE FACTOR &nbsp;</strong>{decisive}
        </div>
        """, unsafe_allow_html=True)

    # Key metrics
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Risk Score", f"{risk_score:.3f}" if risk_score else "—")
    with c2:
        st.metric("AI Decision", decision or "—")
    with c3:
        fcs = fcs_raw if isinstance(fcs_raw, dict) else {}
        if isinstance(fcs_raw, str):
            try:
                fcs = json.loads(fcs_raw)
            except Exception:
                fcs = {}
        overall = fcs.get("overall_score")
        st.metric("Five Cs Score", f"{overall}/10" if overall else "—")

    # Research signals
    if research:
        res = research if isinstance(research, dict) else {}
        if isinstance(research, str):
            try:
                res = json.loads(research)
            except Exception:
                res = {}
        if res:
            st.markdown("<hr class='ic-divider'>", unsafe_allow_html=True)
            _section("Secondary Research Signals")
            with st.expander("📰 News & Legal Signals", expanded=False):
                st.json(res)


# ─── TAB 3: CAM REPORT ────────────────────────────────────────────────────────

def _render_cam(case: dict):
    from pathlib import Path

    cam_path = case.get("cam_path", "")
    if not cam_path:
        st.info("CAM report not generated yet — complete the analysis pipeline first.")
        col_btn, _ = st.columns([2, 6])
        with col_btn:
            if st.button("🔍 Go to Analysis", type="primary", use_container_width=True):
                st.session_state.page = "analysis"
                st.rerun()
        return

    docx_path = cam_path.replace(
        ".pdf", ".docx") if cam_path.endswith(".pdf") else ""

    st.markdown(f"""
    <div class='ic-card'>
        <div style='font-size:0.88rem;color:var(--text-sec);margin-bottom:1rem;'>
            Generated from AI analysis pipeline.
            Download and review before closing the case.
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if cam_path and Path(cam_path).exists():
            with open(cam_path, "rb") as f:
                st.download_button(
                    "📄 Download PDF CAM",
                    data=f.read(),
                    file_name=Path(cam_path).name,
                    mime="application/pdf",
                    use_container_width=True
                )
        else:
            st.caption("PDF report file not found on server.")
    with col2:
        if docx_path and Path(docx_path).exists():
            with open(docx_path, "rb") as f:
                st.download_button(
                    "📝 Download DOCX CAM",
                    data=f.read(),
                    file_name=Path(docx_path).name,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
        else:
            st.caption("DOCX report file not found on server.")

    st.markdown("</div>", unsafe_allow_html=True)


# ─── TAB 4: OFFICER ASSESSMENT ───────────────────────────────────────────────

def _render_closure_form(case: dict):
    case_id = case.get("id")
    status = (case.get("status") or "").upper()
    is_closed = status in ("CLOSED", "COMPLETED")

    # ── Already closed — read-only view ──────────────────────────────────────
    if is_closed:
        st.markdown(f"""
        <div style='background:var(--approve-bg);border:1px solid var(--approve-bd);
                    border-left:5px solid var(--approve);border-radius:10px;
                    padding:1rem 1.4rem;margin-bottom:1.2rem;'>
            <div style='font-weight:700;color:var(--approve);font-size:0.95rem;'>
                ✓ Case Closed
            </div>
            <div style='font-size:0.82rem;color:var(--text-sec);margin-top:4px;'>
                Closed on {(case.get('closed_at') or '')[:10] or '—'}
            </div>
        </div>
        """, unsafe_allow_html=True)

        _info_row("Officer Decision",   case.get("officer_decision", "—"))
        _info_row("Final Interest Rate",
                  f"{case.get('final_interest_rate')}% p.a."
                  if case.get("final_interest_rate") else "—")
        _info_row("Collateral Value",
                  f"₹ {case.get('collateral_value_cr')} Cr"
                  if case.get("collateral_value_cr") else "—")

        if case.get("officer_notes"):
            st.markdown("<hr class='ic-divider'>", unsafe_allow_html=True)
            st.markdown(f"""
            <div style='padding:0.75rem 1rem;background:var(--surface-2);
                        border-radius:8px;border:1px solid var(--border);'>
                <div style='font-size:0.72rem;color:var(--text-muted);
                            text-transform:uppercase;letter-spacing:0.07em;
                            margin-bottom:6px;'>Due Diligence Notes</div>
                <div style='font-size:0.85rem;color:var(--text);line-height:1.6;'>
                    {case.get('officer_notes','')}
                </div>
            </div>
            """, unsafe_allow_html=True)

        if case.get("closure_remarks"):
            st.markdown(f"""
            <div style='margin-top:0.75rem;padding:0.75rem 1rem;
                        background:var(--surface-2);border-radius:8px;
                        border:1px solid var(--border);'>
                <div style='font-size:0.72rem;color:var(--text-muted);
                            text-transform:uppercase;letter-spacing:0.07em;
                            margin-bottom:6px;'>Closure Remarks</div>
                <div style='font-size:0.85rem;color:var(--text);line-height:1.6;'>
                    {case.get('closure_remarks','')}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<hr class='ic-divider'>", unsafe_allow_html=True)
        if st.button("🔄 Re-open Case", use_container_width=False):
            update_case(case_id, {"status": "UNDER_REVIEW"})
            st.success("Case re-opened for review.")
            st.rerun()
        return

    # ── Active form ───────────────────────────────────────────────────────────
    st.markdown("""
    <div style='font-size:0.82rem;color:var(--text-muted);margin-bottom:1.2rem;
                padding:0.75rem 1rem;background:var(--info-bg);
                border-left:3px solid var(--info);border-radius:8px;'>
        Add your final assessment. Use <strong style='color:var(--text);'>Save Progress</strong>
        to save without closing. Use <strong style='color:var(--text);'>Close Case</strong>
        once you have reviewed the CAM report and made your final decision.
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        officer_decision = st.selectbox(
            "Officer Decision *",
            ["", "APPROVE", "CONDITIONAL", "REJECT"],
            index=["", "APPROVE", "CONDITIONAL", "REJECT"].index(
                case.get("officer_decision", "")
            ) if case.get("officer_decision", "") in
            ["", "APPROVE", "CONDITIONAL", "REJECT"] else 0,
            key="cv_decision"
        )
        final_interest = st.number_input(
            "Final Interest Rate (% p.a.)",
            min_value=0.0, max_value=36.0,
            value=float(case.get("final_interest_rate") or 0.0),
            step=0.25, format="%.2f",
            key="cv_interest",
            help="Interest rate agreed based on risk analysis"
        )

    with col2:
        entity = case.get("entities") or {}
        loan_amt = float(entity.get("loan_amount_cr") or 0)
        collateral_val = st.number_input(
            "Collateral Value (₹ Cr)",
            min_value=0.0,
            value=float(case.get("collateral_value_cr") or 0.0),
            step=0.5, format="%.2f",
            key="cv_collateral",
            help="Market value of security offered"
        )
        # Live coverage indicator
        coverage = round((collateral_val / loan_amt * 100),
                         1) if loan_amt > 0 else 0
        color = "#00E676" if coverage >= 100 else \
            "#FFD740" if coverage >= 60 else "#FF5252"
        label = "✓ Fully covered" if coverage >= 100 else \
            "⚠ Partially covered" if coverage >= 60 else "✗ Under-collateralised"
        st.markdown(f"""
        <div class='ic-card' style='text-align:center;padding:0.8rem;margin-top:1.6rem;'>
            <div style='font-size:0.68rem;color:var(--text-muted);
                        text-transform:uppercase;letter-spacing:0.08em;'>
                Collateral Coverage
            </div>
            <div style='font-size:1.8rem;font-weight:700;
                        font-family:JetBrains Mono,monospace;color:{color};margin:4px 0;'>
                {coverage:.0f}%
            </div>
            <div style='font-size:0.75rem;color:{color};'>{label}</div>
        </div>
        """, unsafe_allow_html=True)

    officer_notes = st.text_area(
        "Site Visit & Due Diligence Notes",
        value=case.get("officer_notes") or "",
        placeholder="e.g. Factory running at full capacity, strong order book from Tata Motors...",
        height=120,
        key="cv_notes"
    )

    closure_remarks = st.text_area(
        "Closure Remarks",
        value=case.get("closure_remarks") or "",
        placeholder="e.g. Approved subject to quarterly DSCR monitoring and personal guarantee...",
        height=80,
        key="cv_remarks"
    )

    st.markdown("<hr class='ic-divider'>", unsafe_allow_html=True)

    col_save, col_close, col_gap = st.columns([1.8, 1.8, 4])
    with col_save:
        if st.button("💾  Save Progress", use_container_width=True):
            update_case(case_id, {
                "officer_decision":    officer_decision or None,
                "final_interest_rate": final_interest if final_interest > 0 else None,
                "collateral_value_cr": collateral_val if collateral_val > 0 else None,
                "officer_notes":       officer_notes or None,
                "closure_remarks":     closure_remarks or None,
                "status":              "UNDER_REVIEW"
            })
            st.success("✅ Progress saved.")
            st.rerun()

    with col_close:
        if st.button("🔒  Close Case", type="primary", use_container_width=True):
            if not officer_decision:
                st.error("Select a decision before closing.")
            else:
                from datetime import datetime, timezone
                update_case(case_id, {
                    "officer_decision":    officer_decision,
                    "final_interest_rate": final_interest if final_interest > 0 else None,
                    "collateral_value_cr": collateral_val if collateral_val > 0 else None,
                    "officer_notes":       officer_notes or None,
                    "closure_remarks":     closure_remarks or None,
                    "status":              "CLOSED",
                    "decision":            officer_decision,
                    "closed_at":           datetime.now(timezone.utc).isoformat()
                })
                st.success("🔒 Case closed.")
                st.balloons()
                st.rerun()


# ─── MAIN RENDER ──────────────────────────────────────────────────────────────

def render():
    case_id = st.session_state.get("case_id")

    if not case_id:
        st.warning("No case selected. Open a case from the dashboard.")
        if st.button("← Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()
        return

    with st.spinner("Loading case..."):
        case = get_case(case_id)

    if not case:
        st.error(f"Case not found: {case_id}")
        return

    # Header
    _render_header(case)

    # Navigation row
    col_back, col_upload, col_analyse, col_gap = st.columns([1.5, 2, 2, 3])
    with col_back:
        if st.button("← Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
    with col_upload:
        if st.button("📂 Upload & Classify", use_container_width=True):
            st.session_state.page = "classify"
            st.rerun()
    with col_analyse:
        if st.button("🔍 Run Analysis", use_container_width=True):
            st.session_state.page = "analysis"
            st.rerun()

    st.markdown("<hr class='ic-divider'>", unsafe_allow_html=True)

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊  Extraction Results",
        "🤖  Analysis",
        "🧩  SWOT",
        "📄  CAM Report",
        "✅  Officer Assessment"
    ])

    with tab1:
        _section("Extracted Financial Data")
        _render_extractions(case)

    with tab2:
        _section("AI Analysis & Decision")
        _render_analysis(case)

    with tab3:
        _section("SWOT Analysis")
        swot_raw = case.get("swot_json")
        if swot_raw:
            from src.swot_generator import SWOTAnalysis, render_swot_ui
            swot = swot_raw if isinstance(
                swot_raw, SWOTAnalysis) else SWOTAnalysis(**swot_raw)
            render_swot_ui(swot)
        else:
            st.info("SWOT not generated yet — run the analysis pipeline first.")
            # Allow manual generation from case view
            if st.button("🧩 Generate SWOT Now", type="primary"):
                with st.spinner("Generating SWOT..."):
                    from src.swot_generator import generate_swot, save_swot_to_case
                    swot = generate_swot(case_dict=case)
                    save_swot_to_case(case_id, swot)
                    st.success("SWOT generated and saved.")
                    st.rerun()

    with tab4:
        _section("Credit Appraisal Memorandum")
        _render_cam(case)

    with tab5:
        _section("Officer Assessment & Case Closure")
        _render_closure_form(case)
