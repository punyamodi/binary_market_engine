import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class MarketData:
    id: str
    platform: str
    question: str
    yes_price: float
    no_price: float
    volume: float
    liquidity: float
    spread: float
    age_minutes: Optional[float]
    timestamp: str
    description: str
    end_date: Optional[str] = None


@dataclass
class Position:
    market_id: str
    symbol: str
    side: str
    quantity: float
    entry_price: float
    current_price: float
    open_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    max_hold_minutes: Optional[int] = None

    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        return (self.current_price - self.entry_price) * self.quantity

    @property
    def unrealized_pnl_pct(self) -> float:
        if self.entry_price == 0:
            return 0.0
        return (self.current_price - self.entry_price) / self.entry_price

    @property
    def age_minutes(self) -> float:
        return (datetime.now() - self.open_time).total_seconds() / 60.0


@dataclass
class Trade:
    market_id: str
    symbol: str
    side: str
    action: str
    quantity: float
    price: float
    reason: str
    realized_pnl: float = 0.0
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Signal:
    market_id: str
    market: MarketData
    outcome: str
    true_yes_prob: float
    true_no_prob: float
    confidence: float
    expected_value: float
    edge: float
    kelly_pct: float
    recommended_position_usd: float
    sharpe_ratio: float
    implied_volatility: float
    reason: str
    risk_reward: float


@dataclass
class PortfolioSnapshot:
    timestamp: datetime
    cash: float
    positions_value: float
    total_equity: float
    unrealized_pnl: float
    position_count: int

    @property
    def total_return_pct(self) -> float:
        return 0.0
