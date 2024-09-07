import pandas as pd
from prem.utils.fixed import columns_to_join, team_name_mapping


def who_scored_data(raw_data, who_scored):

    who_scored['datetime'] = pd.to_datetime(who_scored['datetime'])
    who_scored['date'] = who_scored['datetime'].dt.date
    ws_subset = who_scored[['team', 'opp', 'date'] + columns_to_join]

    ws_subset['team'] = ws_subset['team'].map(team_name_mapping)
    ws_subset['opp'] = ws_subset['opp'].map(team_name_mapping)

    merged_data = pd.merge(raw_data, ws_subset, on=['team', 'opp', 'date'], how='left')

    return merged_data

