import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import shap
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.datasets import load_iris
import pandas as pd

# Matplotlib backend (optional)
import matplotlib
matplotlib.use('TkAgg')

# Generate some data
x = np.linspace(0, 10, 100)
y = np.sin(x)

# Simple Matplotlib plot
plt.figure(figsize=(10, 6))
plt.plot(x, y)
plt.title('Simple Plot')
plt.xlabel('X-axis')
plt.ylabel('Y-axis')
plt.show()

# Seaborn plot
sns.set(style="darkgrid")
data = sns.load_dataset("iris")
sns.scatterplot(x="sepal_length", y="sepal_width", hue="species", data=data)
plt.title('Iris Dataset Scatterplot')
plt.show()

# Load example data for SHAP
iris = load_iris()
X = pd.DataFrame(iris.data, columns=iris.feature_names)
y = iris.target

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train XGBoost model
model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='mlogloss')
model.fit(X_train, y_train)

# SHAP explainer
explainer = shap.Explainer(model)
shap_values = explainer(X_train)

# SHAP summary plot
shap.summary_plot(shap_values, X_train)
plt.show()

# SHAP bar plot
shap.summary_plot(shap_values, X_train, plot_type="bar")
plt.show()
