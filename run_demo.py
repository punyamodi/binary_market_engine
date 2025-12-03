import fetch_data
import strategy
import json

def main():
    print("="*60)
    print("Binary Market Strategy Engine - 'Buy No Early'")
    print("Targeting: Polymarket & Kalshi")
    print("="*60)
    
    USE_MOCK = True
    
    print("\n[1] Fetching Market Data...")
    if USE_MOCK:
        print("    (Using Synthetic Mock Data for Demonstration)")
    else:
        print("    (Using Real Polymarket API Data)")
        
    markets = fetch_data.get_all_markets(use_mock=USE_MOCK) 
    print(f"    -> Found {len(markets)} active markets.")
    
    print("\n[2] Analyzing Markets for Inefficiencies...")
    opportunities = strategy.run_strategy(markets)
    
    print(f"    -> Found {len(opportunities)} opportunities.\n")
    
    if not opportunities:
        print("No opportunities found matching criteria.")
    else:
        for i, opp in enumerate(opportunities, 1):
            m = opp['market']
            print(f"Opportunity #{i}:")
            print(f"  Platform: {m['platform']}")
            print(f"  Question: {m['question']}")
            print(f"  Price: Yes ${m['yes_price']:.2f} | No ${m['no_price']:.2f}")
            print(f"  Age: {m['age_minutes']} minutes")
            print(f"  Signal: {opp['signal']}")
            print(f"  Reason: {opp['reason']}")
            print("-" * 40)

    with open('demo_output.json', 'w') as f:
        json.dump(opportunities, f, indent=2)
    print("\n[3] Run Complete. Results saved to demo_output.json")

if __name__ == "__main__":
    main()
