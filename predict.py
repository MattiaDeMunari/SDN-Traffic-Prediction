from prophet import Prophet
import pandas as pd


data = pd.read_csv('topology/train.csv')

model = Prophet()

model.fit(data)

future = model.make_future_dataframe(periods=30)  # forecasting 30 days into the future
forecast = model.predict(future)

print(forecast)

