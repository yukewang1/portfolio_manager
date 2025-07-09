import pytest
from src.portfolio_manager.models import Holding, Account, Portfolio


class TestHolding:
    def test_holding_creation(self):
        """Test creating a basic holding."""
        holding = Holding(
            ticker="AAPL",
            quantity=100.0,
            currency="USD"
        )
        assert holding.ticker == "AAPL"
        assert holding.quantity == 100.0
        assert holding.currency == "USD"
        assert holding.market_price == 0.0
        assert holding.market_value == 0.0

    def test_holding_with_market_data(self):
        """Test holding with market price and value."""
        holding = Holding(
            ticker="GOOGL",
            quantity=50.0,
            currency="USD",
            market_price=2500.0,
            market_value=125000.0
        )
        assert holding.ticker == "GOOGL"
        assert holding.quantity == 50.0
        assert holding.currency == "USD"
        assert holding.market_price == 2500.0
        assert holding.market_value == 125000.0

    def test_holding_fractional_quantity(self):
        """Test holding with fractional shares."""
        holding = Holding(
            ticker="VTI",
            quantity=10.5,
            currency="USD"
        )
        assert holding.quantity == 10.5


class TestAccount:
    def test_account_creation_empty(self):
        """Test creating an empty account."""
        account = Account(
            name="Test Account",
            broker="test_broker"
        )
        assert account.name == "Test Account"
        assert account.broker == "test_broker"
        assert account.holdings == []
        assert account.cash_balances == {}
        assert account.total_value == 0.0

    def test_account_with_holdings(self):
        """Test account with holdings."""
        holdings = [
            Holding(ticker="AAPL", quantity=100.0, currency="USD"),
            Holding(ticker="GOOGL", quantity=50.0, currency="USD")
        ]
        account = Account(
            name="Investment Account",
            broker="fidelity",
            holdings=holdings
        )
        assert len(account.holdings) == 2
        assert account.holdings[0].ticker == "AAPL"
        assert account.holdings[1].ticker == "GOOGL"

    def test_account_with_cash_balances(self):
        """Test account with multiple currency cash balances."""
        cash_balances = {"USD": 1000.0, "CAD": 500.0}
        account = Account(
            name="Multi-Currency Account",
            broker="questrade",
            cash_balances=cash_balances
        )
        assert account.cash_balances["USD"] == 1000.0
        assert account.cash_balances["CAD"] == 500.0

    def test_account_with_total_value(self):
        """Test account with total value set."""
        account = Account(
            name="Valued Account",
            broker="test_broker",
            total_value=50000.0
        )
        assert account.total_value == 50000.0


class TestPortfolio:
    def test_portfolio_creation_empty(self):
        """Test creating an empty portfolio."""
        portfolio = Portfolio()
        assert portfolio.accounts == []
        assert portfolio.total_value == 0.0

    def test_portfolio_with_accounts(self):
        """Test portfolio with multiple accounts."""
        account1 = Account(name="Account 1", broker="broker1")
        account2 = Account(name="Account 2", broker="broker2")
        portfolio = Portfolio(accounts=[account1, account2])
        
        assert len(portfolio.accounts) == 2
        assert portfolio.accounts[0].name == "Account 1"
        assert portfolio.accounts[1].name == "Account 2"

    def test_portfolio_with_total_value(self):
        """Test portfolio with total value set."""
        portfolio = Portfolio(total_value=100000.0)
        assert portfolio.total_value == 100000.0

    def test_portfolio_complex_structure(self):
        """Test portfolio with complex nested structure."""
        # Create holdings
        holdings1 = [
            Holding(ticker="VTI", quantity=100.0, currency="USD", market_value=25000.0),
            Holding(ticker="VXUS", quantity=50.0, currency="USD", market_value=10000.0)
        ]
        holdings2 = [
            Holding(ticker="VFV.TO", quantity=200.0, currency="CAD", market_value=15000.0)
        ]
        
        # Create accounts
        account1 = Account(
            name="US Account",
            broker="fidelity",
            holdings=holdings1,
            cash_balances={"USD": 1000.0},
            total_value=36000.0
        )
        account2 = Account(
            name="Canadian Account", 
            broker="questrade",
            holdings=holdings2,
            cash_balances={"CAD": 500.0, "USD": 200.0},
            total_value=15700.0
        )
        
        # Create portfolio
        portfolio = Portfolio(
            accounts=[account1, account2],
            total_value=51700.0
        )
        
        # Verify structure
        assert len(portfolio.accounts) == 2
        assert portfolio.total_value == 51700.0
        assert len(portfolio.accounts[0].holdings) == 2
        assert len(portfolio.accounts[1].holdings) == 1
        assert portfolio.accounts[0].cash_balances["USD"] == 1000.0
        assert portfolio.accounts[1].cash_balances["CAD"] == 500.0