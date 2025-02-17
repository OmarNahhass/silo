import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression  

def perform_linear_regression(data):
    """Perform linear regression prediction."""
    # Preprocess the data
    data = data[['4. close']]  # Use the correct column name
    data.columns = ['Close']
    data.loc[:, 'Next Day Close'] = data['Close'].shift(-1)

    # Drop the last row since it won't have a next day close value
    data = data.dropna()

    X = np.array(data['Close']).reshape(-1, 1)
    y = np.array(data['Next Day Close'])

    model = LinearRegression()
    model.fit(X, y)

    last_close_price = data['Close'].iloc[-1]
    next_day_prediction = model.predict(np.array([[last_close_price]]))

    return next_day_prediction[0]  # Return the prediction value