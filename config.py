POLYMARKET_API_URL = "https://gamma-api.polymarket.com/events"
POLYMARKET_ORDERBOOK_URL = "https://clob.polymarket.com/book"
KALSHI_API_URL = "https://trading-api.kalshi.com/trade-api/v2"

STRATEGY_CONFIG = {
    "buy_no_early": {
        "max_age_minutes": 20,
        "min_yes_price": 0.70,
        "min_volume": 1000,
        "min_liquidity": 500,
        "max_spread": 0.10,
        "min_expected_return": 0.10,
        "confidence_threshold": 0.60,
    },
    "position_sizing": {
        "kelly_fraction": 0.25,
        "max_position_size": 1000,
        "min_position_size": 100,
    },
    "risk_management": {
        "max_drawdown": 0.20,
        "stop_loss": 0.15,
        "take_profit": 0.30,
        "max_concurrent_positions": 5,
    }
}

HISTORICAL_YES_RATE = 0.22
HISTORICAL_NO_RATE = 0.78

CATEGORY_YES_RATES = {
    "crypto": 0.18,
    "politics": 0.25,
    "sports": 0.48,
    "weather": 0.35,
    "finance": 0.28,
    "entertainment": 0.20,
    "technology": 0.22,
    "default": 0.22
}

SENSATIONAL_KEYWORDS = [
    "war", "collapse", "crisis", "crash", "revolutionary",
    "unprecedented", "shocking", "dramatic", "explosive",
    "catastrophic", "miracle", "scandal", "emergency"
]

CRYPTO_KEYWORDS = [
    "bitcoin", "ethereum", "crypto", "token", "nft", "defi",
    "blockchain", "coin", "web3", "airdrop", "launch"
]

POLITICS_KEYWORDS = [
    "president", "election", "congress", "senate", "vote",
    "policy", "governor", "politician", "impeach", "resign"
]

BACKTEST_CONFIG = {
    "initial_capital": 10000,
    "transaction_fee": 0.02,
    "slippage": 0.01,
    "min_hold_minutes": 60,
    "max_hold_minutes": 4320,
}

FETCH_CONFIG = {
    "timeout": 10,
    "retry_attempts": 3,
    "retry_delay": 2,
    "rate_limit_delay": 1,
}
