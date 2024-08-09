import os
import pandas as pd
from src.scraper.match_data import parallel_scrape


def international_game_scraper(scrape_type, new_urls_file=None, save_as=None, all_urls_list=None):
    all_urls = []
    dfs = []
    game_id = 1001

    if scrape_type == 'full':
        for file in os.listdir('./data/urls'):
            file_path = os.path.join('./data/urls', file)
            if os.path.isfile(file_path):
                with open(file_path, 'r') as f:
                    urls = f.readlines()
                    all_urls.extend([url.strip() for url in urls])
        all_urls = [url.strip() for url in all_urls]

    elif scrape_type == 'new':
        new_urls_path = f'./data/urls/{new_urls_file}.txt'
        with open(new_urls_path, 'r') as f:
            urls = f.readlines()
            all_urls.extend([url.strip() for url in urls])
        all_urls = [url.strip() for url in all_urls]
        master_data = pd.read_csv('data/raw_master.csv')
        game_id = master_data['game_id'].max() + 1

    elif scrape_type == 'list':
        all_urls = all_urls_list

    results = parallel_scrape(all_urls)

    for result in results:
        result['game_id'] = game_id
        game_id += 1
        dfs.append(result)

    final_df = pd.concat(dfs, ignore_index=True)
    if scrape_type == 'new':
        previous_df = pd.read_csv('data/raw/raw_master.csv')
        final_df = pd.concat([previous_df, final_df], axis=0)
        final_df = final_df.drop_duplicates()

    if not save_as:
        final_df.to_csv('data/raw/int_raw_master.csv', index=False)
    else:
        final_df.to_csv(f'data/raw/{save_as}.csv', index=False)
    return final_df
