from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Holding:
    """Represents a single asset holding."""
    ticker: str
    quantity: float
    currency: str  # Native currency of the asset
    market_price: float = 0.0
    market_value: float = 0.0

@dataclass
class Account:
    """Represents a single account at a broker."""
    name: str
    broker: str
    holdings: List[Holding] = field(default_factory=list)
    # Cash balances in multiple currencies
    cash_balances: Dict[str, float] = field(default_factory=dict)
    total_value: float = 0.0 # In the reporting currency

@dataclass
class Portfolio:
    """Represents the entire portfolio across all accounts."""
    accounts: List[Account] = field(default_factory=list)
    total_value: float = 0.0 # In the reporting currency
