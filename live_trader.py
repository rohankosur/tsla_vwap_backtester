import os
import time
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, TakeProfitRequest, StopLossRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
from strategy import apply_strategy_indicators

def get_today_data(data_client, symbol):
    # Fetch data for today to calculate VWAP
    # VWAP resets daily, so we only need today's data (or yesterday's for ATR)
    # We'll fetch the last 3 days to ensure we have enough data for a 14-period ATR
    end = pd.Timestamp.now(tz='UTC')
    start = end - timedelta(days=3)
    
    req = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Minute,
        start=start,
        end=end
    )
    bars = data_client.get_stock_bars(req)
    if not bars or bars.df is None or bars.df.empty:
        return pd.DataFrame()
        
    df = bars.df
    if isinstance(df.index, pd.MultiIndex):
        df = df.xs(symbol, level='symbol')
    return df

def run_live_trader():
    load_dotenv()
    API_KEY = os.environ.get("ALPACA_API_KEY")
    API_SECRET = os.environ.get("ALPACA_API_SECRET")
    
    if not API_KEY or not API_SECRET or API_KEY == "YOUR_API_KEY":
        print("Missing API credentials. Check .env file.")
        return

    # Initialize Clients (Paper Trading = True)
    trading_client = TradingClient(API_KEY, API_SECRET, paper=True)
    data_client = StockHistoricalDataClient(API_KEY, API_SECRET)
    
    symbol = "TSLA"
    qty = 10  # Paper trading quantity
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting Live VWAP Trader for {symbol}...")
    
    # Run loop until 11:00 AM EST
    while True:
        now_est = pd.Timestamp.now(tz='America/New_York')
        current_time = now_est.strftime('%H:%M')
        
        # Exit if past trading window
        if current_time > "11:00":
            print("Trading window closed for today. Exiting.")
            break
            
        # Only trade during the window
        if "09:45" <= current_time <= "11:00":
            # 1. Check if we already have an open position
            try:
                position = trading_client.get_open_position(symbol)
                print(f"[{current_time}] Already in position. Managing via bracket order. Sleeping...")
                time.sleep(60)
                continue
            except Exception:
                pass # No open position
                
            # 2. Fetch recent data and apply strategy
            df = get_today_data(data_client, symbol)
            if df.empty:
                print(f"[{current_time}] Failed to fetch data. Retrying in 60s...")
                time.sleep(60)
                continue
                
            df = apply_strategy_indicators(df)
            
            # 3. Check Signal on previous closed candle (i-1)
            # The most recent complete candle is df.iloc[-2] if the current minute is still forming,
            # or df.iloc[-1] if data API only returns completed candles.
            # Alpaca historical minute bars are typically returned once the minute is closed.
            # So the last row is i-1, and second to last is i-2.
            prev = df.iloc[-1]
            prev_prev = df.iloc[-2]
            
            crossed_above_vwap = (prev['close'] > prev['vwap']) and (prev_prev['close'] <= prev_prev['vwap'])
            
            if crossed_above_vwap:
                print(f"[{current_time}] SIGNAL DETECTED! Previous close ({prev['close']}) crossed VWAP ({prev['vwap']})")
                
                entry_price = prev['close']
                current_atr = prev['atr']
                
                if pd.isna(current_atr) or current_atr == 0:
                    current_atr = entry_price * 0.005
                
                # 1.5:1 R:R
                stop_loss_price = round(entry_price - current_atr, 2)
                take_profit_price = round(entry_price + (1.5 * current_atr), 2)
                
                print(f"Executing Buy for {qty} shares. SL: {stop_loss_price}, TP: {take_profit_price}")
                
                # 4. Execute Bracket Order
                order_data = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY,
                    order_class=OrderClass.BRACKET,
                    take_profit=TakeProfitRequest(limit_price=take_profit_price),
                    stop_loss=StopLossRequest(stop_price=stop_loss_price)
                )
                
                try:
                    trading_client.submit_order(order_data=order_data)
                    print("Order successfully submitted!")
                except Exception as e:
                    print(f"Failed to submit order: {e}")
                    
        # Sleep until the top of the next minute
        time.sleep(60 - datetime.now().second)

if __name__ == "__main__":
    run_live_trader()
