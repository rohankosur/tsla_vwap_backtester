import numpy as pd
import pandas as pd
import numpy as np

def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """
    Calculate the daily Volume Weighted Average Price (VWAP).
    Resets at the start of each trading session.
    """
    df = df.copy()
    # Typical price
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
    df['pv'] = df['typical_price'] * df['volume']
    
    # Calculate cumulative sums grouped by trading day
    # Assuming the index is timezone-aware or localized to EST
    df['date'] = df.index.date
    cumulative_pv = df.groupby('date')['pv'].cumsum()
    cumulative_vol = df.groupby('date')['volume'].cumsum()
    
    return cumulative_pv / cumulative_vol

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate the Average True Range (ATR) over the given period.
    """
    df = df.copy()
    df['prev_close'] = df['close'].shift(1)
    
    tr1 = df['high'] - df['low']
    tr2 = (df['high'] - df['prev_close']).abs()
    tr3 = (df['low'] - df['prev_close']).abs()
    
    df['true_range'] = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
    
    # Use exponential moving average for Wilder's Smoothing, or simple rolling mean
    # Standard Wilder's ATR uses an alpha of 1/period
    return df['true_range'].ewm(alpha=1/period, adjust=False).mean()

def apply_strategy_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply VWAP and ATR to the dataframe.
    """
    if df.empty:
        return df
        
    df = df.copy()
    
    # Convert timezone to EST/America/New_York for proper daily grouping and time filtering
    if df.index.tz is None:
        # Assume UTC if no timezone
        df = df.tz_localize('UTC').tz_convert('America/New_York')
    else:
        df = df.tz_convert('America/New_York')
        
    df['vwap'] = calculate_vwap(df)
    df['atr'] = calculate_atr(df, period=14)
    
    return df

def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate Long entry signals based on the logic:
    1. Time is between 9:45 AM and 11:00 AM EST.
    2. Previous closed candle (i-1) crosses above VWAP.
    """
    df = df.copy()
    
    # Get hour and minute (dataframe is already in EST)
    df['time_str'] = df.index.strftime('%H:%M')
    
    # Boolean mask for trading window (9:45 AM - 11:00 AM)
    in_window = (df['time_str'] >= '09:45') & (df['time_str'] <= '11:00')
    
    # Repainting fix: only use the previous candle for crossing logic
    prev_close = df['close'].shift(1)
    prev_open = df['open'].shift(1)
    prev_vwap = df['vwap'].shift(1)
    prev_prev_close = df['close'].shift(2)
    prev_prev_vwap = df['vwap'].shift(2)
    
    # Cross over VWAP condition for the PREVIOUS candle:
    # It must have started below/equal and closed above VWAP
    # Or previous close > previous VWAP and prev prev close < prev prev VWAP
    crossed_above_vwap = (prev_close > prev_vwap) & (prev_prev_close <= prev_prev_vwap)
    
    # Signal is true if both conditions hold
    df['entry_signal'] = in_window & crossed_above_vwap
    
    return df
