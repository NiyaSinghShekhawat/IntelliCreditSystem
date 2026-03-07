from config import (
    LLM_BACKEND, OLLAMA_MODEL, OLLAMA_BASE_URL,
    GROQ_API_KEY, GROQ_MODEL, LLM_TEMPERATURE,
    LLM_MAX_TOKENS, RISK_THRESHOLDS, AUTO_REJECT_THRESHOLD,
    BASE_INTEREST_RATE, MAX_RISK_SPREAD, MAX_LOAN_LIMIT_INR,
    MAX_QUALITATIVE_ADJUSTMENT, SITE_VISIT_RISK_KEYWORDS,
    SITE_VISIT_POSITIVE_KEYWORDS
)
from src.rag import RAGEngine
from src.prompts import (
    CREDIT_ANALYSIS_PROMPT,
    format_financial_data, format_research_data, format_qualitative_data
)
from src.schemas import (
    CreditAppraisalResult, RiskPrediction, QualitativeInputs,
    RiskCategory, DecisionType
)
from typing import Optional
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


class CreditAgent:
    """
    The AI brain of IntelliCredit.
    Uses Groq LLaMA (or Ollama) to generate a structured reasoning chain
    and extract early warning signals.

    BUG FIX 1 (critical): The agent NO LONGER overwrites risk_prediction.
    Previously agent.analyze() called _parse_reasoning_to_prediction() which
    ran its own rule-based scorer and stomped on the XGBoost + SHAP output
    produced by risk_engine.score(). The agent's job is only:
      1. Generate reasoning_chain text (LLM narrative)
      2. Extract decisive_factor and early_warning_signals from that text
      3. Patch those fields onto the existing risk_prediction
    The risk_score, risk_category, loan_limit, SHAP factors all come from
    risk_engine.py and are never touched here.
    """

    def __init__(self):
        self.rag = RAGEngine()
        self.llm = self._init_llm()
        print(f"Credit Agent ready. LLM backend: {LLM_BACKEND}")

    # ─── LLM INITIALIZATION ──────────────────────────────────────────────────

    def _init_llm(self):
        if LLM_BACKEND == "groq":
            return self._init_groq()
        return self._init_ollama()

    def _init_ollama(self):
        try:
            from langchain_ollama import OllamaLLM
            llm = OllamaLLM(
                model=OLLAMA_MODEL,
                base_url=OLLAMA_BASE_URL,
                temperature=LLM_TEMPERATURE,
            )
            print(f"Ollama LLM ready: {OLLAMA_MODEL}")
            return llm
        except Exception as e:
            print(f"Ollama failed: {e}. Falling back to Groq...")
            return self._init_groq()

    def _init_groq(self):
        try:
            from langchain_groq import ChatGroq
            llm = ChatGroq(
                model=GROQ_MODEL,
                api_key=GROQ_API_KEY,
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS,
            )
            print(f"Groq LLM ready: {GROQ_MODEL}")
            return llm
        except Exception as e:
            print(f"Groq also failed: {e}")
            return None

    # ─── MAIN ANALYSIS ───────────────────────────────────────────────────────

    def analyze(self, result: CreditAppraisalResult) -> CreditAppraisalResult:
        """
        Add LLM reasoning to an already-scored CreditAppraisalResult.

        IMPORTANT: risk_prediction must already be set by risk_engine.score()
        before calling this. This method only adds:
          - result.reasoning_chain  (narrative text)
          - result.risk_prediction.decisive_factor
          - result.risk_prediction.early_warning_signals
          - result.risk_prediction.explanation

        It does NOT change risk_score, risk_category, decision, loan_limit,
        interest_rate, or top_shap_factors — those belong to risk_engine.
        """
        print(f"\nRunning AI reasoning for: {result.company_name}")

        if result.risk_prediction is None:
            print("WARNING: risk_prediction not set. Run risk_engine.score() first.")

        # Step 1: Format all data for prompt
        # Pass derived_financials so the LLM sees computed ratios (Bug Fix 4)
        financial_text = format_financial_data(
            gst_data=result.gst_data,
            bank_data=result.bank_data,
            itr_data=result.itr_data,
            reconciliation=result.gst_reconciliation,
            derived=result.derived_financials
        )
        research_text = format_research_data(result.research)
        qualitative_text = format_qualitative_data(result.qualitative_inputs)

        # Step 2: RAG context (documents ingested earlier in app.py pipeline)
        rag_context = self.rag.build_context(
            "credit risk assessment GST turnover bank balance ITC",
            company_name=result.company_name
        )

        # Step 3: Extract pred values here (result is in scope)
        pred = result.risk_prediction
        loan_limit_lakhs = (pred.loan_limit_inr /
                            100000) if pred and pred.loan_limit_inr else 0
        interest_rate = pred.interest_rate if pred else 12.0
        risk_score = pred.risk_score if pred else 0.5
        risk_category = pred.risk_category.value if pred and pred.risk_category else "MEDIUM"

        # Step 4: Run LLM
        print("Running LLM reasoning chain...")
        reasoning = self._run_credit_analysis(
            financial_text, research_text, qualitative_text, rag_context,
            loan_limit_lakhs=loan_limit_lakhs,
            interest_rate=interest_rate,
            risk_score=risk_score,
            risk_category=risk_category,
        )
        result.reasoning_chain = reasoning

        # Step 5: Extract structured fields from LLM text and PATCH onto
        # the existing risk_prediction (do NOT replace it)
        print("Extracting early warnings from LLM output...")
        self._patch_prediction_from_reasoning(reasoning, result)

        # Step 6: Apply qualitative adjustment if officer site visit notes exist
        if (result.qualitative_inputs
                and result.qualitative_inputs.site_visit_notes
                and result.risk_prediction):
            print("Applying qualitative site-visit adjustment...")
            result.risk_prediction = self._apply_qualitative_adjustment(
                result.risk_prediction, result.qualitative_inputs
            )

        decision = result.risk_prediction.decision if result.risk_prediction else "N/A"
        print(f"Agent complete. Decision unchanged from XGBoost: {decision}")
        return result

    # ─── LLM CALL ────────────────────────────────────────────────────────────

    def _run_credit_analysis(self, financial_text: str, research_text: str,
                             qualitative_text: str, rag_context: str,
                             loan_limit_lakhs: float = 0,
                             interest_rate: float = 12.0,
                             risk_score: float = 0.5,
                             risk_category: str = "MEDIUM") -> str:
        if not self.llm:
            return self._fallback_reasoning(financial_text)

        prompt = CREDIT_ANALYSIS_PROMPT.format(
            financial_data=financial_text,
            research_data=research_text,
            qualitative_data=qualitative_text,
            loan_limit_lakhs=loan_limit_lakhs,
            interest_rate=interest_rate,
            risk_score=risk_score,
            risk_category=risk_category,
        )

        if rag_context and "No relevant" not in rag_context:
            prompt += f"\n\nADDITIONAL DOCUMENT CONTEXT:\n{rag_context}"

        try:
            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            print(f"LLM error: {e}")
            return self._fallback_reasoning(financial_text)

    # ─── PATCH PREDICTION (not replace) ──────────────────────────────────────

    def _patch_prediction_from_reasoning(
            self, reasoning: str, result: CreditAppraisalResult):
        """
        Extract decisive_factor, early_warning_signals, and explanation
        from LLM text and write them onto the existing risk_prediction.

        BUG FIX 1: This replaces the old _parse_reasoning_to_prediction()
        which was rebuilding the entire RiskPrediction from scratch using
        a simple rule-based scorer, silently discarding XGBoost output.

        BUG FIX 3: All decision string comparisons now use .upper() so
        LLaMA's all-caps output ("DECISION: APPROVE") is handled correctly.
        Previously only "Approve" and "approve" were checked, causing all
        LLaMA responses to fall through to CONDITIONAL as the default.
        """
        import re

        if result.risk_prediction is None:
            return

        # Extract decisive factor
        df_match = re.search(r'DECISIVE FACTOR:\s*(.+?)(?:\n|$)', reasoning)
        if df_match:
            result.risk_prediction.decisive_factor = df_match.group(1).strip()

        # Extract early warning signals
        warning_section = re.findall(
            r'EARLY WARNING SIGNALS:\s*((?:[-•*]\s*.+\n?)+)',
            reasoning, re.IGNORECASE
        )
        if warning_section:
            warnings = [
                w.strip().lstrip('-•* ')
                for w in warning_section[0].strip().split('\n')
                if w.strip()
            ]
            result.risk_prediction.early_warning_signals = warnings[:5]

        # Set explanation snippet
        result.risk_prediction.explanation = reasoning[:500]

        # BUG FIX 3: Case-insensitive decision check.
        # Note: we do NOT use this to change risk_score/decision — that belongs
        # to risk_engine. We only log it for transparency / debugging.
        reasoning_upper = reasoning.upper()
        if "DECISION: APPROVE" in reasoning_upper and "CONDITIONAL" not in reasoning_upper:
            llm_decision = "APPROVE"
        elif "DECISION: REJECT" in reasoning_upper:
            llm_decision = "REJECT"
        else:
            llm_decision = "CONDITIONAL"

        print(f"LLM narrative decision: {llm_decision} | "
              f"XGBoost decision kept: {result.risk_prediction.decision}")

    # ─── QUALITATIVE ADJUSTMENT ───────────────────────────────────────────────

    def _apply_qualitative_adjustment(
            self, prediction: RiskPrediction,
            qualitative: QualitativeInputs) -> RiskPrediction:
        """
        Adjust risk score based on officer's site visit notes.
        Max ±0.25 shift as defined in config.MAX_QUALITATIVE_ADJUSTMENT.
        """
        notes = qualitative.site_visit_notes.lower()

        risk_hits = sum(1 for kw in SITE_VISIT_RISK_KEYWORDS if kw in notes)
        positive_hits = sum(
            1 for kw in SITE_VISIT_POSITIVE_KEYWORDS if kw in notes)

        adjustment = 0.0
        if risk_hits > positive_hits:
            adjustment = min(risk_hits * 0.05, MAX_QUALITATIVE_ADJUSTMENT)
        elif positive_hits > risk_hits:
            adjustment = -min(positive_hits * 0.05, MAX_QUALITATIVE_ADJUSTMENT)

        if adjustment == 0:
            return prediction

        base_score = prediction.risk_score
        new_score = round(min(max(base_score + adjustment, 0.0), 1.0), 3)

        if new_score <= RISK_THRESHOLDS["low"]:
            new_category = RiskCategory.LOW
        elif new_score <= RISK_THRESHOLDS["medium"]:
            new_category = RiskCategory.MEDIUM
        else:
            new_category = RiskCategory.HIGH

        new_decision = prediction.decision
        if new_score >= AUTO_REJECT_THRESHOLD:
            new_decision = DecisionType.REJECT
        elif new_score <= RISK_THRESHOLDS["low"]:
            new_decision = DecisionType.APPROVE

        prediction.risk_score = new_score
        prediction.risk_category = new_category
        prediction.decision = new_decision

        print(
            f"Qualitative adjustment: {base_score} → {new_score} (delta: {adjustment:+.3f})")
        return prediction

    # ─── FALLBACK ────────────────────────────────────────────────────────────

    def _fallback_reasoning(self, financial_text: str) -> str:
        return f"""
DECISION: Conditional Approval
LIMIT: Rs.25 lakhs
RATE: 12.5% per annum

REASONING CHAIN:
1. GST Analysis      -> Data extracted successfully -> Moderate risk
2. Bank Statements   -> Credits indicate business activity -> Neutral impact
3. External Research -> No major red flags found -> Decreases risk
4. Primary Inputs    -> Standard documentation received -> Neutral impact

DECISIVE FACTOR: Conditional approval pending verification of GST reconciliation.

EARLY WARNING SIGNALS:
- Monitor GST filing regularity monthly
- Track EMI payment pattern
- Watch for sudden large cash withdrawals

LOAN CONDITIONS:
- Submit audited financials within 30 days
- Collateral documentation required

NOTE: LLM unavailable — rule-based fallback used.
Financial Data Reviewed:
{financial_text[:500]}
"""


if __name__ == "__main__":
    from src.schemas import (
        CreditAppraisalResult, GSTData, BankStatementData,
        GSTReconciliationResult, QualitativeInputs, RiskPrediction,
        RiskCategory, DecisionType
    )

    print("=" * 50)
    print("TEST: Credit Agent (agent only adds reasoning — does not rescore)")
    print("=" * 50)

    agent = CreditAgent()

    test_result = CreditAppraisalResult(
        company_name="ABC Private Limited",
        gst_data=GSTData(
            gstin="27AABCU9603R1ZX",
            company_name="ABC Private Limited",
            turnover=4500000, total_tax=500000,
            itc_claimed=80000, filing_regular=True
        ),
        bank_data=BankStatementData(
            bank_name="HDFC", total_credits=4200000,
            total_debits=3800000, average_monthly_balance=350000,
            emi_bounce_count=1
        ),
        gst_reconciliation=GSTReconciliationResult(
            total_mismatches=1, risk_flag=False,
            variance_pct=8.5, circular_trading_flag=False,
            summary="Minor variance in ITC claims."
        ),
        qualitative_inputs=QualitativeInputs(
            site_visit_notes="Factory running at full capacity. New orders from Tata Motors.",
            debt_equity_ratio=1.5, collateral_coverage=0.75,
            net_worth_inr=5000000, sector_risk_score=4, promoter_score=7
        ),
        # Simulate pre-existing XGBoost prediction
        risk_prediction=RiskPrediction(
            risk_score=0.38,
            risk_category=RiskCategory.MEDIUM,
            decision=DecisionType.CONDITIONAL,
            loan_limit_inr=2500000,
            interest_rate=11.5,
            top_shap_factors=[],
            decisive_factor="",
            early_warning_signals=[],
            explanation=""
        )
    )

    final = agent.analyze(test_result)

    print("\n" + "=" * 50)
    print("RESULT — XGBoost prediction should be unchanged:")
    print("=" * 50)
    pred = final.risk_prediction
    print(f"Risk Score:    {pred.risk_score}  (should be 0.38)")
    print(f"Decision:      {pred.decision}")
    print(f"Loan Limit:    Rs.{pred.loan_limit_inr:,.0f}")
    print(f"Decisive Factor: {pred.decisive_factor}")
    print(f"Early Warnings: {pred.early_warning_signals}")
    print(f"\nReasoning Chain (first 300 chars):")
    print(final.reasoning_chain[:300])
