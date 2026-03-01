import json
import logging
import time
from datetime import datetime, timedelta
from typing import List, Optional

import requests

import config
from models import MarketData

logger = logging.getLogger(__name__)


class MarketDataFetcher:
    def __init__(self, cfg: config.FetchConfig = None):
        self._cfg = cfg or config.FetchConfig()
        self._session = requests.Session()
        self._last_request_time: dict = {}

    def _rate_limited_get(self, url: str, params: dict = None, platform: str = "generic") -> Optional[dict]:
        now = time.time()
        last = self._last_request_time.get(platform, 0)
        wait = self._cfg.rate_limit_delay - (now - last)
        if wait > 0:
            time.sleep(wait)

        for attempt in range(self._cfg.retry_attempts):
            try:
                response = self._session.get(url, params=params, timeout=self._cfg.timeout)
                response.raise_for_status()
                self._last_request_time[platform] = time.time()
                return response.json()
            except requests.RequestException as exc:
                logger.warning("Request failed (attempt %d/%d): %s", attempt + 1, self._cfg.retry_attempts, exc)
                if attempt < self._cfg.retry_attempts - 1:
                    time.sleep(self._cfg.retry_delay * (attempt + 1))
        return None

    def fetch_polymarket_markets(self) -> List[MarketData]:
        params = {"limit": 50, "closed": "false", "order": "startDate", "ascending": "false"}
        data = self._rate_limited_get(config.POLYMARKET_API_URL, params=params, platform="polymarket")
        if not data:
            logger.warning("No data returned from Polymarket API")
            return []

        markets: List[MarketData] = []
        for event in data:
            for m in event.get("markets", []):
                parsed = self._parse_polymarket(event, m)
                if parsed:
                    markets.append(parsed)

        logger.info("Fetched %d markets from Polymarket", len(markets))
        return markets

    def _parse_polymarket(self, event: dict, market: dict) -> Optional[MarketData]:
        try:
            raw_prices = market.get("outcomePrices")
            if not raw_prices:
                return None
            outcomes = json.loads(raw_prices)
            if len(outcomes) < 2:
                return None

            yes_price = float(outcomes[0])
            no_price = float(outcomes[1])

            age_minutes: Optional[float] = None
            start_date_str = event.get("startDate")
            if start_date_str:
                try:
                    start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
                    age_minutes = (datetime.now(start_date.tzinfo) - start_date).total_seconds() / 60.0
                except ValueError:
                    pass

            return MarketData(
                id=market.get("id", "unknown"),
                platform="Polymarket",
                question=event.get("title", "Unknown"),
                yes_price=yes_price,
                no_price=no_price,
                volume=float(market.get("volume", 0)),
                liquidity=float(market.get("liquidity", 0)),
                spread=abs(yes_price + no_price - 1.0),
                age_minutes=age_minutes,
                timestamp=datetime.now().isoformat(),
                description=event.get("description", ""),
                end_date=event.get("endDate"),
            )
        except (KeyError, ValueError, TypeError) as exc:
            logger.debug("Failed to parse Polymarket market: %s", exc)
            return None

    def fetch_kalshi_markets(self, api_key: str) -> List[MarketData]:
        headers = {"Authorization": f"Bearer {api_key}"}
        url = f"{config.KALSHI_API_URL}/markets"
        params = {"limit": 50, "status": "open"}

        try:
            response = self._session.get(url, headers=headers, params=params, timeout=self._cfg.timeout)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            logger.warning("Kalshi API request failed: %s", exc)
            return []

        markets: List[MarketData] = []
        for m in data.get("markets", []):
            parsed = self._parse_kalshi(m)
            if parsed:
                markets.append(parsed)

        logger.info("Fetched %d markets from Kalshi", len(markets))
        return markets

    def _parse_kalshi(self, market: dict) -> Optional[MarketData]:
        try:
            yes_price = market.get("yes_bid", 50) / 100.0
            no_price = market.get("no_bid", 50) / 100.0

            age_minutes: Optional[float] = None
            open_time_str = market.get("open_time")
            if open_time_str:
                try:
                    open_time = datetime.fromisoformat(open_time_str.replace("Z", "+00:00"))
                    age_minutes = (datetime.now(open_time.tzinfo) - open_time).total_seconds() / 60.0
                except ValueError:
                    pass

            return MarketData(
                id=market.get("ticker", "unknown"),
                platform="Kalshi",
                question=market.get("title", "Unknown"),
                yes_price=yes_price,
                no_price=no_price,
                volume=float(market.get("volume", 0)),
                liquidity=float(market.get("open_interest", 0)),
                spread=abs(yes_price + no_price - 1.0),
                age_minutes=age_minutes,
                timestamp=datetime.now().isoformat(),
                description=market.get("subtitle", ""),
                end_date=market.get("close_time"),
            )
        except (KeyError, ValueError, TypeError) as exc:
            logger.debug("Failed to parse Kalshi market: %s", exc)
            return None


def generate_synthetic_markets() -> List[MarketData]:
    raw = [
        {
            "question": "Will the US have a civil war in 2025?",
            "description": "Shocking reports suggest unprecedented internal conflict risk. Experts warn of catastrophic collapse.",
            "yes_price": 0.78,
            "volume": 450000,
            "age_minutes": 8,
            "platform": "Polymarket",
        },
        {
            "question": "Will Gavin Newsom launch a cryptocurrency token in Q1 2025?",
            "description": "Rumors of a revolutionary government-backed crypto token launch. Dramatic shift in policy.",
            "yes_price": 0.85,
            "volume": 120000,
            "age_minutes": 12,
            "platform": "Polymarket",
        },
        {
            "question": "Will the US military engage Venezuela by December 2025?",
            "description": "Explosive tensions rising. Emergency meetings held.",
            "yes_price": 0.72,
            "volume": 280000,
            "age_minutes": 15,
            "platform": "Polymarket",
        },
        {
            "question": "Will OpenSea launch a token by March 2025?",
            "description": "Unprecedented leak confirms token plans. Massive airdrop expected.",
            "yes_price": 0.81,
            "volume": 95000,
            "age_minutes": 6,
            "platform": "Kalshi",
        },
        {
            "question": "Will Monad do an airdrop by February 2025?",
            "description": "Crypto twitter in a frenzy over potential airdrop.",
            "yes_price": 0.76,
            "volume": 175000,
            "age_minutes": 18,
            "platform": "Kalshi",
        },
        {
            "question": "Will it rain in London tomorrow?",
            "description": "Standard weather prediction market.",
            "yes_price": 0.45,
            "volume": 25000,
            "age_minutes": 120,
            "platform": "Kalshi",
        },
        {
            "question": "Will Bitcoin be above $100k by year end?",
            "description": "End of year Bitcoin price prediction.",
            "yes_price": 0.62,
            "volume": 850000,
            "age_minutes": 480,
            "platform": "Polymarket",
        },
        {
            "question": "Will the Federal Reserve cut rates in Q2 2025?",
            "description": "Monetary policy prediction for upcoming Fed meeting.",
            "yes_price": 0.55,
            "volume": 320000,
            "age_minutes": 240,
            "platform": "Polymarket",
        },
    ]

    markets: List[MarketData] = []
    for idx, m in enumerate(raw):
        yes_price = m["yes_price"]
        markets.append(
            MarketData(
                id=f"synthetic_{idx}",
                platform=m["platform"],
                question=m["question"],
                yes_price=yes_price,
                no_price=round(1.0 - yes_price, 4),
                volume=float(m["volume"]),
                liquidity=float(m["volume"]) * 0.3,
                spread=0.02,
                age_minutes=float(m["age_minutes"]),
                timestamp=datetime.now().isoformat(),
                description=m.get("description", m["question"]),
                end_date=(datetime.now() + timedelta(days=90)).isoformat(),
            )
        )
    return markets


def get_all_markets(
    use_mock: bool = True,
    kalshi_api_key: Optional[str] = None,
    cfg: config.FetchConfig = None,
) -> List[MarketData]:
    if use_mock:
        markets = generate_synthetic_markets()
        logger.info("Using %d synthetic markets", len(markets))
        return markets

    fetcher = MarketDataFetcher(cfg=cfg)
    markets = fetcher.fetch_polymarket_markets()

    if kalshi_api_key:
        markets.extend(fetcher.fetch_kalshi_markets(kalshi_api_key))

    if not markets:
        logger.warning("No live markets fetched; falling back to synthetic data")
        return generate_synthetic_markets()

    return markets

