import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import config
from models import MarketData, Position, PortfolioSnapshot, Trade

logger = logging.getLogger(__name__)


class TradingEngine:
    def __init__(self, initial_capital: float = 10000.0, cfg: config.AppConfig = None):
        self._cfg = cfg or config.default_config()
        self._risk = self._cfg.risk
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self._snapshots: List[PortfolioSnapshot] = []

    def execute_buy(
        self,
        market: MarketData,
        outcome: str,
        quantity: float,
        price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        reason: str = "",
    ) -> bool:
        if len(self.positions) >= self._risk.max_concurrent_positions:
            logger.warning("Max concurrent positions reached; skipping %s", market.question)
            return False

        cost = quantity * price
        if cost > self.cash:
            logger.warning("Insufficient funds: need %.2f, have %.2f", cost, self.cash)
            return False

        self.cash -= cost

        if market.id in self.positions:
            pos = self.positions[market.id]
            total_cost = (pos.quantity * pos.entry_price) + cost
            total_qty = pos.quantity + quantity
            pos.entry_price = total_cost / total_qty
            pos.quantity = total_qty
            pos.current_price = price
        else:
            self.positions[market.id] = Position(
                market_id=market.id,
                symbol=f"{market.question} [{outcome}]",
                side=outcome,
                quantity=quantity,
                entry_price=price,
                current_price=price,
                open_time=datetime.now(),
                stop_loss=stop_loss,
                take_profit=take_profit,
                max_hold_minutes=self._risk.max_hold_minutes,
            )

        self._record_trade(market.id, market.question, outcome, "BUY", quantity, price, reason, 0.0)
        return True

    def execute_sell(
        self,
        market_id: str,
        outcome: str,
        quantity: float,
        price: float,
        reason: str = "",
    ) -> bool:
        if market_id not in self.positions:
            logger.warning("No position for market_id %s", market_id)
            return False

        pos = self.positions[market_id]
        quantity = min(quantity, pos.quantity)
        proceeds = quantity * price
        realized_pnl = (price - pos.entry_price) * quantity

        self.cash += proceeds
        pos.quantity -= quantity

        if pos.quantity <= 1e-6:
            del self.positions[market_id]

        symbol = pos.symbol.split(" [")[0]
        self._record_trade(market_id, symbol, outcome, "SELL", quantity, price, reason, realized_pnl)
        return True

    def _record_trade(
        self,
        market_id: str,
        symbol: str,
        side: str,
        action: str,
        quantity: float,
        price: float,
        reason: str,
        realized_pnl: float,
    ) -> None:
        trade = Trade(
            market_id=market_id,
            symbol=symbol,
            side=side,
            action=action,
            quantity=quantity,
            price=price,
            reason=reason,
            realized_pnl=realized_pnl,
        )
        self.trades.append(trade)
        logger.info(
            "%s %.0f shares of '%s' at %.4f | PnL: %.2f | %s",
            action, quantity, symbol, price, realized_pnl, reason,
        )

    def update_prices(self, markets: List[MarketData]) -> None:
        market_map = {m.id: m for m in markets}
        for market_id, position in self.positions.items():
            if market_id in market_map:
                m = market_map[market_id]
                position.current_price = m.no_price if position.side == "NO" else m.yes_price

    def check_risk_controls(self) -> None:
        for market_id, pos in list(self.positions.items()):
            if pos.max_hold_minutes is not None and pos.age_minutes >= pos.max_hold_minutes:
                self.execute_sell(market_id, pos.side, pos.quantity, pos.current_price, "Time exit")
                continue

            if pos.stop_loss is not None and pos.current_price <= pos.stop_loss:
                self.execute_sell(
                    market_id, pos.side, pos.quantity, pos.current_price,
                    f"Stop loss {pos.current_price:.4f} <= {pos.stop_loss:.4f}",
                )
                continue

            if pos.take_profit is not None and pos.current_price >= pos.take_profit:
                self.execute_sell(
                    market_id, pos.side, pos.quantity, pos.current_price,
                    f"Take profit {pos.current_price:.4f} >= {pos.take_profit:.4f}",
                )

    def close_all_positions(self, reason: str = "Session end") -> None:
        for market_id, pos in list(self.positions.items()):
            self.execute_sell(market_id, pos.side, pos.quantity, pos.current_price, reason)

    def snapshot(self) -> PortfolioSnapshot:
        positions_value = sum(p.market_value for p in self.positions.values())
        total_equity = self.cash + positions_value
        unrealized_pnl = sum(p.unrealized_pnl for p in self.positions.values())
        snap = PortfolioSnapshot(
            timestamp=datetime.now(),
            cash=self.cash,
            positions_value=positions_value,
            total_equity=total_equity,
            unrealized_pnl=unrealized_pnl,
            position_count=len(self.positions),
        )
        self._snapshots.append(snap)
        return snap

    def performance_metrics(self) -> Dict:
        total_trades = len(self.trades)
        buys = [t for t in self.trades if t.action == "BUY"]
        sells = [t for t in self.trades if t.action == "SELL"]
        realized_pnl = sum(t.realized_pnl for t in sells)
        win_trades = [t for t in sells if t.realized_pnl > 0]
        win_rate = len(win_trades) / len(sells) if sells else 0.0

        peak = self.initial_capital
        max_drawdown = 0.0
        running = self.initial_capital
        for snap in self._snapshots:
            running = snap.total_equity
            if running > peak:
                peak = running
            drawdown = (peak - running) / peak if peak > 0 else 0.0
            max_drawdown = max(max_drawdown, drawdown)

        final_equity = self.cash + sum(p.market_value for p in self.positions.values())
        roi = (final_equity - self.initial_capital) / self.initial_capital

        returns = []
        prev = self.initial_capital
        for snap in self._snapshots:
            if prev > 0:
                returns.append((snap.total_equity - prev) / prev)
            prev = snap.total_equity

        if len(returns) > 1:
            import statistics
            avg_return = statistics.mean(returns)
            std_return = statistics.stdev(returns)
            sharpe = (avg_return / std_return) * (252 ** 0.5) if std_return > 0 else 0.0
        else:
            sharpe = 0.0

        return {
            "initial_capital": round(self.initial_capital, 2),
            "final_equity": round(final_equity, 2),
            "total_return_usd": round(final_equity - self.initial_capital, 2),
            "roi_pct": round(roi * 100, 2),
            "realized_pnl": round(realized_pnl, 2),
            "total_trades": total_trades,
            "buy_count": len(buys),
            "sell_count": len(sells),
            "win_rate_pct": round(win_rate * 100, 2),
            "max_drawdown_pct": round(max_drawdown * 100, 2),
            "sharpe_ratio": round(sharpe, 2),
        }

