import os
import re

def extract_market_and_ticker(filename):
    """
    Extracts the ticker symbol and market name from filenames formatted as:
    'TICKER_MARKET_Equity.csv' (e.g., 'COST_US_Equity.csv').
    """
    match = re.match(r"([A-Z0-9]+)_([A-Z]+)_Equity\.csv", filename)
    if match:
        ticker, market = match.groups()
        return market, ticker
    return None, None

def list_market_tickers(directory="Histories"):
    """
    Lists all unique market names and their ticker symbols in a given directory.
    """
    market_ticker_map = {}
    for file in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, file)):
            market, ticker = extract_market_and_ticker(file)
            if market and ticker:
                if market not in market_ticker_map:
                    market_ticker_map[market] = set()
                market_ticker_map[market].add(ticker)

    # Convert sets to lists for better readability
    return {market: list(tickers) for market, tickers in market_ticker_map.items()}

# Run the function in the current directory
market_ticker_data = list_market_tickers()
# Print the result
with open('market_names.txt', 'w') as file:
    for market, tickers in market_ticker_data.items():
        file.write(f"Market: {market} | Tickers: \n{', '.join(tickers)}".replace(', ','\n'))