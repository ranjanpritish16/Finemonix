import pandas as pd

df = pd.read_parquet(r"E:\Finemonix\Finemonix\backend\ml\backend\data\loan_training\full_dataset.parquet")

print(df.head())