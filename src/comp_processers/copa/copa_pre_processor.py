import pandas as pd
from src.comp_processers.copa.copa_cleaner import cleaner, stats_cols
from src.feature_engineering.simple_fe import feature_engineering

# Load Data
raw_data = pd.read_csv('data/raw/int_raw_master.csv')

# Clean Data
cleaned_data = cleaner(raw_data)
cleaned_data[stats_cols] = cleaned_data[stats_cols].apply(pd.to_numeric, errors='coerce')

# Feature Engineering
processed_data = feature_engineering(cleaned_data, stats_cols)
processed_data.to_csv('data/int_processed_master.csv', index=False)
# print number of nans in every column
processed_data = processed_data.dropna(subset=stats_cols)
for col in processed_data.columns:
    print(f"Column: {col}, nans: {processed_data[col].isna().sum()}")
