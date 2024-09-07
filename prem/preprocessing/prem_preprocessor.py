import pandas as pd
from prem.utils.who_scored_cleaner import who_scored_data
from prem.feature_engineering.area_of_interest.heatmap import process_heatmap_row
from prem.utils.cleaner import training_cleaner, create_season_column
from prem.utils.fixed import stats_cols, columns_to_join
from prem.feature_engineering.simple_fe import feature_engineering


def prem_preprocessor(raw_data, ws_df):
    # Clean Data
    raw_data = raw_data.drop(columns=['touches_in_opposition_box', 'conc_touches_in_opposition_box'])

    cleaned_data = training_cleaner(raw_data)
    cleaned_data['datetime'] = pd.to_datetime(cleaned_data['datetime'])
    cleaned_data['date'] = cleaned_data['datetime'].dt.date

    # Join Who scored data
    pre_processed_data = who_scored_data(cleaned_data, ws_df)

    # Create a dictionary to store the statistics for each team in each game
    stats_dict = {}

    # Populate the dictionary
    for index, row in pre_processed_data.iterrows():
        game_id = row['game_id']
        team = row['team']
        total_tackles = row['total_tackles']
        passes_own_half = row['passes_own_half']
        passes_opp_half = row['passes_opp_half']
        total_touches = row['total_touches']
        wide_touches = row['wide_touches']
        wide_touches_pc = row['wide_touches_pc']

        if game_id not in stats_dict:
            stats_dict[game_id] = {}

        stats_dict[game_id][team] = {
            'total_tackles': total_tackles,
            'passes_own_half': passes_own_half,
            'passes_opp_half': passes_opp_half,
            'total_touches': total_touches,
            'wide_touches': wide_touches,
            'wide_touches_pc': wide_touches_pc
        }

    # Apply the function to get the opponent's statistics by passing stats_dict to the function
    pre_processed_data[['conc_total_tackles', 'conc_passes_own_half', 'conc_passes_opp_half',
                        'conc_total_touches', 'conc_wide_touches', 'conc_wide_touches_pc']] = pre_processed_data.apply(
                         lambda row: get_opponent_stats(row, stats_dict), axis=1)

    pre_processed_data.to_csv('prem/data/preprocessed/prem_pre_processed_data.csv', index=False)

    return pre_processed_data


def get_opponent_stats(row, stats_dict):
    game_id = row['game_id']
    team = row['team']
    opponent_stats = {'conc_total_tackles': None, 'conc_passes_own_half': None, 'conc_passes_opp_half': None,
                      'total_touches': None, 'wide_touches': None, 'wide_touches_pc': None}

    if game_id in stats_dict:
        for opp_team, stats in stats_dict[game_id].items():
            if opp_team != team:
                opponent_stats['conc_total_tackles'] = stats['total_tackles']
                opponent_stats['conc_passes_own_half'] = stats['passes_own_half']
                opponent_stats['conc_passes_opp_half'] = stats['passes_opp_half']
                opponent_stats['total_touches'] = stats['total_touches']
                opponent_stats['wide_touches'] = stats['wide_touches']
                opponent_stats['wide_touches_pc'] = stats['wide_touches_pc']

    return pd.Series(opponent_stats)
