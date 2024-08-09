import os
import pandas as pd
from src.scraper.match_data import copa_single_match, euro_single_match, scrape_single_match


all_urls = []

# ---- SCRAPE ALL MATCHES ----

for file in os.listdir('./data/urls'):
    file_path = os.path.join('./data/urls', file)
    if os.path.isfile(file_path):
        with open(file_path, 'r') as f:
            urls = f.readlines()
            all_urls.extend([url.strip() for url in urls])

# Remove leading and trailing whitespace, and newline characters
all_urls = [url.strip() for url in all_urls]


# # ---- SCRAPE NEW MATCHES ----
# master_data = pd.read_csv('data/raw_master.csv')
# game_id = master_data['game_id'].max() + 1
# new_urls_file = './data/new_urls/new_copa_2024_urls.txt'
# with open(new_urls_file, 'r') as f:
#     urls = f.readlines()
#     all_urls.extend([url.strip() for url in urls])
# all_urls = [url.strip() for url in all_urls]

dfs = []
game_id = 1001
for url in all_urls:
    try:
        df = scrape_single_match(url)
        df['game_id'] = game_id
        game_id += 1
        dfs.append(df)
    except Exception as e:
        print(f"Error scraping data from {url}: {e}")

# Step 3: Concatenate the dataframes into a single dataframe
final_df = pd.concat(dfs, ignore_index=True)
# previous_df = pd.read_csv('data/raw_master.csv')
# final_df = pd.concat([previous_df, final_df], axis=0)

# Print or save the final dataframe
print(final_df)
# print duplicates
print(final_df[final_df.duplicated()])
final_df.to_csv('data/int_raw_master.csv', index=False)  # Uncomment this line to save the dataframe to a CSV file

# make new col, compeition + year  = tourney_id
final_df['tourney_id'] = final_df['competition'] + '_' + final_df['year'].astype(str)