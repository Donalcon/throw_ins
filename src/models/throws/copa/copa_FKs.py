import optuna
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import xgboost as xgb
import time
import shap
import matplotlib.pyplot as plt
import joblib
from imblearn.over_sampling import SMOTE
from src.comp_processers.copa.copa_cleaner import cols_not_for_modelling

# Load data
full_df = pd.read_csv("data/int_processed_master.csv")
full_df = full_df.drop(columns=cols_not_for_modelling, errors='ignore')

# Preprocessing
full_df.dropna(inplace=True)

# Convert to categorical
full_df['team_id'] = full_df['team_id'].astype('category')
full_df['referee_id'] = full_df['referee_id'].astype('category')
full_df['opp_id'] = full_df['opp_id'].astype('category')
full_df['round'] = full_df['round'].astype('category')
full_df['division'] = full_df['division'].astype('category')

# Define feature columns and target column
feature_columns = full_df.columns.difference(['fouls_committed', 'datetime', 'game_id'])
target_column = 'fouls_committed'

# Split the data into features and target
X = full_df[feature_columns]
y = full_df[target_column]

# Handle categorical variables
X = pd.get_dummies(X, drop_first=True)
# Filter out classes with fewer than 2 instances
value_counts = y.value_counts()
to_remove = value_counts[value_counts < 2].index
X_filtered = X[~y.isin(to_remove)]
y_filtered = y[~y.isin(to_remove)]

# Apply SMOTE to balance the dataset
smote = SMOTE(k_neighbors=1)  # Set the number of neighbors to 1
X_res, y_res = smote.fit_resample(X_filtered, y_filtered)

# Split data into training and testing sets using stratified split
X_train, X_test, y_train, y_test = train_test_split(X_res, y_res, test_size=0.2, random_state=42)


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
print(f"Best Parameters: {best_params}")

# Train the final model using the best parameters
final_model = xgb.XGBRegressor(**best_params, objective='reg:squarederror')
final_model.fit(X_train, y_train)

# Get feature importances
feature_importances = final_model.feature_importances_
not_important_df = pd.DataFrame({
    'feature': X_train.columns,
    'importance': feature_importances
})
# order not_important_df by importance
not_important_df = not_important_df.sort_values(by='importance', ascending=False)

# Filter out low importance features
threshold = 0.01  # You can adjust this threshold based on your needs
important_features = not_important_df[not_important_df['importance'] > threshold]['feature']
unimportant_features = not_important_df[not_important_df['importance'] <= threshold]['feature']

print("Unimportant features to drop:", unimportant_features.tolist())

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
# Sort features by their importance
sorted_idx = np.argsort(feature_importances)[-10:]  # Gets the indices of the top 10 features
print("Top 10 Features:")
for idx in sorted_idx:
    print(X_train.columns[idx])  # Gets the indices of the top 10 features

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
print(f"Standard Deviation of Residuals: {residuals.std()}")

# Create a SHAP explainer object
explainer = shap.Explainer(final_model)

# Calculate SHAP values for all instances in the training data
shap_values = explainer(X_train)

# Summary plot (for regression or classification)
shap.summary_plot(shap_values, X_train)
plt.show()

# Save the model
joblib.dump(final_model, 'FKs_XGB_SMOTE_optuna.joblib')
