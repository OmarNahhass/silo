import pandas as pd  # Import pandas
from statsmodels.tsa.arima.model import ARIMA  # Import ARIMA

def perform_arima_prediction(data):
    """Perform ARIMA prediction."""
    # Preprocess the data
    data = data[['4. close']]  # Use the correct column name
    data.columns = ['Close']

    # Ensure the index is a proper datetime index and sorted
    data.index = pd.to_datetime(data.index)
    data = data.sort_index()

    # Ensure daily frequency
    data = data.asfreq('D')

    model = ARIMA(data['Close'], order=(5, 1, 0))  
    model_fit = model.fit()

    forecast = model_fit.forecast(steps=1)

    return forecast.iloc[0]  # Return the prediction value