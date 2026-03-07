"""
cam_generator.py  —  IntelliCredit v1.3
Credit Appraisal Memorandum  —  PDF + DOCX

COLOUR SYSTEM
─────────────
  Navy  #0d1f5c  — ALL structural chrome: header bars, table headers,
                    section rules, borders, signature block
  Gold  #c9970a  — Cover accent rule only
  Green #1a6b2a  — APPROVE decision (badge / banner / gauge segment)
  Amber #b85c00  — CONDITIONAL decision + early-warning header
  Red   #b71c1c  — REJECT decision + adverse items
  White #ffffff  — text on dark backgrounds
  LBlue #e8edf8  — label-column tint in all info tables
  Tint  #f5f7fd  — alternating row tint
  MGray #c6cad8  — grid lines, dividers
  DGray #4c5068  — footer text, captions, notes
"""

from config import CAM_BANK_NAME, CAM_REPORT_TITLE, CAM_AUTHOR, OUTPUTS_DIR
from src.schemas import CreditAppraisalResult
from datetime import datetime
import sys
import math
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# ── Palette constants ──────────────────────────────────────────────────────────
NAV = "#0d1f5c"   # deep navy
NAV2 = "#1a3080"   # section heading navy
GOLD = "#c9970a"   # gold accent (cover only)
LBLU = "#e8edf8"   # label column background
TINT = "#f5f7fd"   # alternating row tint
MGRY = "#c6cad8"   # grid / divider
DGRY = "#4c5068"   # footer / caption
GRN = "#1a6b2a"   # APPROVE
AMB = "#b85c00"   # CONDITIONAL
RED = "#b71c1c"   # REJECT
WHT = "#ffffff"
GRN_L = "#e8f5ea"  # light green tint
AMB_L = "#fff4e5"  # light amber tint
RED_L = "#ffeaea"  # light red tint


class CAMGenerator:
    """Generates Credit Appraisal Memorandum in PDF and DOCX."""

    # ── public ────────────────────────────────────────────────────────────────

    def generate_both(self, result: CreditAppraisalResult) -> dict:
        safe = result.company_name.replace(" ", "_").replace("/", "-")
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        pdf = str(OUTPUTS_DIR / f"CAM_{safe}_{ts}.pdf")
        docx = str(OUTPUTS_DIR / f"CAM_{safe}_{ts}.docx")
        print("Generating PDF CAM...")
        self.generate_pdf(result, pdf)
        print("Generating DOCX CAM...")
        self.generate_docx(result, docx)
        print(f"Reports saved: {OUTPUTS_DIR}")
        return {"pdf": pdf, "docx": docx}

    # ── shared helpers ────────────────────────────────────────────────────────

    def _pred_strings(self, pred):
        if not pred:
            return "PENDING", "UNKNOWN", WHT, WHT, "PENDING"
        ds = str(pred.decision).replace("DecisionType.", "").upper()
        cs = str(pred.risk_category).replace("RiskCategory.", "").upper()
        if "APPROVE" in ds:
            bg, lt, label = GRN, GRN_L, "APPROVED"
        elif "REJECT" in ds:
            bg, lt, label = RED, RED_L, "REJECTED"
        else:
            bg, lt, label = AMB, AMB_L, "CONDITIONAL APPROVAL"
        return ds, cs, bg, lt, label

    def _derived_rows(self, result):
        d = result.derived_financials
        if not d:
            return []
        rows = []
        if d.debt_equity_ratio is not None:
            rows.append(("Debt / Equity Ratio",
                        f"{d.debt_equity_ratio:.2f}x"))
        if d.net_worth_inr is not None:
            rows.append(
                ("Net Worth",                f"Rs. {d.net_worth_inr:,.0f}"))
        if d.dscr is not None:
            rows.append(("DSCR",                     f"{d.dscr:.2f}x"))
        if d.net_profit_margin is not None:
            rows.append(("Net Profit Margin",
                        f"{d.net_profit_margin:.1f}%"))
        if getattr(d, "avg_monthly_balance_inr", None) is not None:
            rows.append(
                ("Avg Monthly Balance",  f"Rs. {d.avg_monthly_balance_inr:,.0f}"))
        if getattr(d, "monthly_credit_avg_inr", None) is not None:
            rows.append(
                ("Monthly Credit Avg",   f"Rs. {d.monthly_credit_avg_inr:,.0f}"))
        if d.data_completeness_pct is not None:
            rows.append(
                ("Data Completeness",    f"{d.data_completeness_pct:.0f}%"))
        for i, n in enumerate((getattr(d, "derivation_notes", None) or [])[:3]):
            rows.append((f"Note {i+1}", n))
        return rows

    # ── risk gauge ────────────────────────────────────────────────────────────

    def _risk_gauge(self, score: float, W=200, H=130):
        """
        Semi-circular needle gauge.
        Left-zone = Green (LOW 0–0.33)
        Mid-zone  = Amber (MED 0.33–0.66)
        Right-zone= Red   (HIGH 0.66–1.0)
        Needle angle maps score 0→180°, score 1→0°.
        """
        from reportlab.graphics.shapes import (
            Drawing, Wedge, Circle, String, Line, Rect
        )
        from reportlab.lib import colors as rc

        d = Drawing(W, H)
        cx = W / 2
        cy = H * 0.12           # pivot near bottom
        ro = H * 0.82           # outer arc radius
        ri = H * 0.49           # inner cutout radius  (donut thickness)
        rn = H * 0.70           # needle length

        # ── draw three coloured arc segments ─────────────────────────────────
        for start_a, end_a, colour in [
            (180, 120, GRN),      # LOW  — left  60°
            (120,  60, "#e8a020"),  # MED  — mid   60° (bright amber)
            (60,   0, RED),      # HIGH — right 60°
        ]:
            # outer wedge
            d.add(Wedge(cx, cy, ro, end_a, start_a,
                        fillColor=rc.HexColor(colour),
                        strokeColor=rc.white, strokeWidth=2))
            # inner white cutout (donut hole)
            d.add(Wedge(cx, cy, ri, end_a, start_a,
                        fillColor=rc.white,
                        strokeColor=rc.white, strokeWidth=1))

        # ── needle ────────────────────────────────────────────────────────────
        ang = math.radians(180 - score * 180)
        nx = cx + rn * math.cos(ang)
        ny = cy + rn * math.sin(ang)
        # shadow line (offset 1 px for depth)
        d.add(Line(cx+1, cy-1, nx+1, ny-1,
                   strokeColor=rc.HexColor("#aaaacc"), strokeWidth=2))
        # main needle
        d.add(Line(cx, cy, nx, ny,
                   strokeColor=rc.HexColor(NAV), strokeWidth=3.2))
        # pivot circle
        d.add(Circle(cx, cy, 7,
                     fillColor=rc.HexColor(NAV),
                     strokeColor=rc.white, strokeWidth=1.5))

        # ── score text centred in donut ───────────────────────────────────────
        sc_col = GRN if score < 0.33 else ("#e8a020" if score < 0.66 else RED)
        d.add(String(cx, cy + ri * 0.18, f"{score:.3f}",
                     fontSize=16, fontName="Helvetica-Bold",
                     fillColor=rc.HexColor(sc_col), textAnchor="middle"))

        # ── axis ticks & labels ───────────────────────────────────────────────
        for val, deg in [(0.0, 180), (0.5, 90), (1.0, 0)]:
            ax = cx + (ro + 4) * math.cos(math.radians(deg))
            ay = cy + (ro + 4) * math.sin(math.radians(deg))
            d.add(String(ax, ay - 3, str(val), fontSize=6.5,
                         fillColor=rc.HexColor(DGRY),
                         textAnchor="middle"))

        # ── zone labels inside arcs ───────────────────────────────────────────
        for lbl, angle_deg, col in [
            ("LOW",  150, GRN),
            ("MED",   90, "#e8a020"),
            ("HIGH",  30, RED),
        ]:
            mid_r = (ro + ri) / 2
            lx = cx + mid_r * math.cos(math.radians(angle_deg))
            ly = cy + mid_r * math.sin(math.radians(angle_deg))
            d.add(String(lx, ly - 3, lbl, fontSize=7.5,
                         fontName="Helvetica-Bold",
                         fillColor=rc.white,
                         textAnchor="middle"))
        return d

    # ══════════════════════════════════════════════════════════════════════════
    # PDF
    # ══════════════════════════════════════════════════════════════════════════

    def generate_pdf(self, result: CreditAppraisalResult, output_path: str) -> str:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
        from reportlab.platypus import (
            BaseDocTemplate, Frame, PageTemplate,
            Paragraph, Spacer, Table, TableStyle,
            HRFlowable, PageBreak, NextPageTemplate,
        )
        from reportlab.graphics.shapes import Drawing, Rect, String, Line

        PW, PH = A4                    # 595.3 × 841.9 pt
        LM = RM = 1.9 * cm
        TM = 2.4 * cm
        BM = 2.0 * cm
        TW = PW - LM - RM              # usable text width ≈ 17.6 cm

        # colour shortcuts
        C = colors.HexColor
        cNAV = C(NAV)
        cNAV2 = C(NAV2)
        cGOLD = C(GOLD)
        cLBL = C(LBLU)
        cTNT = C(TINT)
        cMGR = C(MGRY)
        cDGR = C(DGRY)
        cGRN = C(GRN)
        cAMB = C(AMB)
        cRED = C(RED)
        cWHT = colors.white

        # ── typography ─────────────────────────────────────────────────────────
        SS = getSampleStyleSheet()
        _id = [0]

        def PS(base_name="Normal", **kw):
            _id[0] += 1
            base = kw.pop("parent", SS.get(base_name, SS["Normal"]))
            return ParagraphStyle(f"_s{_id[0]}", parent=base, **kw)

        # body
        pN = PS(fontSize=9,  fontName="Helvetica",
                leading=13.5, textColor=colors.black)
        pB = PS(fontSize=9,  fontName="Helvetica-Bold",
                leading=13.5, textColor=colors.black)
        pS = PS(fontSize=7.5, fontName="Helvetica",
                leading=11,   textColor=cDGR)
        pSB = PS(fontSize=7.5, fontName="Helvetica-Bold",
                 leading=11,   textColor=colors.black)
        pJ = PS(fontSize=9,  fontName="Helvetica",       leading=14,
                alignment=TA_JUSTIFY, textColor=colors.black)
        # centred variants
        pNC = PS(fontSize=9,  fontName="Helvetica",       leading=13.5,
                 alignment=TA_CENTER, textColor=colors.black)
        pBC = PS(fontSize=9,  fontName="Helvetica-Bold",  leading=13.5,
                 alignment=TA_CENTER, textColor=colors.black)
        pWC = PS(fontSize=9,  fontName="Helvetica-Bold",
                 leading=13.5, alignment=TA_CENTER, textColor=cWHT)
        pWL = PS(fontSize=9,  fontName="Helvetica-Bold",
                 leading=13.5, textColor=cWHT)

        # ── runtime data ───────────────────────────────────────────────────────
        pred = result.risk_prediction
        ds, cs, dec_bg, dec_lt, dec_label = self._pred_strings(pred)
        now = datetime.now()
        ref = (f"CAM/{now.year}/"
               f"{result.company_name[:4].upper()}/"
               f"{now.strftime('%m%d%H%M')}")

        # ── page background callbacks ──────────────────────────────────────────

        def _cover_bg(canv, doc):
            canv.saveState()
            # full-bleed navy top bar (≈ 3.8 cm)
            canv.setFillColor(cNAV)
            canv.rect(0, PH - 3.8*cm, PW, 3.8*cm, fill=1, stroke=0)
            # bank name centred in bar
            canv.setFont("Helvetica-Bold", 16)
            canv.setFillColor(cWHT)
            canv.drawCentredString(PW/2, PH - 1.85*cm, CAM_BANK_NAME.upper())
            # sub-line
            canv.setFont("Helvetica", 9)
            canv.setFillColor(C("#b8c8f0"))
            canv.drawCentredString(
                PW/2, PH - 2.7*cm, "Credit Risk Management Division")
            # gold divider rule
            canv.setStrokeColor(cGOLD)
            canv.setLineWidth(2.2)
            canv.line(LM, PH - 3.95*cm, PW - RM, PH - 3.95*cm)
            # navy bottom strip
            canv.setFillColor(cNAV)
            canv.rect(0, 0, PW, 1.35*cm, fill=1, stroke=0)
            canv.setFont("Helvetica", 7)
            canv.setFillColor(C("#b8c8f0"))
            canv.drawCentredString(
                PW/2, 0.48*cm,
                "STRICTLY CONFIDENTIAL  —  FOR INTERNAL USE ONLY  —  NOT FOR DISTRIBUTION")
            # watermark
            canv.saveState()
            canv.translate(PW/2, PH/2 - 1*cm)
            canv.rotate(35)
            canv.setFont("Helvetica-Bold", 58)
            canv.setFillColor(colors.Color(0.78, 0.82, 0.92, alpha=0.10))
            canv.drawCentredString(0, 0, "CONFIDENTIAL")
            canv.restoreState()
            canv.restoreState()

        def _body_bg(canv, doc):
            canv.saveState()
            # ── header ──────────────────────────────────────────────────────
            canv.setFillColor(cNAV)
            canv.rect(0, PH - 1.35*cm, PW, 1.35*cm, fill=1, stroke=0)
            # bank name — left
            canv.setFont("Helvetica-Bold", 8)
            canv.setFillColor(cWHT)
            canv.drawString(LM, PH - 0.82*cm, CAM_BANK_NAME.upper())
            # ref + page — right
            canv.setFont("Helvetica", 7.5)
            canv.setFillColor(C("#b8c8f0"))
            canv.drawRightString(PW - RM, PH - 0.82*cm,
                                 f"Ref: {ref}   |   Page {doc.page}")
            # gold hairline beneath header
            canv.setStrokeColor(cGOLD)
            canv.setLineWidth(1.4)
            canv.line(0, PH - 1.46*cm, PW, PH - 1.46*cm)
            # ── footer ──────────────────────────────────────────────────────
            canv.setStrokeColor(cMGR)
            canv.setLineWidth(0.5)
            canv.line(LM, 1.5*cm, PW - RM, 1.5*cm)
            canv.setFont("Helvetica", 7)
            canv.setFillColor(cDGR)
            canv.drawString(LM, 0.82*cm,
                            "STRICTLY CONFIDENTIAL  —  FOR INTERNAL USE ONLY")
            canv.drawRightString(PW - RM, 0.82*cm,
                                 f"{now.strftime('%d %b %Y, %I:%M %p')}   |   {CAM_AUTHOR}")
            canv.restoreState()

        # ── page templates + frames ────────────────────────────────────────────
        cover_frame = Frame(LM, 1.5*cm, TW, PH - 4.1*cm - 1.5*cm,
                            id="cover", showBoundary=0)
        body_frame = Frame(LM, BM, TW, PH - TM - BM,
                           id="body",  showBoundary=0)

        pdf_doc = BaseDocTemplate(
            output_path, pagesize=A4,
            leftMargin=LM, rightMargin=RM,
            topMargin=TM,  bottomMargin=BM,
        )
        pdf_doc.addPageTemplates([
            PageTemplate(id="Cover", frames=[cover_frame], onPage=_cover_bg),
            PageTemplate(id="Body",  frames=[body_frame],  onPage=_body_bg),
        ])

        # ── reusable table builders ────────────────────────────────────────────

        def info_tbl(rows, lw=5.0*cm, fs=9, pad=5):
            """Two-column label→value info table. rows = list of (label, value) pairs."""
            rw = TW - lw
            lp = pad + 1
            data = []
            for lbl, val in rows:
                data.append([
                    Paragraph(str(lbl), PS(fontSize=fs, fontName="Helvetica-Bold",
                                           leading=fs+4, textColor=colors.black)),
                    Paragraph(str(val), PS(fontSize=fs, fontName="Helvetica",
                                           leading=fs+4, textColor=colors.black)),
                ])
            t = Table(data, colWidths=[lw, rw])
            t.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (0, -1), cLBL),
                ("BACKGROUND",    (1, 0), (1, -1), cWHT),
                ("ROWBACKGROUNDS", (1, 0), (1, -1), [cWHT, cTNT]),
                ("BOX",           (0, 0), (-1, -1), 0.7, cNAV2),
                ("INNERGRID",     (0, 0), (-1, -1), 0.3, cMGR),
                ("LEFTPADDING",   (0, 0), (-1, -1), lp),
                ("RIGHTPADDING",  (0, 0), (-1, -1), pad),
                ("TOPPADDING",    (0, 0), (-1, -1), pad),
                ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
                ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ]))
            return t

        def section_hdr(title):
            """Navy left-bar + grey hairline + bold title — section separator."""
            BAR = 15        # total height of the drawing
            drw = Drawing(TW, BAR + 4)
            # solid navy left bar
            drw.add(Rect(0, 0, 4, BAR + 4,
                         fillColor=cNAV, strokeColor=None))
            # hairline rule spanning full width at bottom
            drw.add(Line(0, 0, TW, 0,
                         strokeColor=cMGR, strokeWidth=0.6))
            # title text
            drw.add(String(11, 3.5, title,
                           fontSize=10.5, fontName="Helvetica-Bold",
                           fillColor=C(NAV2)))
            return drw

        def col_tbl(rows, widths, hdr_col=NAV):
            """Multi-column table. rows[0] = header. Returns styled Table."""
            t = Table(rows, colWidths=widths, repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0),  C(hdr_col)),
                ("TEXTCOLOR",     (0, 0), (-1, 0),  cWHT),
                ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
                ("FONTSIZE",      (0, 0), (-1, -1),  8.5),
                ("LEADING",       (0, 0), (-1, -1),  12),
                ("BOX",           (0, 0), (-1, -1),  0.7, cNAV2),
                ("INNERGRID",     (0, 0), (-1, -1),  0.3, cMGR),
                ("LEFTPADDING",   (0, 0), (-1, -1),  6),
                ("RIGHTPADDING",  (0, 0), (-1, -1),  6),
                ("TOPPADDING",    (0, 0), (-1, -1),  5),
                ("BOTTOMPADDING", (0, 0), (-1, -1),  5),
                ("VALIGN",        (0, 0), (-1, -1),  "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),  [cWHT, cTNT]),
            ]))
            return t

        def gap(h):
            return Spacer(1, h * cm)

        # ══════════════════════════════════════════════════════════════════════
        # STORY
        # ══════════════════════════════════════════════════════════════════════
        story = [NextPageTemplate("Cover")]

        # ── COVER PAGE ─────────────────────────────────────────────────────────
        story.append(gap(0.8))   # clear the navy bar

        story.append(Paragraph(
            "CREDIT APPRAISAL MEMORANDUM",
            PS(fontSize=22, fontName="Helvetica-Bold",
               alignment=TA_CENTER, textColor=C(NAV), spaceAfter=5)
        ))
        story.append(Paragraph(
            "Internal Document  —  Credit Committee Submission",
            PS(fontSize=9, fontName="Helvetica",
               alignment=TA_CENTER, textColor=cDGR, spaceAfter=0)
        ))
        story.append(gap(0.28))
        story.append(HRFlowable(width="75%", thickness=1.8,
                                color=cGOLD, hAlign="CENTER"))
        story.append(gap(0.55))

        # cover detail table — navy label column, clean value column
        cov_rows_data = [
            ("Applicant / Borrower",    result.company_name),
            ("Reference No.",           ref),
            ("Loan Purpose",
             getattr(result, "loan_purpose", "Working Capital")),
            ("Facility Amount",
             (f"Rs. {pred.loan_limit_inr:,.0f}  "
              f"(Rs. {pred.loan_limit_inr/100000:.2f} Lakhs)")
             if pred else "N/A"),
            ("AI Decision",             dec_label),
            ("Risk Score",
             f"{pred.risk_score:.3f} / 1.000  ({cs} risk)" if pred else "N/A"),
            ("Interest Rate",
             f"{pred.interest_rate:.2f}% p.a." if pred else "N/A"),
            ("Report Date",             now.strftime("%d %B %Y")),
            ("Prepared By",             CAM_AUTHOR),
            ("Classification",          "STRICTLY CONFIDENTIAL"),
        ]
        # build as raw list for custom per-row styling
        cov_tbl_data = [
            [Paragraph(l, PS(fontSize=9, fontName="Helvetica-Bold",
                             leading=13, textColor=cWHT)),
             Paragraph(v, PS(fontSize=9, fontName="Helvetica",
                             leading=13, textColor=colors.black))]
            for l, v in cov_rows_data
        ]
        cov_tbl = Table(cov_tbl_data, colWidths=[5.6*cm, TW - 5.6*cm])
        cov_style = TableStyle([
            ("BACKGROUND",    (0, 0), (0, -1),  cNAV),     # label col navy
            ("BACKGROUND",    (1, 0), (1, -1),  cWHT),
            ("ROWBACKGROUNDS", (1, 0), (1, -1),  [cWHT, cTNT]),
            ("BOX",           (0, 0), (-1, -1),  1.1, cNAV),
            ("INNERGRID",     (0, 0), (-1, -1),  0.4, cMGR),
            ("LEFTPADDING",   (0, 0), (-1, -1),  9),
            ("RIGHTPADDING",  (0, 0), (-1, -1),  9),
            ("TOPPADDING",    (0, 0), (-1, -1),  7),
            ("BOTTOMPADDING", (0, 0), (-1, -1),  7),
            ("VALIGN",        (0, 0), (-1, -1),  "MIDDLE"),
            # Decision row (row 4) — green / amber / red background
            ("BACKGROUND",    (1, 4), (1, 4),   C(dec_bg)),
            ("TEXTCOLOR",     (1, 4), (1, 4),   cWHT),
            ("FONTNAME",      (1, 4), (1, 4),   "Helvetica-Bold"),
            # Classification row — amber tint
            ("BACKGROUND",    (1, -1), (1, -1),  C(AMB_L)),
            ("TEXTCOLOR",     (1, -1), (1, -1),  C(AMB)),
            ("FONTNAME",      (1, -1), (1, -1),  "Helvetica-Bold"),
        ])
        cov_tbl.setStyle(cov_style)
        story.append(cov_tbl)
        story.append(gap(0.65))

        # credit committee approval block
        story.append(Paragraph(
            "FOR CREDIT COMMITTEE USE",
            PS(fontSize=8.5, fontName="Helvetica-Bold",
               alignment=TA_CENTER, textColor=C(NAV2))
        ))
        story.append(gap(0.15))
        cw3 = TW / 3
        appr_data = [
            # header row
            [Paragraph("Prepared by",  pWC),
             Paragraph("Reviewed by",  pWC),
             Paragraph("Approved by",  pWC)],
            # role row
            [Paragraph("Credit Analyst",          pNC),
             Paragraph("Credit Manager / AGM",    pNC),
             Paragraph("Chief Credit Officer",    pNC)],
            # signature row
            [Paragraph("\n\n\n___________________________", pNC),
             Paragraph("\n\n\n___________________________", pNC),
             Paragraph("\n\n\n___________________________", pNC)],
            # name row
            [Paragraph("Name & Emp. ID", pS),
             Paragraph("Name & Emp. ID", pS),
             Paragraph("Name & Emp. ID", pS)],
            # date row
            [Paragraph("Date:  _________________", pS),
             Paragraph("Date:  _________________", pS),
             Paragraph("Date:  _________________", pS)],
        ]
        appr_tbl = Table(appr_data, colWidths=[cw3, cw3, cw3])
        appr_tbl.setStyle(TableStyle([
            ("BOX",           (0, 0), (-1, -1), 0.8, cNAV),
            ("INNERGRID",     (0, 0), (-1, -1), 0.4, cMGR),
            ("BACKGROUND",    (0, 0), (-1, 1),  cNAV),
            ("BACKGROUND",    (0, 2), (-1, -1),  cTNT),
            ("TOPPADDING",    (0, 0), (-1, -1),  6),
            ("BOTTOMPADDING", (0, 0), (-1, -1),  6),
            ("LEFTPADDING",   (0, 0), (-1, -1),  5),
            ("RIGHTPADDING",  (0, 0), (-1, -1),  5),
            ("ALIGN",         (0, 0), (-1, -1),  "CENTER"),
        ]))
        story.append(appr_tbl)

        # ── body pages ─────────────────────────────────────────────────────────
        story.append(NextPageTemplate("Body"))
        story.append(PageBreak())

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 1  —  EXECUTIVE SUMMARY
        # ══════════════════════════════════════════════════════════════════════
        story.append(section_hdr("SECTION 1   —   EXECUTIVE SUMMARY"))
        story.append(gap(0.28))

        if pred:
            # ── small gauge, centred on its own line ──────────────────────────
            gauge = self._risk_gauge(pred.risk_score, W=148, H=96)

            # decision badge
            badge_d = Table(
                [[Paragraph(f"<b>{dec_label}</b>",
                            PS(fontSize=9, fontName="Helvetica-Bold",
                                alignment=TA_CENTER, textColor=cWHT))]],
                colWidths=[4.4*cm]
            )
            badge_d.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), C(dec_bg)),
                ("TOPPADDING",    (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("BOX",           (0, 0), (-1, -1), 0, cWHT),
            ]))

            # gauge card — narrow, centred
            gauge_card = Table(
                [[gauge],
                 [Paragraph("RISK SCORE GAUGE",
                            PS(fontSize=7, fontName="Helvetica-Bold",
                                alignment=TA_CENTER, textColor=cDGR))],
                 [badge_d],
                 [Paragraph(f"Score: {pred.risk_score:.3f}   |   {cs} Risk",
                            PS(fontSize=7, fontName="Helvetica",
                                alignment=TA_CENTER, textColor=cDGR,
                                spaceBefore=3))]],
                colWidths=[4.8*cm],
                hAlign="CENTER"
            )
            gauge_card.setStyle(TableStyle([
                ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
                ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING",    (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("BOX",           (0, 0), (-1, -1), 0.6, cMGR),
                ("BACKGROUND",    (0, 0), (-1, -1), cTNT),
            ]))

            # full-width wrapper to centre the card
            gauge_wrapper = Table([[gauge_card]], colWidths=[TW])
            gauge_wrapper.setStyle(TableStyle([
                ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
                ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING",    (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING",   (0, 0), (-1, -1), 0),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
            ]))
            story.append(gauge_wrapper)
            story.append(gap(0.25))

            # ── executive summary table — full width, starts on next line ─────
            exec_rows = [
                ("Company / Borrower",  result.company_name),
                ("GSTIN",
                 result.gst_data.gstin if result.gst_data else "N/A"),
                ("Constitution",
                 getattr(result, "constitution", "Private Limited Company")),
                ("Industry / Sector",
                 getattr(result, "sector", "—")),
                ("Reference No.",       ref),
                ("Report Date",         now.strftime("%d-%m-%Y")),
                ("AI Decision",         dec_label),
                ("Risk Category",       cs),
                ("Risk Score",          f"{pred.risk_score:.3f} / 1.000"),
                ("Recommended Limit",
                 f"Rs. {pred.loan_limit_inr:,.0f}  "
                 f"(Rs. {pred.loan_limit_inr/100000:.2f} Lakhs)"),
                ("Interest Rate",       f"{pred.interest_rate:.2f}% p.a."),
            ]
            et = info_tbl(exec_rows, lw=5.0*cm, fs=9, pad=5)

            # highlight decision row (index 6 = "AI Decision")
            et.setStyle(TableStyle([
                ("BACKGROUND", (1, 6), (1, 6), C(dec_bg)),
                ("TEXTCOLOR",  (1, 6), (1, 6), cWHT),
                ("FONTNAME",   (1, 6), (1, 6), "Helvetica-Bold"),
            ]))
            story.append(et)
        else:
            story.append(info_tbl([
                ("Company",   result.company_name),
                ("GSTIN",     result.gst_data.gstin if result.gst_data else "N/A"),
                ("Date",      now.strftime("%d-%m-%Y")),
                ("Decision",  "Pending"),
            ]))
        story.append(gap(0.4))

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 2  —  BORROWER PROFILE
        # ══════════════════════════════════════════════════════════════════════
        story.append(section_hdr("SECTION 2   —   BORROWER PROFILE"))
        story.append(gap(0.22))
        story.append(info_tbl([
            ("Legal Name",          result.company_name),
            ("GSTIN",
             result.gst_data.gstin if result.gst_data else "N/A"),
            ("PAN",
             result.itr_data.pan if result.itr_data else "N/A"),
            ("Assessment Year",
             result.itr_data.assessment_year if result.itr_data else "N/A"),
            ("Constitution",        "Private Limited Company"),
            ("Business Activity",   getattr(result, "sector", "—")),
            ("Key Promoters",
             getattr(result, "promoter_name", "As per application")),
            ("Registered Office",   "As per MCA records"),
        ]))
        story.append(gap(0.4))

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 3  —  FINANCIAL ANALYSIS
        # ══════════════════════════════════════════════════════════════════════
        story.append(section_hdr("SECTION 3   —   FINANCIAL ANALYSIS"))
        story.append(gap(0.2))

        sub_hdr = PS(fontSize=9, fontName="Helvetica-Bold", leading=13,
                     textColor=C(NAV2), spaceBefore=4, spaceAfter=6)

        story.append(Paragraph(
            "3.1   Key Financial Ratios  (auto-derived from documents)", sub_hdr))
        dr = self._derived_rows(result)
        if dr:
            story.append(info_tbl(dr, fs=8.5, pad=4))
        else:
            story.append(Paragraph(
                "Financial ratios could not be derived — upload ITR and Bank Statement.", pS))
        story.append(gap(0.2))

        story.append(Paragraph("3.2   GST Reconciliation", sub_hdr))
        gst = result.gst_data
        if gst:
            story.append(info_tbl([
                ("GSTIN",          gst.gstin or "N/A"),
                ("Turnover (3B)",
                 f"Rs. {gst.turnover:,.0f}" if gst.turnover else "N/A"),
                ("ITC Claimed",
                 f"Rs. {gst.itc_claimed:,.0f}" if gst.itc_claimed else "N/A"),
                ("Total Tax Paid",
                 f"Rs. {gst.total_tax:,.0f}" if gst.total_tax else "N/A"),
            ], fs=8.5, pad=4))
        else:
            story.append(Paragraph("GST data not available.", pS))
        story.append(gap(0.2))

        story.append(Paragraph("3.3   Bank Statement Summary", sub_hdr))
        bk = result.bank_data
        if bk:
            story.append(info_tbl([
                ("Total Credits (period)",
                 f"Rs. {bk.total_credits:,.0f}"
                 if getattr(bk, "total_credits", None) else "N/A"),
                ("Total Debits (period)",
                 f"Rs. {bk.total_debits:,.0f}"
                 if getattr(bk, "total_debits", None) else "N/A"),
                ("Avg Monthly Balance",
                 f"Rs. {bk.average_monthly_balance:,.0f}"
                 if getattr(bk, "average_monthly_balance", None) else "N/A"),
                ("EMI Bounces",
                 str(getattr(bk, "emi_bounce_count", None) or 0)),
                ("Cheque Returns",
                 str(getattr(bk, "cheque_returns", None) or 0)),
            ], fs=8.5, pad=4))
        else:
            story.append(Paragraph("Bank statement data not available.", pS))
        story.append(gap(0.4))

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 4  —  FIVE Cs CREDIT ANALYSIS
        # ══════════════════════════════════════════════════════════════════════
        story.append(section_hdr("SECTION 4   —   FIVE Cs CREDIT ANALYSIS"))
        story.append(gap(0.22))

        if result.five_cs:
            obj5 = result.five_cs
            W0, W1, W2, W3 = 2.9*cm, 1.9*cm, 2.6*cm, TW - 7.8*cm
            hdr5 = [Paragraph("Parameter", pWL), Paragraph("Score", pWC), Paragraph(
                "Rating", pWC), Paragraph("Assessment Summary", pWL)]
            rows5 = [hdr5]
            for lbl, o in [
                ("Character",  obj5.character), ("Capacity",   obj5.capacity),
                ("Capital",    obj5.capital),   ("Collateral", obj5.collateral),
                ("Conditions", obj5.conditions),
            ]:
                sc = o.score
                if sc >= 8.5:
                    rat, rc = "Excellent", GRN
                elif sc >= 7.0:
                    rat, rc = "Good",      GRN
                elif sc >= 5.5:
                    rat, rc = "Adequate",  AMB
                else:
                    rat, rc = "Weak",      RED
                rows5.append([
                    Paragraph(lbl, pB),
                    Paragraph(f"{sc}/10", pBC),
                    Paragraph(f'<font color="{rc}"><b>{rat}</b></font>', pNC),
                    Paragraph(o.summary, pN),
                ])
            rows5.append([
                Paragraph("<b>OVERALL</b>",              pB),
                Paragraph(f"<b>{obj5.overall_score}/10</b>", pBC),
                Paragraph("<b>Weighted Avg.</b>",        pBC),
                Paragraph(
                    "Combined weighted score across all five parameters.", pN),
            ])
            five_tbl = Table(rows5, colWidths=[W0, W1, W2, W3])
            five_tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0),  cNAV),
                ("TEXTCOLOR",     (0, 0), (-1, 0),  cWHT),
                ("BACKGROUND",    (0, -1), (-1, -1), cLBL),
                ("FONTNAME",      (0, -1), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE",      (0, 0), (-1, -1),  8.5),
                ("LEADING",       (0, 0), (-1, -1),  12.5),
                ("BOX",           (0, 0), (-1, -1),  0.7, cNAV2),
                ("INNERGRID",     (0, 0), (-1, -1),  0.3, cMGR),
                ("LEFTPADDING",   (0, 0), (-1, -1),  6),
                ("RIGHTPADDING",  (0, 0), (-1, -1),  6),
                ("TOPPADDING",    (0, 0), (-1, -1),  5),
                ("BOTTOMPADDING", (0, 0), (-1, -1),  5),
                ("VALIGN",        (0, 0), (-1, -1),  "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2),  [cWHT, cTNT]),
            ]))
            story.append(five_tbl)
        else:
            story.append(Paragraph("Five Cs analysis not available.", pS))
        story.append(gap(0.4))

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 5  —  AI RISK DRIVERS  (SHAP)
        # ══════════════════════════════════════════════════════════════════════
        story.append(section_hdr(
            "SECTION 5   —   AI RISK DRIVERS  (SHAP ANALYSIS)"))
        story.append(gap(0.18))
        story.append(Paragraph(
            "Factors ranked by absolute SHAP contribution to the XGBoost risk score. "
            "Higher values indicate stronger influence on the model output.",
            pJ))
        story.append(gap(0.12))

        if pred and pred.top_shap_factors:
            WS0, WS1, WS2, WS3 = 5.4*cm, 2.4*cm, 3.2*cm, TW - 11.4*cm
            shap_rows = [[
                Paragraph("Risk Factor",    pWL),
                Paragraph("SHAP Impact",    pWC),
                Paragraph("Direction",      pWC),
                Paragraph("Interpretation", pWL),
            ]]
            for f in pred.top_shap_factors:
                up = "increases" in f.direction.lower()
                dcol = RED if up else GRN
                dicon = "▲ Increases" if up else "▼ Decreases"
                interp = ("Unfavourable — pushes score higher"
                          if up else "Favourable — reduces risk score")
                shap_rows.append([
                    Paragraph(f.display_name, pN),
                    Paragraph(f"{f.shap_value:.4f}", pNC),
                    Paragraph(
                        f'<font color="{dcol}"><b>{dicon}</b></font>', pNC),
                    Paragraph(interp, pS),
                ])
            story.append(col_tbl(shap_rows, [WS0, WS1, WS2, WS3]))
        else:
            story.append(Paragraph("SHAP analysis not available.", pS))
        story.append(gap(0.4))

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 6  —  AI REASONING CHAIN
        # ══════════════════════════════════════════════════════════════════════
        story.append(section_hdr("SECTION 6   —   AI REASONING CHAIN"))
        story.append(gap(0.18))
        story.append(Paragraph(
            "Output of Groq LLaMA 3.3 70B. Supplementary to the quantitative XGBoost "
            "score — does not override the model output.",
            pJ))
        story.append(gap(0.12))

        if result.reasoning_chain:
            key_starts = ("DECISION:", "LIMIT:", "RATE:", "REASONING",
                          "DECISIVE", "LOAN")
            rc_data = []
            for line in result.reasoning_chain.split("\n"):
                line = line.strip()
                if not line:
                    continue
                is_key = any(line.upper().startswith(k) for k in key_starts)
                rc_data.append([Paragraph(line, pB if is_key else pN)])
            if rc_data:
                rc_tbl = Table(rc_data, colWidths=[TW])
                rc_tbl.setStyle(TableStyle([
                    ("BOX",           (0, 0), (-1, -1), 0.7, cNAV2),
                    ("INNERGRID",     (0, 0), (-1, -1), 0.2, cTNT),
                    ("BACKGROUND",    (0, 0), (-1, -1), C("#f8f9ff")),
                    ("LEFTPADDING",   (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
                    ("TOPPADDING",    (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
                ]))
                story.append(rc_tbl)
        else:
            story.append(Paragraph("AI reasoning not available.", pS))
        story.append(gap(0.4))

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 7  —  EXTERNAL RESEARCH & DUE DILIGENCE
        # ══════════════════════════════════════════════════════════════════════
        story.append(section_hdr(
            "SECTION 7   —   EXTERNAL RESEARCH & DUE DILIGENCE"))
        story.append(gap(0.22))

        if result.research:
            r = result.research
            story.append(info_tbl([
                ("News Risk Score",    f"{r.news_risk_score}/10"),
                ("Negative Articles",  str(len(r.negative_news))),
                ("Litigation Detected",
                 "YES — see below" if r.litigation_found else "None found"),
                ("MCA Charges",
                 f"{len(r.mca_charges)} charge(s)"
                 if r.mca_charges else "None found"),
                ("RBI / SEBI Actions", "None found"),
            ], fs=8.5, pad=4))
            if r.research_summary:
                story.append(gap(0.15))
                story.append(Paragraph(r.research_summary, pJ))
            if r.negative_news:
                story.append(gap(0.12))
                story.append(Paragraph("Adverse News Articles:", pB))
                story.append(gap(0.08))
                neg_rows = [[
                    Paragraph("Date",     pWL),
                    Paragraph("Headline", pWL),
                    Paragraph("Source",   pWL),
                ]]
                for item in r.negative_news[:5]:
                    neg_rows.append([
                        Paragraph(str(item.date)[:10], pS),
                        Paragraph(item.title,          pS),
                        Paragraph(item.source,         pS),
                    ])
                neg_tbl = Table(neg_rows, colWidths=[2.1*cm, 10.8*cm, 3.1*cm])
                neg_tbl.setStyle(TableStyle([
                    ("BACKGROUND",    (0, 0), (-1, 0),  C(RED_L)),
                    ("TEXTCOLOR",     (0, 0), (-1, 0),  cRED),
                    ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
                    ("FONTSIZE",      (0, 0), (-1, -1),  8),
                    ("LEADING",       (0, 0), (-1, -1),  11),
                    ("BOX",           (0, 0), (-1, -1),  0.5, cMGR),
                    ("INNERGRID",     (0, 0), (-1, -1),  0.3, cMGR),
                    ("LEFTPADDING",   (0, 0), (-1, -1),  5),
                    ("RIGHTPADDING",  (0, 0), (-1, -1),  5),
                    ("TOPPADDING",    (0, 0), (-1, -1),  4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1),  4),
                    ("VALIGN",        (0, 0), (-1, -1),  "MIDDLE"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1),  [cWHT, C(RED_L)]),
                ]))
                story.append(neg_tbl)
        else:
            story.append(
                Paragraph("No external research results available.", pS))
        story.append(gap(0.4))

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 8  —  EARLY WARNING SIGNALS
        # ══════════════════════════════════════════════════════════════════════
        story.append(section_hdr("SECTION 8   —   EARLY WARNING SIGNALS"))
        story.append(gap(0.22))

        if pred and pred.early_warning_signals:
            freqs = ["Monthly", "Quarterly",
                     "Quarterly", "At Renewal", "Annually"]
            ew_rows = [[
                Paragraph("#",        pWC),
                Paragraph("Signal",   pWL),
                Paragraph("Frequency", pWC),
            ]]
            for i, w in enumerate(pred.early_warning_signals):
                ew_rows.append([
                    Paragraph(str(i+1), pNC),
                    Paragraph(w,        pN),
                    Paragraph(freqs[i] if i < len(freqs)
                              else "Quarterly", pNC),
                ])
            ew_tbl = Table(ew_rows,
                           colWidths=[1.0*cm, TW - 5.6*cm, 4.1*cm])
            ew_tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0),  C(AMB)),
                ("TEXTCOLOR",     (0, 0), (-1, 0),  cWHT),
                ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
                ("FONTSIZE",      (0, 0), (-1, -1),  8.5),
                ("LEADING",       (0, 0), (-1, -1),  12),
                ("BOX",           (0, 0), (-1, -1),  0.7, cNAV2),
                ("INNERGRID",     (0, 0), (-1, -1),  0.3, cMGR),
                ("LEFTPADDING",   (0, 0), (-1, -1),  6),
                ("RIGHTPADDING",  (0, 0), (-1, -1),  6),
                ("TOPPADDING",    (0, 0), (-1, -1),  5),
                ("BOTTOMPADDING", (0, 0), (-1, -1),  5),
                ("VALIGN",        (0, 0), (-1, -1),  "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),  [cWHT, C(AMB_L)]),
            ]))
            story.append(ew_tbl)
        else:
            story.append(Paragraph("No early warning signals identified.", pS))
        story.append(gap(0.4))

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 9  —  CREDIT CONDITIONS & COVENANTS
        # ══════════════════════════════════════════════════════════════════════
        story.append(section_hdr(
            "SECTION 9   —   CREDIT CONDITIONS & COVENANTS"))
        story.append(gap(0.18))
        story.append(Paragraph(
            "The following standard conditions shall form part of the sanction, "
            "subject to Credit Committee approval and applicable RBI guidelines.",
            pJ))
        story.append(gap(0.12))

        cond_rows = [[
            Paragraph("#",         pWC),
            Paragraph("Type",      pWL),
            Paragraph("Condition", pWL),
        ]]
        for i, (ct, cx) in enumerate([
            ("Pre-Disbursement",
             "Submit audited financials and GST returns for the past 3 financial years."),
            ("Pre-Disbursement",
             "Execute all security documents; create SARFAESI-compliant first charge."),
            ("Pre-Disbursement",
             "Satisfactory legal opinion on property / security documents obtained."),
            ("Ongoing Covenant",
             "Quarterly submission of stock and debtor statements to the branch."),
            ("Ongoing Covenant",
             "Maintain DSCR above 1.25x at all times; report any breach within 7 days."),
            ("Ongoing Covenant", "Prior written approval required for additional long-term borrowings > Rs. 50 Lakhs."),
            ("Annual Review",
             "Submit audited Balance Sheet and P&L within 6 months of financial year-end."),
            ("Annual Review",    "Annual site inspection by relationship / credit manager."),
        ], 1):
            cond_rows.append([
                Paragraph(str(i),  pNC),
                Paragraph(ct,      pSB),
                Paragraph(cx,      pN),
            ])
        cond_tbl = Table(cond_rows,
                         colWidths=[0.8*cm, 3.6*cm, TW - 4.8*cm])
        cond_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  cNAV),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  cWHT),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1),  8.5),
            ("LEADING",       (0, 0), (-1, -1),  12),
            ("BOX",           (0, 0), (-1, -1),  0.7, cNAV2),
            ("INNERGRID",     (0, 0), (-1, -1),  0.3, cMGR),
            ("LEFTPADDING",   (0, 0), (-1, -1),  6),
            ("RIGHTPADDING",  (0, 0), (-1, -1),  6),
            ("TOPPADDING",    (0, 0), (-1, -1),  5),
            ("BOTTOMPADDING", (0, 0), (-1, -1),  5),
            ("VALIGN",        (0, 0), (-1, -1),  "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),  [cWHT, cTNT]),
        ]))
        story.append(cond_tbl)
        story.append(gap(0.4))

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 10  —  RECOMMENDATION & SANCTION TERMS   (new page)
        # ══════════════════════════════════════════════════════════════════════
        story.append(PageBreak())
        story.append(section_hdr(
            "SECTION 10   —   RECOMMENDATION & PROPOSED SANCTION TERMS"))
        story.append(gap(0.25))

        if pred:
            story.append(info_tbl([
                ("Borrower",               result.company_name),
                ("Facility Type",
                 getattr(result, "loan_purpose", "Working Capital")),
                ("Sanctioned Limit",
                 f"Rs. {pred.loan_limit_inr:,.0f}  "
                 f"(Rupees {pred.loan_limit_inr/100000:.2f} Lakhs only)"),
                ("Rate of Interest",
                 f"{pred.interest_rate:.2f}% p.a.  (Floating — linked to MCLR)"),
                ("Repayment Period",
                 "As per facility terms — refer Facility Letter"),
                ("Primary Security",
                 "Hypothecation of current assets — stock & book debts"),
                ("Collateral Security",
                 "As per application / approved valuation report"),
                ("Processing Fees",        "0.50% of sanctioned limit + applicable GST"),
                ("Annual Review Due",
                 now.replace(year=now.year + 1).strftime("%d-%m-%Y")),
            ]))
            story.append(gap(0.28))

        # decisive factor box
        if pred and pred.decisive_factor:
            df_tbl = Table(
                [[Paragraph(
                    f"<b>Decisive Factor:</b>  {pred.decisive_factor}", pJ
                )]],
                colWidths=[TW]
            )
            df_tbl.setStyle(TableStyle([
                ("BOX",           (0, 0), (-1, -1), 1.2, cNAV2),
                ("LEFTPADDING",   (0, 0), (-1, -1), 12),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
                ("TOPPADDING",    (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ("BACKGROUND",    (0, 0), (-1, -1), cLBL),
            ]))
            story.append(df_tbl)
            story.append(gap(0.28))

        # recommendation banner — solid decision colour
        banner = Table(
            [[Paragraph(
                f"<b>{dec_label}</b>",
                PS(fontSize=15, fontName="Helvetica-Bold",
                   alignment=TA_CENTER, textColor=cWHT)
            )]],
            colWidths=[TW]
        )
        banner.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), C(dec_bg)),
            ("TOPPADDING",    (0, 0), (-1, -1), 14),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ("BOX",           (0, 0), (-1, -1), 0, cWHT),
        ]))
        story.append(banner)
        story.append(gap(0.45))

        # signature / approval block
        story.append(Paragraph(
            "CREDIT COMMITTEE SIGN-OFF",
            PS(fontSize=9, fontName="Helvetica-Bold",
               textColor=C(NAV2), spaceAfter=6)
        ))
        cw4 = TW / 4
        sig_hdrs = ["Credit Analyst", "Credit Manager / AGM",
                    "Head of Credit",  "Chief Credit Officer"]
        sig_data = [
            [Paragraph(f"<b>{h}</b>", pWC) for h in sig_hdrs],
            [Paragraph("\n\n\n___________________________", pNC)] * 4,
            [Paragraph("Name:  _____________________", pS)] * 4,
            [Paragraph("Emp. ID:  __________________", pS)] * 4,
            [Paragraph("Date:  _____________________", pS)] * 4,
        ]
        sig_tbl = Table(sig_data, colWidths=[cw4]*4)
        sig_tbl.setStyle(TableStyle([
            ("BOX",           (0, 0), (-1, -1), 0.8, cNAV),
            ("INNERGRID",     (0, 0), (-1, -1), 0.4, cMGR),
            ("BACKGROUND",    (0, 0), (-1, 0),  cNAV),
            ("BACKGROUND",    (0, 1), (-1, -1), cTNT),
            ("FONTSIZE",      (0, 0), (-1, -1), 8.5),
            ("LEADING",       (0, 0), (-1, -1), 12),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ]))
        story.append(sig_tbl)
        story.append(gap(0.45))

        # disclaimer
        story.append(HRFlowable(width="100%", thickness=0.4, color=cMGR))
        story.append(gap(0.1))
        story.append(Paragraph(
            "DISCLAIMER: This Credit Appraisal Memorandum is generated by an AI-assisted "
            "scoring system (IntelliCredit v1.3) for internal credit evaluation purposes only. "
            "The AI model's output is supplementary to human judgment and does not constitute "
            "a binding credit decision. All sanctions are subject to applicable RBI guidelines, "
            "internal credit policy, and Credit Committee approval. This document is strictly "
            "confidential and must not be shared with the applicant or any external party.",
            PS(fontSize=7, fontName="Helvetica", leading=10.5,
               textColor=cDGR, alignment=TA_JUSTIFY)
        ))

        pdf_doc.build(story)
        print(f"PDF saved: {output_path}")
        return output_path

    # ══════════════════════════════════════════════════════════════════════════
    # DOCX
    # ══════════════════════════════════════════════════════════════════════════

    def generate_docx(self, result: CreditAppraisalResult, output_path: str) -> str:
        from docx import Document
        from docx.shared import Pt, Cm, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement

        doc = Document()
        for sec in doc.sections:
            sec.top_margin = Cm(2.2)
            sec.bottom_margin = Cm(2.2)
            sec.left_margin = Cm(2.5)
            sec.right_margin = Cm(2.5)

        pred = result.risk_prediction
        ds, cs, dec_bg, dec_lt, dec_label = self._pred_strings(pred)
        now = datetime.now()
        ref = (f"CAM/{now.year}/"
               f"{result.company_name[:4].upper()}/"
               f"{now.strftime('%m%d%H%M')}")

        def rgb(h):
            return RGBColor(int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16))

        def shade(cell, hex_c):
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            shd = OxmlElement("w:shd")
            shd.set(qn("w:fill"),  hex_c.lstrip("#"))
            shd.set(qn("w:val"),   "clear")
            shd.set(qn("w:color"), "auto")
            tcPr.append(shd)

        def cell_fmt(cell, text, bold=False, size=9,
                     color=None, align=WD_ALIGN_PARAGRAPH.LEFT):
            p = cell.paragraphs[0]
            p.clear()
            run = p.add_run(str(text))
            run.bold = bold
            run.font.size = Pt(size)
            run.font.name = "Arial"
            if color:
                run.font.color.rgb = rgb(color)
            p.alignment = align
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)

        def sec_hdr(txt):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(5)
            run = p.add_run(txt)
            run.bold = True
            run.font.size = Pt(11)
            run.font.name = "Arial"
            run.font.color.rgb = rgb(NAV2)
            pPr = p._p.get_or_add_pPr()
            pBdr = OxmlElement("w:pBdr")
            lft = OxmlElement("w:left")
            lft.set(qn("w:val"),   "single")
            lft.set(qn("w:sz"),    "18")
            lft.set(qn("w:space"), "6")
            lft.set(qn("w:color"), NAV.lstrip("#"))
            pBdr.append(lft)
            pPr.append(pBdr)

        def info_tbl_d(rows, w0=4.5):
            t = doc.add_table(rows=0, cols=2)
            t.style = "Table Grid"
            for lbl, val in rows:
                row = t.add_row()
                c0, c1 = row.cells[0], row.cells[1]
                c0.width = Cm(w0)
                c1.width = Cm(13.5 - w0)
                shade(c0, LBLU)
                cell_fmt(c0, lbl, bold=True)
                cell_fmt(c1, val)
            return t

        # ── cover ──────────────────────────────────────────────────────────────
        h1 = doc.add_heading(CAM_BANK_NAME.upper(), level=1)
        h1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if h1.runs:
            h1.runs[0].font.color.rgb = rgb(NAV)
            h1.runs[0].font.size = Pt(14)
            h1.runs[0].font.name = "Arial"

        p_sub = doc.add_paragraph("Credit Risk Management Division")
        p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p_sub.runs:
            r.font.size = Pt(9)
            r.font.color.rgb = rgb(DGRY)
            r.font.name = "Arial"

        doc.add_paragraph()
        p_title = doc.add_paragraph("CREDIT APPRAISAL MEMORANDUM")
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p_title.runs:
            r.bold = True
            r.font.size = Pt(18)
            r.font.color.rgb = rgb(NAV)
            r.font.name = "Arial"
        doc.add_paragraph()

        # cover detail table
        cov_d = [
            ("Applicant / Borrower", result.company_name),
            ("Reference No.",        ref),
            ("AI Decision",          dec_label),
            ("Risk Category",        cs),
            ("Loan Limit",
             f"Rs. {pred.loan_limit_inr:,.0f} ({pred.loan_limit_inr/100000:.2f} Lakhs)"
             if pred else "N/A"),
            ("Interest Rate",
             f"{pred.interest_rate:.2f}% p.a." if pred else "N/A"),
            ("Report Date",          now.strftime("%d %B %Y")),
            ("Prepared By",          CAM_AUTHOR),
            ("Classification",       "STRICTLY CONFIDENTIAL"),
        ]
        ct = info_tbl_d(cov_d, w0=5.0)
        # colour decision row (row index 2)
        shade(ct.rows[2].cells[1], dec_lt)
        cell_fmt(ct.rows[2].cells[1], dec_label, bold=True, color=dec_bg)

        doc.add_paragraph()

        # approval block
        ap = doc.add_table(rows=4, cols=3)
        ap.style = "Table Grid"
        for ci, h_ in enumerate(["Credit Analyst", "Credit Manager / AGM", "Chief Credit Officer"]):
            shade(ap.rows[0].cells[ci], NAV)
            cell_fmt(ap.rows[0].cells[ci], h_, bold=True, color=WHT,
                     align=WD_ALIGN_PARAGRAPH.CENTER)
        for ri, lbl in enumerate(["Name", "Signature\n\n", "Date"], 1):
            for ci in range(3):
                cell_fmt(ap.rows[ri].cells[ci],
                         lbl if ci == 0 else "",
                         bold=(ci == 0))

        doc.add_page_break()

        # ── sections ────────────────────────────────────────────────────────────

        # S1 Executive Summary
        sec_hdr("SECTION 1 — EXECUTIVE SUMMARY")
        info_tbl_d([
            ("Company / Borrower",  result.company_name),
            ("GSTIN",
             result.gst_data.gstin if result.gst_data else "N/A"),
            ("Reference No.",       ref),
            ("AI Decision",         dec_label),
            ("Risk Category",       cs),
            ("Risk Score",
             f"{pred.risk_score:.3f} / 1.000" if pred else "N/A"),
            ("Loan Limit",
             f"Rs. {pred.loan_limit_inr:,.0f} ({pred.loan_limit_inr/100000:.2f} Lakhs)"
             if pred else "N/A"),
            ("Interest Rate",
             f"{pred.interest_rate:.2f}% p.a." if pred else "N/A"),
        ])
        doc.add_paragraph()

        # S2 Financial Analysis
        sec_hdr("SECTION 2 — FINANCIAL ANALYSIS")
        dr = self._derived_rows(result)
        if dr:
            info_tbl_d(dr)
        else:
            doc.add_paragraph("Financial ratios not available.")
        doc.add_paragraph()

        # S3 Five Cs
        sec_hdr("SECTION 3 — FIVE Cs CREDIT ANALYSIS")
        if result.five_cs:
            obj5 = result.five_cs
            t5 = doc.add_table(rows=1, cols=3)
            t5.style = "Table Grid"
            for ci, h_ in enumerate(["Parameter", "Score", "Assessment Summary"]):
                shade(t5.rows[0].cells[ci], NAV)
                cell_fmt(t5.rows[0].cells[ci], h_, bold=True, color=WHT)
            for lbl, o in [
                ("Character",  obj5.character), ("Capacity",   obj5.capacity),
                ("Capital",    obj5.capital),   ("Collateral", obj5.collateral),
                ("Conditions", obj5.conditions),
            ]:
                row = t5.add_row().cells
                cell_fmt(row[0], lbl, bold=True)
                cell_fmt(row[1], f"{o.score}/10",
                         align=WD_ALIGN_PARAGRAPH.CENTER)
                cell_fmt(row[2], o.summary)
            ov = t5.add_row().cells
            for c in ov:
                shade(c, LBLU)
            cell_fmt(ov[0], "OVERALL",               bold=True)
            cell_fmt(ov[1], f"{obj5.overall_score}/10",
                     bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
            cell_fmt(ov[2], "Weighted average",       bold=True)
        doc.add_paragraph()

        # S4 SHAP
        sec_hdr("SECTION 4 — AI RISK DRIVERS (SHAP)")
        if pred and pred.top_shap_factors:
            t4 = doc.add_table(rows=1, cols=3)
            t4.style = "Table Grid"
            for ci, h_ in enumerate(["Factor", "SHAP Impact", "Direction"]):
                shade(t4.rows[0].cells[ci], NAV)
                cell_fmt(t4.rows[0].cells[ci], h_, bold=True, color=WHT)
            for f in pred.top_shap_factors:
                row = t4.add_row().cells
                cell_fmt(row[0], f.display_name)
                cell_fmt(row[1], f"{f.shap_value:.4f}",
                         align=WD_ALIGN_PARAGRAPH.CENTER)
                cell_fmt(row[2], f.direction)
        doc.add_paragraph()

        # S5 Early Warnings
        sec_hdr("SECTION 5 — EARLY WARNING SIGNALS")
        if pred and pred.early_warning_signals:
            t5w = doc.add_table(rows=1, cols=2)
            t5w.style = "Table Grid"
            for ci, h_ in enumerate(["Signal", "Monitor Frequency"]):
                shade(t5w.rows[0].cells[ci], AMB)
                cell_fmt(t5w.rows[0].cells[ci], h_, bold=True, color=WHT)
            freqs = ["Monthly", "Quarterly",
                     "Quarterly", "At Renewal", "Annually"]
            for i, w in enumerate(pred.early_warning_signals):
                row = t5w.add_row().cells
                cell_fmt(row[0], w)
                cell_fmt(row[1], freqs[i] if i < len(freqs) else "Quarterly",
                         align=WD_ALIGN_PARAGRAPH.CENTER)
        doc.add_paragraph()

        # S6 Reasoning
        sec_hdr("SECTION 6 — AI REASONING CHAIN")
        if result.reasoning_chain:
            key_starts = ("DECISION:", "LIMIT:", "RATE:",
                          "REASONING", "DECISIVE", "LOAN")
            for line in result.reasoning_chain.split("\n"):
                line = line.strip()
                if not line:
                    continue
                is_key = any(line.upper().startswith(k) for k in key_starts)
                p2 = doc.add_paragraph(line)
                p2.paragraph_format.space_after = Pt(2)
                for r2 in p2.runs:
                    r2.font.size = Pt(9)
                    r2.font.name = "Arial"
                    r2.bold = is_key
        doc.add_paragraph()

        # S7 Recommendation
        sec_hdr("SECTION 7 — RECOMMENDATION")
        if pred:
            p_rec = doc.add_paragraph()
            r_rec = p_rec.add_run(f"DECISION: {dec_label}")
            r_rec.bold = True
            r_rec.font.size = Pt(13)
            r_rec.font.name = "Arial"
            r_rec.font.color.rgb = rgb(dec_bg)
            if pred.decisive_factor:
                p_df = doc.add_paragraph(
                    f"Decisive Factor: {pred.decisive_factor}")
                for r2 in p_df.runs:
                    r2.font.size = Pt(9)
                    r2.font.name = "Arial"

        # footer
        footer = doc.sections[0].footer
        fp = footer.paragraphs[0]
        fp.text = (f"Ref: {ref}  |  {CAM_BANK_NAME}  |  "
                   f"STRICTLY CONFIDENTIAL  |  "
                   f"{now.strftime('%d %b %Y')}  |  {CAM_AUTHOR}")
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if fp.runs:
            fp.runs[0].font.size = Pt(7.5)
            fp.runs[0].font.color.rgb = rgb(DGRY)
            fp.runs[0].font.name = "Arial"

        doc.save(output_path)
        print(f"DOCX saved: {output_path}")
        return output_path
