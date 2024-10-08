import pandas as pd
import re
import pickle


def cleaner(raw_data):
    raw_data = raw_data.drop(columns=['expected_goals_(xg)', 'xg_open_play', 'xg_set_play', 'non-penalty_xg',
                                      'xg_on_target_(xgot)', 'conc_expected_goals_(xg)', 'conc_xg_open_play',
                                      'conc_xg_set_play', 'conc_non-penalty_xg', 'conc_xg_on_target_(xgot)',
                                      'conc_touches_in_opposition_box','touches_in_opposition_box',
    ])
    raw_data.columns = raw_data.columns.str.strip()
    raw_data = raw_data.drop_duplicates()
    raw_data['datetime'] = pd.to_datetime(raw_data['datetime'])
    raw_data = raw_data.sort_values('datetime')
    raw_data['year'] = raw_data['datetime'].dt.year
    raw_data['tourney_id'] = raw_data['competition'] + '_' + raw_data['year'].astype(str)
    raw_data['ranking'] = raw_data['ranking'].astype(int)
    raw_data['total_tackles'] = raw_data['tackles_won'] / (raw_data['tackles_won_pc'] / 100)
    raw_data['datetime'] = pd.to_datetime(raw_data['datetime'])
    raw_data['tournament'] = 0
    raw_data['division'] = 0
    raw_data['knockout'] = 0
    # clean competition column
    for index, row in raw_data.iterrows():
        competition = row['competition'].lower()
        if 'round' in competition:
            if 'round of 16' in competition:
                raw_data.at[index, 'round'] = 16
                raw_data.at[index, 'knockout'] = 1
            else:
                match = re.search(r'round (\d+)', competition)
                if match:
                    raw_data.at[index, 'round'] = int(match.group(1))
                    raw_data.at[index, 'knockout'] = 1

        # Check for semi-final, quarter-final, and final
        if 'semi-final' in competition:
            raw_data.at[index, 'round'] = 'SF'
            raw_data.at[index, 'knockout'] = 1
        elif 'quarter-final' in competition:
            raw_data.at[index, 'round'] = 'QF'
            raw_data.at[index, 'knockout'] = 1
        elif 'final' in competition and 'semi' not in competition and 'quarter' not in competition:
            raw_data.at[index, 'round'] = 'F'
            raw_data.at[index, 'knockout'] = 1
        if 'friendly' in competition:
            raw_data.at[index, 'competition'] = 'friendly'
            raw_data.at[index, 'division'] = 1
            raw_data.at[index, 'round'] = 0
        elif 'qualification' in competition:
            raw_data.at[index, 'competition'] = 'qualifier'
            raw_data.at[index, 'division'] = 2
        elif 'qualifier' in competition:
            raw_data.at[index, 'competition'] = 'qualifier'
            raw_data.at[index, 'division'] = 2
        elif 'nations league' in competition:
            raw_data.at[index, 'competition'] = 'nations league'
            raw_data.at[index, 'division'] = 3
        elif 'euros' in competition:
            raw_data.at[index, 'competition'] = 'euros'
            raw_data.at[index, 'tournament'] = 1
            raw_data.at[index, 'division'] = 4
        elif 'euro' in competition:
            raw_data.at[index, 'competition'] = 'euros'
            raw_data.at[index, 'tournament'] = 1
            raw_data.at[index, 'division'] = 4
        elif 'copa america' in competition:
            raw_data.at[index, 'competition'] = 'copa america'
            raw_data.at[index, 'tournament'] = 1
            raw_data.at[index, 'division'] = 5
        elif 'world cup' in competition:
            raw_data.at[index, 'competition'] = 'world cup'
            raw_data.at[index, 'tournament'] = 1
            raw_data.at[index, 'division'] = 6

    # rename own_half to passes_own_half
    raw_data.rename(columns={'own_half': 'passes_own_half'}, inplace=True)
    raw_data.rename(columns={'opposition_half': 'passes_opp_half'}, inplace=True)
    raw_data.rename(columns={'conc_own_half': 'conc_passes_own_half'}, inplace=True)
    raw_data.rename(columns={'conc_opposition_half': 'conc_passes_opp_half'}, inplace=True)

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
    with open('data/fixed/team_id_mapping.pkl', 'wb') as f:
        pickle.dump(team_id_mapping, f)
    raw_data['team_id'] = raw_data['team'].map(team_id_mapping)
    raw_data['opp_id'] = raw_data['opp'].map(team_id_mapping)
    # Create a mapping of referee to referee_id
    raw_data['referee'] = raw_data['referee'].replace({
        'Fernando Rapallini': 'Fernando Andrés Rapallini',
        'Wilton Sampaio': 'Wilton Pereira Sampaio',
        'César Arturo Ramos Palazuelos': 'Cesar Ramos',
        'Iván Arcides Barton Cisneros': 'Ivan Arcides Barton Cisneros',
        'Jesús Valenzuela Sáez': 'Jesus Valenzuela',
        'Slavko Vincic': 'Slavko Vinčić',
        'Clement Turpin': 'Clément Turpin',
        'Istvan Kovacs': 'István Kovács',
        'Tamás Bognár': 'Tamas Bognar',
        'Halil Umut Meler': 'Halil Meler',
        'Espen Eskås': 'Espen Eskaas'
    })
    referees = pd.unique(raw_data['referee'])
    referee_id_mapping = {referee: idx for idx, referee in enumerate(referees, start=1)}

    # Map the referee_id back to the DataFrame
    raw_data['referee_id'] = raw_data['referee'].map(referee_id_mapping)

    # Save the dictionary to a file
    with open('data/fixed/referee_id_mapping.pkl', 'wb') as f:
        pickle.dump(referee_id_mapping, f)

    return raw_data


stats_cols = [
    'possession',
    'opp_possession',
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
    'venue_href',
    'latitude',
    'longitude',
    'stadium',
    'attendance',
    'referee',
    'possession',
    'opp_possession',
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
    'conc_ground_duels_won',
    'conc_ground_duels_won_pc',
    'conc_aerial_duels_won',
    'conc_aerial_duels_won_pc',
    'conc_successful_dribbles',
    'conc_successful_dribbles_pc',
    'conc_total_tackles',
    'tourney_id',
    'datetime',
    'conc_throws',
    'opp',
    'team',
    'competition',
]