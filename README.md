# Binary Market Strategy Engine

End-to-end algorithmic trading system for binary prediction markets (Polymarket and Kalshi).

## Strategy

**Buy No Early** exploits retail trader bias in newly launched prediction markets. Historically, only ~22% of sensational binary markets resolve as "Yes," yet early traders systematically overprice "Yes" outcomes in the first minutes after launch.

The engine:
1. Detects new markets within a configurable age window
2. Scores pricing inefficiencies using Bayesian probability estimation
3. Executes "Buy No" orders when edge and expected value thresholds are met
4. Manages positions with stop-loss, take-profit, and time-based exits
5. Produces detailed JSON performance reports

## Architecture

```
fetch_data.py   ->  strategy.py  ->  engine.py
   (data)          (signals)       (execution)

simulator.py  +  backtest.py  ->  main.py
 (price sim)    (orchestration)  (CLI entry)

config.py + models.py  (shared types)
```

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

By default the engine runs on synthetic markets for reproducible demonstration.

## CLI Options

```
python main.py --help

Options:
  --capital FLOAT       Initial capital in USD (default: 10000)
  --live                Fetch live market data from Polymarket
  --kalshi-key KEY      Kalshi API key for live Kalshi markets
  --output FILE         JSON output path (default: results.json)
  --seed INT            Random seed for simulation (default: 42)
  --log-level LEVEL     DEBUG / INFO / WARNING / ERROR
  --max-age FLOAT       Max market age in minutes for entry (default: 20)
  --min-yes-price FLOAT Min Yes price threshold (default: 0.70)
  --min-ev FLOAT        Min expected value for entry (default: 0.10)
```

### Live Data

Polymarket is public and requires no key:

```bash
python main.py --live
```

Kalshi requires an API key from https://kalshi.com:

```bash
python main.py --live --kalshi-key YOUR_KEY
```

## File Structure

```
binary_market_engine/
├── main.py          CLI entry point and orchestration
├── backtest.py      Backtesting loop and performance reporting
├── engine.py        Order execution, position tracking, risk controls
├── strategy.py      Bayesian EV, Kelly criterion, signal generation
├── simulator.py     Price evolution simulation for backtesting
├── fetch_data.py    Polymarket and Kalshi data fetchers
├── models.py        MarketData, Position, Trade, Signal dataclasses
├── config.py        Typed configuration dataclasses and constants
├── requirements.txt Python dependencies
└── results.json     Generated output (after first run)
```

## Strategy Parameters

Edit via CLI flags or by modifying `config.py` defaults:

| Parameter | Default | Description |
|---|---|---|
| max_age_minutes | 20 | Maximum market age for entry |
| min_yes_price | 0.70 | Minimum Yes price (overpricing threshold) |
| min_expected_return | 0.10 | Minimum expected value |
| confidence_threshold | 0.60 | Minimum confidence score |
| kelly_fraction | 0.25 | Kelly safety multiplier |
| max_position_usd | 1000 | Maximum position size |
| stop_loss_pct | 0.10 | Stop-loss percentage below entry |
| take_profit_pct | 0.20 | Take-profit percentage above entry |
| max_hold_minutes | 60 | Maximum position hold time |

## Algorithms

**Bayesian Probability Estimation**

```
P(Yes | Market) = BaseCategoryRate * (1 - 0.5 * SensationalismScore)
```

Sensationalism score is derived from keyword frequency. Confidence combines volume, sentiment, and category signals.

**Kelly Criterion Position Sizing**

```
Kelly% = (b * p - q) / b
where b = (1 - no_price) / no_price
      p = true P(No)
      q = 1 - p

Position = Kelly% * SafetyFactor * Capital
```

**Expected Value**

```
EV = P(No) * (1 - no_price) - P(Yes) * no_price
EV_net = EV * (1 - transaction_fee)
```

## Output

`results.json` contains:
- Run timestamp and configuration snapshot
- Performance metrics: ROI, win rate, Sharpe ratio, max drawdown
- All signals with EV, edge, and confidence
- Full trade log with realized PnL per trade
- Portfolio equity snapshots at each simulation step

## Limitations

- Order execution is simulated; real exchange integration requires additional API handling
- Fill price assumes no slippage beyond the configured factor
- Synthetic data demonstrates the strategy thesis; live markets may not always satisfy entry criteria

