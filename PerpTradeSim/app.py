import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta
import logging
from trading_bot import TradingBot

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Page configuration
st.set_page_config(
    page_title="Perpetual Trading Bot Simulator",
    page_icon="💹",
    layout="wide"
)

# Initialize session state
if 'bot' not in st.session_state:
    st.session_state.bot = TradingBot()
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()

def format_currency(value: float) -> str:
    """Format currency values"""
    return f"${value:,.2f}"

def format_percentage(value: float) -> str:
    """Format percentage values"""
    return f"{value:.2f}%"

def create_price_chart(price_history, trade_log, current_position):
    """Create price chart with trading signals"""
    if not price_history:
        return go.Figure().add_annotation(
            text="No price data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    # Convert to DataFrame
    df = pd.DataFrame(price_history)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=('SOL/USDC Price', 'Trading Actions'),
        row_heights=[0.7, 0.3]
    )
    
    # Price line
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['price'],
            mode='lines',
            name='SOL/USDC',
            line=dict(color='blue', width=2)
        ),
        row=1, col=1
    )
    
    # Add trade markers
    if trade_log:
        trade_df = pd.DataFrame(trade_log)
        trade_df['timestamp'] = pd.to_datetime(trade_df['timestamp'])
        
        # Entry points
        entries = trade_df[trade_df['action'].isin(['opened_long', 'opened_short'])]
        if not entries.empty:
            for i, (_, row) in enumerate(entries.iterrows()):
                color = 'green' if row['action'] == 'opened_long' else 'red'
                symbol = 'triangle-up' if row['action'] == 'opened_long' else 'triangle-down'
                
                fig.add_trace(
                    go.Scatter(
                        x=[row['timestamp']],
                        y=[row['price']],
                        mode='markers',
                        name=f"{str(row['action']).replace('_', ' ').title()}",
                        marker=dict(
                            color=color,
                            size=12,
                            symbol=symbol
                        ),
                        showlegend=i == 0
                    ),
                    row=1, col=1
                )
        
        # Exit points
        exits = trade_df[trade_df['action'].isin(['closed_position', 'liquidated', 'manual_close'])]
        if not exits.empty:
            fig.add_trace(
                go.Scatter(
                    x=exits['timestamp'],
                    y=exits['price'],
                    mode='markers',
                    name='Position Closed',
                    marker=dict(
                        color='orange',
                        size=10,
                        symbol='x'
                    )
                ),
                row=1, col=1
            )
    
    # Current position line
    if current_position and price_history:
        entry_price = current_position['entry_price']
        liquidation_price = current_position['liquidation_price']
        
        fig.add_hline(
            y=entry_price,
            line_dash="dash",
            line_color="blue",
            annotation_text=f"Entry: ${entry_price:.4f}"
        )
        
        fig.add_hline(
            y=liquidation_price,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Liquidation: ${liquidation_price:.4f}"
        )
    
    # Trading volume/activity subplot
    if trade_log:
        trade_counts = pd.Series([1] * len(trade_log), index=pd.to_datetime([t['timestamp'] for t in trade_log]))
        trade_counts = trade_counts.resample('1h').sum().fillna(0)
        
        fig.add_trace(
            go.Bar(
                x=trade_counts.index,
                y=trade_counts.values,
                name='Trading Activity',
                marker_color='lightblue'
            ),
            row=2, col=1
        )
    
    fig.update_layout(
        title="Trading Bot Performance",
        xaxis_title="Time",
        yaxis_title="Price (USDC)",
        height=600,
        showlegend=True
    )
    
    return fig

def create_pnl_chart(completed_trades):
    """Create PnL chart"""
    if not completed_trades:
        return go.Figure().add_annotation(
            text="No completed trades yet",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    # Calculate cumulative PnL
    cumulative_pnl = 0
    pnl_data = []
    
    for trade in completed_trades:
        cumulative_pnl += trade.pnl
        pnl_data.append({
            'timestamp': trade.exit_time,
            'trade_pnl': trade.pnl,
            'cumulative_pnl': cumulative_pnl
        })
    
    df = pd.DataFrame(pnl_data)
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=('Cumulative PnL', 'Individual Trade PnL'),
        row_heights=[0.6, 0.4]
    )
    
    # Cumulative PnL
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['cumulative_pnl'],
            mode='lines+markers',
            name='Cumulative PnL',
            line=dict(color='green', width=3),
            fill='tozeroy'
        ),
        row=1, col=1
    )
    
    # Individual trade PnL
    colors = ['green' if pnl > 0 else 'red' for pnl in df['trade_pnl']]
    fig.add_trace(
        go.Bar(
            x=df['timestamp'],
            y=df['trade_pnl'],
            name='Trade PnL',
            marker_color=colors
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        title="Profit & Loss Analysis",
        height=500,
        showlegend=True
    )
    
    return fig

def main():
    st.title("💹 Perpetual Trading Bot Simulator")
    st.markdown("**SOL/USDC Trend Following Strategy with Jupiter API**")
    
    # Sidebar controls
    st.sidebar.header("Controls")
    
    # Bot control buttons
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("🚀 Start Bot", disabled=st.session_state.bot.is_running):
            st.session_state.bot.start()
            st.success("Bot started!")
            st.rerun()
    
    with col2:
        if st.button("⏹️ Stop Bot", disabled=not st.session_state.bot.is_running):
            st.session_state.bot.stop()
            st.success("Bot stopped!")
            st.rerun()
    
    # Manual actions
    st.sidebar.subheader("Manual Actions")
    
    # Check if we have a position and price data
    has_position = st.session_state.bot.strategy.current_position is not None
    has_price = st.session_state.bot.last_price is not None
    
    # Show position status for debugging
    if has_position:
        pos = st.session_state.bot.strategy.current_position
        st.sidebar.write(f"Current Position: {pos.side.upper()} at ${pos.entry_price:.4f}")
    
    if st.sidebar.button("❌ Close Position", disabled=not (has_position and has_price)):
        trade = st.session_state.bot.manual_close_position()
        if trade:
            st.sidebar.success(f"Position closed! PnL: {format_currency(trade.pnl)}")
        else:
            if not has_position:
                st.sidebar.warning("No position to close")
            elif not has_price:
                st.sidebar.warning("No current price data")
            else:
                st.sidebar.error("Failed to close position")
        st.rerun()
    
    # Manual position opening buttons
    if not has_position and has_price:
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("📈 Open Long"):
                if st.session_state.bot.strategy.open_position('long', st.session_state.bot.last_price, datetime.now()):
                    st.sidebar.success("Long position opened!")
                else:
                    st.sidebar.error("Failed to open position")
                st.rerun()
        with col2:
            if st.button("📉 Open Short"):
                if st.session_state.bot.strategy.open_position('short', st.session_state.bot.last_price, datetime.now()):
                    st.sidebar.success("Short position opened!")
                else:
                    st.sidebar.error("Failed to open position")
                st.rerun()
    
    if st.sidebar.button("📊 Fetch Price Now"):
        st.session_state.bot._fetch_and_process_price()
        st.sidebar.success("Price fetched and processed!")
        st.rerun()
    
    if st.sidebar.button("🔄 Reset Strategy"):
        st.session_state.bot.reset_strategy()
        st.sidebar.success("Strategy reset!")
        st.rerun()
    
    # Auto-refresh toggle
    st.sidebar.subheader("Display Options")
    auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)", value=st.session_state.auto_refresh)
    st.session_state.auto_refresh = auto_refresh
    
    # Strategy parameters
    st.sidebar.subheader("Strategy Parameters")
    
    with st.sidebar.expander("Adjust Parameters"):
        leverage = st.slider("Leverage", 1.0, 20.0, st.session_state.bot.strategy.leverage, 0.5)
        position_size = st.slider("Position Size (USDC)", 50.0, 500.0, st.session_state.bot.strategy.position_size, 10.0)
        lookback_periods = st.slider("Lookback Periods", 2, 10, st.session_state.bot.strategy.lookback_periods, 1)
        min_trend_strength = st.slider("Min Trend Strength (%)", 0.01, 1.0, st.session_state.bot.strategy.min_trend_strength * 100, 0.01) / 100
        
        if st.button("Update Parameters"):
            st.session_state.bot.update_strategy_params(
                leverage=leverage,
                position_size=position_size,
                lookback_periods=lookback_periods,
                min_trend_strength=min_trend_strength
            )
            st.success("Parameters updated!")
            st.rerun()
    
    # Main dashboard
    status = st.session_state.bot.get_current_status()
    
    # Status indicators
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_color = "🟢" if status['is_running'] else "🔴"
        st.metric("Bot Status", f"{status_color} {'Running' if status['is_running'] else 'Stopped'}")
    
    with col2:
        if status['last_price']:
            st.metric("Current SOL Price", format_currency(status['last_price']))
        else:
            st.metric("Current SOL Price", "N/A")
    
    with col3:
        if status['last_update']:
            time_diff = datetime.now() - status['last_update']
            st.metric("Last Update", f"{int(time_diff.total_seconds())}s ago")
        else:
            st.metric("Last Update", "Never")
    
    with col4:
        st.metric("Data Points", f"{status['price_history_count']}")
    
    # Current position info
    if status['current_position']:
        st.subheader("📊 Current Position")
        pos = status['current_position']
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            side_emoji = "📈" if pos['side'] == 'long' else "📉"
            st.metric("Side", f"{side_emoji} {pos['side'].upper()}")
        with col2:
            st.metric("Entry Price", format_currency(pos['entry_price']))
        with col3:
            st.metric("Position Size", format_currency(pos['size']))
        with col4:
            st.metric("Leverage", f"{pos['leverage']:.1f}x")
        with col5:
            pnl_color = "normal" if pos['unrealized_pnl'] >= 0 else "inverse"
            st.metric("Unrealized PnL", format_currency(pos['unrealized_pnl']), delta_color=pnl_color)
        
        # Risk metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Liquidation Price", format_currency(pos['liquidation_price']))
        with col2:
            if status['last_price']:
                distance_to_liq = abs(status['last_price'] - pos['liquidation_price']) / status['last_price'] * 100
                st.metric("Distance to Liquidation", format_percentage(distance_to_liq))
        with col3:
            duration = datetime.now() - pos['entry_time']
            st.metric("Position Duration", f"{int(duration.total_seconds() / 60)}m")
    
    # Strategy statistics
    stats = st.session_state.bot.get_strategy_stats()
    
    st.subheader("📈 Performance Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Balance", format_currency(stats['current_balance']))
    with col2:
        pnl_color = "normal" if stats['realized_pnl'] >= 0 else "inverse"
        st.metric("Realized PnL", format_currency(stats['realized_pnl']), delta_color=pnl_color)
    with col3:
        st.metric("Total Trades", stats['total_trades'])
    with col4:
        st.metric("Win Rate", format_percentage(stats['win_rate']))
    with col5:
        st.metric("Total Fees", format_currency(stats['total_fees']))
    
    if stats['total_trades'] > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            avg_color = "normal" if stats['avg_trade'] >= 0 else "inverse"
            st.metric("Avg Trade", format_currency(stats['avg_trade']), delta_color=avg_color)
        with col2:
            st.metric("Avg Win", format_currency(stats['avg_win']))
        with col3:
            st.metric("Avg Loss", format_currency(stats['avg_loss']))
    
    # Charts
    price_history = st.session_state.bot.get_price_history()
    trade_log = st.session_state.bot.get_trade_log()
    completed_trades = st.session_state.bot.get_completed_trades()
    
    # Price chart
    st.subheader("📊 Price Chart & Trading Signals")
    price_chart = create_price_chart(price_history, trade_log, status['current_position'])
    st.plotly_chart(price_chart, use_container_width=True)
    
    # PnL chart
    if completed_trades:
        st.subheader("💰 Profit & Loss Analysis")
        pnl_chart = create_pnl_chart(completed_trades)
        st.plotly_chart(pnl_chart, use_container_width=True)
    
    # Recent activity
    if trade_log:
        st.subheader("📋 Recent Trading Activity")
        recent_trades = trade_log[-10:]  # Last 10 activities
        
        for activity in reversed(recent_trades):
            action_emoji = {
                'opened_long': '📈',
                'opened_short': '📉',
                'closed_position': '❌',
                'liquidated': '💥',
                'manual_close': '✋'
            }.get(activity['action'], '❓')
            
            st.write(f"{action_emoji} **{activity['action'].replace('_', ' ').title()}** at {format_currency(activity['price'])} - {activity['datetime_str']}")
    
    # Data tables
    with st.expander("📊 Detailed Data"):
        tab1, tab2, tab3 = st.tabs(["Price History", "Trade Log", "Completed Trades"])
        
        with tab1:
            if price_history:
                df_prices = pd.DataFrame(price_history[-50:])  # Last 50 prices
                df_prices = df_prices[['datetime_str', 'price']].rename(columns={'datetime_str': 'Time', 'price': 'Price'})
                st.dataframe(df_prices, use_container_width=True)
        
        with tab2:
            if trade_log:
                df_trades = pd.DataFrame(trade_log)
                df_trades = df_trades[['datetime_str', 'action', 'price']].rename(columns={
                    'datetime_str': 'Time', 
                    'action': 'Action', 
                    'price': 'Price'
                })
                st.dataframe(df_trades, use_container_width=True)
        
        with tab3:
            if completed_trades:
                trades_data = []
                for trade in completed_trades:
                    trades_data.append({
                        'Entry Time': trade.entry_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'Exit Time': trade.exit_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'Side': trade.side.upper(),
                        'Entry Price': trade.entry_price,
                        'Exit Price': trade.exit_price,
                        'Size': trade.size,
                        'Leverage': f"{trade.leverage}x",
                        'PnL': trade.pnl,
                        'Reason': trade.reason
                    })
                
                df_completed = pd.DataFrame(trades_data)
                st.dataframe(df_completed, use_container_width=True)
    
    # Auto-refresh logic
    if auto_refresh and status['is_running']:
        time_since_refresh = datetime.now() - st.session_state.last_refresh
        if time_since_refresh.total_seconds() >= 30:
            st.session_state.last_refresh = datetime.now()
            st.rerun()
        else:
            remaining = 30 - int(time_since_refresh.total_seconds())
            st.sidebar.write(f"🔄 Next refresh in {remaining}s")
    
    # Footer
    st.markdown("---")
    st.markdown("💡 **Tips**: Monitor the distance to liquidation price and adjust leverage accordingly. The bot follows trends based on consecutive higher/lower prices.")

if __name__ == "__main__":
    main()
