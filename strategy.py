import logging
from typing import Dict, List, Optional, Tuple

import config
from models import MarketData, Signal

logger = logging.getLogger(__name__)


class MarketAnalyzer:
    def __init__(self, cfg: config.AppConfig = None):
        self._cfg = cfg or config.default_config()
        self._strategy = self._cfg.strategy
        self._sizing = self._cfg.position_sizing

    def categorize_market(self, question: str, description: str = "") -> str:
        text = (question + " " + description).lower()
        if any(kw in text for kw in config.CRYPTO_KEYWORDS):
            return "crypto"
        if any(kw in text for kw in config.POLITICS_KEYWORDS):
            return "politics"
        if any(kw in text for kw in config.SPORTS_KEYWORDS):
            return "sports"
        if any(kw in text for kw in config.WEATHER_KEYWORDS):
            return "weather"
        return "default"

    def sensationalism_score(self, question: str, description: str = "") -> float:
        text = (question + " " + description).lower()
        count = sum(1 for kw in config.SENSATIONAL_KEYWORDS if kw in text)
        return min(count / 3.0, 1.0)

    def true_probability(self, market: MarketData) -> Tuple[float, float]:
        category = self.categorize_market(market.question, market.description)
        base_yes = config.CATEGORY_YES_RATES.get(category, config.HISTORICAL_YES_RATE)

        sentiment = self.sensationalism_score(market.question, market.description)
        adjusted_yes = base_yes * (1.0 - self._strategy.sensationalism_adjustment * sentiment)

        volume_conf = min(market.volume / 100000.0, 1.0) * 0.3
        sentiment_conf = sentiment * 0.4
        category_conf = 0.3 if category != "default" else 0.1
        confidence = min(volume_conf + sentiment_conf + category_conf, 1.0)

        return adjusted_yes, confidence

    def expected_value(self, market: MarketData, true_yes_prob: float, fee: float = 0.02) -> float:
        true_no_prob = 1.0 - true_yes_prob
        profit = 1.0 - market.no_price
        loss = market.no_price
        ev = (true_no_prob * profit) - (true_yes_prob * loss)
        return ev * (1.0 - fee)

    def kelly_criterion(self, market: MarketData, true_yes_prob: float) -> float:
        if market.no_price >= 1.0 or market.no_price <= 0.0:
            return 0.0
        true_no_prob = 1.0 - true_yes_prob
        b = (1.0 - market.no_price) / market.no_price
        p = true_no_prob
        q = 1.0 - p
        raw_kelly = (b * p - q) / b
        return max(0.0, min(raw_kelly * self._sizing.kelly_fraction, 1.0))

    def position_size(self, market: MarketData, true_yes_prob: float, capital: float) -> float:
        kelly_pct = self.kelly_criterion(market, true_yes_prob)
        size = kelly_pct * capital
        return max(self._sizing.min_position_usd, min(size, self._sizing.max_position_usd))

    def sharpe_ratio(self, expected_return: float, implied_vol: float) -> float:
        risk_free = 0.05
        if implied_vol == 0.0:
            return 0.0
        return (expected_return - risk_free) / implied_vol

    def analyze(self, market: MarketData, capital: float = 10000.0) -> Optional[Signal]:
        s = self._strategy

        if market.age_minutes is None or market.age_minutes > s.max_age_minutes:
            return None
        if market.yes_price < s.min_yes_price:
            return None
        if market.volume < s.min_volume:
            return None
        if market.liquidity < s.min_liquidity:
            return None
        if market.spread > s.max_spread:
            return None

        true_yes, confidence = self.true_probability(market)
        if confidence < s.confidence_threshold:
            return None

        ev = self.expected_value(market, true_yes)
        if ev < s.min_expected_return:
            return None

        true_no = 1.0 - true_yes
        kelly_pct = self.kelly_criterion(market, true_yes)
        size = self.position_size(market, true_yes, capital)
        implied_vol = market.yes_price * 0.5
        sharpe = self.sharpe_ratio(ev, implied_vol)
        edge = true_no - market.no_price
        risk_reward = ev / market.no_price if market.no_price > 0 else 0.0

        reason = self._build_reason(market, true_yes, ev, edge, confidence)

        return Signal(
            market_id=market.id,
            market=market,
            outcome="NO",
            true_yes_prob=round(true_yes, 4),
            true_no_prob=round(true_no, 4),
            confidence=round(confidence, 4),
            expected_value=round(ev, 4),
            edge=round(edge, 4),
            kelly_pct=round(kelly_pct, 4),
            recommended_position_usd=round(size, 2),
            sharpe_ratio=round(sharpe, 2),
            implied_volatility=round(implied_vol, 4),
            reason=reason,
            risk_reward=round(risk_reward, 2),
        )

    def _build_reason(
        self,
        market: MarketData,
        true_yes: float,
        ev: float,
        edge: float,
        confidence: float,
    ) -> str:
        sentiment = self.sensationalism_score(market.question, market.description)
        parts = [
            f"Age:{market.age_minutes:.0f}m",
            f"Yes:{market.yes_price:.2f}",
            f"TrueYes:{true_yes:.1%}",
            f"Edge:{edge:.1%}",
            f"EV:{ev:.1%}",
            f"Conf:{confidence:.1%}",
        ]
        if sentiment > 0.3:
            parts.append(f"Hype:{sentiment:.2f}")
        return " | ".join(parts)


def run_strategy(markets: List[MarketData], capital: float = 10000.0, cfg: config.AppConfig = None) -> List[Signal]:
    analyzer = MarketAnalyzer(cfg=cfg)
    signals = [sig for m in markets if (sig := analyzer.analyze(m, capital=capital))]
    signals.sort(key=lambda s: s.expected_value, reverse=True)
    logger.info("Strategy identified %d signals from %d markets", len(signals), len(markets))
    return signals


def portfolio_metrics(signals: List[Signal]) -> Dict:
    if not signals:
        return {}
    return {
        "total_signals": len(signals),
        "total_expected_value": round(sum(s.expected_value for s in signals), 4),
        "total_recommended_capital": round(sum(s.recommended_position_usd for s in signals), 2),
        "average_confidence": round(sum(s.confidence for s in signals) / len(signals), 4),
        "average_sharpe": round(sum(s.sharpe_ratio for s in signals) / len(signals), 2),
        "best_opportunity": signals[0].market.question,
    }

