import yaml
from typing import Dict, Any, Set, List

from .models import Portfolio
from .connectors.alpha_vantage import AlphaVantageConnector, AlphaVantageFXConnector
from .connectors.file_connector import FileBrokerConnector

def load_config(path: str) -> Dict[str, Any]:
    """Loads the YAML configuration file."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)

class Engine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Load the portfolio from the file specified in the config
        portfolio_path = self.config.get('portfolio_file')
        if not portfolio_path:
            raise ValueError("'portfolio_file' not specified in config.yaml")
        broker_connector = FileBrokerConnector(portfolio_path)
        self.portfolio = broker_connector.get_portfolio()

        self.market_data = {}
        self.fx_rates = {config['reporting_currency']: 1.0} # Base rate

        # Initialize real data connectors
        api_key = self.config.get('api_keys', {}).get('alpha_vantage', None)
        if not api_key or api_key == "YOUR_API_KEY_HERE":
            raise ValueError("Alpha Vantage API key not found or not set in config.yaml")
        self.market_data_connector = AlphaVantageConnector(api_key)
        self.fx_connector = AlphaVantageFXConnector(api_key)

    def run(self):
        """The main method to run the full analysis pipeline with live data."""
        tickers_to_fetch = self._get_all_tickers()
        currencies_to_fetch = self._get_all_currencies()

        self.market_data = self.market_data_connector.get_prices(list(tickers_to_fetch))
        self._fetch_fx_rates(currencies_to_fetch)

        self._calculate_market_values()
        self._normalize_to_reporting_currency()

    def _get_all_tickers(self) -> Set[str]:
        return {holding.ticker for account in self.portfolio.accounts for holding in account.holdings}

    def _get_all_currencies(self) -> Set[str]:
        currencies = {self.config['reporting_currency']}
        for account in self.portfolio.accounts:
            currencies.update(account.cash_balances.keys())
            for holding in account.holdings:
                currencies.add(holding.currency)
        return currencies

    def _fetch_fx_rates(self, currencies: Set[str]):
        reporting_currency = self.config['reporting_currency']
        for currency in currencies:
            if currency != reporting_currency and currency not in self.fx_rates:
                rate_dict = self.fx_connector.get_rates(from_currency=currency, to_currency=reporting_currency)
                if rate_dict:
                    self.fx_rates[currency] = list(rate_dict.values())[0]

    def _calculate_market_values(self):
        for account in self.portfolio.accounts:
            for holding in account.holdings:
                if holding.ticker in self.market_data:
                    holding.market_value = holding.quantity * self.market_data[holding.ticker]

    def _normalize_to_reporting_currency(self):
        total_portfolio_value = 0.0
        for account in self.portfolio.accounts:
            account_total_value = 0.0
            for holding in account.holdings:
                fx_rate = self.fx_rates.get(holding.currency, 1.0)
                normalized_value = holding.market_value * fx_rate
                account_total_value += normalized_value
            for currency, amount in account.cash_balances.items():
                fx_rate = self.fx_rates.get(currency, 1.0)
                account_total_value += amount * fx_rate
            account.total_value = account_total_value
            total_portfolio_value += account_total_value
        self.portfolio.total_value = total_portfolio_value

    def get_current_allocations(self) -> Dict[str, float]:
        active_portfolio_value = self._get_active_portfolio_value()
        if active_portfolio_value == 0: return {}
        allocations = {}
        aggregated_holdings = self._get_aggregated_active_holdings()
        for ticker, total_value in aggregated_holdings.items():
            allocations[ticker] = total_value / active_portfolio_value
        return allocations

    def calculate_drift(self, current_allocations: Dict[str, float], target_allocations: Dict[str, float]) -> float:
        drift = 0.0
        all_tickers = set(current_allocations.keys()) | set(target_allocations.keys())
        for ticker in all_tickers:
            current = current_allocations.get(ticker, 0.0)
            target = target_allocations.get(ticker, 0.0)
            drift += abs(current - target)
        return (drift / 2) * 100

    def generate_rebalancing_plan(self, current_allocations: Dict[str, float], target_allocations: Dict[str, float]) -> List[str]:
        plan = []
        active_value = self._get_active_portfolio_value()
        for ticker in set(current_allocations.keys()) | set(target_allocations.keys()):
            delta = target_allocations.get(ticker, 0.0) - current_allocations.get(ticker, 0.0)
            if abs(delta) > 0.0001:
                trade_value = delta * active_value
                action = "BUY" if trade_value > 0 else "SELL"
                plan.append(f"{action: <5} {abs(trade_value):>10,.2f} {self.config['reporting_currency']} of {ticker}")
        return plan

    def _get_active_portfolio_value(self) -> float:
        skipped_tickers = self.config.get('rebalance_options', {}).get('skip_tickers', [])
        skipped_value = 0.0
        for account in self.portfolio.accounts:
            for holding in account.holdings:
                if holding.ticker in skipped_tickers:
                    fx_rate = self.fx_rates.get(holding.currency, 1.0)
                    skipped_value += holding.market_value * fx_rate
        return self.portfolio.total_value - skipped_value

    def _get_aggregated_active_holdings(self) -> Dict[str, float]:
        skipped_tickers = self.config.get('rebalance_options', {}).get('skip_tickers', [])
        aggregated = {}
        for account in self.portfolio.accounts:
            for holding in account.holdings:
                if holding.ticker not in skipped_tickers:
                    fx_rate = self.fx_rates.get(holding.currency, 1.0)
                    normalized_value = holding.market_value * fx_rate
                    aggregated[holding.ticker] = aggregated.get(holding.ticker, 0) + normalized_value
        return aggregated
