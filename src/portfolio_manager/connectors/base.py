from abc import ABC, abstractmethod
from typing import List, Dict

from ..models import Portfolio

class BrokerConnectorBase(ABC):
    """Abstract base class for all broker connectors."""

    @abstractmethod
    def get_portfolio(self) -> Portfolio:
        """Fetches the portfolio data from the broker."""
        pass

class MarketDataConnectorBase(ABC):
    """Abstract base class for all market data connectors."""

    @abstractmethod
    def get_prices(self, tickers: List[str]) -> Dict[str, float]:
        """Fetches the latest prices for a list of tickers."""
        pass

class FXConnectorBase(ABC):
    """Abstract base class for all foreign exchange rate connectors."""

    @abstractmethod
    def get_rates(self, symbols: List[str]) -> Dict[str, float]:
        """Fetches the latest FX rates for a list of currency symbols."""
        pass
