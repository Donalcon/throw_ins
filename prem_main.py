import pandas as pd
import logging
import time
import joblib
import numpy as np
from prem.feature_engineering.feat_eng_pred import prediction_feature_engineering
from prem.scraper.fotmob.prem_url_scraper import prem_url_scraper
from prem.scraper.fotmob.prem_match_scraper import prem_game_scraper
from prem.feature_engineering.simple_fe import feature_engineering
from prem.feature_engineering.area_of_interest.area_of_interest import process_images_to_dataframe
from prem.feature_engineering.area_of_interest.heatmap import process_heatmap_row
from prem.prediction.pred_processing import pred_scraper, pred_processor
from prem.prediction.prediction import predictor
from prem.preprocessing.prem_preprocessor import prem_preprocessor
from prem.scraper.who_scored.aoi_url_scraper import scrape_ws_urls
from prem.scraper.who_scored.area_of_interest_scraper import parallel_scrape
from prem.utils.helper import log_missing_data
from src.weather_engineering.weather_engineering import weather_engineering
from prem.models.throws import throws_regressor_model
from prem.models.classification_model import throws_classification_model
from prem.utils.cleaner import training_cleaner
from prem.utils.fixed import stats_cols

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
gameweek = 3
new_url_scrape_page = gameweek - 2

# # 1. Scraping
# # ------------------------------------------------
# logger.info("Starting Scraping Process.")
# # FOTMOB
# new_fm_urls = prem_url_scraper(2024, 2025, new_url_scrape_page)
# raw_data = prem_game_scraper(scrape_type='new', new_urls=new_fm_urls)
# # WHO SCORED
# ws_urls = scrape_ws_urls(gameweek, file_name="24-25_who_scored_urls.txt")
# parallel_scrape(ws_urls, filepath='prem/data/images/new/', hmap_filepath='prem/data/heatmaps/new/', max_workers=4)
# ws_df = process_images_to_dataframe(directory_path='prem/data/images/new/')
# # HEATMAPS
# ws_df[['total_touches', 'wide_touches', 'wide_touches_pc']] = ws_df.apply(process_heatmap_row, axis=1)
# for col in ws_df.columns:
#     ws_df[col] = ws_df[col].replace('None', np.nan)
#     nans = ws_df[col].isna().sum()
#     if nans > 0:
#         logger.warning(f"Column: {col}, nans: {nans}")
# logger.info("Finished URL scraping.")
# ws_df.to_csv('./prem/data/processed/area_of_interest_processed.csv', index=False)

# Load existing raw match data from a CSV file
logger.info("Loading raw match data from CSV.")
raw_data = pd.read_csv('./prem/data/raw/prem_raw_master.csv')
ws_df = pd.read_csv('./prem/data/processed/area_of_interest_processed.csv')
logger.info(f"Loaded raw match data with {raw_data.shape[0]} rows and {raw_data.shape[1]} columns.")


# 2. Cleaning - Preprocessing - Feature Engineering
# ------------------------------------------------
logger.info("Starting data preprocessing.")
start_time = time.time()
pre_processed_data = prem_preprocessor(raw_data, ws_df)
logger.info(f"Data preprocessing completed, new shape: {raw_data.shape[0]} rows and {raw_data.shape[1]} columns.")
# log_missing_data(preprocessed_data)
processed_data, elo_ratings = feature_engineering(pre_processed_data, stats_cols)

# logger.info("Starting weather feature engineering.")
# processed_data = weather_engineering(cleaned_data, perspective='forecast')
# logger.info("Weather feature engineering completed.")


# load in processed data
# preprocessed_data = pd.read_csv('./prem/data/preprocessed/preprocessed_master.csv')
processed_data[stats_cols] = processed_data[stats_cols].apply(pd.to_numeric, errors='coerce')
# Print the number of NaN values in every column for quality control
logger.info("Checking for NaN values in processed data.")
for col in processed_data.columns:
    nans = processed_data[col].isna().sum()
    if nans > 0:
        logger.warning(f"Column: {col}, nans: {nans}")
    else:
        logger.info(f"Column: {col}, nans: 0")
processed_data = processed_data.dropna()
processed_data.to_csv('./prem/data/processed/processed_master_throws.csv', index=False)

logger.info(f"Data preprocessing and feature engineering took {time.time() - start_time:.2f} seconds.")
logger.info(f"New shape: {processed_data.shape[0]} rows and {processed_data.shape[1]} columns.")

# 3. Modelling
# ------------------------------------------------

# processed_data = pd.read_csv('./prem/data/processed/processed_master_throws.csv')
logger.info(f"Training on processed data, {processed_data.shape[0]} rows and {processed_data.shape[1]} columns.")
# print unique values of throws and their counts
unique_values_counts = processed_data['throws'].value_counts()

logger.info("Starting Classification model training.")
start_time = time.time()
prem_model_class = throws_classification_model(processed_data)
logger.info(f"Classification Model training completed in {time.time() - start_time:.2f} seconds.")

logger.info("Starting Regressor model training.")
start_time = time.time()
prem_model_reg = throws_regressor_model(processed_data)
logger.info(f"Regressor Model training completed in {time.time() - start_time:.2f} seconds.")

# load './prem/data/models/Prem_throws_classification_smote_sample_weights.joblib'
# prem_model_class = joblib.load('./prem/data/models/Prem_throws_classification_smote_sample_weights.joblib')
# prem_model_reg = joblib.load('prem/data/models/Prem_throws_xgbreg.joblib')


# 4. Prediction
# ------------------------------------------------
# Scrape new games
next_games = pred_scraper(gameweek)
logger.info(f"Scraped {len(next_games)} URLs for future matches.")
# Clean & Process
prediction_df = pred_processor(next_games, processed_data)
logger.info(f"Cleaned and processed prediction set: {prediction_df.shape[1]} cols, {prediction_df.shape[0]} rows.")
# Feature Engineering
master_data = prediction_feature_engineering(prediction_df, stats_cols, elo_ratings)
logger.info(f"Feature engineering completed, prediction set: {master_data.shape[1]} cols, {master_data.shape[0]} rows.")
# reg_prediction = predictor(prediction_df, next_games, prem_model_reg)
class_prediction = predictor(prediction_df, next_games, prem_model_class)


# 5. Betting Opportunities
# ------------------------------------------------
# Placeholder section for calculating and identifying betting opportunities
# Scrape odds from a betting website like Bet365
# Calculate expected value (EV) for each betting opportunity
# Print betting opportunities that have a high enough margin to be worth pursuing

logger.info("Pipeline execution completed.")
