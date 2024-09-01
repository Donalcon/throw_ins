import pandas as pd
import numpy as np


# Function to calculate the expected outcome based on the Elo difference
def expected_outcome(elo_diff):
    return 1 / (1 + 10 ** (-elo_diff / 400))


def calculate_elo(latest_results, df, k=20, initial_elo=1500, HFA_initial=100):
    # Initialize Elo ratings in a dictionary
    elo_ratings = {}
    team_first_appearance = {}

    # Initialize Home Field Advantage (HFA)
    HFA = HFA_initial

    # List to store updated results with Elo ratings
    updated_results = []

    # Iterate over the latest_results DataFrame row by row
    for idx, row in latest_results.iterrows():
        home_team = row['HomeTeam']
        away_team = row['AwayTeam']
        home_goals = row['FTHG']
        away_goals = row['FTAG']
        match_date = row['DateTime']

        # Check and initialize Elo ratings for home and away teams
        for team in [home_team, away_team]:
            if team not in elo_ratings:
                # Check if this is the first appearance in the season
                if team not in team_first_appearance:
                    team_first_appearance[team] = match_date

                # Determine Elo rating for new team based on the 18th ranked team
                if len(elo_ratings) >= 18:
                    sorted_elo = sorted(elo_ratings.values(), reverse=True)
                    team_elo = sorted_elo[17]  # 18th ranked team
                else:
                    team_elo = min(elo_ratings.values(), default=initial_elo)

                elo_ratings[team] = team_elo

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

    # Convert the updated results back to a DataFrame
    updated_results_df = pd.DataFrame(updated_results)

    # First merge: team = HomeTeam, opp = AwayTeam
    df = df.merge(
        updated_results_df[['DateTime', 'HomeTeam', 'AwayTeam', 'home_elo', 'away_elo']],
        how='left',
        left_on=['datetime', 'team', 'opp'],
        right_on=['DateTime', 'HomeTeam', 'AwayTeam']
    )

    # Rename the columns from the first merge to avoid conflicts in the second merge
    df.rename(columns={'home_elo': 'team_elo_home_perspective', 'away_elo': 'opp_elo_home_perspective'}, inplace=True)

    # Second merge: team = AwayTeam, opp = HomeTeam
    df = df.merge(
        updated_results_df[['DateTime', 'HomeTeam', 'AwayTeam', 'home_elo', 'away_elo']],
        how='left',
        left_on=['datetime', 'team', 'opp'],
        right_on=['DateTime', 'AwayTeam', 'HomeTeam']
    )

    # Rename the columns from the second merge to distinguish them
    df.rename(columns={'home_elo': 'opp_elo_away_perspective', 'away_elo': 'team_elo_away_perspective'}, inplace=True)

    # Combine the two perspectives to create the final 'team_elo_before' and 'opp_elo_before'
    df['team_elo'] = df['team_elo_home_perspective'].combine_first(df['team_elo_away_perspective'])
    df['opp_elo'] = df['opp_elo_home_perspective'].combine_first(df['opp_elo_away_perspective'])

    # Drop the intermediate columns used for merging
    df.drop(columns=['team_elo_home_perspective', 'opp_elo_home_perspective', 'team_elo_away_perspective',
                     'opp_elo_away_perspective', 'DateTime_x', 'HomeTeam_x', 'AwayTeam_x', 'DateTime_y', 'HomeTeam_y',
                     'AwayTeam_y'], inplace=True)

    return df, elo_ratings
