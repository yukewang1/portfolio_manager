import pytest
from unittest.mock import patch, MagicMock, mock_open
from src.portfolio_manager.engine import Engine, load_config
from src.portfolio_manager.models import Portfolio, Account, Holding


class TestLoadConfig:
    def test_load_config_success(self):
        """Test successful config loading."""
        yaml_content = """
reporting_currency: "USD"
portfolio_file: "test.yaml"
api_keys:
  alpha_vantage: "test_key"
"""
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config = load_config("config.yaml")
            assert config["reporting_currency"] == "USD"
            assert config["portfolio_file"] == "test.yaml"
            assert config["api_keys"]["alpha_vantage"] == "test_key"

    def test_load_config_file_not_found(self):
        """Test config loading when file doesn't exist."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            with pytest.raises(FileNotFoundError):
                load_config("nonexistent.yaml")


class TestEngine:
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "reporting_currency": "USD",
            "portfolio_file": "test.yaml",
            "api_keys": {"alpha_vantage": "test_key"},
            "rebalance_options": {
                "skip_tickers": ["GOOG"],
                "rebalance_threshold": 5.0
            }
        }
        
        # Mock portfolio data
        self.mock_portfolio = Portfolio(
            accounts=[
                Account(
                    name="Test Account",
                    broker="test_broker",
                    holdings=[
                        Holding(ticker="VTI", quantity=100, currency="USD", market_value=25000.0),
                        Holding(ticker="GOOG", quantity=10, currency="USD", market_value=17500.0),
                        Holding(ticker="VFV.TO", quantity=50, currency="CAD", market_value=10000.0)
                    ],
                    cash_balances={"USD": 1000.0, "CAD": 500.0}
                )
            ]
        )

    def test_engine_initialization_success(self):
        """Test successful engine initialization."""
        with patch('src.portfolio_manager.engine.FileBrokerConnector') as mock_connector:
            mock_connector.return_value.get_portfolio.return_value = self.mock_portfolio
            
            engine = Engine(self.config)
            assert engine.config == self.config
            assert engine.portfolio == self.mock_portfolio
            assert engine.fx_rates == {"USD": 1.0}

    def test_engine_initialization_no_portfolio_file(self):
        """Test engine initialization with missing portfolio_file config."""
        config = self.config.copy()
        del config["portfolio_file"]
        
        with pytest.raises(ValueError, match="'portfolio_file' not specified"):
            Engine(config)

    def test_engine_initialization_invalid_api_key(self):
        """Test engine initialization with invalid API key."""
        config = self.config.copy()
        config["api_keys"]["alpha_vantage"] = "YOUR_API_KEY_HERE"
        
        with patch('src.portfolio_manager.engine.FileBrokerConnector') as mock_connector:
            mock_connector.return_value.get_portfolio.return_value = self.mock_portfolio
            
            with pytest.raises(ValueError, match="Alpha Vantage API key not found"):
                Engine(config)

    def test_get_all_tickers(self):
        """Test getting all unique tickers from portfolio."""
        with patch('src.portfolio_manager.engine.FileBrokerConnector') as mock_connector:
            mock_connector.return_value.get_portfolio.return_value = self.mock_portfolio
            
            engine = Engine(self.config)
            tickers = engine._get_all_tickers()
            
            assert tickers == {"VTI", "GOOG", "VFV.TO"}

    def test_get_all_currencies(self):
        """Test getting all unique currencies from portfolio."""
        with patch('src.portfolio_manager.engine.FileBrokerConnector') as mock_connector:
            mock_connector.return_value.get_portfolio.return_value = self.mock_portfolio
            
            engine = Engine(self.config)
            currencies = engine._get_all_currencies()
            
            assert currencies == {"USD", "CAD"}

    def test_calculate_market_values(self):
        """Test calculating market values for holdings."""
        with patch('src.portfolio_manager.engine.FileBrokerConnector') as mock_connector:
            mock_connector.return_value.get_portfolio.return_value = self.mock_portfolio
            
            engine = Engine(self.config)
            engine.market_data = {"VTI": 250.0, "GOOG": 1750.0, "VFV.TO": 200.0}
            
            engine._calculate_market_values()
            
            holdings = engine.portfolio.accounts[0].holdings
            assert holdings[0].market_value == 25000.0  # 100 * 250
            assert holdings[1].market_value == 17500.0  # 10 * 1750
            assert holdings[2].market_value == 10000.0  # 50 * 200

    def test_normalize_to_reporting_currency(self):
        """Test normalizing portfolio values to reporting currency."""
        with patch('src.portfolio_manager.engine.FileBrokerConnector') as mock_connector:
            mock_connector.return_value.get_portfolio.return_value = self.mock_portfolio
            
            engine = Engine(self.config)
            engine.fx_rates = {"USD": 1.0, "CAD": 0.75}
            
            # Set market values
            engine.portfolio.accounts[0].holdings[0].market_value = 25000.0  # VTI
            engine.portfolio.accounts[0].holdings[1].market_value = 17500.0  # GOOG
            engine.portfolio.accounts[0].holdings[2].market_value = 10000.0  # VFV.TO (CAD)
            
            engine._normalize_to_reporting_currency()
            
            account = engine.portfolio.accounts[0]
            # Expected: 25000 + 17500 + (10000 * 0.75) + 1000 + (500 * 0.75) = 51375
            assert account.total_value == 51375.0
            assert engine.portfolio.total_value == 51375.0

    def test_get_current_allocations(self):
        """Test getting current allocations with skip_tickers."""
        with patch('src.portfolio_manager.engine.FileBrokerConnector') as mock_connector:
            mock_connector.return_value.get_portfolio.return_value = self.mock_portfolio
            
            engine = Engine(self.config)
            engine.fx_rates = {"USD": 1.0, "CAD": 0.75}
            
            # Set market values
            engine.portfolio.accounts[0].holdings[0].market_value = 25000.0  # VTI
            engine.portfolio.accounts[0].holdings[1].market_value = 17500.0  # GOOG (skipped)
            engine.portfolio.accounts[0].holdings[2].market_value = 10000.0  # VFV.TO (CAD)
            
            engine._normalize_to_reporting_currency()
            
            allocations = engine.get_current_allocations()
            
            # Active portfolio value excludes GOOG (17500 USD)
            # Active value: 25000 + (10000 * 0.75) + 1000 + (500 * 0.75) = 33875
            active_value = 33875.0
            expected_vti_allocation = 25000.0 / active_value
            expected_vfv_allocation = (10000.0 * 0.75) / active_value
            
            assert allocations["VTI"] == expected_vti_allocation
            assert allocations["VFV.TO"] == expected_vfv_allocation
            assert "GOOG" not in allocations  # Should be skipped

    def test_calculate_drift(self):
        """Test drift calculation between current and target allocations."""
        with patch('src.portfolio_manager.engine.FileBrokerConnector') as mock_connector:
            mock_connector.return_value.get_portfolio.return_value = self.mock_portfolio
            
            engine = Engine(self.config)
            
            current_allocations = {"VTI": 0.6, "VXUS": 0.2, "BND": 0.2}
            target_allocations = {"VTI": 0.6, "VXUS": 0.3, "BND": 0.1}
            
            drift = engine.calculate_drift(current_allocations, target_allocations)
            
            # Expected drift: (|0.6-0.6| + |0.2-0.3| + |0.2-0.1|) / 2 * 100 = 10%
            assert drift == 10.0

    def test_generate_rebalancing_plan(self):
        """Test generating rebalancing plan."""
        with patch('src.portfolio_manager.engine.FileBrokerConnector') as mock_connector:
            mock_connector.return_value.get_portfolio.return_value = self.mock_portfolio
            
            engine = Engine(self.config)
            engine.portfolio.total_value = 100000.0
            
            # Mock _get_active_portfolio_value
            with patch.object(engine, '_get_active_portfolio_value', return_value=50000.0):
                current_allocations = {"VTI": 0.6, "VXUS": 0.0, "BND": 0.4}
                target_allocations = {"VTI": 0.6, "VXUS": 0.3, "BND": 0.1}
                
                plan = engine.generate_rebalancing_plan(current_allocations, target_allocations)
                
                # Should buy VXUS (0.3 * 50000 = 15000) and sell BND (0.3 * 50000 = 15000)
                assert "BUY    15,000.00 USD of VXUS" in plan
                assert "SELL   15,000.00 USD of BND" in plan

    def test_get_active_portfolio_value(self):
        """Test getting active portfolio value excluding skipped tickers."""
        with patch('src.portfolio_manager.engine.FileBrokerConnector') as mock_connector:
            mock_connector.return_value.get_portfolio.return_value = self.mock_portfolio
            
            engine = Engine(self.config)
            engine.fx_rates = {"USD": 1.0, "CAD": 0.75}
            engine.portfolio.total_value = 100000.0
            
            # Set market values
            engine.portfolio.accounts[0].holdings[0].market_value = 25000.0  # VTI
            engine.portfolio.accounts[0].holdings[1].market_value = 17500.0  # GOOG (skipped)
            engine.portfolio.accounts[0].holdings[2].market_value = 10000.0  # VFV.TO (CAD)
            
            active_value = engine._get_active_portfolio_value()
            
            # Total - GOOG value normalized to USD = 100000 - 17500 = 82500
            assert active_value == 82500.0

    def test_get_aggregated_active_holdings(self):
        """Test getting aggregated active holdings excluding skipped tickers."""
        with patch('src.portfolio_manager.engine.FileBrokerConnector') as mock_connector:
            mock_connector.return_value.get_portfolio.return_value = self.mock_portfolio
            
            engine = Engine(self.config)
            engine.fx_rates = {"USD": 1.0, "CAD": 0.75}
            
            # Set market values
            engine.portfolio.accounts[0].holdings[0].market_value = 25000.0  # VTI
            engine.portfolio.accounts[0].holdings[1].market_value = 17500.0  # GOOG (skipped)
            engine.portfolio.accounts[0].holdings[2].market_value = 10000.0  # VFV.TO (CAD)
            
            aggregated = engine._get_aggregated_active_holdings()
            
            assert aggregated["VTI"] == 25000.0
            assert aggregated["VFV.TO"] == 7500.0  # 10000 * 0.75
            assert "GOOG" not in aggregated  # Should be skipped

    @patch('src.portfolio_manager.engine.AlphaVantageConnector')
    @patch('src.portfolio_manager.engine.AlphaVantageFXConnector')
    def test_run_integration(self, mock_fx_connector, mock_market_connector):
        """Test the main run method integration."""
        with patch('src.portfolio_manager.engine.FileBrokerConnector') as mock_file_connector:
            mock_file_connector.return_value.get_portfolio.return_value = self.mock_portfolio
            
            # Mock market data and FX connectors
            mock_market_connector.return_value.get_prices.return_value = {
                "VTI": 250.0, "GOOG": 1750.0, "VFV.TO": 200.0
            }
            mock_fx_connector.return_value.get_rates.return_value = {"CAD": 0.75}
            
            engine = Engine(self.config)
            engine.run()
            
            # Verify methods were called
            mock_market_connector.return_value.get_prices.assert_called_once()
            mock_fx_connector.return_value.get_rates.assert_called_once()
            
            # Verify portfolio has been updated
            assert engine.portfolio.total_value > 0