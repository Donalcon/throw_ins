from engine.tackle_fe import feature_engineering
from engine.future_scraper import scrape_single_match
from engine.engine_cleaner import simple_cleaner
import pandas as pd
from joblib import load


# Scrape today's fixtures
# Scrape today's fixtures
todays_urls = [
               'https://www.fotmob.com/en-GB/matches/brazil-vs-colombia/296xs5#4377212',
               'https://www.fotmob.com/en-GB/matches/costa-rica-vs-paraguay/1hox8b#4407878']
dfs = []
game_id = 1
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
processed_data = pd.read_csv('data/processed_master_tackles_4.csv')
# make sure datetime is in datetime format
processed_data['datetime'] = pd.to_datetime(processed_data['datetime'])
# Join them
master_data = pd.concat([processed_data, todays_df], axis=0)

# Engineer features
stats_cols = ['accurate_passes', 'accurate_passes_pc',
              'fouls_committed', 'corners', 'blocked_shots', 'passes',
              'passes_own_half', 'passes_opp_half', 'accurate_long_balls', 'accurate_long_balls_pc',
              'accurate_crosses', 'accurate_crosses_pc', 'throws',
              'yellow_cards', 'red_cards', 'tackles_won', 'tackles_won_pc', 'interceptions', 'blocks', 'clearances',
              'duels_won', 'ground_duels_won', 'ground_duels_won_pc', 'aerial_duels_won',
              'aerial_duels_won_pc', 'successful_dribbles', 'successful_dribbles_pc', 'possession', 'total_tackles']
# remove all commas from stats_cols
master_data[stats_cols] = master_data[stats_cols].replace(',', '', regex=True)
# make all stats_cols float
master_data[stats_cols] = master_data[stats_cols].astype(float)
master_data['ranking'] = master_data['ranking'].astype(int)
master_data['opp_ranking'] = master_data['opp_ranking'].astype(int)

master_data = feature_engineering(master_data, stats_cols)

# preprocessing
# Columns to exclude from modelling
cols_not_for_modelling = [
    'total_shots', 'shots_on_target', 'big_chances', 'accurate_passes', 'accurate_passes_pc',
    'fouls_committed', 'corners', 'blocked_shots', 'shots_inside_box', 'shots_outside_box',
    'passes', 'passes_own_half', 'passes_opp_half', 'accurate_long_balls', 'competition',
    'accurate_long_balls_pc', 'accurate_crosses', 'accurate_crosses_pc', 'touches_in_opposition_box',
    'offsides', 'yellow_cards', 'red_cards', 'tackles_won', 'tackles_won_pc', 'interceptions',
    'blocks', 'clearances', 'keeper_saves', 'duels_won', 'ground_duels_won', 'ground_duels_won_pc',
    'aerial_duels_won', 'aerial_duels_won_pc', 'successful_dribbles', 'successful_dribbles_pc',
    'datetime', 'stadium', 'team', 'opp', 'touches_in_opposition_box', 'possession',
    'avg_touches_in_opposition_box', 'poss_adj_throws', 'pass_adj_throws', 'opp_avg_touches_in_opposition_box',
    'avg_div_touches_in_opposition_box', 'throws', 'rolling_avg_touches_in_opposition_box', 'total_tackles'
]

# drop columns not for modelling from full_df if they are in full_df
pred_df = master_data.drop(columns=cols_not_for_modelling, errors='ignore')
# print number of na's in every column
for col in pred_df.columns:
    print(f"Column: {col}, nans: {pred_df[col].isna().sum()}")

# drop ['throws', 'datetime', 'game_id', 'accurate_long_balls_pc'])
# pred_df.drop(['datetime', 'game_id'], axis=1, inplace=True)
pred_df['team_id'] = pred_df['team_id'].astype('category')
pred_df['opp_id'] = pred_df['opp_id'].astype('category')

pred_df = pd.get_dummies(pred_df)

# Remove all rows from master data that are not in todays_df, use game_id to identify
pred_df = pred_df[pred_df['game_id'].isin(todays_df['game_id'])]
# drop game_id
pred_df.drop('game_id', axis=1, inplace=True)

# CHECK FOR ANY COLUMNS THAT ARE NOT INT, FLOAT OR BOOL
print("COLUMNS NOT IN CORRECT DTYPE:", pred_df.select_dtypes(exclude=['int', 'float', 'bool']).columns)

# # MAKE PREDICTIONS
# throw_model = load('throw_in_XGB_final.joblib')
tackle_model = load('tackle_model_XGB_SMOTE.joblib')
# throw_features = throw_model.get_booster().feature_names
tackle_features = tackle_model.get_booster().feature_names

# Check if all expected features are present and match
missing_from_model = [f for f in tackle_features if f not in pred_df.columns]
extra_in_model = [f for f in pred_df.columns if f not in tackle_features]

print("Features expected by model and missing in data:", missing_from_model)
print("Extra features in data not expected by model:", extra_in_model)


# throw_df = pred_df[throw_features]
tackle_df = pred_df[tackle_features]
# total_throws_predictions = throw_model.predict(throw_df)
total_tackle_predictions = tackle_model.predict(tackle_df)
# todays_df['pred_throws'] = total_throws_predictions
todays_df['pred_tackles'] = total_tackle_predictions
