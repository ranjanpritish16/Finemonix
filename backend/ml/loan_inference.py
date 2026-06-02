"""
Loan Inference Service
======================
Loads trained XGBoost models + SHAP explainers once at startup (singleton),
then serves predictions with full SHAP attribution and improvement actions.

Usage:
    from backend.ml.loan_inference import LoanInferenceService
    service = LoanInferenceService()          # call once at startup
    result  = service.predict(features_dict)  # call per request
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import shap

logger = logging.getLogger(__name__)

MODEL_DIR = Path("backend/data/loan_models")

LENDER_TYPES = ["psu", "private", "nbfc", "mfi"]

LENDER_DISPLAY_NAMES = {
    "psu":     "PSU Bank",
    "private": "Private Bank",
    "nbfc":    "NBFC",
    "mfi":     "Microfinance (MFI)",
}

FEATURE_COLS = [
    "cibil_score",
    "debt_to_income_ratio",
    "business_vintage_years",
    "client_concentration_pct",
    "revenue_stability",
    "cash_flow_coverage",
    "gst_compliance_score",
    "monthly_revenue_inr",
    "outstanding_loans_inr",
]

# Human-readable feature names for action messages
FEATURE_DISPLAY = {
    "cibil_score":              "CIBIL score",
    "debt_to_income_ratio":     "debt-to-income ratio",
    "business_vintage_years":   "business vintage",
    "client_concentration_pct": "client concentration",
    "revenue_stability":        "revenue stability (CV)",
    "cash_flow_coverage":       "cash flow coverage ratio",
    "gst_compliance_score":     "GST compliance score",
    "monthly_revenue_inr":      "monthly revenue",
    "outstanding_loans_inr":    "outstanding loan amount",
}

# Whether higher or lower value is better for each feature
FEATURE_DIRECTION = {
    "cibil_score":              "higher",
    "debt_to_income_ratio":     "lower",
    "business_vintage_years":   "higher",
    "client_concentration_pct": "lower",
    "revenue_stability":        "lower",   # lower CV = more stable
    "cash_flow_coverage":       "higher",
    "gst_compliance_score":     "higher",
    "monthly_revenue_inr":      "higher",
    "outstanding_loans_inr":    "lower",
}

# Target improvement values per feature (what to aim for)
FEATURE_TARGETS = {
    "cibil_score":              750,
    "debt_to_income_ratio":     0.35,
    "business_vintage_years":   None,      # cannot be changed
    "client_concentration_pct": 30.0,
    "revenue_stability":        0.3,
    "cash_flow_coverage":       1.5,
    "gst_compliance_score":     85.0,
    "monthly_revenue_inr":      None,      # contextual
    "outstanding_loans_inr":    0.0,
}

# Probability threshold for verdict
APPROVAL_THRESHOLD = 0.5


class LoanInferenceService:
    """
    Singleton service that loads all 4 models + explainers once
    and serves predictions with SHAP attribution.
    """

    def __init__(self) -> None:
        self.models: Dict = {}
        self.explainers: Dict = {}
        self.metadata: Dict = {}
        self._loaded = False
        self._load_all()

    def _load_all(self) -> None:
        """Load all 4 models and recreate SHAP explainers fresh at runtime."""
        import shap
        missing = []
        for lender in LENDER_TYPES:
            model_path    = MODEL_DIR / f"{lender}_model.pkl"
            metadata_path = MODEL_DIR / f"{lender}_metadata.pkl"

            if not model_path.exists():
                missing.append(lender)
                logger.warning("Model file not found for lender: %s", lender)
                continue

            with open(model_path, "rb") as f:
                self.models[lender] = pickle.load(f)

            # Recreate SHAP explainer from the loaded model instead of
            # loading from pkl — avoids TreeEnsemble version mismatch.
            try:
                base_model = self.models[lender].estimator
                self.explainers[lender] = shap.TreeExplainer(base_model)
                logger.info("SHAP explainer recreated for lender: %s", lender)
            except Exception as e:
                logger.warning("SHAP explainer failed for %s: %s", lender, e)

            if metadata_path.exists():
                with open(metadata_path, "rb") as f:
                    self.metadata[lender] = pickle.load(f)

            logger.info("Loaded loan model for lender: %s", lender)

        if missing:
            logger.error("Missing models for lenders: %s", missing)
        else:
            self._loaded = True
            logger.info("All 4 loan models loaded successfully.")
            
    def predict(
        self,
        features: Dict[str, float],
    ) -> Dict:
        """
        Run inference for all 4 lenders.

        Args:
            features: dict with all 9 feature keys

        Returns:
            {
              lender_scores: {psu: {probability, verdict, display_name}},
              shap_attributions: [{feature_name, value, shap_value, impact}],
              top_actions: [{action, current_value, target_value, projected_improvement_pct}],
              best_lender: str,
            }
        """
        if not self._loaded:
            raise RuntimeError(
                "Loan models not loaded. Run Day 14 training pipeline first: "
                "python backend/ml/loan_model.py"
            )

        X = np.array([[features[f] for f in FEATURE_COLS]], dtype=np.float32)

        # ── Run inference for each lender ──────────────────────────────────
        lender_scores = {}
        shap_by_lender: Dict[str, np.ndarray] = {}

        for lender in LENDER_TYPES:
            model     = self.models[lender]
            explainer = self.explainers[lender]

            prob = float(model.predict_proba(X)[0, 1])
            verdict = "approved" if prob >= APPROVAL_THRESHOLD else "rejected"

            lender_scores[lender] = {
                "probability":   round(prob, 4),
                "probability_pct": round(prob * 100, 1),
                "verdict":        verdict,
                "display_name":   LENDER_DISPLAY_NAMES[lender],
            }

            # SHAP for this lender (single sample)
            raw_shap = explainer.shap_values(X)
            if isinstance(raw_shap, list):
                raw_shap = raw_shap[1]   # positive class
            shap_by_lender[lender] = raw_shap.flatten()

        # ── Use best-chance lender's SHAP for attribution display ──────────
        best_lender = max(lender_scores, key=lambda l: lender_scores[l]["probability"])
        best_shap   = shap_by_lender[best_lender]

        # ── Build SHAP attribution list ────────────────────────────────────
        shap_attributions = []
        for i, feat in enumerate(FEATURE_COLS):
            sv = float(best_shap[i])
            shap_attributions.append({
                "feature_name":   feat,
                "display_name":   FEATURE_DISPLAY[feat],
                "value":          features[feat],
                "shap_value":     round(sv, 6),
                "impact":         "positive" if sv > 0 else "negative",
                "abs_shap":       abs(sv),
            })

        # Sort by absolute SHAP descending
        shap_attributions.sort(key=lambda x: x["abs_shap"], reverse=True)
        # Remove internal key before returning
        for a in shap_attributions:
            del a["abs_shap"]

        # ── Generate top 3 improvement actions ────────────────────────────
        top_actions = self._generate_actions(features, shap_attributions, best_lender)

        return {
            "lender_scores":      lender_scores,
            "shap_attributions":  shap_attributions,
            "top_actions":        top_actions,
            "best_lender":        best_lender,
            "best_lender_display": LENDER_DISPLAY_NAMES[best_lender],
            "best_probability_pct": lender_scores[best_lender]["probability_pct"],
            "raw_shap_by_lender": shap_by_lender,
            "raw_probabilities": {l: lender_scores[l]["probability"] for l in LENDER_TYPES},
        }

    def whatif(
        self,
        base_features: Dict[str, float],
        base_probabilities: Dict[str, float],
        base_shap_by_lender: Dict[str, np.ndarray],
        changed_feature: str,
        new_value: float,
    ) -> Dict:
        """
        O(1) SHAP additivity what-if delta.
        Returns exact probability deltas using the SHAP additive property.
        """
        if changed_feature not in FEATURE_COLS:
            raise ValueError(f"Unknown feature: {changed_feature}")

        feat_idx = FEATURE_COLS.index(changed_feature)
        modified = dict(base_features)
        modified[changed_feature] = new_value

        X_modified = np.array(
            [[modified[f] for f in FEATURE_COLS]], dtype=np.float32
        )

        updated_probabilities = {}
        delta = {}

        for lender in LENDER_TYPES:
            # Re-run single sample SHAP inference (~5ms)
            explainer = self.explainers[lender]
            raw_shap = explainer.shap_values(X_modified)
            if isinstance(raw_shap, list):
                raw_shap = raw_shap[1]
            new_shap = raw_shap.flatten()

            old_prob = base_probabilities[lender]
            old_shap_val = float(base_shap_by_lender[lender][feat_idx])
            new_shap_val = float(new_shap[feat_idx])

            # Approximated new score using SHAP additivity
            new_prob = old_prob - old_shap_val + new_shap_val
            new_prob = float(np.clip(new_prob, 0.0, 1.0))
            
            updated_probabilities[lender] = round(new_prob * 100, 1)
            delta[lender] = round((new_prob - old_prob) * 100, 1)

        return {
            "updated_probabilities": updated_probabilities,
            "delta": delta
        }

    def _generate_actions(
        self,
        features: Dict[str, float],
        shap_attributions: List[Dict],
        best_lender: str,
    ) -> List[Dict]:
        """
        Convert the worst negative SHAP contributors into
        specific, actionable improvement recommendations.
        """
        actions = []

        # Take top 5 negative SHAP features
        negative_contribs = [
            a for a in shap_attributions
            if a["impact"] == "negative" and FEATURE_TARGETS.get(a["feature_name"]) is not None
        ][:5]

        for attr in negative_contribs:
            feat   = attr["feature_name"]
            curr   = features[feat]
            target = FEATURE_TARGETS[feat]
            direction = FEATURE_DIRECTION[feat]

            if target is None:
                continue

            # Skip if already at or better than target
            if direction == "higher" and curr >= target:
                continue
            if direction == "lower" and curr <= target:
                continue

            # Estimate improvement: approximate by re-scoring with target value
            improvement_pct = self._estimate_improvement(
                features, feat, target, best_lender
            )

            action_text = _build_action_text(feat, curr, target, improvement_pct)

            actions.append({
                "feature":              feat,
                "display_name":         FEATURE_DISPLAY[feat],
                "action":               action_text,
                "current_value":        round(curr, 2),
                "target_value":         target,
                "direction":            direction,
                "projected_improvement_pct": round(improvement_pct, 1),
            })

            if len(actions) >= 3:
                break

        return actions

    def _estimate_improvement(
        self,
        features: Dict[str, float],
        changed_feature: str,
        new_value: float,
        lender: str,
    ) -> float:
        """
        Estimate probability improvement if one feature reaches its target.
        Uses single-sample re-inference (fast, ~5ms).
        """
        modified = dict(features)
        modified[changed_feature] = new_value

        X_modified = np.array(
            [[modified[f] for f in FEATURE_COLS]], dtype=np.float32
        )
        X_original = np.array(
            [[features[f] for f in FEATURE_COLS]], dtype=np.float32
        )

        model = self.models[lender]
        orig_prob = float(model.predict_proba(X_original)[0, 1])
        new_prob  = float(model.predict_proba(X_modified)[0, 1])

        improvement = (new_prob - orig_prob) * 100  # percentage points
        return max(0.0, improvement)


def _build_action_text(
    feat: str,
    curr: float,
    target: float,
    improvement_pct: float,
) -> str:
    """Build a human-readable action recommendation string."""
    direction = FEATURE_DIRECTION[feat]
    display   = FEATURE_DISPLAY[feat]

    improvement_str = (
        f" to improve approval probability by ~{improvement_pct:.1f} percentage points"
        if improvement_pct > 0.5 else ""
    )

    if feat == "cibil_score":
        return (
            f"Improve {display} from {curr:.0f} to {target:.0f} by paying all dues on time"
            f"{improvement_str}."
        )
    elif feat == "debt_to_income_ratio":
        return (
            f"Reduce {display} from {curr:.2f} to below {target:.2f} by clearing "
            f"existing loans before applying{improvement_str}."
        )
    elif feat == "client_concentration_pct":
        return (
            f"Reduce {display} from {curr:.1f}% to below {target:.0f}% by diversifying "
            f"your customer base{improvement_str}."
        )
    elif feat == "revenue_stability":
        return (
            f"Improve {display} (currently {curr:.2f}) to below {target:.2f} by "
            f"building recurring revenue contracts{improvement_str}."
        )
    elif feat == "cash_flow_coverage":
        return (
            f"Improve {display} from {curr:.2f}x to {target:.2f}x by increasing monthly "
            f"inflows or reducing fixed expenses{improvement_str}."
        )
    elif feat == "gst_compliance_score":
        return (
            f"Improve {display} from {curr:.0f} to {target:.0f} by filing GST returns "
            f"on time every month{improvement_str}."
        )
    elif feat == "outstanding_loans_inr":
        return (
            f"Reduce {display} from ₹{curr:,.0f} to ₹{target:,.0f} by prepaying "
            f"existing EMIs before applying{improvement_str}."
        )
    else:
        verb = "Increase" if direction == "higher" else "Reduce"
        return f"{verb} {display} from {curr:.2f} to {target:.2f}{improvement_str}."


# ── Module-level singleton — loaded once when the module is first imported ────
_service_instance: Optional[LoanInferenceService] = None


def get_loan_service() -> LoanInferenceService:
    """Return the module-level singleton. Creates it on first call."""
    global _service_instance
    if _service_instance is None:
        _service_instance = LoanInferenceService()
    return _service_instance