import json
from datetime import datetime
import fetch_data
import strategy
import backtest

def reproduce():
    print("=" * 80)
    print("  REPRODUCTION SCRIPT - Deterministic Verification")
    print("=" * 80)
    print()
    
    print("Step 1: Loading synthetic test data...")
    markets = fetch_data.generate_synthetic_markets()
    print(f"  ✓ Loaded {len(markets)} synthetic markets")
    
    print("\nMarket Overview:")
    for i, m in enumerate(markets, 1):
        print(f"  {i}. {m['question']}")
        print(f"     Yes: {m['yes_price']:.2f} | Age: {m['age_minutes']}m | Volume: ${m['volume']:,.0f}")
    
    print("\nStep 2: Running strategy analysis...")
    opportunities = strategy.run_strategy(markets)
    print(f"  ✓ Found {len(opportunities)} opportunities")
    
    print("\nStep 3: Verification...")
    
    min_expected_count = 2
    
    if len(opportunities) >= min_expected_count:
        print(f"  ✓ SUCCESS: Found {len(opportunities)} opportunities (expected at least {min_expected_count})")
    else:
        print(f"  ✗ FAILURE: Expected at least {min_expected_count} opportunities, found {len(opportunities)}")
    
    print("\nDetected Opportunities:")
    for i, opp in enumerate(opportunities, 1):
        market = opp['market']
        analytics = opp['analytics']
        print(f"\n  {i}. {market['question']}")
        print(f"     Platform: {market['platform']}")
        print(f"     Signal: {opp['signal']}")
        print(f"     Expected Value: {analytics['expected_value']:.2%}")
        print(f"     True No Probability: {analytics['true_no_probability']:.1%}")
        print(f"     Recommended Position: ${analytics['recommended_position_usd']:,.2f}")
    
    print("\nPortfolio Metrics:")
    portfolio_metrics = strategy.calculate_portfolio_metrics(opportunities)
    for key, value in portfolio_metrics.items():
        print(f"  • {key.replace('_', ' ').title()}: {value}")
    
    print("\nStep 4: Running backtest simulation...")
    backtest_results = backtest.run_simple_backtest(opportunities)
    
    print("\nBacktest Performance:")
    print(f"  • Win Rate: {backtest_results['win_rate']:.1%}")
    print(f"  • Total Return: ${backtest_results['total_return']:,.2f}")
    print(f"  • ROI: {backtest_results['roi_percent']:.1f}%")
    print(f"  • Profit Factor: {backtest_results['profit_factor']:.2f}")
    
    output = {
        "timestamp": datetime.now().isoformat(),
        "test_type": "deterministic_reproduction",
        "markets_analyzed": len(markets),
        "opportunities_found": len(opportunities),
        "min_expected_opportunities": min_expected_count,
        "test_passed": len(opportunities) >= min_expected_count,
        "opportunities": opportunities,
        "portfolio_metrics": portfolio_metrics,
        "backtest_results": backtest_results,
    }
    
    with open('reproduction_output.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print("\n✓ Results saved to reproduction_output.json")
    
    print("\n" + "=" * 80)
    
    return len(opportunities) >= min_expected_count

if __name__ == "__main__":
    success = reproduce()
    exit(0 if success else 1)
