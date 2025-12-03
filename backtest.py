import random
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import config

class BacktestEngine:
    def __init__(self, initial_capital: float = None):
        self.initial_capital = initial_capital or config.BACKTEST_CONFIG["initial_capital"]
        self.capital = self.initial_capital
        self.positions = []
        self.closed_trades = []
        self.transaction_fee = config.BACKTEST_CONFIG["transaction_fee"]
        self.slippage = config.BACKTEST_CONFIG["slippage"]
    
    def execute_trade(self, opportunity: Dict, timestamp: datetime) -> Dict:
        market = opportunity["market"]
        analytics = opportunity["analytics"]
        
        no_price = market["no_price"]
        entry_price = no_price * (1 + self.slippage)
        
        recommended_size = analytics["recommended_position_usd"]
        actual_size = min(recommended_size, self.capital * 0.2)
        
        shares = actual_size / entry_price
        cost = actual_size * (1 + self.transaction_fee)
        self.capital -= cost
        
        trade = {
            "market_id": market["id"],
            "question": market["question"],
            "entry_time": timestamp,
            "entry_price": entry_price,
            "shares": shares,
            "cost": cost,
            "true_yes_prob": analytics["true_yes_probability"],
            "expected_value": analytics["expected_value"],
        }
        
        self.positions.append(trade)
        return trade
    
    def close_trade(self, trade: Dict, exit_price: float, timestamp: datetime, outcome: str) -> Dict:
        if outcome == "win":
            proceeds = trade["shares"] * 1.0
        else:
            proceeds = 0.0
        
        net_proceeds = proceeds * (1 - self.transaction_fee)
        profit = net_proceeds - trade["cost"]
        roi = (profit / trade["cost"]) if trade["cost"] > 0 else 0
        
        self.capital += net_proceeds
        
        closed_trade = {
            **trade,
            "exit_time": timestamp,
            "exit_price": exit_price,
            "outcome": outcome,
            "proceeds": net_proceeds,
            "profit": profit,
            "roi": roi,
            "hold_time_hours": (timestamp - trade["entry_time"]).total_seconds() / 3600,
        }
        
        self.closed_trades.append(closed_trade)
        if trade in self.positions:
            self.positions.remove(trade)
        
        return closed_trade
    
    def simulate_market_resolution(self, trade: Dict) -> Tuple[str, float]:
        true_yes_prob = trade["true_yes_prob"]
        rand = random.random()
        
        if rand < true_yes_prob:
            outcome = "loss"
            exit_price = 0.0
        else:
            outcome = "win"
            exit_price = 1.0
        
        return outcome, exit_price
    
    def run_backtest(self, opportunities: List[Dict], num_simulations: int = 1) -> Dict:
        all_results = []
        
        for _ in range(num_simulations):
            self.capital = self.initial_capital
            self.positions = []
            self.closed_trades = []
            
            base_time = datetime.now()
            for i, opp in enumerate(opportunities):
                entry_time = base_time + timedelta(minutes=i * 30)
                trade = self.execute_trade(opp, entry_time)
                
                hold_hours = random.uniform(
                    config.BACKTEST_CONFIG["min_hold_minutes"] / 60,
                    config.BACKTEST_CONFIG["max_hold_minutes"] / 60
                )
                exit_time = entry_time + timedelta(hours=hold_hours)
                
                outcome, exit_price = self.simulate_market_resolution(trade)
                self.close_trade(trade, exit_price, exit_time, outcome)
            
            sim_results = self._calculate_metrics()
            all_results.append(sim_results)
        
        if num_simulations == 1:
            return all_results[0]
        else:
            return self._aggregate_simulations(all_results)
    
    def _calculate_metrics(self) -> Dict:
        if not self.closed_trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_profit": 0.0,
                "average_profit_per_trade": 0.0,
                "average_win": 0.0,
                "average_loss": 0.0,
                "profit_factor": 0.0,
                "initial_capital": self.initial_capital,
                "final_capital": self.capital,
                "total_return": 0.0,
                "roi_percent": 0.0,
                "max_drawdown_percent": 0.0,
            }
        
        total_trades = len(self.closed_trades)
        winning_trades = [t for t in self.closed_trades if t["outcome"] == "win"]
        losing_trades = [t for t in self.closed_trades if t["outcome"] == "loss"]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        total_profit = sum(t["profit"] for t in self.closed_trades)
        avg_profit = total_profit / total_trades if total_trades > 0 else 0
        
        avg_win = sum(t["profit"] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t["profit"] for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        profit_factor = abs(sum(t["profit"] for t in winning_trades) / sum(t["profit"] for t in losing_trades)) if losing_trades else float('inf')
        
        total_return = self.capital - self.initial_capital
        roi = (total_return / self.initial_capital) * 100
        
        cumulative_returns = []
        running_capital = self.initial_capital
        for trade in self.closed_trades:
            running_capital += trade["profit"]
            cumulative_returns.append(running_capital)
        
        max_drawdown = 0
        peak = self.initial_capital
        for capital in cumulative_returns:
            if capital > peak:
                peak = capital
            drawdown = (peak - capital) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        return {
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": round(win_rate, 4),
            "total_profit": round(total_profit, 2),
            "average_profit_per_trade": round(avg_profit, 2),
            "average_win": round(avg_win, 2),
            "average_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "initial_capital": self.initial_capital,
            "final_capital": round(self.capital, 2),
            "total_return": round(total_return, 2),
            "roi_percent": round(roi, 2),
            "max_drawdown_percent": round(max_drawdown * 100, 2),
        }
    
    def _aggregate_simulations(self, results: List[Dict]) -> Dict:
        aggregated = {}
        for key in results[0].keys():
            values = [r[key] for r in results]
            if isinstance(values[0], (int, float)):
                aggregated[f"avg_{key}"] = round(sum(values) / len(values), 2)
                aggregated[f"min_{key}"] = round(min(values), 2)
                aggregated[f"max_{key}"] = round(max(values), 2)
        
        aggregated["num_simulations"] = len(results)
        return aggregated

def run_simple_backtest(opportunities: List[Dict]) -> Dict:
    engine = BacktestEngine()
    return engine.run_backtest(opportunities, num_simulations=1)

def run_monte_carlo_backtest(opportunities: List[Dict], num_simulations: int = 100) -> Dict:
    engine = BacktestEngine()
    return engine.run_backtest(opportunities, num_simulations=num_simulations)
