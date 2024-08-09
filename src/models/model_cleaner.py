import re


def add_missing_team_id_columns(df, total_teams=101):
    # Extract existing team_id column numbers
    existing_team_ids = [int(re.findall(r'\d+', col)[0]) for col in df.columns if col.startswith('team_id_')]

    # Identify the missing team_id numbers
    all_team_ids = set(range(1, total_teams + 1))
    missing_team_ids = all_team_ids - set(existing_team_ids)

    # Add missing team_id columns with placeholder value 0
    for missing_id in missing_team_ids:
        df[f'team_id_{missing_id}'] = 0

    # Ensure the columns are sorted in numerical order
    df = df.sort_index(axis=1)

    return df


def add_missing_opp_id_columns(df, total_opps=101):
    # Extract existing team_id column numbers
    existing_opp_ids = [int(re.findall(r'\d+', col)[0]) for col in df.columns if col.startswith('opp_id_')]

    # Identify the missing team_id numbers
    all_opp_ids = set(range(1, total_opps + 1))
    missing_opp_ids = all_opp_ids - set(existing_opp_ids)

    # Add missing team_id columns with placeholder value 0
    for missing_id in missing_opp_ids:
        df[f'opp_id_{missing_id}'] = 0

    # Ensure the columns are sorted in numerical order
    df = df.sort_index(axis=1)

    return df


def filter_teams(df, countries):
    return df[df['team'].isin(countries)]


european_countries = [
    'Albania', 'Andorra', 'Armenia', 'Austria', 'Azerbaijan', 'Belarus', 'Belgium', 'Bosnia and Herzegovina',
    'Bulgaria', 'Croatia', 'Cyprus', 'Czech Republic', 'Denmark', 'Estonia', 'Finland', 'France', 'Georgia',
    'Germany', 'Greece', 'Hungary', 'Iceland', 'Ireland', 'Italy', 'Kazakhstan', 'Kosovo', 'Latvia', 'Liechtenstein',
    'Lithuania', 'Luxembourg', 'Malta', 'Moldova', 'Monaco', 'Montenegro', 'Netherlands', 'North Macedonia',
    'Norway', 'Poland', 'Portugal', 'Romania', 'Russia', 'San Marino', 'Serbia', 'Slovakia', 'Slovenia', 'Spain',
    'Sweden', 'Switzerland', 'Turkey', 'Ukraine', 'United Kingdom', 'Wales', 'Scotland', 'Northern Ireland',
    'England', 'Faroe Islands', 'Gibraltar'
]

copa_america_countries = [
    'Argentina', 'Bolivia', 'Brazil', 'Chile', 'Colombia', 'Ecuador', 'Paraguay', 'Peru', 'Uruguay', 'Venezuela',
    'Mexico', 'United States', 'Costa Rica', 'Honduras', 'Panama', 'Canada', 'Jamaica', 'Haiti', 'Trinidad and Tobago'
]
