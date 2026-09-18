import pandas as pd
import numpy as np
from typing import List, Dict, Any

def calculate_metrics(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate performance metrics from a list of trades.
    Required metrics: Total Trades, Win Rate, Profit Factor, Maximum Drawdown
    """
    if not trades:
        return {
            "Total Trades": 0,
            "Win Rate": "0.00%",
            "Profit Factor": 0.0,
            "Maximum Drawdown": "0.00%"
        }
        
    df = pd.DataFrame(trades)
    
    # 1. Total Trades
    total_trades = len(df)
    
    # 2. Win Rate
    winning_trades = df[df['return_pct'] > 0]
    win_rate = len(winning_trades) / total_trades
    
    # 3. Profit Factor (Gross Profit / Gross Loss)
    gross_profit = df[df['return_pct'] > 0]['return_pct'].sum()
    gross_loss = abs(df[df['return_pct'] < 0]['return_pct'].sum())
    
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    # 4. Maximum Drawdown
    # Calculate equity curve assuming compounding 100% of capital each trade
    df['equity_multiplier'] = 1 + df['return_pct']
    df['equity_curve'] = df['equity_multiplier'].cumprod()
    
    # Peak equity so far
    df['peak_equity'] = df['equity_curve'].cummax()
    
    # Drawdown from peak
    df['drawdown'] = (df['equity_curve'] - df['peak_equity']) / df['peak_equity']
    max_drawdown = abs(df['drawdown'].min())
    
    return {
        "Total Trades": total_trades,
        "Win Rate": f"{win_rate * 100:.2f}%",
        "Profit Factor": round(profit_factor, 2),
        "Maximum Drawdown": f"{max_drawdown * 100:.2f}%"
    }

def print_performance_report(metrics: Dict[str, Any], title: str):
    """
    Pretty print the performance report.
    """
    print("=" * 40)
    print(f"{title.upper()} PERFORMANCE REPORT")
    print("=" * 40)
    for key, value in metrics.items():
        print(f"{key.ljust(20)}: {value}")
    print("=" * 40)
    print()
