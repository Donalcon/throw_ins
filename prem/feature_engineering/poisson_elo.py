import pandas as pd
import numpy as np

# Load your dataset
# latest_results = pd.read_csv('path_to_your_file.csv')

# Sample DataFrame creation for demonstration
latest_results = pd.DataFrame({
    'HomeTeam': ['TeamA', 'TeamB', 'TeamC'],
    'AwayTeam': ['TeamD', 'TeamE', 'TeamF'],
    'FTHG': [3, 1, 2],  # Full-Time Home Goals
    'FTAG': [1, 1, 1],  # Full-Time Away Goals
    'DateTime': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03'])
})

# Initialize Elo ratings
elo_ratings = {team: 1500 for team in pd.concat([latest_results['HomeTeam'], latest_results['AwayTeam']]).unique()}

# Home Field Advantage (HFA) initialization
HFA = 100  # You can start with an initial value


# Function to calculate expected outcome
def expected_outcome(elo_diff):
    return 1 / (1 + 10 ** (-elo_diff / 400))


# Update Elo ratings after each match
k = 20  # K-factor as per your description

# Track Tilt
tilt = {team: 1.0 for team in elo_ratings}

for idx, row in latest_results.iterrows():
    home_team = row['HomeTeam']
    away_team = row['AwayTeam']
    home_goals = row['FTHG']
    away_goals = row['FTAG']

    # Calculate goal difference
    goal_diff = abs(home_goals - away_goals)

    # Calculate Elo difference (including HFA)
    elo_diff = (elo_ratings[home_team] + HFA) - elo_ratings[away_team]

    # Expected results
    E_home = expected_outcome(elo_diff)
    E_away = 1 - E_home

    # Actual results
    if home_goals > away_goals:
        R_home = 1
        R_away = 0
    elif home_goals < away_goals:
        R_home = 0
        R_away = 1
    else:
        R_home = 0.5
        R_away = 0.5

    # Weighting by goal difference
    if goal_diff > 0:
        delta_elo_margin = k * (R_home - E_home) * np.sqrt(goal_diff)
    else:
        delta_elo_margin = 0

    # Update Elo ratings
    elo_ratings[home_team] += delta_elo_margin
    elo_ratings[away_team] -= delta_elo_margin

    # Update Tilt
    game_total_goals = home_goals + away_goals
    expected_goals = 2.5  # A typical expected goal total, can be adjusted
    tilt[home_team] = 0.98 * tilt[home_team] + 0.02 * game_total_goals / tilt[away_team] / expected_goals
    tilt[away_team] = 0.98 * tilt[away_team] + 0.02 * game_total_goals / tilt[home_team] / expected_goals

    # Adjust Home Field Advantage (HFA)
    HFA += delta_elo_margin * 0.075

# Print final Elo ratings and Tilt
print("Final Elo Ratings:", elo_ratings)
print("Final Tilt:", tilt)
