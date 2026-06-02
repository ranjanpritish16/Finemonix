"""
Day 13: Synthetic Training Data Generation for Loan Eligibility Engine

Generates 50,000 synthetic MSME loan profiles based on RBI lending guidelines.
Features realistic correlations and approval rules for 4 lender types.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

# ─── RBI Lending Guidelines & Approval Rules ──────────────────────────────

# CIBIL Score ranges (Reserve Bank of India standard)
CIBIL_RANGES = {
    "excellent": (800, 900),
    "good": (700, 799),
    "fair": (600, 699),
    "poor": (300, 599),
}

# Debt-to-Income ratio thresholds (monthly loan payments / avg monthly revenue)
DTI_THRESHOLDS = {
    "psu_bank": 0.4,
    "private_bank": 0.5,
    "nbfc": 0.65,
    "mfi": 0.75,
}

# Business vintage thresholds (years)
VINTAGE_THRESHOLDS = {
    "psu_bank": 3,
    "private_bank": 2,
    "nbfc": 1,
    "mfi": 0.5,
}

# Approval rules per lender type
APPROVAL_RULES = {
    "psu_bank": {
        "min_cibil": 700,
        "max_dti": 0.4,
        "min_vintage": 3,
        "min_gst_score": 70,
        "revenue_stability_cv_max": 0.4,
    },
    "private_bank": {
        "min_cibil": 650,
        "max_dti": 0.5,
        "min_vintage": 2,
        "min_gst_score": 60,
        "revenue_stability_cv_max": 0.5,
    },
    "nbfc": {
        "min_cibil": 550,
        "max_dti": 0.65,
        "min_vintage": 1,
        "min_gst_score": 40,
        "revenue_stability_cv_max": 0.6,
    },
    "mfi": {
        "min_cibil": 300,
        "max_dti": 0.75,
        "min_vintage": 0.5,
        "min_gst_score": 0,
        "revenue_stability_cv_max": 0.8,
    },
}


# ─── Feature Generation with Correlations ─────────────────────────────────

def generate_synthetic_data(
    n_samples: int = 50000,
    random_state: int = 42,
    save_path: str = None,
) -> pd.DataFrame:
    """
    Generate synthetic MSME loan profiles with realistic correlations.
    
    Features:
    - cibil_score: 300-900
    - debt_to_income_ratio: 0-1
    - business_vintage_years: 0-20
    - client_concentration_pct: 0-100
    - revenue_stability: coefficient of variation (0-1, lower=better)
    - cash_flow_coverage: monthly_in / obligations (0-10)
    - gst_compliance_score: 0-100 (% of months filed on time)
    - monthly_revenue_inr: lakhs (0.5-100)
    - outstanding_loans_inr: lakhs (0-50)
    
    Returns:
        pd.DataFrame with features + 4 approval columns
    """
    np.random.seed(random_state)
    
    logger.info(f"Generating {n_samples:,} synthetic loan profiles...")
    
    # ── 1. Generate base features ──────────────────────────────────────────
    
    # Business vintage (older businesses tend to have better metrics)
    business_vintage_years = np.random.exponential(scale=5, size=n_samples)
    business_vintage_years = np.clip(business_vintage_years, 0, 20)
    
    # CIBIL score correlates with vintage (older businesses have better credit history)
    # Base CIBIL influenced by vintage
    cibil_base = 500 + (business_vintage_years * 15)  # +15 per year of vintage
    cibil_noise = np.random.normal(0, 40, n_samples)
    cibil_score = np.clip(cibil_base + cibil_noise, 300, 900).astype(int)
    
    # Monthly revenue (log-normal distribution, skewed towards smaller businesses)
    monthly_revenue_inr = np.random.lognormal(mean=2, sigma=1.2, size=n_samples)
    monthly_revenue_inr = np.clip(monthly_revenue_inr, 0.5, 100)  # in lakhs
    
    # Revenue stability (CV) - larger, older businesses more stable
    base_cv = 0.8 - (business_vintage_years * 0.03)
    revenue_stability = np.clip(np.random.normal(base_cv, 0.15, n_samples), 0.1, 1.0)
    
    # Cash flow coverage - inversely related to business age (young = high coverage)
    cash_flow_coverage = np.random.gamma(shape=2, scale=1.5, size=n_samples)
    cash_flow_coverage = np.clip(cash_flow_coverage, 0.2, 10)
    
    # Outstanding loans - older businesses tend to have more debt
    outstanding_loans_inr = np.random.exponential(scale=2, size=n_samples)
    outstanding_loans_inr = np.clip(outstanding_loans_inr * business_vintage_years, 0, 50)
    
    # Debt-to-income ratio (monthly loan payments assume 10% of principal per month)
    monthly_loan_payments = (outstanding_loans_inr / 12) * 0.1
    dti = monthly_loan_payments / (monthly_revenue_inr + 0.01)  # avoid division by zero
    dti = np.clip(dti, 0, 1)
    
    # Client concentration - high concentration = higher risk
    client_concentration_pct = np.random.beta(a=2, b=5, size=n_samples) * 100
    client_concentration_pct = np.clip(client_concentration_pct, 1, 100)
    
    # GST compliance score - businesses that file GST on time are more reliable
    gst_compliance_score = np.random.beta(a=3, b=2, size=n_samples) * 100
    gst_compliance_score = np.clip(gst_compliance_score, 0, 100).astype(int)
    
    # ── 2. Create DataFrame ────────────────────────────────────────────────
    
    df = pd.DataFrame({
        "cibil_score": cibil_score,
        "debt_to_income_ratio": dti,
        "business_vintage_years": business_vintage_years,
        "client_concentration_pct": client_concentration_pct,
        "revenue_stability": revenue_stability,
        "cash_flow_coverage": cash_flow_coverage,
        "gst_compliance_score": gst_compliance_score,
        "monthly_revenue_inr": monthly_revenue_inr,
        "outstanding_loans_inr": outstanding_loans_inr,
    })
    
    # ── 3. Apply approval rules ────────────────────────────────────────────
    
    logger.info("Applying RBI approval rules...")
    
    df["psu_approved"] = apply_lender_rules(df, "psu_bank").astype(int)
    df["private_approved"] = apply_lender_rules(df, "private_bank").astype(int)
    df["nbfc_approved"] = apply_lender_rules(df, "nbfc").astype(int)
    df["mfi_approved"] = apply_lender_rules(df, "mfi").astype(int)
    
    # ── 4. Add label noise (5%) ────────────────────────────────────────────
    
    logger.info("Adding 5% label noise for realistic edge cases...")
    
    noise_indices = np.random.choice(n_samples, size=int(0.05 * n_samples), replace=False)
    approval_columns = ["psu_approved", "private_approved", "nbfc_approved", "mfi_approved"]
    
    for idx in noise_indices:
        # Flip a random approval label
        random_lender = np.random.choice(approval_columns)
        df.loc[idx, random_lender] = 1 - df.loc[idx, random_lender]
    
    # ── 5. Add edge cases (borderline approvals) ────────────────────────────
    
    logger.info("Adding edge case profiles...")
    
    # Add some borderline cases: businesses just below/above thresholds
    n_edge_cases = int(0.1 * n_samples)
    edge_indices = np.random.choice(n_samples, size=n_edge_cases, replace=False)
    
    for idx in edge_indices:
        # Create a borderline case
        rule_type = np.random.choice(list(APPROVAL_RULES.keys()))
        rules = APPROVAL_RULES[rule_type]
        
        # Set one feature just above/below threshold
        threshold_feature = np.random.choice([
            "min_cibil",
            "max_dti",
            "min_vintage",
            "min_gst_score",
        ])
        
        if threshold_feature == "min_cibil":
            df.loc[idx, "cibil_score"] = int(rules["min_cibil"] + np.random.randint(-10, 10))
        elif threshold_feature == "max_dti":
            df.loc[idx, "debt_to_income_ratio"] = rules["max_dti"] + np.random.uniform(-0.05, 0.05)
        elif threshold_feature == "min_vintage":
            df.loc[idx, "business_vintage_years"] = rules["min_vintage"] + np.random.uniform(-0.5, 0.5)
        elif threshold_feature == "min_gst_score":
            df.loc[idx, "gst_compliance_score"] = max(0, int(rules["min_gst_score"] + np.random.randint(-10, 10)))
    
    # ── 6. Round numeric columns ───────────────────────────────────────────
    
    df["cibil_score"] = df["cibil_score"].astype(int)
    df["gst_compliance_score"] = df["gst_compliance_score"].astype(int)
    df["debt_to_income_ratio"] = df["debt_to_income_ratio"].round(4)
    df["business_vintage_years"] = df["business_vintage_years"].round(2)
    df["client_concentration_pct"] = df["client_concentration_pct"].round(2)
    df["revenue_stability"] = df["revenue_stability"].round(4)
    df["cash_flow_coverage"] = df["cash_flow_coverage"].round(2)
    df["monthly_revenue_inr"] = df["monthly_revenue_inr"].round(2)
    df["outstanding_loans_inr"] = df["outstanding_loans_inr"].round(2)
    
    logger.info(f"Generated {len(df):,} samples")
    logger.info(f"PSU Approval rate: {df['psu_approved'].mean():.1%}")
    logger.info(f"Private Approval rate: {df['private_approved'].mean():.1%}")
    logger.info(f"NBFC Approval rate: {df['nbfc_approved'].mean():.1%}")
    logger.info(f"MFI Approval rate: {df['mfi_approved'].mean():.1%}")
    
    # ── 7. Save to parquet ─────────────────────────────────────────────────
    
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(save_path, index=False, compression="snappy")
        logger.info(f"Saved training data to {save_path}")
    
    return df


def apply_lender_rules(df: pd.DataFrame, lender_type: str) -> pd.Series:
    """
    Apply RBI approval rules for a specific lender type.
    
    Returns a boolean Series indicating approval.
    """
    rules = APPROVAL_RULES[lender_type]
    
    approval = (
        (df["cibil_score"] >= rules["min_cibil"]) &
        (df["debt_to_income_ratio"] <= rules["max_dti"]) &
        (df["business_vintage_years"] >= rules["min_vintage"]) &
        (df["gst_compliance_score"] >= rules["min_gst_score"]) &
        (df["revenue_stability"] <= rules["revenue_stability_cv_max"])
    )
    
    return approval


def split_train_val_test(
    df: pd.DataFrame,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split data into train/val/test sets stratified by approval rates.
    """
    np.random.seed(random_state)
    
    # Stratify by overall approval (at least one lender approves)
    df["any_approval"] = (
        df["psu_approved"] | df["private_approved"] | df["nbfc_approved"] | df["mfi_approved"]
    )
    
    # First split: train vs temp (val+test)
    n_train = int(len(df) * train_ratio)
    indices = np.random.permutation(len(df))
    train_indices = indices[:n_train]
    temp_indices = indices[n_train:]
    
    # Second split: val vs test
    n_val = int(len(temp_indices) * (val_ratio / (val_ratio + test_ratio)))
    val_indices = temp_indices[:n_val]
    test_indices = temp_indices[n_val:]
    
    train_df = df.iloc[train_indices].drop("any_approval", axis=1).reset_index(drop=True)
    val_df = df.iloc[val_indices].drop("any_approval", axis=1).reset_index(drop=True)
    test_df = df.iloc[test_indices].drop("any_approval", axis=1).reset_index(drop=True)
    
    logger.info(f"Train set: {len(train_df):,} samples ({train_ratio:.0%})")
    logger.info(f"Val set: {len(val_df):,} samples ({val_ratio:.0%})")
    logger.info(f"Test set: {len(test_df):,} samples ({test_ratio:.0%})")
    
    return train_df, val_df, test_df


def save_splits(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    output_dir: str = "backend/data/loan_training",
) -> None:
    """Save train/val/test splits to parquet files."""
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    train_df.to_parquet(f"{output_dir}/train.parquet", index=False, compression="snappy")
    val_df.to_parquet(f"{output_dir}/val.parquet", index=False, compression="snappy")
    test_df.to_parquet(f"{output_dir}/test.parquet", index=False, compression="snappy")
    
    logger.info(f"Saved splits to {output_dir}/")


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Generate full dataset
    df = generate_synthetic_data(
        n_samples=50000,
        save_path="backend/data/loan_training/full_dataset.parquet"
    )
    
    # Split and save
    train_df, val_df, test_df = split_train_val_test(df)
    save_splits(train_df, val_df, test_df)
    
    print("\n✅ Synthetic training data generated successfully!")
    print(f"Total samples: {len(df):,}")
    print(f"Features: {len(df.columns) - 4}")  # exclude 4 approval columns
    print(f"Approval labels: 4 (psu, private, nbfc, mfi)")
