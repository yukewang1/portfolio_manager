# Portfolio Manager

![CI](https://github.com/yukewang1/portfolio_manager/workflows/CI/badge.svg)
[![codecov](https://codecov.io/gh/yukewang1/portfolio_manager/branch/main/graph/badge.svg)](https://codecov.io/gh/yukewang1/portfolio_manager)

A Python-based Command-Line Interface (CLI) tool designed to consolidate investment accounts, analyze them against a target allocation, and provide clear rebalancing instructions.

## Features

- **Unified Portfolio View**: See all accounts from multiple brokers in one place
- **Target-Based Rebalancing**: Generate buy/sell orders based on user-defined target allocation
- **Multi-Currency Management**: Normalize all assets and cash into a single reporting currency
- **Configurable Asset Skipping**: Allow certain tickers to be ignored during rebalancing
- **Allocation Drift Score & Threshold**: Calculate how "off-target" the portfolio is

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yukewang1/portfolio_manager.git
   cd portfolio_manager
   ```

2. Set up virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure your portfolio:
   ```bash
   cp config.yaml.example config.yaml
   cp portfolio.yaml.example portfolio.yaml
   # Edit config.yaml with your API keys and settings
   # Edit portfolio.yaml with your account holdings
   ```

## Usage

### View Portfolio
```bash
python main.py show
```

### Generate Rebalancing Plan
```bash
python main.py rebalance
```

### Custom Target Allocation
```bash
python main.py rebalance --target my_target.json
```

## Testing

Run the test suite:
```bash
python -m pytest tests/ -v
```

Run tests with coverage:
```bash
python -m pytest tests/ --cov=src --cov-report=term-missing
```

## Configuration

See `config.yaml.example` and `portfolio.yaml.example` for configuration examples.

## Development

This project uses:
- **Python 3.9+**: Main programming language
- **pytest**: Testing framework
- **Click**: CLI framework
- **Alpha Vantage**: Market data and FX rates
- **YAML**: Configuration format

## License

MIT License