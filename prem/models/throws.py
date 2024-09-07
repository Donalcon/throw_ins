import optuna
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import xgboost as xgb
import shap
import matplotlib
import matplotlib.pyplot as plt
import joblib
import logging
from imblearn.over_sampling import SMOTE
from prem.utils.fixed import cols_not_for_modelling
from src.models.model_cleaner import filter_teams, european_countries
matplotlib.use('Agg')


logger = logging.getLogger(__name__)


def throws_regressor_model(full_df: pd.DataFrame):
    # Drop unnecessary columns
    full_df = full_df.drop(columns=cols_not_for_modelling, errors='ignore')

    # Identify categorical columns
    categorical_columns = ['team_id', 'opp_id']
    continuous_columns = full_df.columns.difference(categorical_columns + ['datetime', 'game_id'])

    # Convert categorical columns to categorical type
    for col in categorical_columns:
        full_df[col] = full_df[col].astype('category')

    # One-hot encode the categorical features (if not using XGBoost's built-in categorical support)
    full_df_categorical = pd.get_dummies(full_df[categorical_columns], drop_first=True)
    full_df_continuous = full_df[continuous_columns]

    # Combine the one-hot encoded categorical features with the continuous features
    full_df = pd.concat([full_df_categorical, full_df_continuous], axis=1)

    # ** Check for and remove duplicate columns **
    full_df = full_df.loc[:, ~full_df.columns.duplicated()]

    # Define feature columns and target column
    feature_columns = full_df.columns.difference(['throws', 'datetime', 'game_id'])
    target_column = 'throws'
    X = full_df[feature_columns]
    y = full_df[target_column]

    # Filter out classes with fewer instances
    value_counts = y.value_counts()
    to_remove = value_counts[value_counts < 5].index
    X_filtered = X[~y.isin(to_remove)]
    y_filtered = y[~y.isin(to_remove)]

    # Dynamically shift class labels to start from 0
    min_label = y_filtered.min()
    y_shifted = y_filtered - min_label

    # Apply SMOTE to balance the dataset
    smote = SMOTE(k_neighbors=1)  # Set the number of neighbors to 1
    X_res, y_res = smote.fit_resample(X_filtered, y_shifted)

    # Split data into training and testing sets using stratified split
    X_train, X_test, y_train, y_test = train_test_split(X_res, y_res, test_size=0.2, random_state=42)

    def objective(trial):
        param = {
            'n_estimators': trial.suggest_int('n_estimators', 100, 400),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1),
            'max_depth': trial.suggest_int('max_depth', 3, 7),
            'gamma': trial.suggest_float('gamma', 0, 0.3),
            'reg_alpha': trial.suggest_float('reg_alpha', 0, 1),
            'reg_lambda': trial.suggest_float('reg_lambda', 1, 2),
            'min_child_weight': trial.suggest_int('min_child_weight', 1, 5),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'objective': 'reg:squarederror',
            'eval_metric': 'rmse'
        }

        model = xgb.XGBRegressor(**param)
        model.set_params(early_stopping_rounds=10)

        # Fit the model
        model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

        # Predict on the test set
        y_pred = model.predict(X_test)

        # Calculate RMSE
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))

        return rmse

    # Run Optuna optimization
    study = optuna.create_study(direction='minimize')
    study.optimize(objective, n_trials=50)

    # Get the best parameters
    best_params = study.best_params
    logger.info(f"Best Parameters: {best_params}")

    # Train the final model using the best parameters
    final_model = xgb.XGBRegressor(**best_params, objective='reg:squarederror')
    final_model.fit(X_train, y_train)

    # Make predictions
    y_pred_train = final_model.predict(X_train)
    y_pred_test = final_model.predict(X_test)

    # Evaluate the model
    train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    train_mae = mean_absolute_error(y_train, y_pred_train)
    test_mae = mean_absolute_error(y_test, y_pred_test)
    train_r2 = r2_score(y_train, y_pred_train)
    test_r2 = r2_score(y_test, y_pred_test)

    logger.info(f"Train RMSE: {train_rmse}")
    logger.info(f"Test RMSE: {test_rmse}")
    logger.info(f"Train MAE: {train_mae}")
    logger.info(f"Test MAE: {test_mae}")
    logger.info(f"Train R^2: {train_r2}")
    logger.info(f"Test R^2: {test_r2}")

    # Feature Importance
    feature_importances = final_model.feature_importances_
    # Sort features by their importance
    sorted_idx = np.argsort(feature_importances)[-10:]  # Gets the indices of the top 10 features
    logger.info("Top 10 Features:")
    for idx in sorted_idx:
        logger.info(X_train.columns[idx])  # Gets the indices of the top 10 features

    # Plot the top 10 feature importances
    plt.figure(figsize=(10, 8))
    plt.barh(X.columns[sorted_idx], feature_importances[sorted_idx])
    plt.xlabel("Feature Importance")
    plt.ylabel("Feature")
    plt.title("Top 10 Feature Importance Using XGBoost")
    plt.tight_layout()  # Adjust the layout to make room for the labels
    plt.show()

    y_pred = final_model.predict(X_test)
    # Plot a histogram of the predicted values
    plt.hist(y_pred, bins=30, alpha=0.5)
    plt.title('Distribution of Predicted Values')
    plt.xlabel('Predicted total score')
    plt.ylabel('Frequency')
    plt.show()

    # Plot the predicted vs. actual values
    plt.scatter(y_test, y_pred, alpha=0.2)
    plt.xlabel('Actual total score')
    plt.ylabel('Predicted total score')
    plt.title('Predicted vs. Actual total score')
    plt.show()

    residuals = y_test - y_pred
    logger.info(f"Standard Deviation of Residuals: {residuals.std()}")

    # Create a SHAP explainer object
    explainer = shap.Explainer(final_model)

    # Calculate SHAP values for all instances in the training data
    shap_values = explainer(X_train)

    # Summary plot (for regression or classification)
    shap.summary_plot(shap_values, X_train)
    plt.show()

    # Save the model
    joblib.dump(final_model, './prem/data/models/Prem_throws_xgbreg.joblib')
    return final_model
