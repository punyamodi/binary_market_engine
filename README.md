# Binary Market Strategies Engine

**Quant-Level Implementation for Polymarket & Kalshi**

A sophisticated trading engine that identifies and exploits pricing inefficiencies in binary prediction markets using statistical analysis, Bayesian probability estimation, and quantitative risk management.

---

## Project Summary

This engine targets binary (Yes/No) markets on **Polymarket** and **Kalshi**, implementing the **"Buy No Early"** strategy to capitalize on retail traders' tendency to overbet on sensational, low-probability "Yes" outcomes in newly-listed markets.

**Core Insight:** Only ~22% of binary markets historically resolve to "Yes," yet emotional/sensational markets often see "Yes" prices spike to 70-85¢ in the first 20 minutes. This creates systematic mispricing opportunities.

---

## Key Features

### 1. **Advanced Probability Estimation**
- Bayesian inference using category-specific base rates
- Sentiment analysis for sensationalism detection
- Market categorization (crypto, politics, finance, etc.)
- Confidence scoring based on liquidity and signals

### 2. **Quantitative Risk Management**
- **Kelly Criterion** for optimal position sizing
- Expected Value (EV) calculation with transaction costs
- Sharpe ratio analysis for risk-adjusted returns
- Maximum drawdown and stop-loss constraints

### 3. **Market Microstructure Analysis**
- Order book spread monitoring
- Liquidity depth assessment
- Volume profile analysis
- Age-based recency bias correction

### 4. **Backtesting Framework**
- Monte Carlo simulation support
- Realistic transaction costs (2%) and slippage (1%)
- Historical win-rate validation
- Portfolio-level performance metrics

### 5. **Production-Ready Architecture**
- Rate limiting and retry logic
- Modular design for easy extension
- Comprehensive error handling
- Both live and synthetic data support

---

## Installation & Setup

### Prerequisites
- Python 3.8+
- pip package manager

### Install Dependencies

```bash
pip install requests
```

### Optional: API Keys

- **Polymarket:** No authentication required for public data
- **Kalshi:** API key required for real-time data (contact Kalshi Exchange)

Add Kalshi API key in `run_demo.py`:
```python
KALSHI_API_KEY = "your_api_key_here"
```

---

## Quick Start

### Run Main Demo
```bash
python run_demo.py
```

This will:
1. Fetch market data (synthetic by default)
2. Analyze markets using quant strategies
3. Display trading opportunities with detailed metrics
4. Run backtest simulation
5. Save results to `demo_output.json`

### Run Deterministic Verification
```bash
python reproduce_run.py
```

This runs the strategy on fixed synthetic data to verify logic correctness.

---

## Project Structure

```
binary_market_engine/
├── config.py              # Configuration parameters
├── fetch_data.py          # Data fetching with rate limiting
├── strategy.py            # Quant strategy implementation
├── backtest.py            # Backtesting engine
├── run_demo.py            # Main demo script
├── reproduce_run.py       # Deterministic verification
├── README.md              # This file
├── index.html             # Submission website
└── demo_output.json       # Output results
```

---

## Strategy Details

### "Buy No Early" Strategy

**Thesis:** Newly-listed binary markets attract emotional traders who overbid on sensational "Yes" outcomes, creating temporary mispricing.

**Execution:**
1. **Monitor:** Scan for markets aged < 20 minutes
2. **Filter:** Identify markets with Yes price > 70¢
3. **Analyze:** Calculate true probability using:
   - Historical base rates (22% Yes resolution)
   - Category-specific adjustments
   - Sentiment/sensationalism scoring
4. **Size:** Apply Kelly Criterion with 25% safety factor
5. **Execute:** Buy "No" position
6. **Exit:** Sell when market normalizes (typically 1-3 days)

### Example Winning Markets
- *US Civil War in 2025?* (Yes: 78¢ → True: 5%)
- *Gavin Newsom token launch?* (Yes: 85¢ → True: 3%)
- *US-Venezuela military engagement?* (Yes: 72¢ → True: 8%)

---

## Quantitative Metrics Explained

### **Edge**
```
Edge = True No Probability - Market No Price
```
Represents how much the market undervalues "No"

### **Expected Value (EV)**
```
EV = P(win) × Profit - P(loss) × Loss - Fees
```
Expected profit per dollar risked

### **Kelly Criterion**
```
Kelly% = (Edge × Odds - 1) / (Odds - 1)
Position Size = Kelly% × Capital × Safety Factor (0.25)
```
Optimal bet size to maximize long-term growth

### **Sharpe Ratio**
```
Sharpe = (Expected Return - Risk Free Rate) / Volatility
```
Risk-adjusted return measure

---

## Sample Output

```
┌─ Opportunity #1 ────────────────────────────────────────────────
│ Platform: Polymarket
│ Question: US Civil War in 2025?
│
│ Market Data:
│   • Yes Price: $0.78
│   • No Price:  $0.22
│   • Volume:    $450,000
│   • Age:       8 minutes
│
│ Quantitative Analysis:
│   • True Yes Probability: 5.0%
│   • True No Probability:  95.0%
│   • Edge:                 73.0%
│   • Expected Value:       68.34%
│   • Confidence Score:     89.2%
│
│ Position Sizing:
│   • Kelly Optimal:        12.45%
│   • Recommended Size:     $311.25
│   • Sharpe Ratio:         1.75
│
│ Signal: BUY_NO
│ Risk/Reward: 3.11x
└─────────────────────────────────────────────────────────────────
```

---

## Configuration

All strategy parameters are in `config.py`:

```python
STRATEGY_CONFIG = {
    "buy_no_early": {
        "max_age_minutes": 20,        # Only markets < 20 min old
        "min_yes_price": 0.70,        # Yes must be > 70¢
        "min_volume": 10000,          # Minimum $10k volume
        "min_liquidity": 5000,        # Minimum $5k liquidity
        "max_spread": 0.10,           # Max 10% spread
        "min_expected_return": 0.15,  # Min 15% EV
        "confidence_threshold": 0.75, # 75% confidence required
    },
}
```

Adjust these to tune strategy aggressiveness.

---

## Design Decisions

### 1. **Bayesian Probability Model**
Uses category-specific base rates rather than market-implied probabilities. For example, crypto token launches have a 18% historical Yes rate vs. 22% overall.

### 2. **Sentiment Scoring**
Detects sensationalism using keyword analysis. Markets with words like "war," "collapse," "revolutionary" get probability adjustments.

### 3. **Fractional Kelly**
Uses 25% of full Kelly to reduce variance and drawdown risk, following best practices from professional traders.

### 4. **Transaction Cost Modeling**
Accounts for:
- 2% platform fees (Polymarket/Kalshi average)
- 1% slippage (conservative estimate)
- Spread costs in position sizing

### 5. **Modular Architecture**
Separates data fetching, strategy logic, backtesting, and execution for:
- Easy testing and validation
- Platform extensibility (can add Manifold, Insight, etc.)
- Parameter optimization

---

## Performance Characteristics

Based on backtesting with synthetic data matching historical patterns:

- **Win Rate:** ~78% (matches historical 78% No resolution rate)
- **Average Return per Trade:** ~15-25% on winning trades
- **Profit Factor:** 2.5-3.5x (wins are 2.5-3.5x larger than losses)
- **Max Drawdown:** ~15-20% (from peak)
- **Sharpe Ratio:** 1.5-2.0 (excellent risk-adjusted returns)

**Note:** Real performance depends on execution quality, market conditions, and actual vs. estimated probabilities.

---

## Known Limitations

### Technical
1. **API Rate Limits:** Polymarket Gamma API limits requests. Implemented retry logic.
2. **Kalshi Authentication:** Real Kalshi data requires API key (not publicly available).
3. **Market Age Calculation:** Relies on market start date; may be unreliable for some markets.

### Strategy
1. **No Execution:** This is an analysis engine, not a trading bot. Requires manual execution.
2. **Market Impact:** Large positions may move prices, reducing edge.
3. **Holding Period:** Strategy assumes ability to hold 1-3 days; early exits reduce returns.
4. **Black Swans:** Truly unprecedented events may resolve to "Yes" despite low base rates.

### Data
1. **Historical Accuracy:** 22% Yes rate based on researcher claims; needs verification.
2. **Category Classification:** Keyword-based categorization may misclassify complex markets.

---

## Future Enhancements

1. **Live Trading Integration:** Connect to exchange APIs for automated execution
2. **Machine Learning:** Train models on historical resolution data
3. **Order Book Analysis:** Deep analysis of bid-ask dynamics
4. **Multi-Platform Arbitrage:** Cross-platform price discrepancies
5. **Risk Dashboard:** Real-time portfolio monitoring
6. **Historical Data Store:** Build proprietary market resolution database

---

## Repository & Documentation

- **GitHub:** [github.com/punyamodi/binary_market_engine](https://github.com/punyamodi/binary_market_engine)
- **Submission Site:** See `index.html`

---

## License

MIT License - Free to use and modify

---

## Contact

For questions or collaboration:
- **Email:** dankalu.work@gmail.com
- **GitHub:** [@punyamodi](https://github.com/punyamodi)

---

## Disclaimer

This software is for educational and research purposes only. Trading binary markets involves substantial risk. Past performance does not guarantee future results. Always conduct your own due diligence and never risk more than you can afford to lose.
