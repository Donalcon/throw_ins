import optuna
import pandas as pd
import numpy as np
from sklearn.utils.class_weight import compute_class_weight
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from imblearn.over_sampling import SMOTE
import xgboost as xgb
import joblib
from prem.utils.fixed import cols_not_for_modelling
import logging


logger = logging.getLogger(__name__)


def throws_classification_model(full_df: pd.DataFrame):
    # Drop unnecessary columns
    full_df = full_df.drop(columns=cols_not_for_modelling, errors='ignore')

    # Identify categorical and continuous columns
    categorical_columns = ['team_id', 'referee_id', 'opp_id']
    continuous_columns = full_df.columns.difference(categorical_columns + ['datetime', 'game_id'])
    logger.info("Modelling Columns:", continuous_columns)

    # Convert categorical columns to categorical type
    for col in categorical_columns:
        full_df[col] = full_df[col].astype('category')

    # One-hot encode categorical features
    full_df_categorical = pd.get_dummies(full_df[categorical_columns], drop_first=True)
    full_df_continuous = full_df[continuous_columns]

    # Combine categorical and continuous features
    full_df = pd.concat([full_df_categorical, full_df_continuous], axis=1)

    # ** Check for and remove duplicate columns **
    full_df = full_df.loc[:, ~full_df.columns.duplicated()]

    # Define feature columns and target column
    feature_columns = full_df.columns.difference(['throws', 'datetime', 'game_id'])
    X = full_df[feature_columns]
    y = full_df['throws'].astype(int)

    # Filter out classes with fewer than 2 instances
    value_counts = y.value_counts()
    to_remove = value_counts[value_counts < 5].index
    X_filtered = X[~y.isin(to_remove)]
    y_filtered = y[~y.isin(to_remove)]

    # Dynamically shift class labels to start from 0
    min_label = y_filtered.min()
    y_shifted = y_filtered - min_label

    # Apply SMOTE to balance the dataset
    smote = SMOTE(k_neighbors=3)
    X_res, y_res = smote.fit_resample(X_filtered, y_shifted)

    # Compute class weights based on the shifted data distribution
    shifted_classes = np.unique(y_res)
    class_weights = compute_class_weight('balanced', classes=shifted_classes, y=y_res)

    # Create sample weights using the computed class weights
    sample_weights = np.array([class_weights[shifted_classes.tolist().index(c)] for c in y_res])

    # Split data into training and testing sets using stratified split
    X_train, X_test, y_train, y_test, sample_weights_train, sample_weights_test = train_test_split(
        X_res, y_res, sample_weights, test_size=0.2, random_state=42, stratify=y_res
    )

    # Objective function for Optuna optimization
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
            'objective': 'multi:softmax',
            'num_class': len(np.unique(y_res)),
            'eval_metric': 'mlogloss'
        }

        model = xgb.XGBClassifier(**param)
        model.set_params(early_stopping_rounds=10)

        # Fit the model with sample weights
        model.fit(X_train, y_train, sample_weight=sample_weights_train, eval_set=[(X_test, y_test)], verbose=False)

        # Predict on the test set
        y_pred = model.predict(X_test)
        y_pred_original = y_pred + 6

        # Calculate accuracy
        accuracy = accuracy_score(y_test + 6, y_pred_original)
        return 1 - accuracy

    # Run Optuna optimization
    study = optuna.create_study(direction='minimize')
    study.optimize(objective, n_trials=50)

    # Get the best parameters
    best_params = study.best_params
    logger.info(f"Best Parameters: {best_params}")

    # Train the final model using the best parameters
    final_model = xgb.XGBClassifier(**best_params, objective='multi:softmax', num_class=len(np.unique(y_res)))
    final_model.fit(X_train, y_train, sample_weight=sample_weights_train)

    # Make predictions
    y_pred_train = final_model.predict(X_train) + 6
    y_pred_test = final_model.predict(X_test) + 6

    # Evaluate the model
    train_accuracy = accuracy_score(y_train + 6, y_pred_train)
    test_accuracy = accuracy_score(y_test + 6, y_pred_test)

    logger.info(f"Train Accuracy: {train_accuracy}")
    logger.info(f"Test Accuracy: {test_accuracy}")

    # Classification Report
    logger.info("Classification Report on Test Set:")
    logger.info(classification_report(y_test + 6, y_pred_test))

    # Save the model
    joblib.dump(final_model, './prem/data/models/Prem_throws_classification_smote_sample_weights.joblib')

    return final_model
