import pandas as pd
from src.utils.simple_cleaner import cleaner, stats_cols
from src.model.model_cleaner import filter_teams, european_countries
from src.feature_engineering.simple_fe import feature_engineering
from src.weather_engineering.weather_engineering import weather_engineering
from src.scraper.international_scraper.int_match_scraper import international_game_scraper
import matplotlib
import seaborn as sns
import matplotlib.pyplot as plt


# fixed_nan_df = international_game_scraper(scrape_type='full')
raw_data = pd.read_csv('data/raw/int_raw_master.csv')
euro_data = filter_teams(raw_data, european_countries)

# cols_to_drop1 = ['yellow_cards', 'red_cards', 'tackles_won', 'tackles_won_pc', 'interceptions', 'blocks',
#                  'total_shots',
#                 'shots_on_target', 'big_chances', 'fouls_committed',
#                 'corners', 'blocked_shots', 'shots_inside_box', 'shots_outside_box',
#                 'throws', 'touches_in_opposition_box', 'offsides', 'keeper_saves',
#                 'ground_duels_won', 'ground_duels_won_pc', 'aerial_duels_won', 'aerial_duels_won_pc',
#                 'successful_dribbles_pc']

cleaned_data = cleaner(euro_data)
# drop nan values
cleaned_data = cleaned_data.dropna(subset=['latitude', 'longitude'])

cleaned_data['datetime'] = pd.to_datetime(cleaned_data['datetime'])
cleaned_data = cleaned_data.sort_values('datetime')
cleaned_data['year'] = cleaned_data['datetime'].dt.year
cleaned_data['tourney_id'] = cleaned_data['competition'] + '_' + cleaned_data['year'].astype(str)

# stats_cols = ['accurate_passes', 'accurate_passes_pc', 'passes',
#               'passes_own_half', 'passes_opp_half', 'accurate_long_balls', 'accurate_long_balls_pc',
#               'accurate_crosses', 'accurate_crosses_pc', 'throws', 'clearances', 'duels_won',
#               'successful_dribbles', 'successful_dribbles_pc', 'possession', 'total_tackles']

# cleaned_data = weather_engineering(cleaned_data, perspective='forecast')
# make stats_cols numeric
cleaned_data[stats_cols] = cleaned_data[stats_cols].apply(pd.to_numeric, errors='coerce')
processed_data = feature_engineering(cleaned_data, stats_cols)
# save processed data
processed_data.to_csv('data/processed_master_throws_6.csv', index=False)
# print number of nans in every column
processed_data = processed_data.dropna(subset=stats_cols)
for col in processed_data.columns:
    print(f"Column: {col}, nans: {processed_data[col].isna().sum()}")
# drop na of processed_data
# id group stage is nan make it 0
# sns.kdeplot(processed_data['throws'])
# plt.show()
# plot distribution of passes
# sns.kdeplot(processed_data['passes'])
# plt.show()

# print(processed_data['passes'].describe())
# TODO: Make competition and round accurate
# TODO: H2h avg total throws
# TODO: SOrt out attributees
# TODO: Avg throw in division
# TODO: FE: Throw_in_div_opp_pass, pass_opp_half_pc, throw_in_div_opp_poss,
# TODO: FE: Check distribution of passes and possession
# TODO: FE: Replication passes function for poss buckets function
# TODO: Scrape Euros Data
# TODO: Throw ins reflected over rank difference?
# TODO: Coordinates of every stadium.
# TODO: Run model on rows that only feature european teams.
# TODO: Add in xG
# TODO: Check mapped names
# TODO: End 2 End automation
# TODO: Typical opposition stats vs actual opp stats
# TODO: opposition avg throw in conceded
# TODO: stratified split
# TODO: % attendance of capacity
# TODO: interaction variable between attendance and % attendance
# print max game_id
# print(processed_data['game_id'].max())
