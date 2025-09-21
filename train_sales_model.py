import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import pickle

# Load data
df = pd.read_csv("D:\Major project\maruti_sales_data.csv")

X = df[['car_model', 'marketing_spend', 'economic_index']]
y = df['units_sold']

# Encode 'car_model'
preprocessor = ColumnTransformer(
    transformers=[('car_model', OneHotEncoder(), ['car_model'])],
    remainder='passthrough'
)

# Build pipeline
model = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('regressor', LinearRegression())
])

# Train
model.fit(X, y)

# Save model
with open('maruti_sales_predictor.pkl', 'wb') as f:
    pickle.dump(model, f)

print("Model trained and saved!")
