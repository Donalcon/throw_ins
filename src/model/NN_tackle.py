import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
import kerastuner as kt
import matplotlib.pyplot as plt
import shap
import joblib
from src.model.model_cleaner import add_missing_team_id_columns

# Load data
full_df = pd.read_csv("data/processed_master.csv")

# Columns to exclude from modelling
cols_not_for_modelling = [
    'total_shots', 'shots_on_target', 'big_chances', 'accurate_passes', 'accurate_passes_pc',
    'fouls_committed', 'corners', 'blocked_shots', 'shots_inside_box', 'shots_outside_box',
    'passes', 'passes_own_half', 'passes_opp_half', 'accurate_long_balls', 'competition',
    'accurate_long_balls_pc', 'accurate_crosses', 'accurate_crosses_pc', 'touches_in_opposition_box',
    'offsides', 'yellow_cards', 'red_cards', 'tackles_won', 'tackles_won_pc', 'interceptions',
    'blocks', 'clearances', 'keeper_saves', 'duels_won', 'ground_duels_won', 'ground_duels_won_pc',
    'aerial_duels_won', 'aerial_duels_won_pc', 'successful_dribbles', 'successful_dribbles_pc',
    'datetime', 'stadium', 'team', 'opp', 'game_id', 'touches_in_opposition_box', 'possession',
    'avg_touches_in_opposition_box', 'poss_adj_throws', 'pass_adj_throws', 'opp_avg_touches_in_opposition_box',
    'avg_div_touches_in_opposition_box',
]

# drop columns not for modelling from full_df if they are in full_df
full_df = full_df.drop(columns=cols_not_for_modelling, errors='ignore')
full_df.dropna(inplace=True)

# Convert team_id to categorical
full_df['team_id'] = full_df['team_id'].astype('category')
full_df['opp_id'] = full_df['opp_id'].astype('category')

# Define feature columns and target column
feature_columns = full_df.columns.difference(['throws', 'datetime', 'game_id'])
target_column = 'throws'

# Split the data into features and target
X = full_df[feature_columns]
y = full_df[target_column]

# Handle categorical variables
X = pd.get_dummies(X, drop_first=True)
X = add_missing_team_id_columns(X)

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Define the model
def build_model(hp):
    model = Sequential()
    model.add(Dense(units=hp.Int('units1', min_value=32, max_value=512, step=32), activation='relu', input_dim=X_train.shape[1]))
    model.add(Dropout(rate=hp.Float('dropout1', min_value=0.0, max_value=0.5, step=0.1)))
    model.add(Dense(units=hp.Int('units2', min_value=32, max_value=512, step=32), activation='relu'))
    model.add(Dropout(rate=hp.Float('dropout2', min_value=0.0, max_value=0.5, step=0.1)))
    model.add(Dense(units=hp.Int('units3', min_value=32, max_value=512, step=32), activation='relu'))
    model.add(Dense(1))

    model.compile(optimizer=hp.Choice('optimizer', values=['adam', 'rmsprop', 'sgd']),
                  loss='mse',
                  metrics=['mse'])
    return model

# Hyperparameter tuning
tuner = kt.RandomSearch(build_model,
                        objective='val_mse',
                        max_trials=50,
                        executions_per_trial=3,
                        directory='tuner_results',
                        project_name='football_throws')

early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

# Perform hyperparameter tuning
tuner.search(X_train, y_train, epochs=200, validation_split=0.2, callbacks=[early_stopping])

# Get the optimal hyperparameters
best_hps = tuner.get_best_hyperparameters(num_trials=1)[0]

# Build the best model
model = tuner.hypermodel.build(best_hps)

# Fit the model
history = model.fit(X_train, y_train, validation_split=0.2, epochs=200, batch_size=32, callbacks=[early_stopping])

# Make predictions
y_pred_train = model.predict(X_train).flatten()
y_pred_test = model.predict(X_test).flatten()

# Evaluate the model
train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
train_r2 = r2_score(y_train, y_pred_train)
test_r2 = r2_score(y_test, y_pred_test)

print(f"Train RMSE: {train_rmse}")
print(f"Test RMSE: {test_rmse}")
print(f"Train R^2: {train_r2}")
print(f"Test R^2: {test_r2}")

# Plot the loss curve
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.title('Training and Validation Loss Curve')
plt.legend()
plt.show()

# Plot the predicted vs. actual values
plt.scatter(y_test, y_pred_test, alpha=0.2)
plt.xlabel('Actual Throws')
plt.ylabel('Predicted Throws')
plt.title('Predicted vs. Actual Throws')
plt.show()

# Save the model
model.save('throw_in_nn_model.h5')

# Save the neural network model using joblib
joblib.dump(model, 'throw_in_nn_model.joblib')

# SHAP values
explainer = shap.KernelExplainer(model.predict, X_train)
shap_values = explainer.shap_values(X_train)

# Summary plot
shap.summary_plot(shap_values, X_train)
