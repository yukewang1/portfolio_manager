import pytest
import requests
from unittest.mock import patch, MagicMock
from src.portfolio_manager.connectors.alpha_vantage import AlphaVantageConnector, AlphaVantageFXConnector


class TestAlphaVantageConnector:
    def setup_method(self):
        """Set up test fixtures."""
        self.api_key = "test_api_key"
        self.connector = AlphaVantageConnector(self.api_key)

    def test_initialization(self):
        """Test connector initialization."""
        assert self.connector.api_key == self.api_key

    @patch('src.portfolio_manager.connectors.alpha_vantage.requests.get')
    def test_get_prices_success_single_ticker(self, mock_get):
        """Test successful price fetching for single ticker."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Global Quote": {
                "01. symbol": "AAPL",
                "05. price": "150.25"
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        prices = self.connector.get_prices(["AAPL"])
        
        assert prices == {"AAPL": 150.25}
        mock_get.assert_called_once_with(
            "https://www.alphavantage.co/query",
            params={
                "function": "GLOBAL_QUOTE",
                "symbol": "AAPL",
                "apikey": self.api_key
            }
        )

    @patch('src.portfolio_manager.connectors.alpha_vantage.requests.get')
    def test_get_prices_success_multiple_tickers(self, mock_get):
        """Test successful price fetching for multiple tickers."""
        def mock_response_side_effect(url, params):
            response = MagicMock()
            response.raise_for_status.return_value = None
            
            if params["symbol"] == "AAPL":
                response.json.return_value = {
                    "Global Quote": {
                        "01. symbol": "AAPL",
                        "05. price": "150.25"
                    }
                }
            elif params["symbol"] == "GOOGL":
                response.json.return_value = {
                    "Global Quote": {
                        "01. symbol": "GOOGL",
                        "05. price": "2500.75"
                    }
                }
            return response

        mock_get.side_effect = mock_response_side_effect
        
        prices = self.connector.get_prices(["AAPL", "GOOGL"])
        
        assert prices == {"AAPL": 150.25, "GOOGL": 2500.75}
        assert mock_get.call_count == 2

    @patch('src.portfolio_manager.connectors.alpha_vantage.requests.get')
    def test_get_prices_api_error_response(self, mock_get):
        """Test handling of API error responses."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Error Message": "Invalid API call"
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with patch('builtins.print') as mock_print:
            prices = self.connector.get_prices(["INVALID"])
            
            assert prices == {}
            mock_print.assert_called_once()
            assert "Warning: Could not fetch price for INVALID" in mock_print.call_args[0][0]

    @patch('src.portfolio_manager.connectors.alpha_vantage.requests.get')
    def test_get_prices_missing_price_field(self, mock_get):
        """Test handling of response missing price field."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Global Quote": {
                "01. symbol": "AAPL"
                # Missing "05. price" field
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with patch('builtins.print') as mock_print:
            prices = self.connector.get_prices(["AAPL"])
            
            assert prices == {}
            mock_print.assert_called_once()

    @patch('src.portfolio_manager.connectors.alpha_vantage.requests.get')
    def test_get_prices_network_error(self, mock_get):
        """Test handling of network errors."""
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        with patch('builtins.print') as mock_print:
            prices = self.connector.get_prices(["AAPL"])
            
            assert prices == {}
            mock_print.assert_called_once()
            assert "Error fetching price for AAPL" in mock_print.call_args[0][0]

    @patch('src.portfolio_manager.connectors.alpha_vantage.requests.get')
    def test_get_prices_http_error(self, mock_get):
        """Test handling of HTTP errors."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        with patch('builtins.print') as mock_print:
            prices = self.connector.get_prices(["AAPL"])
            
            assert prices == {}
            mock_print.assert_called_once()

    @patch('src.portfolio_manager.connectors.alpha_vantage.requests.get')
    def test_get_prices_partial_success(self, mock_get):
        """Test partial success when some tickers succeed and others fail."""
        def mock_response_side_effect(url, params):
            response = MagicMock()
            
            if params["symbol"] == "AAPL":
                response.raise_for_status.return_value = None
                response.json.return_value = {
                    "Global Quote": {
                        "01. symbol": "AAPL",
                        "05. price": "150.25"
                    }
                }
            elif params["symbol"] == "INVALID":
                response.raise_for_status.side_effect = requests.exceptions.HTTPError("Invalid symbol")
            
            return response

        mock_get.side_effect = mock_response_side_effect
        
        with patch('builtins.print'):
            prices = self.connector.get_prices(["AAPL", "INVALID"])
            
            assert prices == {"AAPL": 150.25}


class TestAlphaVantageFXConnector:
    def setup_method(self):
        """Set up test fixtures."""
        self.api_key = "test_api_key"
        self.connector = AlphaVantageFXConnector(self.api_key)

    def test_initialization(self):
        """Test connector initialization."""
        assert self.connector.api_key == self.api_key

    @patch('src.portfolio_manager.connectors.alpha_vantage.requests.get')
    def test_get_rates_success(self, mock_get):
        """Test successful FX rate fetching."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Realtime Currency Exchange Rate": {
                "1. From_Currency Code": "CAD",
                "3. To_Currency Code": "USD",
                "5. Exchange Rate": "0.7500"
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        rates = self.connector.get_rates("CAD", "USD")
        
        assert rates == {"CADUSD": 0.75}
        mock_get.assert_called_once_with(
            "https://www.alphavantage.co/query",
            params={
                "function": "CURRENCY_EXCHANGE_RATE",
                "from_currency": "CAD",
                "to_currency": "USD",
                "apikey": self.api_key
            }
        )

    @patch('src.portfolio_manager.connectors.alpha_vantage.requests.get')
    def test_get_rates_api_error_response(self, mock_get):
        """Test handling of API error responses."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Error Message": "Invalid API call"
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with patch('builtins.print') as mock_print:
            rates = self.connector.get_rates("CAD", "USD")
            
            assert rates == {}
            mock_print.assert_called_once()
            assert "Warning: Could not fetch FX rate for CAD->USD" in mock_print.call_args[0][0]

    @patch('src.portfolio_manager.connectors.alpha_vantage.requests.get')
    def test_get_rates_missing_exchange_rate(self, mock_get):
        """Test handling of response missing exchange rate."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Realtime Currency Exchange Rate": {
                "1. From_Currency Code": "CAD",
                "3. To_Currency Code": "USD"
                # Missing "5. Exchange Rate" field
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with patch('builtins.print') as mock_print:
            rates = self.connector.get_rates("CAD", "USD")
            assert rates == {}
            mock_print.assert_called_once()
            assert "Warning: Could not fetch FX rate for CAD->USD" in mock_print.call_args[0][0]

    @patch('src.portfolio_manager.connectors.alpha_vantage.requests.get')
    def test_get_rates_network_error(self, mock_get):
        """Test handling of network errors."""
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        with patch('builtins.print') as mock_print:
            rates = self.connector.get_rates("CAD", "USD")
            
            assert rates == {}
            mock_print.assert_called_once()
            assert "Error fetching FX rate" in mock_print.call_args[0][0]

    @patch('src.portfolio_manager.connectors.alpha_vantage.requests.get')
    def test_get_rates_http_error(self, mock_get):
        """Test handling of HTTP errors."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("429 Too Many Requests")
        mock_get.return_value = mock_response

        with patch('builtins.print') as mock_print:
            rates = self.connector.get_rates("CAD", "USD")
            
            assert rates == {}
            mock_print.assert_called_once()

    @patch('src.portfolio_manager.connectors.alpha_vantage.requests.get')
    def test_get_rates_different_currencies(self, mock_get):
        """Test FX rate fetching for different currency pairs."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Realtime Currency Exchange Rate": {
                "1. From_Currency Code": "EUR",
                "3. To_Currency Code": "USD",
                "5. Exchange Rate": "1.1000"
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        rates = self.connector.get_rates("EUR", "USD")
        
        assert rates == {"EURUSD": 1.1}

    @patch('src.portfolio_manager.connectors.alpha_vantage.requests.get')
    def test_get_rates_rate_limit_response(self, mock_get):
        """Test handling of rate limit responses."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Information": "We have detected your API key and our standard API rate limit is 25 requests per day."
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with patch('builtins.print') as mock_print:
            rates = self.connector.get_rates("CAD", "USD")
            
            assert rates == {}
            mock_print.assert_called_once()
            assert "rate limit" in mock_print.call_args[0][0].lower()