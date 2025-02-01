from alpha_vantage.cryptocurrencies import CryptoCurrencies

# Alpha Vantage API key and setup
key = '9RA8738HVDJTCLR0'
cc = CryptoCurrencies(key=key, output_format='pandas')

def fetch_data(ticker):
    """Fetch data for the given ticker."""
    response, meta_data = cc.get_digital_currency_daily(symbol=ticker, market='USD')
    return response