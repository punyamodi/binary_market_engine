import json
import time
import copy
import sys
from datetime import datetime, timedelta
import fetch_data
import strategy
from engine import TradingEngine

sys.stdout.reconfigure(encoding='utf-8')

def print_header():
    print("=" * 80)
    print("  BINARY MARKET STRATEGY ENGINE - 'BUY NO EARLY'")
    print("  End-to-End Execution & Management System")
    print("=" * 80)
    print()

def print_section(title: str):
    print(f"\n{'─' * 80}")
    print(f"  {title}")
    print(f"{'─' * 80}\n")

def simulate_price_movement(markets, time_step_minutes):
    """
    Simulates price evolution for the 'Buy No' strategy.
    Hypothesis: 'No' prices tend to rise (Yes prices fall) as hype fades.
    
    This simulation demonstrates the core thesis:
    - Sensational markets are overpriced early (high Yes price)
    - As hype fades, rational pricing emerges (Yes price drops, No price rises)
    - Our "No" positions appreciate in value
    """
    updated_markets = []
    for m in markets:
        new_m = copy.deepcopy(m)
        
        is_sensational = any(keyword in m['question'] for keyword in 
                            ["Civil War", "Token", "Airdrop", "military", "Newsom", "OpenSea", "Monad", "Venezuela"])
        
        if is_sensational:
            
            initial_hype_level = m['yes_price']
            
            time_factor = time_step_minutes / 15.0
            hype_fade_rate = 0.08 * time_factor * initial_hype_level
            
            new_m['yes_price'] = max(0.05, new_m['yes_price'] - hype_fade_rate)
            
            new_m['no_price'] = min(0.95, 1.0 - new_m['yes_price'])
            
        else:
            import random
            noise = random.uniform(-0.01, 0.01)
            new_m['yes_price'] = max(0.01, min(0.99, new_m['yes_price'] + noise))
            new_m['no_price'] = 1.0 - new_m['yes_price']
            
        updated_markets.append(new_m)
    return updated_markets

def main():
    print_header()
    
    engine = TradingEngine(initial_capital=10000.0)
    print(f"Initialized Trading Engine with ${engine.cash:,.2f} capital.")
    
    print_section("T=00:00 | MARKET SCAN & ENTRY")
    markets = fetch_data.get_all_markets(use_mock=True)
    print(f"Fetched {len(markets)} active markets.")
    
    opportunities = strategy.run_strategy(markets)
    print(f"Identified {len(opportunities)} 'Buy No' opportunities.")
    
    for opp in opportunities:
        market = opp['market']
        analytics = opp['analytics']
        
        size_usd = analytics['recommended_position_usd']
        price = market['no_price']
        quantity = size_usd / price
        
        stop_loss = price * 0.90
        take_profit = price * 1.20
        
        print(f"  > Executing BUY for '{market['question']}'")
        print(f"    Qty: {quantity:.0f} | Price: ${price:.2f} | TP: ${take_profit:.2f} | SL: ${stop_loss:.2f}")
        
        engine.execute_order(
            market=market,
            action="BUY",
            outcome="NO",
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            max_hold_time=60,
            reason=opp['reason']
        )
        
    summary = engine.get_portfolio_summary()
    print(f"\n[Portfolio Status] Cash: ${summary['cash']:,.2f} | Equity: ${summary['total_equity']:,.2f} | Positions: {summary['position_count']}")

    print_section("T+00:15 | POSITION MANAGEMENT (Hype Fading...)")
    
    markets_t15 = simulate_price_movement(markets, time_step_minutes=15)
    
    engine.update_market_prices(markets_t15)
    engine.check_risk_management()
    
    summary = engine.get_portfolio_summary()
    print(f"\n[Portfolio Status] Cash: ${summary['cash']:,.2f} | Equity: ${summary['total_equity']:,.2f} | Unrealized PnL: ${summary['unrealized_pnl']:,.2f}")
    
    print_section("T+00:45 | POSITION MANAGEMENT (Trend Continues...)")
    
    markets_t45 = simulate_price_movement(markets_t15, time_step_minutes=30)
    
    engine.update_market_prices(markets_t45)
    engine.check_risk_management()
    
    summary = engine.get_portfolio_summary()
    print(f"\n[Portfolio Status] Cash: ${summary['cash']:,.2f} | Equity: ${summary['total_equity']:,.2f} | Unrealized PnL: ${summary['unrealized_pnl']:,.2f}")

    print_section("T+01:00 | SESSION CLOSE")
    
    print("Closing all remaining positions...")
    for market_id, pos in list(engine.positions.items()):
        engine._force_close(pos, "End of Session")
        
    print_section("FINAL PERFORMANCE REPORT")
    
    final_equity = engine.cash
    roi = ((final_equity - engine.initial_capital) / engine.initial_capital) * 100
    
    print(f"Initial Capital: ${engine.initial_capital:,.2f}")
    print(f"Final Capital:   ${final_equity:,.2f}")
    print(f"Total Return:    ${final_equity - engine.initial_capital:,.2f}")
    print(f"ROI:             {roi:.2f}%")
    print(f"Total Trades:    {len(engine.trades)}")
    
    print("\nTrade History:")
    for t in engine.trades:
        print(f"  • {t.timestamp.strftime('%H:%M:%S')} {t.action} {t.symbol} @ ${t.price:.2f} ({t.reason})")

    results = {
        "timestamp": datetime.now().isoformat(),
        "final_equity": final_equity,
        "roi": roi,
        "trades": [
            {
                "symbol": t.symbol,
                "action": t.action,
                "price": t.price,
                "quantity": t.quantity,
                "reason": t.reason
            } for t in engine.trades
        ]
    }
    with open("demo_output.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n✓ Results saved to demo_output.json")

if __name__ == "__main__":
    main()
