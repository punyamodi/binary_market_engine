import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import config
import strategy
from engine import TradingEngine
from models import MarketData, Signal
from simulator import PriceSimulator

logger = logging.getLogger(__name__)


@dataclass
class SimulationStep:
    label: str
    elapsed_minutes: float


DEFAULT_STEPS: List[SimulationStep] = [
    SimulationStep("T+15m  | Hype fading", 15),
    SimulationStep("T+45m  | Trend continues", 30),
    SimulationStep("T+60m  | Near time exit", 15),
]


@dataclass
class BacktestResult:
    metrics: Dict
    trades: List[Dict]
    snapshots: List[Dict]
    signals: List[Dict]

    @property
    def roi_pct(self) -> float:
        return self.metrics.get("roi_pct", 0.0)

    @property
    def win_rate_pct(self) -> float:
        return self.metrics.get("win_rate_pct", 0.0)


class Backtester:
    def __init__(self, cfg: config.AppConfig = None, seed: int = 42):
        self._cfg = cfg or config.default_config()
        self._simulator = PriceSimulator(cfg=self._cfg, seed=seed)

    def run(
        self,
        markets: List[MarketData],
        steps: Optional[List[SimulationStep]] = None,
        verbose: bool = True,
    ) -> BacktestResult:
        if steps is None:
            steps = DEFAULT_STEPS

        engine = TradingEngine(
            initial_capital=self._cfg.backtest.initial_capital,
            cfg=self._cfg,
        )

        signals = strategy.run_strategy(markets, capital=engine.cash, cfg=self._cfg)
        if verbose:
            self._print_section("T=00:00 | Market Scan and Entry")
            logger.info("Fetched %d markets. Identified %d signals.", len(markets), len(signals))

        self._execute_entries(engine, signals, verbose)
        snap = engine.snapshot()
        if verbose:
            self._print_snapshot("Entry", snap)

        current_markets = markets
        for step in steps:
            current_markets = self._simulator.step(current_markets, step.elapsed_minutes)
            engine.update_prices(current_markets)
            engine.check_risk_controls()
            snap = engine.snapshot()
            if verbose:
                self._print_section(step.label)
                self._print_snapshot(step.label, snap)

        if engine.positions:
            engine.close_all_positions("Session end")
            engine.snapshot()

        metrics = engine.performance_metrics()
        if verbose:
            self._print_section("Final Performance Report")
            self._print_metrics(metrics, engine)

        return BacktestResult(
            metrics=metrics,
            trades=[
                {
                    "id": t.id,
                    "symbol": t.symbol,
                    "action": t.action,
                    "side": t.side,
                    "quantity": round(t.quantity, 2),
                    "price": round(t.price, 4),
                    "reason": t.reason,
                    "realized_pnl": round(t.realized_pnl, 2),
                    "timestamp": t.timestamp.isoformat(),
                }
                for t in engine.trades
            ],
            snapshots=[
                {
                    "timestamp": s.timestamp.isoformat(),
                    "cash": round(s.cash, 2),
                    "positions_value": round(s.positions_value, 2),
                    "total_equity": round(s.total_equity, 2),
                    "unrealized_pnl": round(s.unrealized_pnl, 2),
                    "position_count": s.position_count,
                }
                for s in engine._snapshots
            ],
            signals=[
                {
                    "market_id": s.market_id,
                    "question": s.market.question,
                    "outcome": s.outcome,
                    "expected_value": s.expected_value,
                    "edge": s.edge,
                    "confidence": s.confidence,
                    "recommended_position_usd": s.recommended_position_usd,
                    "sharpe_ratio": s.sharpe_ratio,
                    "reason": s.reason,
                }
                for s in signals
            ],
        )

    def _execute_entries(self, engine: TradingEngine, signals: List[Signal], verbose: bool) -> None:
        risk = self._cfg.risk
        fee_factor = 1.0 + self._cfg.backtest.transaction_fee

        for sig in signals:
            market = sig.market
            price = market.no_price * (1.0 + self._cfg.backtest.slippage)
            quantity = sig.recommended_position_usd / price
            stop_loss = price * (1.0 - risk.stop_loss_pct)
            take_profit = price * (1.0 + risk.take_profit_pct)

            if verbose:
                logger.info(
                    "Entering %s | Qty=%.0f | Price=%.4f | SL=%.4f | TP=%.4f",
                    market.question[:60], quantity, price, stop_loss, take_profit,
                )

            engine.execute_buy(
                market=market,
                outcome=sig.outcome,
                quantity=quantity,
                price=price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                reason=sig.reason,
            )

    @staticmethod
    def _print_section(title: str) -> None:
        print(f"\n{'=' * 72}")
        print(f"  {title}")
        print(f"{'=' * 72}")

    @staticmethod
    def _print_snapshot(label: str, snap) -> None:
        print(
            f"  Cash: ${snap.cash:,.2f} | "
            f"Equity: ${snap.total_equity:,.2f} | "
            f"Unrealized PnL: ${snap.unrealized_pnl:,.2f} | "
            f"Positions: {snap.position_count}"
        )

    @staticmethod
    def _print_metrics(metrics: Dict, engine: TradingEngine) -> None:
        print(f"  Initial Capital : ${metrics['initial_capital']:,.2f}")
        print(f"  Final Equity    : ${metrics['final_equity']:,.2f}")
        print(f"  Total Return    : ${metrics['total_return_usd']:+,.2f}")
        print(f"  ROI             : {metrics['roi_pct']:+.2f}%")
        print(f"  Realized PnL    : ${metrics['realized_pnl']:+,.2f}")
        print(f"  Win Rate        : {metrics['win_rate_pct']:.1f}%")
        print(f"  Max Drawdown    : {metrics['max_drawdown_pct']:.2f}%")
        print(f"  Total Trades    : {metrics['total_trades']}")
        print()
        print("  Trade Log:")
        for t in engine.trades:
            print(
                f"    {t.timestamp.strftime('%H:%M:%S')} "
                f"{t.action:4s} {t.symbol[:50]:50s} "
                f"@ {t.price:.4f} | PnL: {t.realized_pnl:+.2f} | {t.reason}"
            )
