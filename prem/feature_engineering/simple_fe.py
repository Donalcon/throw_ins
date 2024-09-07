import numpy as np
import pandas as pd
import pickle
from prem.feature_engineering.elo import calculate_elo, add_latest_results
from prem.utils.fixed import team_name_mapping


def calculate_h2h(df, stat_columns):
    df = df.sort_values(by='datetime').reset_index(drop=True)
    # Create new columns for rolling averages
    for column in stat_columns:
        df[f'avg_h2h_{column}'] = np.nan

    # Calculate rolling averages using groupby for h2h data
    for team_id, opp_id in df.groupby(['team_id', 'opp_id']).groups:
        team_past_data = df[(df['team_id'] == team_id) & (df['opp_id'] == opp_id)].copy()
        team_past_data = team_past_data.sort_values(by='datetime')

        for column in stat_columns:
            avg_column = f'avg_h2h_{column}'
            team_past_data[avg_column] = team_past_data[column].expanding().mean().shift(1)
            df.loc[(df['team_id'] == team_id) & (df['opp_id'] == opp_id), avg_column] = team_past_data[avg_column]

    return df


def calculate_team_div_averages(df, stat_columns):
    df = df.sort_values(by='datetime').reset_index(drop=True)

    # Ensure that df has a 'game_id' column for unique game identification
    if 'game_id' not in df.columns:
        raise ValueError("DataFrame must contain a 'game_id' column")

    # Create new columns for rolling averages
    for column in stat_columns:
        df[f'avg_team_div_{column}'] = np.nan

    # Calculate rolling averages using groupby for team and division data
    grouped = df.groupby(['team_id', 'division'])

    for (team_id, division), group in grouped:
        group = group.sort_values(by='datetime').reset_index(drop=True)

        for idx in range(len(group)):
            current_game_id = group.loc[idx, 'game_id']
            past_data = group[group['game_id'] != current_game_id]

            for column in stat_columns:
                avg_column = f'avg_team_div_{column}'
                if not past_data.empty:
                    df.loc[(df['team_id'] == team_id) & (df['division'] == division) & (
                                df['game_id'] == current_game_id), avg_column] = past_data[column].mean()

    return df


def calculate_averages(df, stat_columns):
    """
    Calculate rolling averages for specified columns in a DataFrame, ensuring only past data is used for each row.

    Args:
        df: The DataFrame containing match data.
        stat_columns: List of columns for which to calculate the rolling averages.

    Returns:
        The DataFrame with new rolling average columns added.
    """
    df = df.sort_values(by='datetime').reset_index(drop=True)

    # Create new columns for rolling averages
    for column in stat_columns:
        df[f'avg_{column}'] = np.nan

    # Iterate over the DataFrame to calculate rolling averages
    for i, row in df.iterrows():
        team_past_data = df[(df['datetime'] < row['datetime']) & (df['team_id'] == row['team_id'])]
        # game_id is not equal to game_id
        team_past_data = team_past_data[team_past_data['game_id'] != row['game_id']]
        for column in stat_columns:
            if not team_past_data.empty:
                df.at[i, f'avg_{column}'] = team_past_data[column].mean()

    return df


def calculate_rolling_averages(df, stat_columns, window=5):
    """
    Calculate rolling averages for specified columns in a DataFrame, ensuring only past data is used for each row.

    Args:
        df: The DataFrame containing match data.
        stat_columns: List of columns for which to calculate the rolling averages.
        window: The window size for calculating the rolling average (default is 5).

    Returns:
        The DataFrame with new rolling average columns added.
    """
    df = df.sort_values(by=['team_id', 'datetime']).reset_index(drop=True)

    for column in stat_columns:
        df[f'rolling_avg_{column}'] = np.nan

    for team_id, group in df.groupby('team_id'):
        for column in stat_columns:
            group = group.copy()
            group[f'shifted_{column}'] = group[column].shift(1)
            group[f'expanding_avg_{column}'] = group[f'shifted_{column}'].expanding().mean()
            group[f'rolling_avg_{column}'] = group[f'shifted_{column}'].rolling(window=window, min_periods=1).mean()

            for i, row in group.iterrows():
                past_data = group[(group['datetime'] < row['datetime']) & (group['game_id'] != row['game_id'])]
                df.at[i, f'rolling_avg_{column}'] = past_data[f'rolling_avg_{column}'].iloc[-1] if not past_data.empty else np.nan

    return df


def add_opponent_stats(df, stats_cols):
    """
    Add opponent's average stats and ranking to each team's row using game_id.

    Args:
        df: The DataFrame containing match data.
        stats_cols: List of columns for which to calculate the rolling averages.

    Returns:
        The DataFrame with opponent's average stats and ranking added.
    """
    df = df.sort_values(by='datetime').reset_index(drop=True)

    # Create new columns for the opponent's average stats and ranking
    for col in stats_cols:
        df[f'opp_avg_{col}'] = np.nan

    # Iterate over each row
    for i in range(len(df)):
        current_datetime = df.loc[i, 'datetime']
        current_opp = df.loc[i, 'opp']
        current_game = df.loc[i, 'game_id']
        # Subset to include only past games
        past_games = df[(df['datetime'] < current_datetime) & (df['team'] == current_opp)]
        past_games = past_games[past_games['game_id'] != current_game]
        if not past_games.empty:
            for col in stats_cols:
                df.at[i, f'opp_avg_{col}'] = past_games[col].mean()

    return df


def calculate_average_throw_ins_adjusted_for_opp_quality(df):
    """
    Calculate the average throw-ins adjusted for opponent quality using only past data.

    Args:
        df: The DataFrame containing match data.

    Returns:
        The DataFrame with the new column for average throw-ins adjusted for opponent quality.
    """
    # Ensure data is sorted by datetime
    df = df.sort_values(by='datetime').reset_index(drop=True)

    # Initialize a list to store average throw-ins for each match
    average_throw_ins_list = []

    # Iterate over each row in the DataFrame
    for i in range(len(df)):
        # Get current match details
        current_opp_rank = df.loc[i, 'opp_elo']
        current_datetime = df.loc[i, 'datetime']
        current_game = df.loc[i, 'game_id']

        # Filter previous matches before current datetime
        previous_matches = df.loc[df['datetime'] < current_datetime]
        previous_matches = previous_matches[previous_matches['game_id'] != current_game]
        # Calculate average throw-ins against similar quality opponents (within ±5 ranks)
        similar_quality_matches = previous_matches[
            (previous_matches['opp_elo'] >= current_opp_rank - 100) &
            (previous_matches['opp_elo'] <= current_opp_rank + 100)
            ]

        if not similar_quality_matches.empty:
            average_throw_ins = similar_quality_matches['throws'].mean()
        else:
            average_throw_ins = np.nan  # Handle cases where no similar quality matches found

        # Store the calculated average throw-ins
        average_throw_ins_list.append(average_throw_ins)

    # Add the average throw-ins as a new column in the DataFrame
    df['avg_TI_adj_opp_quality'] = average_throw_ins_list

    return df


def calculate_average_tackles_adjusted_for_opp_quality(df):
    """
    Calculate the average tackles adjusted for opponent quality using only past data.

    Args:
        df: The DataFrame containing match data.

    Returns:
        The DataFrame with the new column for average tackles adjusted for opponent quality.
    """
    # Ensure data is sorted by datetime
    df = df.sort_values(by='datetime').reset_index(drop=True)

    # Initialize a list to store average tackles for each match
    average_tackles_list = []

    # Iterate over each row in the DataFrame
    for i in range(len(df)):
        # Get current match details
        current_opp_rank = df.loc[i, 'opp_elo']
        current_datetime = df.loc[i, 'datetime']
        current_game = df.loc[i, 'game_id']
        # Filter previous matches before current datetime
        previous_matches = df.loc[df['datetime'] < current_datetime]
        previous_matches = previous_matches[previous_matches['game_id'] != current_game]

        # Calculate average tackles against similar quality opponents (within ±5 ranks)
        similar_quality_matches = previous_matches[
            (previous_matches['opp_elo'] >= current_opp_rank - 100) &
            (previous_matches['opp_elo'] <= current_opp_rank + 100)
            ]

        if not similar_quality_matches.empty:
            average_tackles = similar_quality_matches['total_tackles'].mean()
        else:
            average_tackles = np.nan  # Handle cases where no similar quality matches found

        # Store the calculated average tackles
        average_tackles_list.append(average_tackles)

    # Add the average tackles as a new column in the DataFrame
    df['avg_tackles_adj_opp_quality'] = average_tackles_list

    return df


def calculate_average_throw_ins_adjusted_for_rank_diff(df):
    """
    Calculate the average throw-ins adjusted for rank difference using only past data.

    Args:
        df: The DataFrame containing match data.

    Returns:
        The DataFrame with the new column for average throw-ins adjusted for rank difference.
    """
    # Ensure data is sorted by datetime
    df = df.sort_values(by='datetime').reset_index(drop=True)

    # Initialize a list to store average throw-ins for each match
    average_throw_ins_list = []

    # Iterate over each row in the DataFrame
    for i in range(len(df)):
        # Get current match details
        rank_diff = df.loc[i, 'elo_diff']
        current_datetime = df.loc[i, 'datetime']
        current_game = df.loc[i, 'game_id']
        # Filter previous matches before current datetime
        previous_matches = df.loc[df['datetime'] < current_datetime]
        previous_matches = previous_matches[previous_matches['game_id'] != current_game]
        # Calculate average throw-ins against similar quality opponents (within ±5 rank difference)
        similar_quality_matches = previous_matches[
            (previous_matches['elo_diff'] >= rank_diff - 100) &
            (previous_matches['elo_diff'] <= rank_diff + 100)
            ]

        if not similar_quality_matches.empty:
            average_throw_ins = similar_quality_matches['throws'].mean()
        else:
            average_throw_ins = np.nan  # Handle cases where no similar quality matches found

        # Store the calculated average throw-ins
        average_throw_ins_list.append(average_throw_ins)

    # Add the average throw-ins as a new column in the DataFrame
    df['avg_TI_adj_elo_diff'] = average_throw_ins_list

    return df


def calculate_avg_throw_ins_adj_opp_poss(df):
    """
    Calculate the average throw-ins adjusted by opponent possession using only past data.

    Args:
        df: The DataFrame containing match data.

    Returns:
        The DataFrame with the new column for average throw-ins adjusted by opponent possession.
    """
    # Define possession buckets
    possession_buckets = [
        (65, 100),
        (58, 64),
        (53, 57),
        (48, 52),
        (43, 47),
        (36, 42),
        (0, 35)
    ]

    # Ensure data is sorted by datetime
    df = df.sort_values(by='datetime').reset_index(drop=True)
    # Initialize list to store average throw-ins adjusted by opponent possession
    avg_throw_ins_adj_opp_poss_list = []

    # Iterate over each row in the DataFrame
    for i in range(len(df)):
        current_opp_poss = df.loc[i, 'avg_opp_possession']
        current_datetime = df.loc[i, 'datetime']
        current_game = df.loc[i, 'game_id']
        # Filter previous matches before current datetime
        previous_matches = df.loc[df['datetime'] < current_datetime]
        previous_matches = previous_matches[previous_matches['game_id'] != current_game]
        # Determine opponent possession bucket
        for start, end in possession_buckets:
            if start <= current_opp_poss <= end:
                possession_bucket_name = f'possession_{start}_{end}'
                break

        # Calculate average throw-ins adjusted by opponent possession bucket
        similar_possession_matches = previous_matches[
            (previous_matches['avg_opp_possession'] >= start) &
            (previous_matches['avg_opp_possession'] <= end)
            ]

        if not similar_possession_matches.empty:
            avg_throw_ins_adj_opp_poss = similar_possession_matches['throws'].mean()
        else:
            avg_throw_ins_adj_opp_poss = np.nan  # Handle cases where no similar possession matches found

        # Store the calculated average throw-ins adjusted by opponent possession
        avg_throw_ins_adj_opp_poss_list.append(avg_throw_ins_adj_opp_poss)

    # Add avg_throw_ins_adj_opp_poss as a new column in the DataFrame
    df['avg_throw_ins_adj_opp_poss'] = avg_throw_ins_adj_opp_poss_list

    return df


def calculate_avg_tackles_adj_opp_poss(df):
    """
    Calculate the average tackles adjusted by opponent possession using only past data.

    Args:
        df: The DataFrame containing match data.

    Returns:
        The DataFrame with the new column for average tackles adjusted by opponent possession.
    """
    # Define possession buckets
    possession_buckets = [
        (65, 100),
        (58, 64),
        (53, 57),
        (48, 52),
        (43, 47),
        (36, 42),
        (0, 35)
    ]

    # Ensure data is sorted by datetime
    df = df.sort_values(by='datetime').reset_index(drop=True)

    # Initialize list to store average tackles adjusted by opponent possession
    avg_tackles_adj_opp_poss_list = []

    # Iterate over each row in the DataFrame
    for i in range(len(df)):
        current_opp_poss = df.loc[i, 'opp_avg_possession']
        current_datetime = df.loc[i, 'datetime']
        current_game = df.loc[i, 'game_id']
        # Filter previous matches before current datetime
        previous_matches = df.loc[df['datetime'] < current_datetime]
        previous_matches = previous_matches[previous_matches['game_id'] != current_game]
        # Determine opponent possession bucket
        for start, end in possession_buckets:
            if start <= current_opp_poss <= end:
                possession_bucket_name = f'possession_{start}_{end}'
                break

        # Calculate average tackles adjusted by opponent possession bucket
        similar_possession_matches = previous_matches[
            (previous_matches['opp_avg_possession'] >= start) &
            (previous_matches['opp_avg_possession'] <= end)
            ]

        if not similar_possession_matches.empty:
            avg_tackles_adj_opp_poss = similar_possession_matches['total_tackles'].mean()
        else:
            avg_tackles_adj_opp_poss = np.nan  # Handle cases where no similar possession matches found

        # Store the calculated average tackles adjusted by opponent possession
        avg_tackles_adj_opp_poss_list.append(avg_tackles_adj_opp_poss)

    # Add avg_tackles_adj_opp_poss as a new column in the DataFrame
    df['avg_tackles_adj_opp_poss'] = avg_tackles_adj_opp_poss_list

    return df


def feature_engineering(df, stats_cols):

    # ELO
    latest_results = add_latest_results(df)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date'] = df['datetime'].dt.date
    df = df.sort_values(by='date').reset_index(drop=True)
    latest_results = latest_results.sort_values(by='date').reset_index(drop=True)
    df, elo_ratings = calculate_elo(latest_results, df)
    # df['team_elo'] = df['team_elo'].fillna(1500)
    # df['opp_elo'] = df['opp_elo'].fillna(1500)
    df['elo_diff'] = df['team_elo'] - df['opp_elo']

    # Averages
    df = calculate_averages(df, stats_cols)
    df = calculate_rolling_averages(df, stats_cols)
    df = calculate_average_throw_ins_adjusted_for_opp_quality(df)
    df = calculate_average_throw_ins_adjusted_for_rank_diff(df)
    df = calculate_avg_throw_ins_adj_opp_poss(df)

    # Opponent stats
    df = add_opponent_stats(df, stats_cols)

    # df = calculate_avg_throw_ins_adj_opp_pass(df)
    # df = calculate_average_tackles_adjusted_for_opp_quality(df)
    # df = calculate_avg_tackles_adj_opp_poss(df)
    # df = calculate_h2h(df, stats_cols)
    # df = calculate_div_averages(df, stats_cols)
    df.to_csv('./prem/data/preprocessed/prem_preprocessed_master.csv', index=False)
    return df, elo_ratings
