import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import xgboost as xgb
import time
import shap
import matplotlib.pyplot as plt
import joblib
from src.model.model_cleaner import filter_teams, european_countries
from imblearn.over_sampling import SMOTE
from src.utils.simple_cleaner import cols_not_for_modelling

# Load data
full_df = pd.read_csv("data/processed_master_throws_6.csv")

# Drop columns not for modelling from full_df if they are in full_df
full_df = full_df.drop(columns=cols_not_for_modelling, errors='ignore')

# Print number of NaNs in every column
for col in full_df.columns:
    print(f"Column: {col}, nans: {full_df[col].isna().sum()}")

# Drop rows with NaN values
full_df.dropna(inplace=True)

# Convert team_id to categorical
full_df['team_id'] = full_df['team_id'].astype('category')
full_df['opp_id'] = full_df['opp_id'].astype('category')
full_df['stadium'] = full_df['stadium'].astype('category')
full_df['referee'] = full_df['referee'].astype('category')
full_df['round'] = full_df['round'].astype('category')
full_df['competition'] = full_df['competition'].astype('category')

# Define feature columns and target column
feature_columns = full_df.columns.difference(['throws', 'datetime', 'game_id'])
target_column = 'throws'

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


# Initialize XGBoost regressor
xgb_regressor = xgb.XGBRegressor(objective='reg:squarederror')

# Define hyperparameters to tune
param_grid = {
    'n_estimators': [100, 200],
    'learning_rate': [0.01, 0.05],
    'max_depth': [3, 5],
    'gamma': [0, 0.1],
    'reg_alpha': [0, 0.5],
    'reg_lambda': [1, 1.5],
}

# param_grid = {
#     'n_estimators': [100, 200, 300],
#     'learning_rate': [0.01, 0.05, 0.1],
#     'max_depth': [3, 5, 7],
#     'gamma': [0, 0.1, 0.3],
#     'reg_alpha': [0, 0.5, 1],
#     'reg_lambda': [1, 1.5, 2],
# }
# 'min_child_weight': [1, 3, 5],
# 'subsample': [0.6, 0.8, 1.0],
# 'colsample_bytree': [0.6, 0.8, 1.0],
# Perform grid search with cross-validation
grid_search = GridSearchCV(
    estimator=xgb_regressor,
    param_grid=param_grid,
    scoring='neg_mean_squared_error',
    cv=5,
    verbose=2,
    n_jobs=-1
)

# Fit the model
start_time = time.time()
grid_search.fit(X_train, y_train)
end_time = time.time()

print(f"GridSearchCV took {end_time - start_time:.2f} seconds")

# Get the best parameters and best score
best_params = grid_search.best_params_
best_score = grid_search.best_score_

print(f"Best Parameters: {best_params}")
print(f"Best Cross-Validation Score: {best_score}")

# Train the final model using the best parameters
final_model = xgb.XGBRegressor(**best_params, objective='reg:squarederror')
final_model.fit(X_train, y_train)

# Get feature importances
feature_importances = final_model.feature_importances_
not_important_df = pd.DataFrame({
    'feature': X_train.columns,
    'importance': feature_importances
})

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
joblib.dump(final_model, 'throw_in_XGB_SMOTE_euro_5.joblib')
