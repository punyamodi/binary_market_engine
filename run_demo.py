import json
from datetime import datetime
import fetch_data
import strategy
import backtest

def print_header():
    print("=" * 80)
    print("  BINARY MARKET STRATEGY ENGINE - 'BUY NO EARLY'")
    print("  Quant-Level Implementation for Polymarket & Kalshi")
    print("=" * 80)
    print()

def print_section(title: str):
    print(f"\n{'─' * 80}")
    print(f"  {title}")
    print(f"{'─' * 80}\n")

def print_opportunity(opp: dict, index: int):
    market = opp["market"]
    analytics = opp["analytics"]
    
    print(f"┌─ Opportunity #{index} {'─' * 60}")
    print(f"│ Platform: {market['platform']}")
    print(f"│ Question: {market['question']}")
    print(f"│")
    print(f"│ Market Data:")
    print(f"│   • Yes Price: ${market['yes_price']:.2f}")
    print(f"│   • No Price:  ${market['no_price']:.2f}")
    print(f"│   • Volume:    ${market['volume']:,.0f}")
    print(f"│   • Liquidity: ${market['liquidity']:,.0f}")
    print(f"│   • Age:       {market['age_minutes']:.0f} minutes")
    print(f"│")
    print(f"│ Quantitative Analysis:")
    print(f"│   • True Yes Probability: {analytics['true_yes_probability']:.1%}")
    print(f"│   • True No Probability:  {analytics['true_no_probability']:.1%}")
    print(f"│   • Edge:                 {analytics['edge']:.1%}")
    print(f"│   • Expected Value:       {analytics['expected_value']:.2%}")
    print(f"│   • Confidence Score:     {analytics['confidence']:.1%}")
    print(f"│")
    print(f"│ Position Sizing:")
    print(f"│   • Kelly Optimal:        {analytics['kelly_optimal_pct']:.2%}")
    print(f"│   • Recommended Size:     ${analytics['recommended_position_usd']:,.2f}")
    print(f"│   • Sharpe Ratio:         {analytics['sharpe_ratio']:.2f}")
    print(f"│")
    print(f"│ Signal: {opp['signal']}")
    print(f"│ Risk/Reward: {opp['risk_reward']:.2f}x")
    print(f"└{'─' * 78}")

def print_portfolio_metrics(metrics: dict):
    print(f"┌─ Portfolio Metrics {'─' * 60}")
    print(f"│ Total Opportunities:       {metrics['total_opportunities']}")
    print(f"│ Total Expected Value:      {metrics['total_expected_value']:.2%}")
    print(f"│ Total Recommended Capital: ${metrics['total_recommended_capital']:,.2f}")
    print(f"│ Average Confidence:        {metrics['average_confidence']:.1%}")
    print(f"│ Average Sharpe Ratio:      {metrics['average_sharpe_ratio']:.2f}")
    print(f"│ Best Opportunity:          {metrics['best_opportunity']}")
    print(f"└{'─' * 78}")

def print_backtest_results(results: dict):
    print(f"┌─ Backtest Results {'─' * 61}")
    print(f"│ Total Trades:              {results['total_trades']}")
    print(f"│ Winning Trades:            {results['winning_trades']}")
    print(f"│ Losing Trades:             {results['losing_trades']}")
    print(f"│ Win Rate:                  {results['win_rate']:.1%}")
    print(f"│")
    print(f"│ Initial Capital:           ${results['initial_capital']:,.2f}")
    print(f"│ Final Capital:             ${results['final_capital']:,.2f}")
    print(f"│ Total Return:              ${results['total_return']:,.2f}")
    print(f"│ ROI:                       {results['roi_percent']:.2f}%")
    print(f"│")
    print(f"│ Average Profit/Trade:      ${results['average_profit_per_trade']:,.2f}")
    print(f"│ Average Win:               ${results['average_win']:,.2f}")
    print(f"│ Average Loss:              ${results['average_loss']:,.2f}")
    print(f"│ Profit Factor:             {results['profit_factor']:.2f}")
    print(f"│ Max Drawdown:              {results['max_drawdown_percent']:.2f}%")
    print(f"└{'─' * 78}")

def save_results(opportunities: list, portfolio_metrics: dict, backtest_results: dict, filename: str = "demo_output.json"):
    output = {
        "timestamp": datetime.now().isoformat(),
        "opportunities": opportunities,
        "portfolio_metrics": portfolio_metrics,
        "backtest_results": backtest_results,
    }
    
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2, default=str)

def main():
    print_header()
    
    USE_MOCK = True
    KALSHI_API_KEY = None
    
    print_section("STEP 1: Fetching Market Data")
    
    if USE_MOCK:
        print("Using synthetic market data for demonstration...")
    else:
        print("Fetching live market data from Polymarket and Kalshi...")
    
    markets = fetch_data.get_all_markets(use_mock=USE_MOCK)
    print(f"✓ Fetched {len(markets)} active binary markets")
    
    print_section("STEP 2: Analyzing Markets for Inefficiencies")
    
    print("Running quant analysis:")
    print("  • Calculating true probabilities using Bayesian methods")
    print("  • Detecting sentiment and sensationalism")
    print("  • Computing expected values and edge")
    print("  • Applying Kelly Criterion for position sizing")
    
    opportunities = strategy.run_strategy(markets)
    print(f"\n✓ Found {len(opportunities)} trading opportunities")
    
    if opportunities:
        print_section("STEP 3: Trading Opportunities (Sorted by Expected Value)")
        
        for i, opp in enumerate(opportunities[:5], 1):
            print_opportunity(opp, i)
        
        if len(opportunities) > 5:
            print(f"\n... and {len(opportunities) - 5} more opportunities")
        
        print_section("STEP 4: Portfolio-Level Metrics")
        portfolio_metrics = strategy.calculate_portfolio_metrics(opportunities)
        print_portfolio_metrics(portfolio_metrics)
        
        print_section("STEP 5: Backtesting Strategy Performance")
        print("Running Monte Carlo simulation with:")
        print("  • Historical win rates (22% Yes resolution)")
        print("  • Transaction fees (2%)")
        print("  • Realistic slippage (1%)")
        
        backtest_results = backtest.run_simple_backtest(opportunities)
        print()
        print_backtest_results(backtest_results)
        
        print_section("STEP 6: Saving Results")
        save_results(opportunities, portfolio_metrics, backtest_results)
        print("✓ Results saved to demo_output.json")
        
    else:
        print("\n⚠ No opportunities found matching strategy criteria.")
        portfolio_metrics = {}
        backtest_results = {}
    
    print_section("Run Complete")

if __name__ == "__main__":
    main()
