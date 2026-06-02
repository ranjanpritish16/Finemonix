"""
Day 14: XGBoost Training + SHAP Explainability for Loan Eligibility

Trains 4 separate XGBoost binary classifiers (one per lender type):
- PSU Bank
- Private Bank
- NBFC
- MFI

Includes hyperparameter tuning with Optuna, probability calibration, and SHAP setup.
"""

import numpy as np
import pandas as pd
import pickle
import logging
from pathlib import Path
from typing import Dict, Tuple, Any

import xgboost as xgb
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import cross_val_score
import optuna
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler
import shap

logger = logging.getLogger(__name__)

# Model configuration
MODEL_DIR = Path("backend/data/loan_models")
TRAINING_DATA_DIR = Path("backend/data/loan_training")
N_TRIALS = 50
N_CV_FOLDS = 5
RANDOM_STATE = 42

LENDER_TYPES = ["psu", "private", "nbfc", "mfi"]
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


# ─── Hyperparameter Tuning with Optuna ────────────────────────────────────

def objective(trial: optuna.Trial, X_train: np.ndarray, y_train: np.ndarray) -> float:
    """
    Objective function for Optuna hyperparameter tuning.
    Optimizes ROC-AUC score.
    """
    params = {
        "n_estimators": trial.suggest_int("n_estimators", 100, 500),
        "max_depth": trial.suggest_int("max_depth", 3, 8),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "reg_alpha": trial.suggest_float("reg_alpha", 0, 1),
        "reg_lambda": trial.suggest_float("reg_lambda", 0, 1),
        "random_state": RANDOM_STATE,
        "verbosity": 0,
    }
    
    model = xgb.XGBClassifier(**params)
    
    # Cross-validation with ROC-AUC metric
    scores = cross_val_score(
        model, X_train, y_train, cv=N_CV_FOLDS, scoring="roc_auc", n_jobs=-1
    )
    
    mean_score = scores.mean()
    
    # Prune unpromising trials
    trial.report(mean_score, step=0)
    if trial.should_prune():
        raise optuna.TrialPruned()
    
    return mean_score


def train_xgboost_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    lender_type: str,
) -> Tuple[xgb.XGBClassifier, Dict[str, Any]]:
    """
    Train and calibrate XGBoost model for a specific lender type.
    
    Returns:
        Tuple of (calibrated_model, hyperparameters_dict)
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"Training {lender_type.upper()} Model")
    logger.info(f"{'='*80}")
    
    # ── 1. Hyperparameter tuning with Optuna ────────────────────────────
    logger.info(f"Running Optuna hyperparameter tuning ({N_TRIALS} trials)...")
    
    sampler = TPESampler(seed=RANDOM_STATE)
    pruner = MedianPruner()
    
    study = optuna.create_study(
        direction="maximize",
        sampler=sampler,
        pruner=pruner,
    )
    
    study.optimize(
        lambda trial: objective(trial, X_train, y_train),
        n_trials=N_TRIALS,
        show_progress_bar=True,
    )
    
    best_params = study.best_trial.params
    best_score = study.best_trial.value
    
    logger.info(f"Best CV ROC-AUC: {best_score:.4f}")
    logger.info(f"Best hyperparameters: {best_params}")
    
    # ── 2. Train final model with best hyperparameters ─────────────────
    logger.info("Training final model with best hyperparameters...")
    
    best_params["random_state"] = RANDOM_STATE
    best_params["verbosity"] = 0
    
    model = xgb.XGBClassifier(**best_params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        early_stopping_rounds=50,
        verbose=False,
    )
    
    # Get validation performance
    val_pred_proba = model.predict_proba(X_val)[:, 1]
    from sklearn.metrics import roc_auc_score, precision_score, recall_score
    val_auc = roc_auc_score(y_val, val_pred_proba)
    
    logger.info(f"Validation ROC-AUC: {val_auc:.4f}")
    
    # ── 3. Probability calibration with isotonic regression ────────────
    logger.info("Calibrating probabilities with isotonic regression...")
    
    calibrated_model = CalibratedClassifierCV(
        model,
        method="isotonic",
        cv=5,
    )
    calibrated_model.fit(X_train, y_train)
    
    cal_pred_proba = calibrated_model.predict_proba(X_val)[:, 1]
    cal_auc = roc_auc_score(y_val, cal_pred_proba)
    
    logger.info(f"Calibrated Validation ROC-AUC: {cal_auc:.4f}")
    
    return calibrated_model, best_params


# ─── SHAP Explainer Setup ──────────────────────────────────────────────────

def setup_shap_explainer(
    model: xgb.XGBClassifier,
    X_background: np.ndarray,
    X_explain: np.ndarray,
    lender_type: str,
) -> Tuple[shap.TreeExplainer, np.ndarray]:
    """
    Set up SHAP TreeExplainer and compute SHAP values for test set.
    
    Returns:
        Tuple of (explainer, shap_values)
    """
    logger.info(f"Setting up SHAP TreeExplainer for {lender_type}...")
    
    # Get the underlying XGBoost model from CalibratedClassifierCV
    if isinstance(model, CalibratedClassifierCV):
        base_model = model.estimator
    else:
        base_model = model
    
    # Create TreeExplainer with background data
    explainer = shap.TreeExplainer(base_model, data=shap.sample(X_background, 100))
    
    # Compute SHAP values for explanation set
    logger.info(f"Computing SHAP values for {len(X_explain)} samples...")
    shap_values = explainer.shap_values(X_explain)
    
    # For binary classification, take positive class SHAP values
    if isinstance(shap_values, list):
        shap_values = shap_values[1]
    
    logger.info(f"SHAP values computed. Shape: {shap_values.shape}")
    
    return explainer, shap_values


# ─── Global Feature Importance ─────────────────────────────────────────────

def compute_global_importance(
    shap_values: np.ndarray,
    feature_names: list,
) -> Dict[str, float]:
    """
    Compute global feature importance as mean |SHAP| per feature.
    """
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    
    importance_dict = {
        feature: float(importance)
        for feature, importance in zip(feature_names, mean_abs_shap)
    }
    
    # Sort by importance
    importance_dict = dict(sorted(
        importance_dict.items(),
        key=lambda x: x[1],
        reverse=True
    ))
    
    return importance_dict


# ─── Save Models and Explainers ────────────────────────────────────────────

def save_model_and_explainer(
    model: Any,
    explainer: shap.TreeExplainer,
    shap_values: np.ndarray,
    feature_importance: Dict[str, float],
    lender_type: str,
    metadata: Dict[str, Any],
) -> None:
    """Save trained model, explainer, and metadata to disk."""
    
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save calibrated model
    model_path = MODEL_DIR / f"{lender_type}_model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    logger.info(f"Saved model: {model_path}")
    
    # Save explainer
    explainer_path = MODEL_DIR / f"{lender_type}_explainer.pkl"
    with open(explainer_path, "wb") as f:
        pickle.dump(explainer, f)
    logger.info(f"Saved explainer: {explainer_path}")
    
    # Save SHAP values
    shap_path = MODEL_DIR / f"{lender_type}_shap_values.npy"
    np.save(shap_path, shap_values)
    logger.info(f"Saved SHAP values: {shap_path}")
    
    # Save feature importance
    importance_path = MODEL_DIR / f"{lender_type}_feature_importance.pkl"
    with open(importance_path, "wb") as f:
        pickle.dump(feature_importance, f)
    logger.info(f"Saved feature importance: {importance_path}")
    
    # Save metadata (hyperparameters, base_value, etc.)
    metadata_path = MODEL_DIR / f"{lender_type}_metadata.pkl"
    with open(metadata_path, "wb") as f:
        pickle.dump(metadata, f)
    logger.info(f"Saved metadata: {metadata_path}")


# ─── Load Trained Models ──────────────────────────────────────────────────

def load_model_and_explainer(lender_type: str) -> Tuple[Any, shap.TreeExplainer]:
    """Load trained model and SHAP explainer from disk."""
    
    model_path = MODEL_DIR / f"{lender_type}_model.pkl"
    explainer_path = MODEL_DIR / f"{lender_type}_explainer.pkl"
    
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    
    with open(explainer_path, "rb") as f:
        explainer = pickle.load(f)
    
    return model, explainer


def load_metadata(lender_type: str) -> Dict[str, Any]:
    """Load model metadata (hyperparameters, base_value, etc.)."""
    
    metadata_path = MODEL_DIR / f"{lender_type}_metadata.pkl"
    
    with open(metadata_path, "rb") as f:
        metadata = pickle.load(f)
    
    return metadata


# ─── Main Training Pipeline ───────────────────────────────────────────────

def train_all_models() -> Dict[str, Dict[str, Any]]:
    """
    Train all 4 lender models with hyperparameter tuning and SHAP setup.
    """
    
    # Load training data
    logger.info("Loading training data...")
    train_df = pd.read_parquet(TRAINING_DATA_DIR / "train.parquet")
    val_df = pd.read_parquet(TRAINING_DATA_DIR / "val.parquet")
    test_df = pd.read_parquet(TRAINING_DATA_DIR / "test.parquet")
    
    X_train = train_df[FEATURE_COLS].values
    X_val = val_df[FEATURE_COLS].values
    X_test = test_df[FEATURE_COLS].values
    
    results = {}
    
    for lender_type in LENDER_TYPES:
        logger.info(f"\n{'#'*80}")
        logger.info(f"# {lender_type.upper()}")
        logger.info(f"{'#'*80}")
        
        # Get target variable for this lender
        target_col = f"{lender_type}_approved"
        y_train = train_df[target_col].values
        y_val = val_df[target_col].values
        y_test = test_df[target_col].values
        
        logger.info(f"Training set: {len(train_df)} samples ({y_train.mean():.1%} approved)")
        logger.info(f"Val set: {len(val_df)} samples ({y_val.mean():.1%} approved)")
        logger.info(f"Test set: {len(test_df)} samples ({y_test.mean():.1%} approved)")
        
        # ── Train model ────────────────────────────────────────────────
        model, best_params = train_xgboost_model(X_train, y_train, X_val, y_val, lender_type)
        
        # ── Setup SHAP ─────────────────────────────────────────────────
        explainer, shap_values_test = setup_shap_explainer(
            model, X_train, X_test, lender_type
        )
        
        # ── Compute global importance ──────────────────────────────────
        feature_importance = compute_global_importance(shap_values_test, FEATURE_COLS)
        
        logger.info(f"\nTop 5 Important Features for {lender_type}:")
        for i, (feature, importance) in enumerate(list(feature_importance.items())[:5], 1):
            logger.info(f"  {i}. {feature}: {importance:.4f}")
        
        # ── Get base value (expected value) for SHAP ───────────────────
        base_value = explainer.expected_value
        if isinstance(base_value, np.ndarray):
            base_value = float(base_value[1])  # positive class
        else:
            base_value = float(base_value)
        
        # ── Compute test set performance ───────────────────────────────
        from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
        
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        y_pred = model.predict(X_test)
        
        test_auc = roc_auc_score(y_test, y_pred_proba)
        test_precision = precision_score(y_test, y_pred, zero_division=0)
        test_recall = recall_score(y_test, y_pred, zero_division=0)
        test_f1 = f1_score(y_test, y_pred, zero_division=0)
        
        logger.info(f"\nTest Set Performance:")
        logger.info(f"  ROC-AUC: {test_auc:.4f}")
        logger.info(f"  Precision: {test_precision:.4f}")
        logger.info(f"  Recall: {test_recall:.4f}")
        logger.info(f"  F1-Score: {test_f1:.4f}")
        
        # ── Save model and explainer ───────────────────────────────────
        metadata = {
            "lender_type": lender_type,
            "features": FEATURE_COLS,
            "hyperparameters": best_params,
            "base_value": base_value,
            "feature_importance": feature_importance,
            "test_metrics": {
                "roc_auc": float(test_auc),
                "precision": float(test_precision),
                "recall": float(test_recall),
                "f1": float(test_f1),
            },
        }
        
        save_model_and_explainer(
            model,
            explainer,
            shap_values_test,
            feature_importance,
            lender_type,
            metadata,
        )
        
        results[lender_type] = metadata
    
    return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    results = train_all_models()
    
    print("\n" + "="*80)
    print("✅ DAY 14: XGBOOST TRAINING + SHAP EXPLAINABILITY COMPLETE!")
    print("="*80)
    print("\nModels trained and saved:")
    for lender_type in LENDER_TYPES:
        print(f"  • {lender_type}")
    print("\nMetrics saved for all 4 lenders in backend/data/loan_models/")
