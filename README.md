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

  
## Usage

### Getting Started
1. Launch the application and wait for initial price data to load
2. Configure your trading parameters in the sidebar:
   - Set leverage (1x to 20x)
   - Adjust position size in USDC
   - Customize trend detection settings

### Manual Trading
- Use **Open Long** when you expect price to rise
- Use **Open Short** when you expect price to fall
- Monitor your position's PnL in real-time
- Close positions manually using **Close Position**

### Automated Trading
- Click **Start Bot** to enable automated trend-following
- The bot will analyze price movements and open/close positions automatically
- Monitor trading actions in the trade log
- Stop automation anytime with **Stop Bot**

### Performance Analysis
- View real-time price charts with your trading signals
- Track cumulative PnL over time
- Analyze win rate and trading statistics
- Review detailed trade history

## Key Components

### Trading Strategy (`strategy.py`)
- Implements trend-following algorithm
- Manages position lifecycle and PnL calculation
- Handles liquidation logic and risk management

### Jupiter API Client (`jupiter_api.py`)
- Fetches real-time SOL/USDC prices
- Implements retry logic for reliable data access
- No authentication required

### Trading Bot (`trading_bot.py`)
- Coordinates strategy execution with price updates
- Manages automated trading loop
- Provides manual trading interface

### Streamlit App (`app.py`)
- User interface and visualization
- Real-time dashboard updates
- Interactive controls and configuration
