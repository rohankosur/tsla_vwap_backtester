# TSLA Intraday VWAP Strategy Backtester

This repository contains a modular Python backtesting engine built with `alpaca-py` to test an intraday VWAP strategy on Tesla (TSLA).

## Architecture
- **Data Pipeline (`data.py`)**: Fetches 2 years of 1-minute OHLCV data in chunks to respect Alpaca's free tier rate limits (200 requests/minute).
- **Strategy Logic (`strategy.py`)**: Implements the daily Volume Weighted Average Price (VWAP) calculation and 14-period Average True Range (ATR). It contains strict repainting prevention by ensuring trading logic relies exclusively on closed candles.
- **Backtest Engine (`engine.py`)**: An event-driven loop that simulates historical execution, including dynamic stop-loss and take-profit mechanisms.
- **Metrics (`metrics.py`)**: Calculates robust performance statistics including Win Rate, Profit Factor, and Maximum Drawdown to evaluate strategy viability.
- **Main (`main.py`)**: Orchestrates the pipeline and performs Out-of-Sample (OOS) vs. In-Sample (IS) curve fitting analysis.

## Strategy Rules
- **Instrument**: TSLA
- **Timeframe**: 1-minute
- **Trading Window**: 9:45 AM - 11:00 AM EST
- **Entry**: Long only. Triggers when the *previous* closed candle (i-1) crosses above the daily VWAP.
- **Risk Management**:
  - Stop-Loss: Dynamic, 1x 14-period ATR
  - Take-Profit: 2:1 Reward-to-Risk ratio (2x ATR)
  - Intraday EOD Close: Closes open positions at 15:55 EST.

## Curve Fitting Prevention
The engine automatically splits the fetched dataset into:
1. **In-Sample Data**: First 12 months used for strategy observation.
2. **Out-of-Sample Data**: Last 12 months used to validate the strategy's robustness on unseen market conditions.

## Usage

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your Alpaca API keys as environment variables:
```bash
export ALPACA_API_KEY="your_api_key_here"
export ALPACA_API_SECRET="your_api_secret_here"
```

3. Run the backtest:
```bash
python main.py
```
