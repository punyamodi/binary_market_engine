def analyze_market(market):
    """
    Analyzes a single market to determine if it fits the 'Buy No Early' strategy.
    
    Strategy Criteria:
    1. Market is 'young' (e.g., < 15 minutes old).
    2. 'Yes' price is 'high' (e.g., > 0.70), indicating hype.
    """
    MAX_AGE_MINUTES = 20
    MIN_YES_PRICE = 0.70
    
    age = market.get('age_minutes', 100)
    yes_price = market.get('yes_price', 0.5)
    
    if age <= MAX_AGE_MINUTES and yes_price >= MIN_YES_PRICE:
        return {
            "signal": "BUY_NO",
            "reason": f"Market is young ({age}m) and Yes price is high ({yes_price:.2f}) - Hype detected.",
            "market": market
        }
    
    return None

def run_strategy(markets):
    """
    Runs the strategy over a list of markets.
    """
    opportunities = []
    for market in markets:
        signal = analyze_market(market)
        if signal:
            opportunities.append(signal)
    return opportunities
