import requests
from typing import List, Dict

from .base import MarketDataConnectorBase, FXConnectorBase

API_URL = "https://www.alphavantage.co/query"

class AlphaVantageConnector(MarketDataConnectorBase):
    """Connector for fetching market data from Alpha Vantage."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_prices(self, tickers: List[str]) -> Dict[str, float]:
        prices = {}
        for ticker in tickers:
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": ticker,
                "apikey": self.api_key
            }
            try:
                response = requests.get(API_URL, params=params)
                response.raise_for_status() # Raise an exception for bad status codes
                data = response.json()
                if "Global Quote" in data and "05. price" in data["Global Quote"]:
                    prices[ticker] = float(data["Global Quote"]["05. price"])
                else:
                    print(f"Warning: Could not fetch price for {ticker}. Response: {data}")
            except requests.exceptions.RequestException as e:
                print(f"Error fetching price for {ticker}: {e}")
        return prices

class AlphaVantageFXConnector(FXConnectorBase):
    """Connector for fetching FX rates from Alpha Vantage."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_rates(self, from_currency: str, to_currency: str) -> Dict[str, float]:
        # Note: Alpha Vantage free tier has limited currency pairs.
        # A more robust solution might use a different provider.
        rates = {}
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency,
            "to_currency": to_currency,
            "apikey": self.api_key
        }
        try:
            response = requests.get(API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            if "Realtime Currency Exchange Rate" in data:
                rate = float(data["Realtime Currency Exchange Rate"]["5. Exchange Rate"])
                rates[f"{from_currency}{to_currency}"] = rate
            else:
                print(f"Warning: Could not fetch FX rate for {from_currency}->{to_currency}. Response: {data}")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching FX rate: {e}")
        return rates
