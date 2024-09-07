import optuna
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import xgboost as xgb
import shap
import matplotlib.pyplot as plt
import joblib
from prem.preprocessing.cleaner import cols_not_for_modelling


def simple_throws_model(full_df: pd.DataFrame):
    full_df = full_df.drop(columns=cols_not_for_modelling, errors='ignore')

    # Identify categorical columns
    categorical_columns = ['team_id', 'referee_id', 'opp_id', 'round']
    continuous_columns = full_df.columns.difference(categorical_columns + ['datetime', 'game_id'])

    # Convert categorical columns to categorical type
    for col in categorical_columns:
        full_df[col] = full_df[col].astype('category')

    # One-hot encode the categorical features
    full_df_categorical = pd.get_dummies(full_df[categorical_columns], drop_first=True)
    full_df_continuous = full_df[continuous_columns]

    # Combine the one-hot encoded categorical features with the continuous features
    full_df = pd.concat([full_df_categorical, full_df_continuous], axis=1)

    # Define feature columns and target column
    feature_columns = full_df.columns.difference(['throws', 'datetime', 'game_id'])
    target_column = 'throws'
    X = full_df[feature_columns]
    y = full_df[target_column]

    # Filter out classes with fewer than 2 instances (if needed)
    value_counts = y.value_counts()
    to_remove = value_counts[value_counts < 2].index
    X_filtered = X[~y.isin(to_remove)]
    y_filtered = y[~y.isin(to_remove)]

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X_filtered, y_filtered, test_size=0.2, random_state=42)

    # Define the Optuna objective function for hyperparameter optimization
    def objective(trial):
        param = {
            'n_estimators': trial.suggest_int('n_estimators', 100, 300),
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

        # Train the model
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
    print(f"Best Parameters: {best_params}")

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

    print(f"Train RMSE: {train_rmse}")
    print(f"Test RMSE: {test_rmse}")
    print(f"Train MAE: {train_mae}")
    print(f"Test MAE: {test_mae}")
    print(f"Train R^2: {train_r2}")
    print(f"Test R^2: {test_r2}")

    # Feature Importance
    feature_importances = final_model.feature_importances_
    sorted_idx = np.argsort(feature_importances)[-10:]  # Top 10 features
    print("Top 10 Features:")
    for idx in sorted_idx:
        print(X_train.columns[idx])

    # Plot the top 10 feature importances
    plt.figure(figsize=(10, 8))
    plt.barh(X.columns[sorted_idx], feature_importances[sorted_idx])
    plt.xlabel("Feature Importance")
    plt.ylabel("Feature")
    plt.title("Top 10 Feature Importance Using XGBoost")
    plt.tight_layout()
    plt.show()

    # Plot predicted vs actual
    y_pred = final_model.predict(X_test)
    plt.scatter(y_test, y_pred, alpha=0.2)
    plt.xlabel('Actual total score')
    plt.ylabel('Predicted total score')
    plt.title('Predicted vs. Actual total score')
    plt.show()

    residuals = y_test - y_pred
    print(f"Standard Deviation of Residuals: {residuals.std()}")

    # Create a SHAP explainer object
    explainer = shap.Explainer(final_model)
    shap_values = explainer(X_train)

    # Summary plot for SHAP values
    shap.summary_plot(shap_values, X_train)
    plt.show()

    # Save the model
    joblib.dump(final_model, './prem/data/models/Prem_throws_optuna_simple.joblib')

    return final_model

