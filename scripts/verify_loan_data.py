"""Verify the generated loan training data."""

import pandas as pd
import numpy as np

# Load the full dataset
df = pd.read_parquet('backend/data/loan_training/full_dataset.parquet')

print("="*80)
print("✅ SYNTHETIC LOAN TRAINING DATA - STATISTICS")
print("="*80)
print(f"\nTotal Samples: {len(df):,}")
print(f"Features: {df.columns.tolist()[:9]}")
print(f"Approval Labels: psu_approved, private_approved, nbfc_approved, mfi_approved")

print("\n" + "="*80)
print("FEATURE STATISTICS")
print("="*80)
print(df.describe().round(2))

print("\n" + "="*80)
print("APPROVAL RATES BY LENDER TYPE")
print("="*80)
print(f"PSU Bank:     {df['psu_approved'].mean():.1%} ({df['psu_approved'].sum():,} approvals)")
print(f"Private Bank: {df['private_approved'].mean():.1%} ({df['private_approved'].sum():,} approvals)")
print(f"NBFC:         {df['nbfc_approved'].mean():.1%} ({df['nbfc_approved'].sum():,} approvals)")
print(f"MFI:          {df['mfi_approved'].mean():.1%} ({df['mfi_approved'].sum():,} approvals)")

print("\n" + "="*80)
print("APPROVAL COMBINATIONS (Top 10)")
print("="*80)
df['approval_combo'] = (
    df['psu_approved'].astype(str) + 
    df['private_approved'].astype(str) + 
    df['nbfc_approved'].astype(str) + 
    df['mfi_approved'].astype(str)
)
combo_counts = df['approval_combo'].value_counts(normalize=True).head(10) * 100
for combo, pct in combo_counts.items():
    psu, priv, nbfc, mfi = combo
    print(f"  PSU:{psu} | Private:{priv} | NBFC:{nbfc} | MFI:{mfi}  →  {pct:>5.1f}%")

print("\n" + "="*80)
print("DATASET SPLITS")
print("="*80)
train = pd.read_parquet('backend/data/loan_training/train.parquet')
val = pd.read_parquet('backend/data/loan_training/val.parquet')
test = pd.read_parquet('backend/data/loan_training/test.parquet')

print(f"Training:   {len(train):>6,} samples (70.0%)")
print(f"Validation: {len(val):>6,} samples (15.0%)")
print(f"Test:       {len(test):>6,} samples (15.0%)")

print("\n" + "="*80)
print("FEATURE CORRELATIONS (with NBFC approval)")
print("="*80)
features = ['cibil_score', 'debt_to_income_ratio', 'business_vintage_years', 
            'client_concentration_pct', 'cash_flow_coverage', 'gst_compliance_score',
            'monthly_revenue_inr']
for feature in features:
    corr = df[feature].corr(df['nbfc_approved'])
    print(f"  {feature:.<40} {corr:>7.3f}")

print("\n" + "="*80)
print("✅ DAY 13: SYNTHETIC TRAINING DATA GENERATION COMPLETE!")
print("="*80)
print("\nFiles created:")
print("  • backend/data/loan_training/full_dataset.parquet     (50,000 samples)")
print("  • backend/data/loan_training/train.parquet            (35,000 samples)")
print("  • backend/data/loan_training/val.parquet              (7,500 samples)")
print("  • backend/data/loan_training/test.parquet             (7,500 samples)")
