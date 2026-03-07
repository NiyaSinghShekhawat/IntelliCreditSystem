from config import (
    RISK_THRESHOLDS, AUTO_REJECT_THRESHOLD,
    BASE_INTEREST_RATE, MAX_RISK_SPREAD,
    MAX_LOAN_LIMIT_INR, FIVE_CS_WEIGHTS
)
from src.schemas import (
    CreditAppraisalResult, RiskPrediction,
    RiskCategory, DecisionType, SHAPFactor,
    DerivedFinancials, QualitativeInputs
)
from typing import List, Optional
import numpy as np
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


class RiskEngine:
    """
    XGBoost-based risk scoring engine with SHAP explanations.
    Falls back to weighted rule-based scoring if no training data.
    """

    FEATURE_NAMES = [
        "gst_filing_regularity",
        "revenue_growth_rate",
        "gstr_mismatch_pct",
        "avg_monthly_balance",
        "emi_bounce_count",
        "cash_flow_volatility",
        "news_risk_score",
        "litigation_flag",
        "debt_equity_ratio",
        "collateral_coverage",
        "promoter_score",
        "sector_risk_score"
    ]

    FEATURE_DISPLAY_NAMES = {
        "gst_filing_regularity":  "GST Filing Regularity",
        "revenue_growth_rate":    "Revenue Growth Rate",
        "gstr_mismatch_pct":      "GSTR 2A vs 3B Variance",
        "avg_monthly_balance":    "Average Monthly Balance",
        "emi_bounce_count":       "EMI Bounce Count",
        "cash_flow_volatility":   "Cash Flow Volatility",
        "news_risk_score":        "External News Risk",
        "litigation_flag":        "Active Litigation",
        "debt_equity_ratio":      "Debt / Equity Ratio",
        "collateral_coverage":    "Collateral Coverage",
        "promoter_score":         "Promoter Integrity Score",
        "sector_risk_score":      "Sector Risk Index"
    }

    FEATURE_RISK_DIRECTION = {
        "gst_filing_regularity":  False,
        "revenue_growth_rate":    False,
        "gstr_mismatch_pct":      True,
        "avg_monthly_balance":    False,
        "emi_bounce_count":       True,
        "cash_flow_volatility":   True,
        "news_risk_score":        True,
        "litigation_flag":        True,
        "debt_equity_ratio":      True,
        "collateral_coverage":    False,
        "promoter_score":         False,
        "sector_risk_score":      True
    }

    def __init__(self):
        self.model = None
        self._try_load_xgboost()

    def _try_load_xgboost(self):
        try:
            import xgboost as xgb
            self.model = self._train_synthetic_model()
            print("XGBoost risk engine ready.")
        except Exception as e:
            print(f"XGBoost unavailable: {e}. Using rule-based scoring.")
            self.model = None

    # ─── DOCUMENT DERIVATION ─────────────────────────────────────────────────

    def derive_from_documents(
            self, result: CreditAppraisalResult) -> DerivedFinancials:
        """
        Auto-compute financial ratios from uploaded documents.
        Called after extraction, before the officer input screen.
        Returns a DerivedFinancials object — also stored on result.derived_financials
        so app.py can pre-fill the UI form.

        Derivation priority: ITR > Bank Statement > GST
        Only computes a ratio when source data is present and non-zero.
        """
        d = DerivedFinancials()
        notes = []
        derived_count = 0
        total_fields = 10  # total computable fields

        itr = result.itr_data
        bank = result.bank_data
        gst = result.gst_data

        # ── From ITR ─────────────────────────────────────────────────────────

        if itr:
            # Net worth — direct field
            if itr.net_worth > 0:
                d.net_worth_inr = itr.net_worth
                derived_count += 1
            else:
                notes.append(
                    "Net worth not found in ITR — officer must enter manually.")

            # D/E ratio — use broken-out debt fields first, fall back to
            # total_liabilities minus estimated non-debt items
            total_debt = itr.long_term_debt + itr.short_term_debt
            if total_debt > 0 and itr.net_worth > 0:
                d.debt_equity_ratio = round(total_debt / itr.net_worth, 2)
                d.total_debt_inr = total_debt
                derived_count += 1
            elif itr.total_liabilities > 0 and itr.net_worth > 0:
                # Fallback: use total_liabilities as proxy for debt
                # This overstates D/E slightly (includes trade payables)
                d.debt_equity_ratio = round(
                    itr.total_liabilities / itr.net_worth, 2
                )
                d.total_debt_inr = itr.total_liabilities
                notes.append(
                    "D/E ratio computed from total liabilities (borrowings not "
                    "separately extracted) — may be slightly overstated."
                )
                derived_count += 1
            else:
                notes.append(
                    "D/E ratio could not be derived — debt or net worth missing.")

            # Net profit margin
            revenue = itr.revenue if itr.revenue > 0 else itr.gross_income
            if revenue > 0 and itr.net_income > 0:
                d.net_profit_margin = round(itr.net_income / revenue * 100, 2)
                derived_count += 1

            # DSCR — EBITDA / (interest + estimated principal)
            # Principal estimated as long_term_debt / 7 (avg 7-year tenor)
            if itr.ebitda > 0 and itr.interest_expense > 0:
                est_principal = itr.long_term_debt / 7 if itr.long_term_debt > 0 else 0
                debt_service = itr.interest_expense + est_principal
                if debt_service > 0:
                    d.dscr = round(itr.ebitda / debt_service, 2)
                    derived_count += 1
            else:
                # Rough DSCR from net income if EBITDA not available
                if itr.net_income > 0 and itr.interest_expense > 0:
                    d.dscr = round(
                        (itr.net_income + itr.interest_expense) /
                        itr.interest_expense, 2
                    )
                    notes.append(
                        "DSCR estimated from net income (EBITDA not extracted).")
                    derived_count += 1

        # ── From Bank Statement ───────────────────────────────────────────────

        if bank:
            if bank.average_monthly_balance > 0:
                d.avg_monthly_balance_inr = bank.average_monthly_balance
                derived_count += 1
            elif bank.monthly_balances:
                d.avg_monthly_balance_inr = round(
                    sum(bank.monthly_balances) / len(bank.monthly_balances), 2
                )
                derived_count += 1
            else:
                notes.append(
                    "Average monthly balance could not be computed from bank statement.")

            if bank.monthly_credits:
                d.monthly_credit_avg_inr = round(
                    sum(bank.monthly_credits) / len(bank.monthly_credits), 2
                )
                derived_count += 1
            elif bank.total_credits > 0:
                # Assume 12-month statement if no monthly breakdown
                d.monthly_credit_avg_inr = round(bank.total_credits / 12, 2)
                notes.append(
                    "Monthly credit avg estimated from total (12-month assumed).")
                derived_count += 1

            if bank.total_credits > 0 and bank.total_debits > 0:
                d.credit_utilisation_pct = round(
                    bank.total_debits / bank.total_credits * 100, 1
                )
                derived_count += 1

        # ── From GST ─────────────────────────────────────────────────────────

        if gst:
            if gst.turnover > 0:
                d.gst_turnover_inr = gst.turnover
                derived_count += 1
            if gst.itc_claimed > 0:
                d.itc_claimed_inr = gst.itc_claimed
            if gst.turnover > 0 and gst.total_tax > 0:
                d.effective_tax_rate_pct = round(
                    gst.total_tax / gst.turnover * 100, 2
                )

        # ── Data completeness score ───────────────────────────────────────────
        d.data_completeness_pct = round(derived_count / total_fields * 100, 1)
        d.derivation_notes = notes

        # Track which fields were successfully auto-derived
        d.auto_filled_fields = [
            f for f in [
                "debt_equity_ratio", "net_worth_inr", "total_debt_inr",
                "dscr", "net_profit_margin", "avg_monthly_balance_inr",
                "monthly_credit_avg_inr", "credit_utilisation_pct",
                "gst_turnover_inr", "itc_claimed_inr", "effective_tax_rate_pct",
            ]
            if getattr(d, f, None) is not None
        ]

        if d.data_completeness_pct < 50:
            d.derivation_notes.insert(
                0,
                f"Only {d.data_completeness_pct}% of financial ratios could be "
                f"auto-derived. Please ensure ITR and Bank Statement are uploaded."
            )

        return d

    def build_qualitative_inputs(
            self,
            derived: Optional[DerivedFinancials],
            officer_overrides: Optional[QualitativeInputs] = None
    ) -> QualitativeInputs:
        """
        Build QualitativeInputs for the scoring pipeline by merging:
          1. Auto-derived values from documents (base layer)
          2. Officer overrides from the UI form (top layer — always wins)

        If officer_overrides is None, returns defaults with auto-filled fields.
        The auto_filled_fields list tells the UI which fields to show with a
        lock/pencil icon so the officer knows they came from documents.

        Call flow in app.py:
            derived = engine.derive_from_documents(result)
            result.derived_financials = derived
            # Show UI form pre-filled with derived values
            # Officer fills in promoter_score, collateral_coverage, site_visit
            # Officer can optionally override D/E ratio and net_worth
            q = engine.build_qualitative_inputs(derived, officer_form_values)
            result.qualitative_inputs = q
        """
        q = officer_overrides or QualitativeInputs()
        auto_filled = []

        if derived:
            # D/E ratio — use derived unless officer explicitly changed it
            if (derived.debt_equity_ratio is not None and
                    q.debt_equity_ratio == 1.5):  # 1.5 is the schema default
                q.debt_equity_ratio = derived.debt_equity_ratio
                auto_filled.append("debt_equity_ratio")

            # Net worth
            if derived.net_worth_inr is not None and q.net_worth_inr == 0.0:
                q.net_worth_inr = derived.net_worth_inr
                auto_filled.append("net_worth_inr")

        q.auto_filled_fields = auto_filled
        return q

    # ─── MAIN SCORING METHOD ─────────────────────────────────────────────────

    def score(self, result: CreditAppraisalResult,
              requested_amount_inr: float = 0.0) -> RiskPrediction:
        """
        Main entry point. Extract features from result,
        score with XGBoost + SHAP, return RiskPrediction.

        Expects result.derived_financials to be populated before calling —
        run derive_from_documents() first if documents were uploaded.

        Args:
            result: Full credit appraisal result with extracted documents.
            requested_amount_inr: Loan amount entered by credit officer (rupees).
                If provided, this becomes the base for loan limit calculation.
        """
        features = self._extract_features(result)
        feature_array = np.array([list(features.values())])

        if self.model:
            risk_score, shap_values = self._xgboost_score(feature_array)
        else:
            risk_score, shap_values = self._rule_based_score(features)

        shap_factors = self._build_shap_factors(
            features, shap_values, risk_score)
        risk_category, decision = self._categorize(risk_score)
        loan_limit = self._calculate_loan_limit(
            result, risk_score, requested_amount_inr)
        interest_rate = round(
            BASE_INTEREST_RATE + (risk_score * MAX_RISK_SPREAD), 2
        )
        warnings = self._generate_warnings(features, result)

        return RiskPrediction(
            risk_score=round(risk_score, 3),
            risk_category=risk_category,
            decision=decision,
            loan_limit_inr=loan_limit,
            interest_rate=interest_rate,
            top_shap_factors=shap_factors,
            early_warning_signals=warnings,
            explanation=self._build_explanation(
                features, shap_factors, risk_score)
        )

    # ─── FEATURE EXTRACTION ──────────────────────────────────────────────────

    def _extract_features(self, result: CreditAppraisalResult) -> dict:
        """
        Extract normalized features from CreditAppraisalResult.

        Priority order for each feature:
          1. qualitative_inputs (officer input or auto-filled from documents)
          2. derived_financials (fallback when qualitative_inputs is absent)
          3. raw document data (final fallback)
          4. 0.0 default (if nothing available)
        """
        features = {name: 0.0 for name in self.FEATURE_NAMES}

        # Shorthand refs
        q = result.qualitative_inputs
        d = result.derived_financials

        # ── GST features ─────────────────────────────────────────────────────
        if result.gst_data:
            features["gst_filing_regularity"] = (
                1.0 if result.gst_data.filing_regular else 0.0
            )

        if result.gst_reconciliation:
            variance = result.gst_reconciliation.variance_pct
            features["gstr_mismatch_pct"] = min(variance / 100, 1.0)

        # ── Bank features ─────────────────────────────────────────────────────
        if result.bank_data:
            credits = result.bank_data.total_credits
            debits = result.bank_data.total_debits

            # Average balance: prefer derived (already validated), then raw
            avg_bal = 0.0
            if d and d.avg_monthly_balance_inr:
                avg_bal = d.avg_monthly_balance_inr
            elif result.bank_data.average_monthly_balance > 0:
                avg_bal = result.bank_data.average_monthly_balance
            features["avg_monthly_balance"] = min(avg_bal / 10_000_000, 1.0)

            if credits > 0:
                features["cash_flow_volatility"] = min(debits / credits, 1.0)

            features["emi_bounce_count"] = min(
                result.bank_data.emi_bounce_count / 10, 1.0
            )

        # ── Research features ─────────────────────────────────────────────────
        if result.research:
            features["news_risk_score"] = result.research.news_risk_score / 10
            features["litigation_flag"] = (
                1.0 if result.research.litigation_found else 0.0
            )

        # ── D/E ratio ────────────────────────────────────────────────────────
        # Priority: qualitative_inputs → derived_financials → 1.5 default
        de_ratio = 1.5  # neutral default
        if q and q.debt_equity_ratio != 1.5:
            # Officer explicitly set a value (not the default)
            de_ratio = q.debt_equity_ratio
        elif q and "debt_equity_ratio" in q.auto_filled_fields:
            # Auto-filled from documents
            de_ratio = q.debt_equity_ratio
        elif d and d.debt_equity_ratio is not None:
            # Derived available but not yet copied to qualitative_inputs
            de_ratio = d.debt_equity_ratio
        features["debt_equity_ratio"] = min(de_ratio / 4, 1.0)

        # ── Net worth (used in loan limit, not a direct feature but stored) ──
        # Pulled into qualitative_inputs in build_qualitative_inputs()

        # ── Collateral coverage ───────────────────────────────────────────────
        # Always officer input — cannot be derived from documents
        if q:
            features["collateral_coverage"] = min(q.collateral_coverage, 1.0)

        # ── Promoter score ────────────────────────────────────────────────────
        if q:
            features["promoter_score"] = q.promoter_score / 10

        # ── Sector risk ───────────────────────────────────────────────────────
        if q:
            features["sector_risk_score"] = q.sector_risk_score / 10

        # ── Revenue growth rate ───────────────────────────────────────────────
        # Can only compute if we have multi-year data — left as 0.0 for now
        # (v1.2 roadmap: multi-year ITR trend analysis)
        features["revenue_growth_rate"] = 0.0

        return features

    # ─── XGBOOST SCORING ─────────────────────────────────────────────────────

    def _xgboost_score(self, feature_array: np.ndarray):
        import shap
        risk_prob = float(self.model.predict_proba(feature_array)[0][1])
        explainer = shap.TreeExplainer(self.model)
        shap_values = explainer.shap_values(feature_array)
        if isinstance(shap_values, list):
            shap_vals = shap_values[1][0]
        else:
            shap_vals = shap_values[0]
        return risk_prob, dict(zip(self.FEATURE_NAMES, shap_vals))

    # ─── RULE-BASED SCORING ───────────────────────────────────────────────────

    def _rule_based_score(self, features: dict):
        weights = {
            "gst_filing_regularity": -0.15,
            "gstr_mismatch_pct":       0.20,
            "avg_monthly_balance": -0.10,
            "emi_bounce_count":        0.15,
            "cash_flow_volatility":    0.10,
            "news_risk_score":         0.10,
            "litigation_flag":         0.15,
            "debt_equity_ratio":       0.10,
            "collateral_coverage": -0.08,
            "promoter_score": -0.10,
            "sector_risk_score":       0.08,
            "revenue_growth_rate": -0.05,
        }
        base_score = 0.40
        shap_values = {}
        for feature, value in features.items():
            weight = weights.get(feature, 0)
            contribution = weight * value
            shap_values[feature] = contribution
            base_score += contribution
        risk_score = min(max(base_score, 0.0), 1.0)
        return risk_score, shap_values

    # ─── SYNTHETIC TRAINING ───────────────────────────────────────────────────

    def _train_synthetic_model(self):
        import xgboost as xgb
        np.random.seed(42)
        n_samples = 500
        X = np.random.rand(n_samples, len(self.FEATURE_NAMES))
        y = np.zeros(n_samples)
        for i in range(n_samples):
            risk = 0.0
            risk += X[i, 2] * 0.25   # gstr_mismatch
            risk += X[i, 4] * 0.20   # emi_bounce
            risk += X[i, 7] * 0.20   # litigation
            risk -= X[i, 0] * 0.15   # gst_regularity
            risk -= X[i, 10] * 0.10  # promoter_score
            risk += X[i, 8] * 0.10   # debt_equity
            y[i] = 1 if risk > 0.3 else 0
        model = xgb.XGBClassifier(
            n_estimators=100, max_depth=4, learning_rate=0.1,
            random_state=42, eval_metric='logloss', verbosity=0
        )
        model.fit(X, y)
        return model

    # ─── HELPERS ─────────────────────────────────────────────────────────────

    def _categorize(self, risk_score: float):
        if risk_score <= RISK_THRESHOLDS["low"]:
            return RiskCategory.LOW, DecisionType.APPROVE
        elif risk_score <= RISK_THRESHOLDS["medium"]:
            return RiskCategory.MEDIUM, DecisionType.CONDITIONAL
        else:
            return RiskCategory.HIGH, DecisionType.REJECT

    def _calculate_loan_limit(self,
                              result: CreditAppraisalResult,
                              risk_score: float,
                              requested_amount_inr: float = 0.0) -> float:
        """
        Loan limit logic (priority order):
          1. If officer entered a requested amount, use that as the base —
             it reflects the actual credit need and has been manually reviewed.
          2. Otherwise derive from documents (GST turnover, bank credits, net income).
          3. Apply a risk multiplier (low risk → full amount, high risk → reduced).
          4. Hard cap at MAX_LOAN_LIMIT_INR to control portfolio concentration.
        """
        if requested_amount_inr and requested_amount_inr > 0:
            base = requested_amount_inr
        else:
            base = 0.0
            if result.gst_data and result.gst_data.turnover > 0:
                base = result.gst_data.turnover * 0.20
            if result.bank_data and result.bank_data.total_credits > 0:
                bank_based = result.bank_data.total_credits * 0.15
                base = max(base, bank_based)
            if result.itr_data and result.itr_data.net_income > 0:
                itr_based = result.itr_data.net_income * 0.30
                base = max(base, itr_based)

        risk_multiplier = 1.0 - (risk_score * 0.5)
        adjusted = base * risk_multiplier
        return round(min(adjusted, MAX_LOAN_LIMIT_INR), 0)

    def _build_shap_factors(self, features: dict,
                            shap_values: dict,
                            risk_score: float) -> List[SHAPFactor]:
        factors = []
        sorted_shap = sorted(
            shap_values.items(), key=lambda x: abs(x[1]), reverse=True
        )
        for feature_name, shap_val in sorted_shap[:4]:
            increases_risk = self.FEATURE_RISK_DIRECTION.get(
                feature_name, True)
            positive_shap = shap_val > 0
            if increases_risk:
                direction = "increases risk" if positive_shap else "decreases risk"
            else:
                direction = "decreases risk" if positive_shap else "increases risk"
            factors.append(SHAPFactor(
                feature_name=feature_name,
                shap_value=round(abs(shap_val), 4),
                direction=direction,
                display_name=self.FEATURE_DISPLAY_NAMES.get(
                    feature_name, feature_name)
            ))
        return factors

    def _generate_warnings(self, features: dict,
                           result: CreditAppraisalResult) -> List[str]:
        warnings = []
        if features["gstr_mismatch_pct"] > 0.10:
            warnings.append(
                "Monitor GSTR-2A vs 3B monthly — current variance is high")
        if features["emi_bounce_count"] > 0:
            warnings.append(
                "EMI bounce history detected — watch payment regularity")
        if features["debt_equity_ratio"] > 0.50:
            warnings.append(
                "Debt/equity ratio elevated — monitor leverage quarterly")
        if features["news_risk_score"] > 0.30:
            warnings.append(
                "Negative media coverage — set Google Alert for company name")
        if features["cash_flow_volatility"] > 0.80:
            warnings.append(
                "High debit/credit ratio — possible cash flow stress")
        if features["litigation_flag"] > 0:
            warnings.append(
                "Active litigation — review case status every 90 days")
        if features["sector_risk_score"] > 0.60:
            warnings.append(
                "High-risk sector — review exposure limits annually")
        return warnings[:5]

    def _build_explanation(self, features: dict,
                           shap_factors: List[SHAPFactor],
                           risk_score: float) -> str:
        lines = [f"Risk Score: {risk_score:.3f}", "Top risk drivers:"]
        for f in shap_factors:
            lines.append(
                f"  - {f.display_name}: {f.direction} (impact: {f.shap_value:.4f})"
            )
        return "\n".join(lines)


# ─── QUICK TEST ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from src.schemas import (
        CreditAppraisalResult, GSTData, BankStatementData, ITRData,
        GSTReconciliationResult, QualitativeInputs, ResearchFindings
    )

    engine = RiskEngine()

    print("\n" + "="*60)
    print("TEST: derive_from_documents() — Sunrise Apparels")
    print("="*60)

    sunrise = CreditAppraisalResult(
        company_name="Sunrise Apparels Pvt Ltd",
        itr_data=ITRData(
            net_worth=32500000,
            long_term_debt=18000000,
            short_term_debt=8500000,
            net_income=14100000,
            revenue=131200000,
            interest_expense=2200000,
            ebitda=25650000,   # PBT + depreciation + interest
            total_assets=73000000,
            total_liabilities=40500000,
        ),
        bank_data=BankStatementData(
            total_credits=62100000,
            total_debits=58200000,
            average_monthly_balance=42856000,
            emi_bounce_count=0,
        ),
        gst_data=GSTData(
            turnover=132000000,
            total_tax=7128000,
            itc_claimed=12000000,
            filing_regular=True,
        ),
        gst_reconciliation=GSTReconciliationResult(
            risk_flag=True,
            variance_pct=62.5,
        ),
        research=ResearchFindings(
            company_name="Sunrise Apparels Pvt Ltd",
            litigation_found=False,
            news_risk_score=1.5,
        ),
    )

    # Step 1: derive from documents
    derived = engine.derive_from_documents(sunrise)
    sunrise.derived_financials = derived

    print(f"D/E Ratio (derived):       {derived.debt_equity_ratio}")
    print(f"Net Worth (derived):        ₹{derived.net_worth_inr:,.0f}")
    print(f"DSCR (derived):             {derived.dscr}")
    print(f"Net Profit Margin:          {derived.net_profit_margin}%")
    print(
        f"Avg Monthly Balance:        ₹{derived.avg_monthly_balance_inr:,.0f}")
    print(f"Credit Utilisation:         {derived.credit_utilisation_pct}%")
    print(f"Data Completeness:          {derived.data_completeness_pct}%")
    print(f"Notes: {derived.derivation_notes}")

    # Step 2: build qualitative inputs (officer adds promoter + collateral + site visit)
    officer_inputs = QualitativeInputs(
        promoter_score=7,
        collateral_coverage=0.75,
        sector_risk_score=4,
        site_visit_notes="Factory operating at 80% capacity. New Tata Trent order confirmed.",
    )
    q = engine.build_qualitative_inputs(derived, officer_inputs)
    sunrise.qualitative_inputs = q

    print(f"\nQualitativeInputs after auto-fill:")
    print(
        f"  D/E Ratio:          {q.debt_equity_ratio}  (auto: {'debt_equity_ratio' in q.auto_filled_fields})")
    print(
        f"  Net Worth:          ₹{q.net_worth_inr:,.0f}  (auto: {'net_worth_inr' in q.auto_filled_fields})")
    print(f"  Promoter Score:     {q.promoter_score}  (officer)")
    print(f"  Collateral:         {q.collateral_coverage}  (officer)")
    print(f"  Auto-filled fields: {q.auto_filled_fields}")

    # Step 3: score
    prediction = engine.score(sunrise)
    print(f"\nRisk Score:   {prediction.risk_score}")
    print(f"Category:     {prediction.risk_category}")
    print(f"Decision:     {prediction.decision}")
    print(f"Interest Rate:{prediction.interest_rate}%")
    print(f"Loan Limit:   ₹{prediction.loan_limit_inr:,.0f}")
    print(f"\nSHAP Factors:")
    for f in prediction.top_shap_factors:
        print(f"  {f.display_name}: {f.direction} ({f.shap_value})")
    print(f"\nWarnings:")
    for w in prediction.early_warning_signals:
        print(f"  - {w}")
