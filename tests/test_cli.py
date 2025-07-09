import pytest
from unittest.mock import patch, MagicMock, mock_open
from click.testing import CliRunner
from src.portfolio_manager.cli import cli, show, rebalance
from src.portfolio_manager.models import Portfolio, Account, Holding
from src.portfolio_manager.engine import Engine


class TestCLI:
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        
        # Mock config
        self.mock_config = {
            "reporting_currency": "USD",
            "portfolio_file": "test.yaml",
            "api_keys": {"alpha_vantage": "test_key"},
            "rebalance_options": {
                "skip_tickers": ["GOOG"],
                "rebalance_threshold": 5.0
            }
        }
        
        # Mock portfolio
        self.mock_portfolio = Portfolio(
            accounts=[
                Account(
                    name="Test Account",
                    broker="test_broker",
                    holdings=[
                        Holding(ticker="VTI", quantity=100, currency="USD", market_value=25000.0, market_price=250.0),
                        Holding(ticker="GOOG", quantity=10, currency="USD", market_value=17500.0, market_price=1750.0)
                    ],
                    cash_balances={"USD": 1000.0},
                    total_value=43500.0
                )
            ],
            total_value=43500.0
        )
        
        # Mock engine
        self.mock_engine = MagicMock(spec=Engine)
        self.mock_engine.portfolio = self.mock_portfolio
        self.mock_engine.fx_rates = {"USD": 1.0}
        self.mock_engine.get_current_allocations.return_value = {
            "VTI": 0.6, "GOOG": 0.4
        }
        self.mock_engine.calculate_drift.return_value = 15.0

    def test_cli_group_help(self):
        """Test CLI group help command."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "A CLI tool to manage your investment portfolio" in result.output
        assert "show" in result.output
        assert "rebalance" in result.output

    def test_show_command_help(self):
        """Test show command help."""
        result = self.runner.invoke(cli, ['show', '--help'])
        assert result.exit_code == 0
        assert "Displays the current state of the portfolio" in result.output

    def test_rebalance_command_help(self):
        """Test rebalance command help."""
        result = self.runner.invoke(cli, ['rebalance', '--help'])
        assert result.exit_code == 0
        assert "Calculates and displays the rebalancing plan" in result.output
        assert "--target" in result.output

    @patch('src.portfolio_manager.cli.Engine')
    @patch('src.portfolio_manager.cli.load_config')
    def test_show_command_success(self, mock_load_config, mock_engine_class):
        """Test successful show command execution."""
        mock_load_config.return_value = self.mock_config
        mock_engine_class.return_value = self.mock_engine
        
        # Mock target file
        target_content = '{"VTI": 0.6, "VXUS": 0.3, "BND": 0.1}'
        with patch("builtins.open", mock_open(read_data=target_content)):
            result = self.runner.invoke(cli, ['show'])
        
        assert result.exit_code == 0
        assert "Analyzing portfolio..." in result.output
        assert "Reporting Currency: USD" in result.output
        assert "Test Account" in result.output
        assert "Total Portfolio Value: 43,500.00 USD" in result.output
        assert "Allocation Drift: 15.00%" in result.output
        assert "Rebalance Threshold: 5.00%" in result.output
        assert "REBALANCE" in result.output

    @patch('src.portfolio_manager.cli.Engine')
    @patch('src.portfolio_manager.cli.load_config')
    def test_show_command_no_rebalance_needed(self, mock_load_config, mock_engine_class):
        """Test show command when no rebalancing is needed."""
        mock_load_config.return_value = self.mock_config
        mock_engine = self.mock_engine
        mock_engine.calculate_drift.return_value = 3.0  # Below threshold
        mock_engine_class.return_value = mock_engine
        
        target_content = '{"VTI": 0.6, "VXUS": 0.3, "BND": 0.1}'
        with patch("builtins.open", mock_open(read_data=target_content)):
            result = self.runner.invoke(cli, ['show'])
        
        assert result.exit_code == 0
        assert "Allocation Drift: 3.00%" in result.output
        assert "HOLD" in result.output

    @patch('src.portfolio_manager.cli.Engine')
    @patch('src.portfolio_manager.cli.load_config')
    def test_show_command_detailed_output(self, mock_load_config, mock_engine_class):
        """Test show command detailed output format."""
        mock_load_config.return_value = self.mock_config
        mock_engine_class.return_value = self.mock_engine
        
        target_content = '{"VTI": 0.6, "VXUS": 0.3, "BND": 0.1}'
        with patch("builtins.open", mock_open(read_data=target_content)):
            result = self.runner.invoke(cli, ['show'])
        
        assert result.exit_code == 0
        
        # Check account details
        assert "Account: Test Account (test_broker)" in result.output
        assert "VTI" in result.output
        assert "100.00" in result.output  # quantity
        assert "250.00" in result.output  # price
        assert "25,000.00 USD" in result.output  # value
        assert "GOOG" in result.output
        assert "1,000.00 USD" in result.output  # cash balance
        assert "Total Account Value: 43,500.00 USD" in result.output

    @patch('src.portfolio_manager.cli.Engine')
    @patch('src.portfolio_manager.cli.load_config')
    def test_rebalance_command_success(self, mock_load_config, mock_engine_class):
        """Test successful rebalance command execution."""
        mock_load_config.return_value = self.mock_config
        mock_engine = self.mock_engine
        mock_engine.generate_rebalancing_plan.return_value = [
            "BUY    15,000.00 USD of VXUS",
            "SELL   10,000.00 USD of VTI"
        ]
        mock_engine_class.return_value = mock_engine
        
        target_content = '{"VTI": 0.6, "VXUS": 0.3, "BND": 0.1}'
        with patch("builtins.open", mock_open(read_data=target_content)):
            result = self.runner.invoke(cli, ['rebalance'])
        
        assert result.exit_code == 0
        assert "Calculating rebalancing plan..." in result.output
        assert "Allocation Drift is 15.00%" in result.output
        assert "Rebalancing is recommended" in result.output
        assert "BUY    15,000.00 USD of VXUS" in result.output
        assert "SELL   10,000.00 USD of VTI" in result.output

    @patch('src.portfolio_manager.cli.Engine')
    @patch('src.portfolio_manager.cli.load_config')
    def test_rebalance_command_no_rebalance_needed(self, mock_load_config, mock_engine_class):
        """Test rebalance command when no rebalancing is needed."""
        mock_load_config.return_value = self.mock_config
        mock_engine = self.mock_engine
        mock_engine.calculate_drift.return_value = 3.0  # Below threshold
        mock_engine_class.return_value = mock_engine
        
        target_content = '{"VTI": 0.6, "VXUS": 0.3, "BND": 0.1}'
        with patch("builtins.open", mock_open(read_data=target_content)):
            result = self.runner.invoke(cli, ['rebalance'])
        
        assert result.exit_code == 0
        assert "Allocation Drift is 3.00%" in result.output
        assert "No rebalancing required" in result.output

    @patch('src.portfolio_manager.cli.Engine')
    @patch('src.portfolio_manager.cli.load_config')
    def test_rebalance_command_custom_target(self, mock_load_config, mock_engine_class):
        """Test rebalance command with custom target file."""
        mock_load_config.return_value = self.mock_config
        mock_engine = self.mock_engine
        mock_engine.generate_rebalancing_plan.return_value = [
            "BUY    20,000.00 USD of BND"
        ]
        mock_engine_class.return_value = mock_engine
        
        target_content = '{"VTI": 0.5, "BND": 0.5}'
        with patch("builtins.open", mock_open(read_data=target_content)):
            result = self.runner.invoke(cli, ['rebalance', '--target', 'custom_target.json'])
        
        assert result.exit_code == 0
        assert "BUY    20,000.00 USD of BND" in result.output

    @patch('src.portfolio_manager.cli.load_config')
    def test_show_command_config_file_error(self, mock_load_config):
        """Test show command with config file error."""
        mock_load_config.side_effect = FileNotFoundError("Config file not found")
        
        result = self.runner.invoke(cli, ['show'])
        assert result.exit_code != 0

    @patch('src.portfolio_manager.cli.Engine')
    @patch('src.portfolio_manager.cli.load_config')
    def test_show_command_target_file_error(self, mock_load_config, mock_engine_class):
        """Test show command with target file error."""
        mock_load_config.return_value = self.mock_config
        mock_engine_class.return_value = self.mock_engine
        
        with patch("builtins.open", side_effect=FileNotFoundError("Target file not found")):
            result = self.runner.invoke(cli, ['show'])
        
        assert result.exit_code != 0

    @patch('src.portfolio_manager.cli.Engine')
    @patch('src.portfolio_manager.cli.load_config')
    def test_rebalance_command_target_file_error(self, mock_load_config, mock_engine_class):
        """Test rebalance command with target file error."""
        mock_load_config.return_value = self.mock_config
        mock_engine_class.return_value = self.mock_engine
        
        with patch("builtins.open", side_effect=FileNotFoundError("Target file not found")):
            result = self.runner.invoke(cli, ['rebalance'])
        
        assert result.exit_code != 0

    @patch('src.portfolio_manager.cli.Engine')
    @patch('src.portfolio_manager.cli.load_config')
    def test_show_command_engine_error(self, mock_load_config, mock_engine_class):
        """Test show command with engine initialization error."""
        mock_load_config.return_value = self.mock_config
        mock_engine_class.side_effect = ValueError("Invalid API key")
        
        result = self.runner.invoke(cli, ['show'])
        assert result.exit_code != 0

    @patch('src.portfolio_manager.cli.Engine')
    @patch('src.portfolio_manager.cli.load_config')
    def test_multi_currency_display(self, mock_load_config, mock_engine_class):
        """Test display of multi-currency portfolio."""
        mock_load_config.return_value = self.mock_config
        
        # Create multi-currency portfolio
        multi_currency_portfolio = Portfolio(
            accounts=[
                Account(
                    name="Multi-Currency Account",
                    broker="questrade",
                    holdings=[
                        Holding(ticker="VFV.TO", quantity=100, currency="CAD", market_value=15000.0, market_price=150.0)
                    ],
                    cash_balances={"CAD": 500.0, "USD": 200.0},
                    total_value=15700.0
                )
            ],
            total_value=15700.0
        )
        
        mock_engine = MagicMock(spec=Engine)
        mock_engine.portfolio = multi_currency_portfolio
        mock_engine.fx_rates = {"USD": 1.0, "CAD": 0.75}
        mock_engine.get_current_allocations.return_value = {"VFV.TO": 1.0}
        mock_engine.calculate_drift.return_value = 10.0
        mock_engine_class.return_value = mock_engine
        
        target_content = '{"VFV.TO": 1.0}'
        with patch("builtins.open", mock_open(read_data=target_content)):
            result = self.runner.invoke(cli, ['show'])
        
        assert result.exit_code == 0
        assert "VFV.TO" in result.output
        assert "15,000.00 CAD" in result.output
        assert "500.00 CAD" in result.output
        assert "200.00 USD" in result.output
        assert "FX Rates (vs USD): {'USD': 1.0, 'CAD': 0.75}" in result.output