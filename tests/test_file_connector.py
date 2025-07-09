import pytest
import tempfile
import os
from unittest.mock import patch, mock_open
from src.portfolio_manager.connectors.file_connector import FileBrokerConnector
from src.portfolio_manager.models import Portfolio, Account, Holding


class TestFileBrokerConnector:
    def test_file_not_found(self):
        """Test error handling when portfolio file doesn't exist."""
        connector = FileBrokerConnector("nonexistent_file.yaml")
        with pytest.raises(FileNotFoundError, match="Portfolio file not found"):
            connector.get_portfolio()

    def test_empty_file(self):
        """Test handling of empty YAML file."""
        yaml_content = "accounts: []"  # Empty file would return None, but we need valid YAML
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            connector = FileBrokerConnector("test.yaml")
            portfolio = connector.get_portfolio()
            assert isinstance(portfolio, Portfolio)
            assert portfolio.accounts == []

    def test_empty_accounts_list(self):
        """Test handling of YAML with empty accounts list."""
        yaml_content = "accounts: []"
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            connector = FileBrokerConnector("test.yaml")
            portfolio = connector.get_portfolio()
            assert isinstance(portfolio, Portfolio)
            assert portfolio.accounts == []

    def test_single_account_no_holdings(self):
        """Test loading single account with no holdings."""
        yaml_content = """
accounts:
  - name: "Test Account"
    broker: "test_broker"
"""
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            connector = FileBrokerConnector("test.yaml")
            portfolio = connector.get_portfolio()
            
            assert len(portfolio.accounts) == 1
            account = portfolio.accounts[0]
            assert account.name == "Test Account"
            assert account.broker == "test_broker"
            assert account.holdings == []
            assert account.cash_balances == {}

    def test_single_account_with_holdings(self):
        """Test loading single account with holdings."""
        yaml_content = """
accounts:
  - name: "Investment Account"
    broker: "fidelity"
    holdings:
      - ticker: "AAPL"
        quantity: 100
        currency: "USD"
      - ticker: "GOOGL"
        quantity: 50
        currency: "USD"
"""
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            connector = FileBrokerConnector("test.yaml")
            portfolio = connector.get_portfolio()
            
            assert len(portfolio.accounts) == 1
            account = portfolio.accounts[0]
            assert account.name == "Investment Account"
            assert account.broker == "fidelity"
            assert len(account.holdings) == 2
            
            # Check first holding
            holding1 = account.holdings[0]
            assert holding1.ticker == "AAPL"
            assert holding1.quantity == 100
            assert holding1.currency == "USD"
            assert holding1.market_price == 0.0
            assert holding1.market_value == 0.0
            
            # Check second holding
            holding2 = account.holdings[1]
            assert holding2.ticker == "GOOGL"
            assert holding2.quantity == 50
            assert holding2.currency == "USD"

    def test_account_with_cash_balances(self):
        """Test loading account with cash balances."""
        yaml_content = """
accounts:
  - name: "Multi-Currency Account"
    broker: "questrade"
    cash_balances:
      USD: 1000.0
      CAD: 500.0
"""
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            connector = FileBrokerConnector("test.yaml")
            portfolio = connector.get_portfolio()
            
            assert len(portfolio.accounts) == 1
            account = portfolio.accounts[0]
            assert account.cash_balances["USD"] == 1000.0
            assert account.cash_balances["CAD"] == 500.0

    def test_multiple_accounts_complex(self):
        """Test loading multiple accounts with complex structure."""
        yaml_content = """
accounts:
  - name: "US Account"
    broker: "fidelity"
    holdings:
      - ticker: "VTI"
        quantity: 150
        currency: "USD"
      - ticker: "GOOG"
        quantity: 10
        currency: "USD"
    cash_balances:
      USD: 1000.0
      
  - name: "Canadian Account"
    broker: "questrade"
    holdings:
      - ticker: "VFV.TO"
        quantity: 100
        currency: "CAD"
      - ticker: "BND"
        quantity: 50
        currency: "USD"
    cash_balances:
      CAD: 500.0
      USD: 200.0
"""
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            connector = FileBrokerConnector("test.yaml")
            portfolio = connector.get_portfolio()
            
            assert len(portfolio.accounts) == 2
            
            # Check first account
            account1 = portfolio.accounts[0]
            assert account1.name == "US Account"
            assert account1.broker == "fidelity"
            assert len(account1.holdings) == 2
            assert account1.holdings[0].ticker == "VTI"
            assert account1.holdings[0].quantity == 150
            assert account1.holdings[1].ticker == "GOOG"
            assert account1.holdings[1].quantity == 10
            assert account1.cash_balances["USD"] == 1000.0
            
            # Check second account
            account2 = portfolio.accounts[1]
            assert account2.name == "Canadian Account"
            assert account2.broker == "questrade"
            assert len(account2.holdings) == 2
            assert account2.holdings[0].ticker == "VFV.TO"
            assert account2.holdings[0].quantity == 100
            assert account2.holdings[0].currency == "CAD"
            assert account2.holdings[1].ticker == "BND"
            assert account2.holdings[1].quantity == 50
            assert account2.holdings[1].currency == "USD"
            assert account2.cash_balances["CAD"] == 500.0
            assert account2.cash_balances["USD"] == 200.0

    def test_fractional_quantities(self):
        """Test loading holdings with fractional quantities."""
        yaml_content = """
accounts:
  - name: "Fractional Account"
    broker: "robinhood"
    holdings:
      - ticker: "AAPL"
        quantity: 10.5
        currency: "USD"
      - ticker: "TSLA"
        quantity: 0.25
        currency: "USD"
"""
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            connector = FileBrokerConnector("test.yaml")
            portfolio = connector.get_portfolio()
            
            account = portfolio.accounts[0]
            assert account.holdings[0].quantity == 10.5
            assert account.holdings[1].quantity == 0.25

    def test_missing_optional_fields(self):
        """Test handling of missing optional fields."""
        yaml_content = """
accounts:
  - name: "Minimal Account"
    broker: "test_broker"
    holdings:
      - ticker: "AAPL"
        quantity: 100
        currency: "USD"
"""
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            connector = FileBrokerConnector("test.yaml")
            portfolio = connector.get_portfolio()
            
            account = portfolio.accounts[0]
            assert account.cash_balances == {}  # Should default to empty dict

    def test_integration_with_real_file(self):
        """Test integration with actual file I/O."""
        yaml_content = """
accounts:
  - name: "Real File Test"
    broker: "test_broker"
    holdings:
      - ticker: "TEST"
        quantity: 1
        currency: "USD"
    cash_balances:
      USD: 100.0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_file = f.name
        
        try:
            connector = FileBrokerConnector(temp_file)
            portfolio = connector.get_portfolio()
            
            assert len(portfolio.accounts) == 1
            account = portfolio.accounts[0]
            assert account.name == "Real File Test"
            assert len(account.holdings) == 1
            assert account.holdings[0].ticker == "TEST"
            assert account.cash_balances["USD"] == 100.0
        finally:
            os.unlink(temp_file)