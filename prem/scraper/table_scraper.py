import bs4
import requests
import pandas as pd


url = "https://www.worldfootball.net/schedule/eng-premier-league-2022-2023-spieltag/2/"

response = requests.get(url)
soup = bs4.BeautifulSoup(response.text, 'html.parser')

# Find all tables with the class 'standard_tabelle'
tables = soup.find_all('table', {'class': 'standard_tabelle'})

# Select the second table
results = tables[0]
point_table = tables[1]  # Index 1 gives the second table
# Initialize an empty list to store the rows
results_data = []

# Iterate through each row in the table (ignoring the header row)
for row in results.find_all('tr')[0:]:
    cols = row.find_all('td')
    if len(cols) > 0:
        # Extract the data for each column
        one = cols[0].text.strip()
        two = cols[2].text.strip()
        three = cols[3].text.strip()
        four = cols[4].text.strip()
        five = cols[5].text.strip()
        six = cols[6].text.strip()

        # Append the data as a dictionary
        results_data.append({
            'date': one,
            'home': two,
            'away': four,
            'score': five,
        })

# Convert the list of dictionaries to a DataFrame
df1 = pd.DataFrame(results_data)

# Initialize an empty list to store the rows
point_table_data = []

# Iterate through each row in the table (ignoring the header row)
for row in point_table.find_all('tr')[1:]:
    cols = row.find_all('td')
    if len(cols) > 0:
        # Extract the data for each column
        position = cols[0].text.strip()
        team_name = cols[2].text.strip()
        matches_played = cols[3].text.strip()
        wins = cols[4].text.strip()
        draws = cols[5].text.strip()
        losses = cols[6].text.strip()
        goals = cols[7].text.strip()
        goal_diff = cols[8].text.strip()
        points = cols[9].text.strip()

        # Append the data as a dictionary
        point_table_data.append({
            'position': position,
            'team': team_name,
            'points': points
        })

# Convert the list of dictionaries to a DataFrame
df = pd.DataFrame(point_table_data)