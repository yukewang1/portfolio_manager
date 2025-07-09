import yaml
from typing import Dict, Any

from .base import BrokerConnectorBase
from ..models import Portfolio, Account, Holding

class FileBrokerConnector(BrokerConnectorBase):
    """A connector that loads portfolio data from a YAML file."""

    def __init__(self, portfolio_path: str):
        self.portfolio_path = portfolio_path

    def get_portfolio(self) -> Portfolio:
        """Reads the portfolio.yaml file and constructs the Portfolio object."""
        try:
            with open(self.portfolio_path, 'r') as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Portfolio file not found at: {self.portfolio_path}")

        accounts = []
        for acc_data in data.get('accounts', []):
            holdings = [
                Holding(
                    ticker=h['ticker'], 
                    quantity=h['quantity'], 
                    currency=h['currency']
                ) for h in acc_data.get('holdings', [])
            ]
            
            account = Account(
                name=acc_data['name'],
                broker=acc_data['broker'],
                holdings=holdings,
                cash_balances=acc_data.get('cash_balances', {})
            )
            accounts.append(account)
        
        return Portfolio(accounts=accounts)
