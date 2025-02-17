from alpha_vantage.cryptocurrencies import CryptoCurrencies

# Alpha Vantage API key and setup
key = '9RA8738HVDJTCLR0'  # Replace with your Alpha Vantage API key
cc = CryptoCurrencies(key=key, output_format='pandas')

def fetch_data(ticker):
    """Fetch data for the given ticker."""
    try:
        response, meta_data = cc.get_digital_currency_daily(symbol=ticker, market='USD')
        print("Fetched Data Columns:", response.columns)  # Print column names
        return response
    except Exception as e:
        raise Exception(f"Failed to fetch data for {ticker}: {e}")