# Binary Market Strategies Engine

## Project Summary
This engine targets binary (Yes/No) markets on **Polymarket** and **Kalshi**. It implements the **"Buy No Early"** strategy, designed to exploit the "wishful thinking" bias where retail traders overbet on sensational "Yes" outcomes immediately after a market opens.

### Strategy Logic
1.  **Monitor**: Watch for new market listings (Age < 20 mins).
2.  **Analyze**: Check if "Yes" price is irrationally high (> 70¢) due to hype.
3.  **Signal**: Generate a "Buy No" signal.
4.  **Exit (Manual)**: The strategy implies holding until hype fades and prices normalize, then selling the "No" position for a profit before resolution.

### Why This Works
-   Historically, only ~22% of these markets resolve to "Yes".
-   Early "Yes" bettors drive prices up on hype.
-   As emotion fades, prices correct, increasing the value of "No" shares with low event risk.

## Setup & Run
1.  **Clone/Download** this repository.
2.  **Install Dependencies**:
    ```bash
    pip install requests
    ```
3.  **Run Demo**:
    ```bash
    python run_demo.py
    ```
    This will fetch market data (mocked by default to ensure opportunities are shown) and print found opportunities.
4.  **Run Reproduction Script**:
    ```bash
    python reproduce_run.py
    ```
    A standalone script using synthetic data to verify the logic deterministically.

## Design Decisions
-   **Modular Architecture**: Separated data fetching (`fetch_data.py`) from strategy logic (`strategy.py`) for easier testing and expansion.
-   **Mock Data Fallback**: Includes a robust mock data generator to ensure the demo works without requiring API keys or active market conditions.
-   **Standardized Market Model**: Normalizes data from different platforms into a common dictionary structure.

## Known Limitations
-   **API Rate Limits**: Public APIs (like Polymarket's Gamma) have rate limits.
-   **Kalshi Auth**: Real-time Kalshi data requires authentication, so the demo relies on mock data for Kalshi examples.
-   **Execution**: This is an analysis engine; it does not execute trades automatically.
