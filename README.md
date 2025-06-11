# PerpTradeSim - Perpetual Trading Bot Simulator

A comprehensive Streamlit-based perpetual trading bot simulator that provides real-time cryptocurrency trading simulation using live SOL/USDC price data from Jupiter API.

## Features

### 🚀 Live Trading Simulation
- Real-time SOL/USDC price data from Jupiter API
- Simulated perpetual trading with configurable leverage (1x to 20x)
- Long and short position support
- Automatic liquidation logic based on leverage ratios

### 📊 Trading Strategy
- Trend-following algorithm with configurable parameters
- Automatic position opening based on price momentum
- Customizable lookback periods and trend strength thresholds
- Trading fee simulation (0.1% default)

### 🎮 Manual Controls
- **Open Long** (📈) - Manually open long positions
- **Open Short** (📉) - Manually open short positions  
- **Close Position** (❌) - Manually close active positions
- **Start/Stop Bot** (🚀/⏹️) - Automated trading control

### 📈 Performance Tracking
- Real-time PnL calculation and display
- Win rate statistics
- Trade history with entry/exit prices
- Interactive price charts with trading signals
- Comprehensive performance metrics

### ⚙️ Customization
- Adjustable leverage (1x to 20x)
- Configurable position size
- Trend detection sensitivity settings
- Trading fee customization

## Technology Stack

- **Frontend**: Streamlit web framework
- **Backend**: Python with asyncio for real-time updates
- **Data Source**: Jupiter API (Solana DEX aggregator)
- **Charting**: Plotly for interactive visualizations
- **Data Processing**: Pandas and NumPy
