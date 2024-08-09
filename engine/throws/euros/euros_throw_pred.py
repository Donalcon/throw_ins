from engine.throw_fe import feature_engineering
from engine.future_scraper import scrape_single_match
from engine.throws.copa.copa_throw_pred_cleaner import simple_cleaner, stats_cols, cols_not_for_modelling
import pandas as pd
from joblib import load

from src.models.model_cleaner import filter_teams, european_countries

# Scrape today's fixtures
todays_urls = ['https://www.fotmob.com/en-GB/matches/netherlands-vs-england/1ws0hn#4043984']
dfs = []
game_id = 2000
for url in todays_urls:
    try:
        df = scrape_single_match(url)
        df['game_id'] = game_id
        game_id += 1
        dfs.append(df)
    except Exception as e:
        print(f"Error scraping data from {url}: {e}")

# Step 3: Concatenate the dataframes into a single dataframe
todays_df = pd.concat(dfs, ignore_index=True)
todays_df = simple_cleaner(todays_df)
# Load in processed Data
processed_data = pd.read_csv('data/euro_processed_master.csv')

processed_data['datetime'] = pd.to_datetime(processed_data['datetime'])
# Join them
master_data = pd.concat([processed_data, todays_df], axis=0)

# make all stats_cols float
master_data[stats_cols] = master_data[stats_cols].astype(float)
master_data['ranking'] = master_data['ranking'].astype(int)
master_data['opp_ranking'] = master_data['opp_ranking'].astype(int)

master_data = feature_engineering(master_data, stats_cols)

# drop columns not for modelling from full_df if they are in full_df
pred_df = master_data.drop(columns=cols_not_for_modelling, errors='ignore')
# print number of na's in every column
for col in pred_df.columns:
    print(f"Column: {col}, nans: {pred_df[col].isna().sum()}")

# drop ['throws', 'datetime', 'game_id', 'accurate_long_balls_pc'])
# pred_df.drop(['datetime', 'game_id'], axis=1, inplace=True)
pred_df['team_id'] = pred_df['team_id'].astype('category')
pred_df['opp_id'] = pred_df['opp_id'].astype('category')
pred_df['referee_id'] = pred_df['referee_id'].astype('category')
pred_df['round'] = pred_df['round'].astype('category')
pred_df['competition'] = pred_df['competition'].astype('category')
pred_df = pd.get_dummies(pred_df)

# Remove all rows from master data that are not in todays_df, use game_id to identify
pred_df = pred_df[pred_df['game_id'].isin(todays_df['game_id'])]
# drop game_id
pred_df.drop('game_id', axis=1, inplace=True)

# CHECK FOR ANY COLUMNS THAT ARE NOT INT, FLOAT OR BOOL
print("COLUMNS NOT IN CORRECT DTYPE:", pred_df.select_dtypes(exclude=['int', 'float', 'bool']).columns)

# # MAKE PREDICTIONS
throw_model = load('throw_in_XGB_SMOTE_optuna_euro.joblib')
throw_features = throw_model.get_booster().feature_names

# Check if all expected features are present and match
missing_from_model = [f for f in throw_features if f not in pred_df.columns]
extra_in_model = [f for f in pred_df.columns if f not in throw_features]

print("Features expected by model and missing in data:", missing_from_model)
print("Extra features in data not expected by model:", extra_in_model)


throw_df = pred_df[throw_features]
# print cols with nan values
print("Columns with nan values:", throw_df.columns[throw_df.isna().any()].tolist())
total_throws_predictions = throw_model.predict(throw_df)
todays_df['pred_throws'] = total_throws_predictions



