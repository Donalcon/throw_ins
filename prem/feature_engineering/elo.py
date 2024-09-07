import pickle
from datetime import timedelta
import datetime
import pandas as pd
import numpy as np
from prem.utils.fixed import team_name_mapping


# Function to calculate the expected outcome based on the Elo difference
def expected_outcome(elo_diff):
    return 1 / (1 + 10 ** (-elo_diff / 400))


def reset_elo_if_inactive(team, match_date, team_last_appearance, elo_ratings, reset_elo=1350, inactivity_period=6):
    """Reset a team's Elo rating if they have been inactive for more than 'inactivity_period' months."""
    if team in team_last_appearance:
        last_appearance = pd.to_datetime(team_last_appearance[team])
        current_match_date = pd.to_datetime(match_date)

        # Check if the team has been inactive for more than the allowed inactivity period
        if (current_match_date - last_appearance) > timedelta(days=inactivity_period * 30):
            elo_ratings[team] = reset_elo
            print(
                f"Reset Elo rating for {team} to {reset_elo} due to inactivity of more than {inactivity_period} months.")


def calculate_elo(latest_results, df, k=20, initial_elo=1500, HFA_initial=100, reset_elo=1350, inactivity_period=6):
    # Initialize Elo ratings and track team's last appearance in a dictionary
    elo_ratings = {}
    team_last_appearance = {}

    # Initialize Home Field Advantage (HFA)
    HFA = HFA_initial

    # List to store updated results with Elo ratings
    updated_results = []

    cutoff_date = datetime.date(2021, 12, 31)

    # Iterate over the latest_results DataFrame row by row
    for idx, row in latest_results.iterrows():
        home_team = row['team']
        away_team = row['opp']
        home_goals = row['team_goals']
        away_goals = row['opp_goals']
        match_date = row['date']

        # Check and initialize Elo ratings for home and away teams
        for team in [home_team, away_team]:
            # Reset Elo rating if the team has been inactive for more than the specified period
            if team in elo_ratings:
                reset_elo_if_inactive(team, match_date, team_last_appearance, elo_ratings, reset_elo, inactivity_period)

            if team not in elo_ratings and match_date < cutoff_date:
                # Initialize every new team with the default Elo rating
                elo_ratings[team] = initial_elo
                team_last_appearance[team] = match_date
            else:
                if team not in elo_ratings:
                    elo_ratings[team] = reset_elo
                    team_last_appearance[team] = match_date

        # Capture the Elo ratings before the game
        home_elo_before = elo_ratings[home_team]
        away_elo_before = elo_ratings[away_team]

        # Calculate the Elo difference including Home Field Advantage (HFA)
        elo_diff = (home_elo_before + HFA) - away_elo_before

        # Calculate expected results
        E_home = expected_outcome(elo_diff)
        E_away = 1 - E_home

        # Determine actual match result
        if home_goals > away_goals:
            R_home = 1
            R_away = 0
        elif home_goals < away_goals:
            R_home = 0
            R_away = 1
        else:
            R_home = 0.5
            R_away = 0.5

        # Calculate Elo change based on result and goal difference
        goal_diff = abs(home_goals - away_goals)
        delta_elo_margin = k * (R_home - E_home) * np.sqrt(goal_diff) if goal_diff > 0 else k * (R_home - E_home)

        # Update Elo ratings after the match
        elo_ratings[home_team] += delta_elo_margin
        elo_ratings[away_team] -= delta_elo_margin

        # Adjust Home Field Advantage (HFA)
        HFA += delta_elo_margin * 0.075

        # Store pre-game Elo ratings in the latest_results DataFrame
        row['home_elo'] = home_elo_before
        row['away_elo'] = away_elo_before
        updated_results.append(row)

        # Update last appearance date for both teams
        team_last_appearance[home_team] = match_date
        team_last_appearance[away_team] = match_date

    # Convert the updated results back to a DataFrame
    updated_results_df = pd.DataFrame(updated_results)

    # Ensure you merge correctly
    # First merge: team = HomeTeam, opp = AwayTeam
    df = df.merge(
        updated_results_df[['date', 'team', 'opp', 'home_elo', 'away_elo']],
        how='left',
        left_on=['date', 'team', 'opp'],
        right_on=['date', 'team', 'opp']
    )

    # Rename the columns from the first merge to avoid conflicts in the second merge
    df.rename(columns={'home_elo': 'team_elo_home_perspective', 'away_elo': 'opp_elo_home_perspective'}, inplace=True)

    # Second merge: team = AwayTeam, opp = HomeTeam
    df = df.merge(
        updated_results_df[['date', 'team', 'opp', 'home_elo', 'away_elo']],
        how='left',
        left_on=['date', 'team', 'opp'],
        right_on=['date', 'opp', 'team']
    )

    # Rename the columns from the second merge to distinguish them
    df.rename(columns={'home_elo': 'opp_elo_away_perspective', 'away_elo': 'team_elo_away_perspective'}, inplace=True)

    # Combine the two perspectives to create the final 'team_elo_before' and 'opp_elo_before'
    df['team_elo'] = df['team_elo_home_perspective'].combine_first(df['team_elo_away_perspective'])
    df['opp_elo'] = df['opp_elo_home_perspective'].combine_first(df['opp_elo_away_perspective'])

    # Rename columns
    df.rename(columns={'team_x': 'team', 'opp_x': 'opp', 'date_x': 'date'}, inplace=True)
    df.drop(columns=['team_elo_home_perspective', 'opp_elo_home_perspective', 'team_elo_away_perspective',
                     'opp_elo_away_perspective', 'team_y', 'opp_y'], inplace=True)

    save_elo_ratings(elo_ratings)

    return df, elo_ratings


def add_latest_results(processed_data):
    latest_results = pd.read_csv('./prem/data/raw/prem_results.csv')
    # print unique values of HomeTeam
    latest_results['HomeTeam'] = latest_results['HomeTeam'].map(team_name_mapping)
    latest_results['AwayTeam'] = latest_results['AwayTeam'].map(team_name_mapping)
    latest_results['DateTime'] = pd.to_datetime(latest_results['DateTime'])
    # rename HomeTeam to team and AwayTeam to opp
    latest_results.rename(columns={'HomeTeam': 'team', 'AwayTeam': 'opp', 'DateTime': 'datetime',
                                   'FTHG': 'team_goals', 'FTAG': 'opp_goals'}, inplace=True)
    mini_df = processed_data[['team', 'opp', 'datetime', 'team_goals', 'opp_goals', 'home_flag']]
    # drop all rows from mini_df where home_flag is 0
    mini_df = mini_df[mini_df['home_flag'] == 1]
    # drop home_flag
    mini_df.drop(columns=['home_flag'], inplace=True)
    # conct dfs
    mini_df = pd.concat([latest_results, mini_df], ignore_index=True)
    # drop duplicates in mini_df
    mini_df['datetime'] = pd.to_datetime(mini_df['datetime'])
    mini_df['date'] = mini_df['datetime'].dt.date
    mini_df.drop(columns=['datetime', 'Season'], inplace=True)
    mini_df.drop_duplicates(inplace=True)
    mini_df.to_csv('./prem/data/raw/prem_results_master.csv', index=False)
    return mini_df


def save_elo_ratings(elo_ratings, filename='./prem/data/fixed/elo_ratings.pkl'):
    """Save Elo ratings to a file using pickle."""
    with open(filename, 'wb') as f:
        pickle.dump(elo_ratings, f)
    print(f"Elo ratings saved to {filename}")


def load_elo_ratings(filename='./prem/data/fixed/elo_ratings.pkl'):
    """Load Elo ratings from a file using pickle."""
    with open(filename, 'rb') as f:
        elo_ratings = pickle.load(f)
    print(f"Elo ratings loaded from {filename}")
    return elo_ratings
