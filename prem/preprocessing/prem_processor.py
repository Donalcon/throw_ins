import pandas as pd
from src.prem.preprocessing.prem_cleaner import cleaner, stats_cols
from src.prem.feature_engineering.simple_fe import feature_engineering


def prem_processer(raw_data):
    # Clean Data
    raw_data = raw_data.drop(columns=['touches_in_opposition_box', 'conc_touches_in_opposition_box'])
    cleaned_data = cleaner(raw_data)
    cleaned_data[stats_cols] = cleaned_data[stats_cols].apply(pd.to_numeric, errors='coerce')
    # Feature Engineering
    processed_data = feature_engineering(cleaned_data, stats_cols)
    cleaned_data['year'] = cleaned_data['datetime'].dt.year
    cleaned_data['tourney_id'] = 'prem-' + cleaned_data['season']
    processed_data.to_csv('data/prem/preprocessed/prem_preprocessed_master.csv', index=False)

    return processed_data
