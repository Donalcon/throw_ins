import pandas as pd

# HIST RESULTS
prem_results = pd.read_csv('data/prem/raw/prem_results.csv', encoding='ISO-8859-1')
# make datetime column datetime onject
prem_results['DateTime'] = pd.to_datetime(prem_results['DateTime'])
# filter to rows that took place from 2019 onwards
prem_results = prem_results[prem_results['DateTime'].dt.year >= 2019]
# filter to only cols: Season, HomeTeam, AwayTeam, FTHG, FTAG, FTR, DateTime
prem_results = prem_results[['Season', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'DateTime']]
# save to csv
prem_results.to_csv('data/prem/raw/prem_results.csv', index=False)

# LATEST RESULTS
latest_results = pd.read_csv('data/prem/raw/prem_raw_master.csv')
latest_results = latest_results[latest_results['datetime'] >= '2022-04-10']
# RENAME COLS, team to HomeTeam, opp to AwayTeam, goals to FTHG, opp_goals to FTAG, datetime to DateTime
latest_results.rename(columns={'team': 'HomeTeam', 'opp': 'AwayTeam', 'team_goals': 'FTHG', 'opp_goals': 'FTAG', 'datetime': 'DateTime'}, inplace=True)
# drop all other cols except for the above renamed
latest_results = latest_results[['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'DateTime', 'game_id']]
# drop the second instance of the same game_id
latest_results = latest_results.drop_duplicates(subset='game_id')
# drop all rows before 10th of april 2022
latest_results['DateTime'] = pd.to_datetime(latest_results['DateTime'])
# order by datetime
latest_results = latest_results.sort_values('DateTime')
# drop season for prem_results
prem_results.drop(columns=['Season'], inplace=True)
# drop all rows in prem_results with date = or greater than '2022-04-10'
prem_results = prem_results[prem_results['DateTime'] < '2022-04-10']

#concat both dfs
all_results = pd.concat([prem_results, latest_results], ignore_index=True)
# save as master_results
all_results.to_csv('data/prem/raw/prem_results_master.csv', index=False)