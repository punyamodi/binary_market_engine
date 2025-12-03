import fetch_data
import strategy

def reproduce():
    """
    A standalone script to reproduce the strategy logic on a fixed set of synthetic data.
    This ensures the logic can be verified without any network dependencies.
    """
    print("Running Reproduction Script (Deterministic Mock Data)...")
    
    markets = fetch_data.generate_mock_data()
    
    opportunities = strategy.run_strategy(markets)
    
    print(f"Found {len(opportunities)} opportunities.")
    
    expected_opps = 3
    if len(opportunities) == expected_opps:
        print("SUCCESS: Strategy identified the correct number of opportunities.")
    else:
        print(f"FAILURE: Expected {expected_opps} opportunities, found {len(opportunities)}.")

    for opp in opportunities:
        print(f" - Detected: {opp['market']['question']} (Signal: {opp['signal']})")

if __name__ == "__main__":
    reproduce()
