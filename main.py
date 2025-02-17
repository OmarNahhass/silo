import warnings
warnings.filterwarnings("ignore")  # Suppress all warnings

import streamlit as st
from data_fetcher import fetch_data
from models.linear_regression import perform_linear_regression
from models.arima import perform_arima_prediction
from models.ets import perform_ets_prediction

def main():
    # Streamlit app title
    st.title("CryptoCast")

    st.write("\n" + "-" * 70 + "\n")

    # Get user input for the cryptocurrency ticker
    ticker = st.text_input("Enter a cryptocurency ticker symbol: " ).upper()

    # Fetch data for the specified ticker
    if st.button("Fetch Data and Predict"):
        try:
            data = fetch_data(ticker)
            st.subheader(f"Fetched Data for {ticker}")
            st.write(data)

            # Perform predictions
            st.subheader("Predictions")

            st.write("### Linear Regression Prediction")
            lr_prediction = perform_linear_regression(data)
            st.write(f"Prediction of next day's closing price using Linear Regression: {lr_prediction:.2f}")

            st.write("### ARIMA Prediction")
            arima_prediction = perform_arima_prediction(data)
            st.write(f"Prediction of next day's closing price using ARIMA: {arima_prediction:.2f}")

            st.write("### ETS Prediction")
            ets_prediction = perform_ets_prediction(data)
            st.write(f"Prediction of next day's closing price using ETS: {ets_prediction:.2f}")

        except Exception as e:
            st.error(f"Error fetching data for {ticker}: {e}")

# Run the main function
if __name__ == "__main__":
    main()