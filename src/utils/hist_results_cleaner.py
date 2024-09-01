import pandas as pd

prem_results = pd.read_csv('data/prem/raw/prem_results.csv', encoding='ISO-8859-1')
# make datetime column datetime onject
prem_results['DateTime'] = pd.to_datetime(prem_results['DateTime'])
# filter to rows that took place from 2019 onwards
prem_results = prem_results[prem_results['DateTime'].dt.year >= 2019]
# filter to only cols: Season, HomeTeam, AwayTeam, FTHG, FTAG, FTR, DateTime
prem_results = prem_results[['Season', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'DateTime']]
