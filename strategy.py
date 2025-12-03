import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import config

class MarketAnalyzer:
    def __init__(self):
        self.strategy_config = config.STRATEGY_CONFIG["buy_no_early"]
        self.position_config = config.STRATEGY_CONFIG["position_sizing"]
        self.risk_config = config.STRATEGY_CONFIG["risk_management"]
    
    def categorize_market(self, question: str, description: str = "") -> str:
        text = (question + " " + description).lower()
        
        if any(kw in text for kw in config.CRYPTO_KEYWORDS):
            return "crypto"
        elif any(kw in text for kw in config.POLITICS_KEYWORDS):
            return "politics"
        else:
            return "default"
    
    def calculate_sentiment_score(self, question: str, description: str = "") -> float:
        text = (question + " " + description).lower()
        sensational_count = sum(1 for kw in config.SENSATIONAL_KEYWORDS if kw in text)
        max_expected = 3
        score = min(sensational_count / max_expected, 1.0)
        return score
    
    def calculate_true_probability(self, market: Dict) -> Tuple[float, float]:
        category = self.categorize_market(
            market.get("question", ""),
            market.get("description", "")
        )
        base_yes_prob = config.CATEGORY_YES_RATES.get(category, config.HISTORICAL_YES_RATE)
        
        sentiment_score = self.calculate_sentiment_score(
            market.get("question", ""),
            market.get("description", "")
        )
        
        adjusted_prob = base_yes_prob * (1 - 0.5 * sentiment_score)
        
        volume_confidence = min(market.get("volume", 0) / 100000, 1.0) * 0.3
        sentiment_confidence = sentiment_score * 0.4
        category_confidence = 0.3 if category != "default" else 0.1
        
        confidence = volume_confidence + sentiment_confidence + category_confidence
        confidence = min(confidence, 1.0)
        
        return adjusted_prob, confidence
    
    def calculate_expected_value(self, market: Dict, true_yes_prob: float) -> float:
        market_no_price = market.get("no_price", 0.5)
        true_no_prob = 1 - true_yes_prob
        
        profit_per_share = 1 - market_no_price
        loss_per_share = market_no_price
        
        expected_value = (true_no_prob * profit_per_share) - ((1 - true_no_prob) * loss_per_share)
        fee_adjusted_ev = expected_value * (1 - config.BACKTEST_CONFIG["transaction_fee"])
        
        return fee_adjusted_ev
    
    def calculate_kelly_criterion(self, market: Dict, true_yes_prob: float) -> float:
        market_no_price = market.get("no_price", 0.5)
        true_no_prob = 1 - true_yes_prob
        
        if market_no_price >= 1.0 or market_no_price <= 0:
            return 0.0
        
        b = (1 - market_no_price) / market_no_price
        p = true_no_prob
        q = 1 - p
        
        kelly_fraction = (b * p - q) / b
        safe_kelly = kelly_fraction * self.position_config["kelly_fraction"]
        
        return max(0, min(safe_kelly, 1.0))
    
    def calculate_position_size(self, market: Dict, true_yes_prob: float, capital: float = 10000) -> float:
        kelly_pct = self.calculate_kelly_criterion(market, true_yes_prob)
        position_size = kelly_pct * capital
        
        position_size = max(
            self.position_config["min_position_size"],
            min(position_size, self.position_config["max_position_size"])
        )
        
        return position_size
    
    def calculate_sharpe_ratio(self, expected_return: float, volatility: float) -> float:
        risk_free_rate = 0.05
        if volatility == 0:
            return 0.0
        sharpe = (expected_return - risk_free_rate) / volatility
        return sharpe
    
    def analyze_market(self, market: Dict) -> Optional[Dict]:
        age = market.get('age_minutes')
        if age is None or age > self.strategy_config["max_age_minutes"]:
            return None
        
        yes_price = market.get('yes_price', 0.5)
        if yes_price < self.strategy_config["min_yes_price"]:
            return None
        
        volume = market.get('volume', 0)
        if volume < self.strategy_config["min_volume"]:
            return None
        
        liquidity = market.get('liquidity', 0)
        if liquidity < self.strategy_config["min_liquidity"]:
            return None
        
        spread = market.get('spread', 0)
        if spread > self.strategy_config["max_spread"]:
            return None
        
        true_yes_prob, confidence = self.calculate_true_probability(market)
        
        if confidence < self.strategy_config["confidence_threshold"]:
            return None
        
        expected_value = self.calculate_expected_value(market, true_yes_prob)
        
        if expected_value < self.strategy_config["min_expected_return"]:
            return None
        
        position_size = self.calculate_position_size(market, true_yes_prob)
        kelly_pct = self.calculate_kelly_criterion(market, true_yes_prob)
        
        implied_volatility = yes_price * 0.5
        sharpe_ratio = self.calculate_sharpe_ratio(expected_value, implied_volatility)
        
        market_implied_no_prob = market.get('no_price', 0.5)
        true_no_prob = 1 - true_yes_prob
        edge = true_no_prob - market_implied_no_prob
        
        return {
            "signal": "BUY_NO",
            "market": market,
            "analytics": {
                "true_yes_probability": round(true_yes_prob, 4),
                "true_no_probability": round(true_no_prob, 4),
                "confidence": round(confidence, 4),
                "expected_value": round(expected_value, 4),
                "edge": round(edge, 4),
                "kelly_optimal_pct": round(kelly_pct, 4),
                "recommended_position_usd": round(position_size, 2),
                "sharpe_ratio": round(sharpe_ratio, 2),
                "implied_volatility": round(implied_volatility, 4),
            },
            "reason": self._generate_reason(market, true_yes_prob, expected_value, edge, confidence),
            "risk_reward": round(expected_value / (market.get('no_price', 0.5)), 2),
        }
    
    def _generate_reason(self, market: Dict, true_yes_prob: float, expected_value: float, edge: float, confidence: float) -> str:
        yes_price = market.get('yes_price', 0.5)
        age = market.get('age_minutes', 0)
        sentiment = self.calculate_sentiment_score(market.get("question", ""), market.get("description", ""))
        
        parts = []
        parts.append(f"Age: {age:.0f}m")
        parts.append(f"Yes: {yes_price:.2f}")
        parts.append(f"True Yes: {true_yes_prob:.1%}")
        parts.append(f"Edge: {edge:.1%}")
        parts.append(f"EV: {expected_value:.1%}")
        if sentiment > 0.3:
            parts.append(f"Sensationalism: {sentiment:.2f}")
        parts.append(f"Conf: {confidence:.1%}")
        
        return " | ".join(parts)

def run_strategy(markets: List[Dict]) -> List[Dict]:
    analyzer = MarketAnalyzer()
    opportunities = []
    for market in markets:
        signal = analyzer.analyze_market(market)
        if signal:
            opportunities.append(signal)
    
    opportunities.sort(key=lambda x: x["analytics"]["expected_value"], reverse=True)
    return opportunities

def calculate_portfolio_metrics(opportunities: List[Dict]) -> Dict:
    if not opportunities:
        return {}
    
    total_ev = sum(opp["analytics"]["expected_value"] for opp in opportunities)
    total_position = sum(opp["analytics"]["recommended_position_usd"] for opp in opportunities)
    avg_confidence = sum(opp["analytics"]["confidence"] for opp in opportunities) / len(opportunities)
    avg_sharpe = sum(opp["analytics"]["sharpe_ratio"] for opp in opportunities) / len(opportunities)
    
    return {
        "total_opportunities": len(opportunities),
        "total_expected_value": round(total_ev, 4),
        "total_recommended_capital": round(total_position, 2),
        "average_confidence": round(avg_confidence, 4),
        "average_sharpe_ratio": round(avg_sharpe, 2),
        "best_opportunity": opportunities[0]["market"]["question"] if opportunities else None,
    }
