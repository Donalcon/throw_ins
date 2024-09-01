import pandas as pd
import re
import pickle


def cleaner(raw_data):
    # Drop ranking if its there
    if 'ranking' in raw_data.columns:
        raw_data = raw_data.drop(columns=['ranking', 'opp_ranking'])
        # drop any , from attendance
    if 'attendance' in raw_data.columns:
        raw_data['attendance'] = raw_data['attendance'].str.replace(',', '')
    raw_data[['competition', 'season', 'round']] = raw_data['competition'].apply(lambda x: pd.Series(process_competition(x)))

    # make all cols numeric
    cols_to_numeric = raw_data.columns.difference(
        ['url', 'team', 'opp', 'venue_href', 'stadium', 'referee', 'competition', 'datetime', 'tourney_id', 'season',
         'round'])
    raw_data[cols_to_numeric] = raw_data[cols_to_numeric].apply(pd.to_numeric, errors='coerce')
    raw_data.columns = raw_data.columns.str.strip()
    raw_data = raw_data.drop_duplicates()
    raw_data['datetime'] = pd.to_datetime(raw_data['datetime'])
    raw_data = raw_data.sort_values('datetime')
    raw_data = create_season_column(raw_data)
    raw_data['year'] = raw_data['datetime'].dt.year
    raw_data['tourney_id'] = 'PL_' + raw_data['year'].astype(str)
    raw_data['total_tackles'] = raw_data['tackles_won'] / (raw_data['tackles_won_pc'] / 100)
    raw_data['datetime'] = pd.to_datetime(raw_data['datetime'])
    raw_data['division'] = 'E1'

    # Latitude and Longitude
    raw_data[['latitude', 'longitude']] = raw_data['venue_href'].apply(lambda x: pd.Series(extract_lat_lng(x)))

    # rename own_half to passes_own_half
    raw_data.rename(columns={'own_half': 'passes_own_half'}, inplace=True)
    raw_data.rename(columns={'opposition_half': 'passes_opp_half'}, inplace=True)
    raw_data.rename(columns={'conc_own_half': 'conc_passes_own_half'}, inplace=True)
    raw_data.rename(columns={'conc_opposition_half': 'conc_passes_opp_half'}, inplace=True)
    raw_data.rename(columns={'expected_goal_(xg)': 'xg'}, inplace=True)
    raw_data.rename(columns={'conc_expected_goal_(xg)': 'conc_xg'}, inplace=True)
    raw_data.rename(columns={'xg_on_target_(xgot)': 'xgot'}, inplace=True)
    raw_data.rename(columns={'conc_xg_on_target_(xgot)': 'conc_xgot'}, inplace=True)
    raw_data.rename(columns={'expected_goals_(xg)': 'xg'}, inplace=True)
    raw_data.rename(columns={'conc_expected_goals_(xg)': 'conc_xg'}, inplace=True)
    raw_data.rename(columns={'non-penalty_xg': 'np_xg'}, inplace=True)
    raw_data.rename(columns={'conc_non-penalty_xg': 'conc_np_xg'}, inplace=True)


    # Create a dictionary to store the statistics for each team in each game
    stats_dict = {}

    # Populate the dictionary
    for index, row in raw_data.iterrows():
        game_id = row['game_id']
        team = row['team']
        total_tackles = row['total_tackles']
        passes_own_half = row['passes_own_half']
        passes_opp_half = row['passes_opp_half']

        if game_id not in stats_dict:
            stats_dict[game_id] = {}

        stats_dict[game_id][team] = {
            'total_tackles': total_tackles,
            'passes_own_half': passes_own_half,
            'passes_opp_half': passes_opp_half
        }

    # Function to find the opponent's statistics
    def get_opponent_stats(row):
        game_id = row['game_id']
        team = row['team']
        opponent_stats = {'conc_total_tackles': None, 'conc_passes_own_half': None, 'conc_passes_opp_half': None}

        for opp_team, stats in stats_dict[game_id].items():
            if opp_team != team:
                opponent_stats['conc_total_tackles'] = stats['total_tackles']
                opponent_stats['conc_passes_own_half'] = stats['passes_own_half']
                opponent_stats['conc_passes_opp_half'] = stats['passes_opp_half']

        return pd.Series(opponent_stats)

    # Apply the function to get the opponent's statistics
    raw_data[['conc_total_tackles', 'conc_passes_own_half', 'conc_passes_opp_half']] = raw_data.apply(get_opponent_stats, axis=1)

    teams = pd.unique(raw_data[['team', 'opp']].values.ravel('K'))
    team_id_mapping = {team: idx for idx, team in enumerate(teams, start=1)}
    # Save the dictionary to a file
    with open('data/PREM/fixed/prem_team_id_mapping.pkl', 'wb') as f:
        pickle.dump(team_id_mapping, f)
    raw_data['team_id'] = raw_data['team'].map(team_id_mapping)
    raw_data['opp_id'] = raw_data['opp'].map(team_id_mapping)
    # Create a mapping of referee to referee_id
    # print("Referees:")
    # print(raw_data['referee'].unique())
    raw_data['referee'] = raw_data['referee'].replace({
        'Andy Madley': 'Andrew Madley'})
    referees = pd.unique(raw_data['referee'])
    referee_id_mapping = {referee: idx for idx, referee in enumerate(referees, start=1)}

    # Map the referee_id back to the DataFrame
    raw_data['referee_id'] = raw_data['referee'].map(referee_id_mapping)

    # Save the dictionary to a file
    with open('data/prem/fixed/prem_referee_id_mapping.pkl', 'wb') as f:
        pickle.dump(referee_id_mapping, f)

    return raw_data


def process_competition(comp):
    # Step 1: Extract the season
    season_match = re.search(r'(\d{4}/\d{4})$', comp)
    season = season_match.group(0) if season_match else None

    if season:
        # Remove the season from the string
        comp = comp[:season_match.start()].strip()

    # Step 2: Extract the round number
    round_match = re.search(r'Round\s(\d{1,2})$', comp)
    round_num = round_match.group(1) if round_match else None

    if round_num:
        # Remove 'Round X' from the string
        comp = comp[:round_match.start()].strip()

    return comp, season, round_num


stats_cols = [
    'possession',
    'opp_possession',
    'xg',
    'total_shots',
    'shots_on_target',
    'big_chances',
    'big_chances_missed',
    'accurate_passes',
    'accurate_passes_pc',
    'fouls_committed',
    'corners',
    'shots_off_target',
    'blocked_shots',
    'hit_woodwork',
    'shots_inside_box',
    'shots_outside_box',
    'xg_open_play',
    'xg_set_play',
    'np_xg',
    'xgot',
    'passes',
    'passes_own_half',
    'passes_opp_half',
    'accurate_long_balls',
    'accurate_long_balls_pc',
    'accurate_crosses',
    'accurate_crosses_pc',
    'throws',
    'offsides',
    'yellow_cards',
    'red_cards',
    'tackles_won',
    'tackles_won_pc',
    'interceptions',
    'blocks',
    'clearances',
    'keeper_saves',
    'duels_won',
    'ground_duels_won',
    'ground_duels_won_pc',
    'aerial_duels_won',
    'aerial_duels_won_pc',
    'successful_dribbles',
    'successful_dribbles_pc',
    'total_tackles',
    'conc_xg',
    'conc_total_shots',
    'conc_shots_on_target',
    'conc_big_chances',
    'conc_big_chances_missed',
    'conc_accurate_passes',
    'conc_accurate_passes_pc',
    'conc_fouls_committed',
    'conc_corners',
    'conc_shots_off_target',
    'conc_blocked_shots',
    'conc_hit_woodwork',
    'conc_shots_inside_box',
    'conc_shots_outside_box',
    'conc_xg_open_play',
    'conc_xg_set_play',
    'conc_np_xg',
    'conc_xgot',
    'conc_passes',
    'conc_passes_own_half',
    'conc_passes_opp_half',
    'conc_accurate_long_balls',
    'conc_accurate_long_balls_pc',
    'conc_accurate_crosses',
    'conc_accurate_crosses_pc',
    'conc_throws',
    'conc_offsides',
    'conc_yellow_cards',
    'conc_red_cards',
    'conc_tackles_won',
    'conc_tackles_won_pc',
    'conc_interceptions',
    'conc_blocks',
    'conc_clearances',
    'conc_keeper_saves',
    'conc_duels_won',
    'conc_ground_duels_won',
    'conc_ground_duels_won_pc',
    'conc_aerial_duels_won',
    'conc_aerial_duels_won_pc',
    'conc_successful_dribbles',
    'conc_successful_dribbles_pc',
    'conc_total_tackles'
]

cols_not_for_modelling = [
    'url',
    'latitude',
    'longitude',
    'possession',
    'opp_possession',
    'xg',
    'total_shots',
    'shots_on_target',
    'big_chances',
    'big_chances_missed',
    'accurate_passes',
    'accurate_passes_pc',
    'fouls_committed',
    'corners',
    'shots_off_target',
    'blocked_shots',
    'hit_woodwork',
    'shots_inside_box',
    'shots_outside_box',
    'xg_open_play',
    'xg_set_play',
    'np_xg',
    'xgot',
    'passes',
    'passes_own_half',
    'passes_opp_half',
    'accurate_long_balls',
    'accurate_long_balls_pc',
    'accurate_crosses',
    'accurate_crosses_pc',
    'offsides',
    'yellow_cards',
    'red_cards',
    'tackles_won',
    'tackles_won_pc',
    'interceptions',
    'blocks',
    'clearances',
    'keeper_saves',
    'duels_won',
    'ground_duels_won',
    'ground_duels_won_pc',
    'aerial_duels_won',
    'aerial_duels_won_pc',
    'successful_dribbles',
    'successful_dribbles_pc',
    'total_tackles',
    'throws'
    'conc_xg',
    'conc_total_shots',
    'conc_shots_on_target',
    'conc_big_chances',
    'conc_big_chances_missed',
    'conc_accurate_passes',
    'conc_accurate_passes_pc',
    'conc_fouls_committed',
    'conc_corners',
    'conc_shots_off_target',
    'conc_blocked_shots',
    'conc_hit_woodwork',
    'conc_shots_inside_box',
    'conc_shots_outside_box',
    'conc_xg_open_play',
    'conc_xg_set_play',
    'conc_np_xg',
    'conc_xgot',
    'conc_passes',
    'conc_passes_own_half',
    'conc_passes_opp_half',
    'conc_accurate_long_balls',
    'conc_accurate_long_balls_pc',
    'conc_accurate_crosses',
    'conc_accurate_crosses_pc',
    'conc_offsides',
    'conc_yellow_cards',
    'conc_red_cards',
    'conc_tackles_won',
    'conc_tackles_won_pc',
    'conc_interceptions',
    'conc_blocks',
    'conc_clearances',
    'conc_keeper_saves',
    'conc_duels_won',
    'conc_throws'
    'conc_ground_duels_won',
    'conc_ground_duels_won_pc',
    'conc_aerial_duels_won',
    'conc_aerial_duels_won_pc',
    'conc_successful_dribbles',
    'conc_successful_dribbles_pc',
    'conc_total_tackles'
]


def create_season_column(df, date_col='datetime'):
    # Convert the date column to datetime format if it's not already
    df[date_col] = pd.to_datetime(df[date_col], format='%d/%m/%y')

    # Define the function to determine the season
    def determine_season(date):
        year = date.year
        if date.month >= 8:  # August to December
            season_start = year
            season_end = year + 1
        else:  # January to July
            season_start = year - 1
            season_end = year
        return f"{str(season_start)[-2:]}-{str(season_end)[-2:]}"

    # Apply the function to the DateTime column
    df['season'] = df[date_col].apply(determine_season)

    return df



# Function to extract latitude and longitude from a URL
def extract_lat_lng(url):
    lat_lng_pattern = r"q=([-+]?\d*\.\d+),([-+]?\d*\.\d+)"
    match = re.search(lat_lng_pattern, url)
    if match:
        return match.group(1), match.group(2)
    else:
        return None, None
