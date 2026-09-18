import os
import pandas as pd
from datetime import timedelta
from dotenv import load_dotenv
from data import DataFetcher
from strategy import apply_strategy_indicators, generate_signals
from engine import BacktestEngine
from metrics import calculate_metrics, print_performance_report

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Credentials should be set as environment variables for security (Github portfolio best practice)
    API_KEY = os.environ.get("ALPACA_API_KEY", "YOUR_API_KEY")
    API_SECRET = os.environ.get("ALPACA_API_SECRET", "YOUR_API_SECRET")
    
    if API_KEY == "YOUR_API_KEY":
        print("WARNING: Using dummy API keys. Please set ALPACA_API_KEY and ALPACA_API_SECRET environment variables.")
        print("Exiting to prevent unauthorized requests.")
        # For demonstration purposes, if you want to run this without credentials, 
        # you would need to load historical data from a CSV.
        return
        
    symbol = "TSLA"
    
    # 2 years of data
    end_date = pd.Timestamp.now(tz='UTC')
    start_date = end_date - timedelta(days=365 * 2)
    
    # 1. Data Pipeline
    fetcher = DataFetcher(API_KEY, API_SECRET)
    df = fetcher.fetch_data(symbol, start_date, end_date)
    
    if df.empty:
        print("No data fetched. Check your API keys and internet connection.")
        return
        
    # 2. Strategy Logic & Repainting Fix
    print("Applying strategy indicators...")
    df = apply_strategy_indicators(df)
    df = generate_signals(df)
    
    # 3. Curve Fitting Prevention (Dataset Split)
    # Split the dataset into 12 months In-Sample and 12 months Out-Of-Sample
    split_date = start_date + timedelta(days=365)
    
    in_sample_df = df[df.index < split_date].copy()
    out_of_sample_df = df[df.index >= split_date].copy()
    
    # 4. Run Backtest
    print("Running backtest engine...")
    engine = BacktestEngine()
    
    is_trades = engine.run(in_sample_df)
    oos_trades = engine.run(out_of_sample_df)
    
    # 5. Output Risk Parameters and Metrics
    is_metrics = calculate_metrics(is_trades)
    oos_metrics = calculate_metrics(oos_trades)
    
    print_performance_report(is_metrics, "In-Sample (Year 1)")
    print_performance_report(oos_metrics, "Out-of-Sample (Year 2)")

if __name__ == "__main__":
    main()
