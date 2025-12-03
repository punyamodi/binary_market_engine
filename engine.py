import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class Position:
    market_id: str
    symbol: str
    side: str
    quantity: float
    entry_price: float
    current_price: float
    timestamp: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    max_hold_time_minutes: Optional[int] = None

    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        return (self.current_price - self.entry_price) * self.quantity

    @property
    def unrealized_pnl_percent(self) -> float:
        if self.entry_price == 0:
            return 0.0
        return (self.current_price - self.entry_price) / self.entry_price

@dataclass
class Trade:
    id: str
    market_id: str
    symbol: str
    side: str
    action: str
    quantity: float
    price: float
    timestamp: datetime
    reason: str

class TradingEngine:
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.history: List[Dict] = []

    def execute_order(self, market: Dict, action: str, outcome: str, quantity: float, price: float, 
                     stop_loss: Optional[float] = None, 
                     take_profit: Optional[float] = None,
                     max_hold_time: Optional[int] = None,
                     reason: str = "") -> bool:
        
        cost = quantity * price
        
        if action == "BUY":
            if cost > self.cash:
                print(f"❌ Insufficient funds to buy {market['question']}")
                return False
            
            self.cash -= cost
            
            market_id = market['id']
            if market_id in self.positions:
                pos = self.positions[market_id]
                total_cost = (pos.quantity * pos.entry_price) + cost
                total_qty = pos.quantity + quantity
                pos.entry_price = total_cost / total_qty
                pos.quantity = total_qty
                pos.current_price = price
            else:
                self.positions[market_id] = Position(
                    market_id=market_id,
                    symbol=f"{market['question']} - {outcome}",
                    side=outcome,
                    quantity=quantity,
                    entry_price=price,
                    current_price=price,
                    timestamp=datetime.now(),
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    max_hold_time_minutes=max_hold_time
                )
            
            self._record_trade(market_id, market['question'], outcome, "BUY", quantity, price, reason)
            return True
        
        elif action == "SELL":
            market_id = market['id']
            if market_id not in self.positions:
                print(f"❌ No position found for {market['question']}")
                return False
            
            pos = self.positions[market_id]
            if quantity > pos.quantity:
                quantity = pos.quantity
            
            proceeds = quantity * price
            self.cash += proceeds
            
            pos.quantity -= quantity
            if pos.quantity <= 0.0001:
                del self.positions[market_id]
            
            self._record_trade(market_id, market['question'], outcome, "SELL", quantity, price, reason)
            return True
            
        return False

    def _record_trade(self, market_id: str, symbol: str, side: str, action: str, quantity: float, price: float, reason: str):
        trade = Trade(
            id=str(uuid.uuid4())[:8],
            market_id=market_id,
            symbol=symbol,
            side=side,
            action=action,
            quantity=quantity,
            price=price,
            timestamp=datetime.now(),
            reason=reason
        )
        self.trades.append(trade)
        print(f"✅ {action} {quantity:.0f} shares of '{symbol}' at ${price:.2f} | Reason: {reason}")

    def update_market_prices(self, current_market_data: List[Dict]):
        """Updates the current price of all positions based on new market data."""
        market_map = {m['id']: m for m in current_market_data}
        
        for market_id, position in list(self.positions.items()):
            if market_id in market_map:
                market = market_map[market_id]
                if position.side == "NO":
                    position.current_price = market.get('no_price', 0.5)
                else:
                    position.current_price = market.get('yes_price', 0.5)

    def check_risk_management(self):
        """Checks all positions for Stop Loss, Take Profit, or Time Exit conditions."""
        for market_id, position in list(self.positions.items()):
            if position.max_hold_time_minutes:
                elapsed = (datetime.now() - position.timestamp).total_seconds() / 60
                if elapsed >= position.max_hold_time_minutes:
                    self._force_close(position, "Time Exit Reached")
                    continue

            if position.stop_loss:
                if position.current_price <= position.stop_loss:
                    self._force_close(position, f"Stop Loss Hit (${position.current_price:.2f} <= ${position.stop_loss:.2f})")
                    continue

            if position.take_profit:
                if position.current_price >= position.take_profit:
                    self._force_close(position, f"Take Profit Hit (${position.current_price:.2f} >= ${position.take_profit:.2f})")
                    continue

    def _force_close(self, position: Position, reason: str):
        """Executes a market sell for the entire position."""
        dummy_market = {
            'id': position.market_id,
            'question': position.symbol.replace(f" - {position.side}", "")
        }
        self.execute_order(
            market=dummy_market,
            action="SELL",
            outcome=position.side,
            quantity=position.quantity,
            price=position.current_price,
            reason=reason
        )

    def get_portfolio_summary(self) -> Dict:
        total_position_value = sum(p.market_value for p in self.positions.values())
        total_equity = self.cash + total_position_value
        unrealized_pnl = sum(p.unrealized_pnl for p in self.positions.values())
        
        return {
            "cash": self.cash,
            "positions_value": total_position_value,
            "total_equity": total_equity,
            "unrealized_pnl": unrealized_pnl,
            "position_count": len(self.positions)
        }
