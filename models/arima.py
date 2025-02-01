import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

def perform_arima_prediction(data):
    """Perform ARIMA prediction."""
    # Preprocess the data
    data = data[['4. close']]
    data.columns = ['Close']

    # Ensure the index is a proper datetime index and sorted
    data.index = pd.to_datetime(data.index)
    data = data.sort_index()

    # aily Frequency
    data = data.asfreq('D')

    model = ARIMA(data['Close'], order=(5, 1, 0))  
    model_fit = model.fit()

    forecast = model_fit.forecast(steps=1)

    print(f"Prediction of next day's closing price using ARIMA: {forecast.iloc[0]:.2f}")