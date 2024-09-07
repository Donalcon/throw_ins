import logging
from prem.utils.fixed import stats_cols, cols_not_for_modelling, categorical_columns
import pandas as pd

logger = logging.getLogger(__name__)

# Example of how class_mapping should be structured (use the same mapping from training)
class_mapping = {
    0: 'low_tail',
    1: 9, 2: 10, 3: 11, 4: 12, 5: 13, 6: 14, 7: 15, 8: 16, 9: 17, 10: 18, 11: 19, 12: 20,
    13: 21, 14: 22, 15: 23, 16: 24, 17: 25, 18: 26, 19: 27, 20: 28, 21: 29, 22: 'high_tail'
}


def predictor(prediction_df, next_games, model):
    # Final Processing
    prediction_df = prediction_df.drop(columns=cols_not_for_modelling, errors='ignore')
    continuous_columns = prediction_df.columns.difference(categorical_columns + ['datetime'])
    # Convert categorical columns to categorical type
    for col in categorical_columns:
        prediction_df[col] = prediction_df[col].astype('category')
    # One-hot encode the categorical features (if not using XGBoost's built-in categorical support)
    full_df_categorical = pd.get_dummies(prediction_df[categorical_columns], drop_first=True)
    full_df_continuous = prediction_df[continuous_columns]
    # Combine the one-hot encoded categorical features with the continuous features
    prediction_df = pd.concat([full_df_categorical, full_df_continuous], axis=1)
    # Remove all rows from master data that are not in todays_df, use game_id to identify
    prediction_df = prediction_df[prediction_df['game_id'].isin(next_games['game_id'])]
    # drop game_id
    prediction_df.drop(['game_id', 'throws'], axis=1, inplace=True)

    # CHECK
    logger.info("COLUMNS NOT IN CORRECT DTYPE:", prediction_df.select_dtypes(exclude=['int', 'float', 'bool']).columns)

    # Predictions
    throw_features = model.get_booster().feature_names
    # Check if all expected features are present and match
    missing_from_model = [f for f in throw_features if f not in prediction_df.columns]
    extra_in_model = [f for f in prediction_df.columns if f not in throw_features]

    logger.info("Features expected by model and missing in data:", missing_from_model)
    logger.info("Extra features in data not expected by model:", extra_in_model)

    throw_df = prediction_df[throw_features]
    print("Columns with nan values:", throw_df.columns[throw_df.isna().any()].tolist())

    # Get the predicted classes
    predicted_classes = model.predict(throw_df)

    # Map predicted classes back to original throw values (including 'low_tail' and 'high_tail')
    predicted_throws = [class_mapping[pred_class] for pred_class in predicted_classes]

    next_games['pred_throws'] = predicted_throws
    prediction = next_games[['team', 'opp', 'datetime', 'pred_throws']]

    return prediction
