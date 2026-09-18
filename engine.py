import pandas as pd
from typing import Dict, List, Any

class BacktestEngine:
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.trades = []
        
    def run(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Run the backtest on the provided dataframe.
        Assumes df already has 'entry_signal', 'atr', and is in EST timezone.
        """
        in_position = False
        entry_price = 0.0
        stop_loss = 0.0
        take_profit = 0.0
        entry_time = None
        
        self.trades = []
        
        # Iterate over the rows
        for timestamp, row in df.iterrows():
            time_str = timestamp.strftime('%H:%M')
            
            if in_position:
                # Check for exits (Stop Loss or Take Profit)
                # Note: Intraday data can gap or wick, we assume pessimistic execution (stop loss hit if low <= stop loss)
                if row['low'] <= stop_loss:
                    exit_price = min(row['open'], stop_loss)  # Gap down protection
                    self._record_trade(entry_time, timestamp, entry_price, exit_price, "Stop Loss", row['atr'])
                    in_position = False
                elif row['high'] >= take_profit:
                    exit_price = max(row['open'], take_profit) # Gap up protection
                    self._record_trade(entry_time, timestamp, entry_price, exit_price, "Take Profit", row['atr'])
                    in_position = False
                # Intraday EOD exit (close position before market close)
                elif time_str >= '15:55':
                    self._record_trade(entry_time, timestamp, entry_price, row['close'], "EOD Close", row['atr'])
                    in_position = False
            
            # Re-check in_position as it might have just closed
            if not in_position and row['entry_signal']:
                in_position = True
                entry_price = row['open'] # Enter at the open of the signal candle
                entry_time = timestamp
                
                # Dynamic Stop Loss using ATR
                current_atr = row['atr']
                if pd.isna(current_atr) or current_atr == 0:
                    current_atr = entry_price * 0.005 # Fallback if ATR is not calculated yet
                
                stop_loss = entry_price - current_atr
                # 1.5:1 Reward-to-Risk ratio to target a ~40-45% win rate
                take_profit = entry_price + (1.5 * current_atr)

        return self.trades
        
    def _record_trade(self, entry_time, exit_time, entry_price, exit_price, exit_reason, atr):
        profit = exit_price - entry_price
        pct_return = profit / entry_price
        
        self.trades.append({
            'entry_time': entry_time,
            'exit_time': exit_time,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'profit_loss': profit,
            'return_pct': pct_return,
            'exit_reason': exit_reason,
            'atr_at_entry': atr
        })
