import time
from datetime import timedelta
import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

class DataFetcher:
    def __init__(self, api_key: str, api_secret: str):
        """Initialize the Alpaca Historical Data Client."""
        self.client = StockHistoricalDataClient(api_key, api_secret)

    def fetch_data(self, symbol: str, start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
        """
        Fetch 1-minute OHLCV data in chunks to respect the 200 requests/minute limit.
        Uses 30-day chunks to minimize API calls while handling large datasets.
        """
        print(f"Fetching data for {symbol} from {start_date.date()} to {end_date.date()}...")
        all_bars = []
        current_start = start_date
        
        while current_start < end_date:
            # Fetch data in ~30 day chunks
            current_end = min(current_start + timedelta(days=30), end_date)
            
            request_params = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Minute,
                start=current_start,
                end=current_end
            )
            
            try:
                bars = self.client.get_stock_bars(request_params)
                if bars and bars.df is not None and not bars.df.empty:
                    # Depending on alpaca-py version, bars.df might have MultiIndex (symbol, timestamp)
                    df = bars.df
                    if isinstance(df.index, pd.MultiIndex):
                        df = df.xs(symbol, level='symbol')
                    all_bars.append(df)
            except Exception as e:
                print(f"Error fetching data from {current_start} to {current_end}: {e}")
            
            # Respect rate limit of 200 requests per minute (~3.3 requests per second)
            # Sleep for 0.4 seconds to stay safely under the limit
            time.sleep(0.4)
            
            # Move to next chunk
            current_start = current_end + timedelta(days=1)
            
        if not all_bars:
            return pd.DataFrame()
            
        # Concatenate all chunks and ensure it is sorted by time
        full_df = pd.concat(all_bars)
        full_df = full_df[~full_df.index.duplicated(keep='first')]
        full_df.sort_index(inplace=True)
        return full_df
