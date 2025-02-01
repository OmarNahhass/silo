import warnings
warnings.filterwarnings("ignore")  # Suppress all warnings

from data_fetcher import fetch_data
from models.linear_regression import perform_linear_regression
from models.arima import perform_arima_prediction
from models.ets import perform_ets_prediction

def main():
    # Welcome to CryptoCast
    print("\nWelcome to CryptoCast!")
    print("This program uses 3 different models to predict cryptocurrency prices:")
    print("1. Linear Regression (not recommended for accurate predictions)")
    print("2. ARIMA (AutoRegressive Integrated Moving Average)")
    print("3. ETS (Error, Trend, Seasonality)")
    print("\n" + "-" * 70 + "\n")

    # Get user input for the cryptocurrency ticker
    ticker = input("Please enter a cryptocurrency ticker symbol (e.g., BTC, ETH): ").upper()

    # Fetch data for the specified ticker
    try:
        data = fetch_data(ticker)
    except Exception as e:
        print(f"\nError fetching data for {ticker}: {e}")
        return

    # Call the functions to perform predictions
    print(f"\nUsing Linear Regression for {ticker}:")
    perform_linear_regression(data)

    print(f"\nUsing ARIMA for {ticker}:")
    perform_arima_prediction(data)

    print(f"\nUsing ETS for {ticker}:")
    perform_ets_prediction(data)

# Run the main function
if __name__ == "__main__":
    main()