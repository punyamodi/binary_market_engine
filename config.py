from dataclasses import dataclass, field
from typing import Dict, List


POLYMARKET_API_URL = "https://gamma-api.polymarket.com/events"
KALSHI_API_URL = "https://trading-api.kalshi.com/trade-api/v2"

HISTORICAL_YES_RATE: float = 0.22

CATEGORY_YES_RATES: Dict[str, float] = {
    "crypto": 0.18,
    "politics": 0.25,
    "sports": 0.48,
    "weather": 0.35,
    "finance": 0.28,
    "entertainment": 0.20,
    "technology": 0.22,
    "default": 0.22,
}

SENSATIONAL_KEYWORDS: List[str] = [
    "war", "collapse", "crisis", "crash", "revolutionary",
    "unprecedented", "shocking", "dramatic", "explosive",
    "catastrophic", "miracle", "scandal", "emergency",
]

CRYPTO_KEYWORDS: List[str] = [
    "bitcoin", "ethereum", "crypto", "token", "nft", "defi",
    "blockchain", "coin", "web3", "airdrop", "launch",
]

POLITICS_KEYWORDS: List[str] = [
    "president", "election", "congress", "senate", "vote",
    "policy", "governor", "politician", "impeach", "resign",
]

SPORTS_KEYWORDS: List[str] = [
    "nba", "nfl", "mlb", "nhl", "fifa", "championship", "league",
    "win", "score", "match", "game", "tournament", "playoff",
]

WEATHER_KEYWORDS: List[str] = [
    "rain", "snow", "hurricane", "tornado", "flood", "temperature",
    "celsius", "fahrenheit", "weather", "storm", "drought",
]


@dataclass
class StrategyConfig:
    max_age_minutes: float = 20.0
    min_yes_price: float = 0.70
    min_volume: float = 1000.0
    min_liquidity: float = 500.0
    max_spread: float = 0.10
    min_expected_return: float = 0.10
    confidence_threshold: float = 0.60
    sensationalism_adjustment: float = 0.5


@dataclass
class PositionSizingConfig:
    kelly_fraction: float = 0.25
    max_position_usd: float = 1000.0
    min_position_usd: float = 100.0


@dataclass
class RiskConfig:
    stop_loss_pct: float = 0.10
    take_profit_pct: float = 0.20
    max_hold_minutes: int = 60
    max_concurrent_positions: int = 5
    max_portfolio_drawdown: float = 0.20


@dataclass
class BacktestConfig:
    initial_capital: float = 10000.0
    transaction_fee: float = 0.02
    slippage: float = 0.005


@dataclass
class FetchConfig:
    timeout: int = 10
    retry_attempts: int = 3
    retry_delay: float = 2.0
    rate_limit_delay: float = 1.0


@dataclass
class AppConfig:
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    position_sizing: PositionSizingConfig = field(default_factory=PositionSizingConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    fetch: FetchConfig = field(default_factory=FetchConfig)


def default_config() -> AppConfig:
    return AppConfig()

