# Binary Market Strategies Engine

## Project Summary
This engine implements the **"Buy No Early"** strategy for **Polymarket** and **Kalshi** binary prediction markets. It identifies pricing inefficiencies in newly-listed (<20 minutes old) markets where retail traders overbet on sensational "Yes" outcomes, using Bayesian probability estimation and Kelly Criterion position sizing to capture the correction.

## Quick Setup & Run Instructions

### Dependencies
*   Python 3.8+
*   `requests`

### Installation
```bash
git clone https://github.com/punyamodi/binary_market_engine.git
cd binary_market_engine
pip install -r requirements.txt
```

### Running the Demo
```bash
python run_demo.py
```
This script fetches market data (synthetic by default), runs the strategy analysis, and outputs trading opportunities to the console and `demo_output.json`.

### Verifying Logic
```bash
python reproduce_run.py
```
Runs the strategy on a fixed dataset to deterministically verify the logic.

## Sample Output

```text
┌─ Opportunity #1 ────────────────────────────────────────────────
│ Platform: Polymarket
│ Question: Will Gavin Newsom launch a cryptocurrency token in Q1 2025?
│ Market Data: Yes: $0.85 | Age: 12m
│ Analysis: True Yes: 18.0% | Edge: 67.0% | EV: 65.66%
│ Signal: BUY_NO | Size: $1,000.00
└─────────────────────────────────────────────────────────────────
```

## Design Decisions

1.  **Bayesian Probability Model:** We use category-specific base rates (e.g., 22% historical "Yes" rate) as the prior, updating with a "sensationalism score" derived from keyword analysis to estimate the true probability of a "Yes" outcome.
2.  **Fractional Kelly Criterion:** To manage risk in these high-variance markets, we utilize a fractional Kelly Criterion (25% of optimal) for position sizing.
3.  **Mock Data First:** The system defaults to synthetic data to ensure the demo is immediately runnable and verifiable without requiring live API keys or handling rate limits during evaluation.
4.  **Architecture:** The system is modularized into `fetch_data` (API abstraction), `strategy` (pure logic), and `backtest` (simulation) to separate concerns and facilitate testing.

## Dependencies

*   **Python Standard Library:** `json`, `datetime`, `math`, `random`, `typing`
*   **External Packages:**
    *   `requests`: For HTTP calls to Polymarket and Kalshi APIs.

## Known Limitations

*   **API Rate Limits:** The Polymarket Gamma API has strict rate limits; the current implementation uses basic backoff/retry logic which may be insufficient for high-frequency polling.
*   **Kalshi Authentication:** Real-time Kalshi data requires a valid API key (not included); the engine falls back to synthetic data if no key is provided.
*   **Execution:** This is an analysis engine only; it identifies opportunities but does not execute live trades on the exchange.
*   **Market Age Accuracy:** "Age" is calculated from the market start date, which may not perfectly reflect when liquidity actually appeared.
