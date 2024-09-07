import pandas as pd
from prem.utils.who_scored_cleaner import who_scored_data
from prem.utils.fixed import stats_cols
from prem.utils.cleaner import prediction_cleaner
from prem.scraper.prediction.future_match_scraper import future_match_scraper
from prem.scraper.prediction.future_url_scraper import future_url_scraper


def pred_scraper(gameweek):
    next_games = future_url_scraper(gameweek)
    # 1: Scrape
    dfs = []
    game_id = 100000
    for url in next_games:
        try:
            df = future_match_scraper(url)
            df['game_id'] = game_id
            game_id += 1
            dfs.append(df)
        except Exception as e:
            print(f"Error scraping data from {url}: {e}")

    fut_games = pd.concat(dfs, ignore_index=True)

    return fut_games


def pred_processor(next_games, processed_data):
    next_games = prediction_cleaner(next_games)
    # Join all data
    master_data = pd.concat([processed_data, next_games], axis=0)
    # make all stats_cols float
    master_data[stats_cols] = master_data[stats_cols].astype(float)

    return master_data

