import click
import json
from .engine import Engine, load_config

CONFIG_PATH = "config.yaml"

@click.group()
def cli():
    """A CLI tool to manage your investment portfolio."""
    pass

@cli.command()
def show():
    """Displays the current state of the portfolio."""
    click.echo("Analyzing portfolio...")
    
    config = load_config(CONFIG_PATH)
    engine = Engine(config)
    engine.run()

    # For now, we load the target here to calculate drift for the show command
    with open('target.json', 'r') as f:
        target_allocations = json.load(f)

    current_allocations = engine.get_current_allocations()
    drift = engine.calculate_drift(current_allocations, target_allocations)
    threshold = config.get('rebalance_options', {}).get('rebalance_threshold', 5.0)

    click.echo(f"\nReporting Currency: {config.get('reporting_currency')}\nFX Rates (vs {config.get('reporting_currency')}): {engine.fx_rates}\n\n--- Portfolio Details ---")

    for account in engine.portfolio.accounts:
        click.echo()
        click.echo(f"Account: {account.name} ({account.broker})")
        click.echo("--------------------------------------------------------------------------------")
        reporting_currency = config.get('reporting_currency', 'USD')
        click.echo(f"{'TICKER':<10} {'QTY':<10} {'PRICE':<10} {'VALUE (Native)':<18} {'VALUE (' + reporting_currency + ')':<18}")
        click.echo("--------------------------------------------------------------------------------")
        for holding in account.holdings:
            native_value_str = f"{holding.market_value:,.2f} {holding.currency}"
            normalized_value_str = f"{holding.market_value * engine.fx_rates.get(holding.currency, 1.0):,.2f} {config.get('reporting_currency')}"
            click.echo(f"{holding.ticker:<10} {holding.quantity:<10.2f} {holding.market_price:<10.2f} {native_value_str:<18} {normalized_value_str:<18}")
        
        # Display cash balances
        for currency, amount in account.cash_balances.items():
            normalized_cash_value_str = f"{amount * engine.fx_rates.get(currency, 1.0):,.2f} {config.get('reporting_currency')}"
            click.echo(f"{'Cash':<10} {'-':<10} {'-':<10} {f'{amount:,.2f} {currency}':<18} {normalized_cash_value_str:<18}")

        click.echo("--------------------------------------------------------------------------------")
        click.echo(f"Total Account Value: {account.total_value:,.2f} {config.get('reporting_currency')}")

    click.echo("Portfolio Summary ---")
    click.echo(f"Total Portfolio Value: {engine.portfolio.total_value:,.2f} {config.get('reporting_currency')}")
    click.echo(f"Allocation Drift: {drift:.2f}%")
    click.echo(f"Rebalance Threshold: {threshold:.2f}%")

    if drift > threshold:
        click.secho("Recommendation: REBALANCE (run 'rebalance' command)", fg="yellow")
    else:
        click.secho("Recommendation: HOLD", fg="green")

@cli.command()
@click.option('--target', default='target.json', help='Path to the target allocation JSON file.')
def rebalance(target):
    """Calculates and displays the rebalancing plan."""
    click.echo("Calculating rebalancing plan...")

    config = load_config(CONFIG_PATH)
    engine = Engine(config)
    engine.run()

    with open(target, 'r') as f:
        target_allocations = json.load(f)

    current_allocations = engine.get_current_allocations()
    drift = engine.calculate_drift(current_allocations, target_allocations)
    threshold = config.get('rebalance_options', {}).get('rebalance_threshold', 5.0)

    click.echo(f"Allocation Drift is {drift:.2f}%. Threshold is {threshold:.2f}%")

    if drift > threshold:
        click.echo("Rebalancing is recommended.")
        plan = engine.generate_rebalancing_plan(current_allocations, target_allocations)
        click.echo("Rebalancing Plan ---")
        for trade in plan:
            click.echo(trade)
    else:
        click.echo("No rebalancing required at this time.")
