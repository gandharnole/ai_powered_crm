import pandas as pd
import numpy as np
import os
import joblib
from statsmodels.tsa.statespace.sarimax import SARIMAX

# Load your CSV dataset
sales_df = pd.read_csv("D:\Major project\maruti_monthly_sales.csv")
sales_df['month'] = pd.to_datetime(sales_df['month'])

# Define car models
car_models = ['Ertiga', 'WagonR', 'Brezza', 'Grand Vitara']

# Directory to save models
model_dir = "sales_models"
os.makedirs(model_dir, exist_ok=True)

# Train and save model per car
for car in car_models:
    car_data = sales_df[sales_df['car_model'] == car].copy()
    car_data.set_index('month', inplace=True)
    ts = car_data['units_sold'].asfreq('MS')

    # Train ARIMA model
    model = SARIMAX(ts, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
    results = model.fit(disp=False)

    # Save model
    model_path = os.path.join(model_dir, f"{car.lower().replace(' ', '_')}_arima_model.pkl")
    joblib.dump(results, model_path)

print("✅ All models trained and saved in:", model_dir)
