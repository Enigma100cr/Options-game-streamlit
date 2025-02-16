# app.py
import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# Set page config
st.set_page_config(page_title="Options Trading Journal", layout="wide")

# Initialize session state variables
if 'trades' not in st.session_state:
    st.session_state.trades = pd.DataFrame(columns=[
        'date', 'symbol', 'trade_type', 'entry_price', 'exit_price', 
        'stop_loss', 'target', 'position_size', 'pnl', 'setup_type',
        'market_condition', 'psychology', 'notes'
    ])

def calculate_position_size(capital, risk_percent, entry, stop_loss):
    risk_amount = capital * (risk_percent / 100)
    position_size = risk_amount / abs(entry - stop_loss)
    return round(position_size)

# Header
st.title("🚀 Advanced Options Trading Journal")
st.markdown("Track your trades, analyze performance, and improve your psychology")

# Sidebar for analytics
with st.sidebar:
    st.header("📊 Trading Statistics")
    if not st.session_state.trades.empty:
        total_trades = len(st.session_state.trades)
        winning_trades = len(st.session_state.trades[st.session_state.trades['pnl'] > 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        st.metric("Total Trades", total_trades)
        st.metric("Win Rate", f"{win_rate:.2f}%")
        st.metric("Profit Factor", "1.5")  # Calculate this based on actual trades
        
        # Show equity curve
        if len(st.session_state.trades) > 0:
            fig = px.line(st.session_state.trades, x='date', y='pnl', title='Equity Curve')
            st.plotly_chart(fig)

# Main content
tabs = st.tabs(["Trade Entry", "Trade Journal", "Analytics"])

with tabs[0]:
    st.header("📝 Trade Entry Form")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Market Analysis
        st.subheader("Market Analysis")
        market_condition = st.selectbox(
            "Market Condition",
            ["Bullish", "Bearish", "Sideways", "Volatile"]
        )
        setup_type = st.selectbox(
            "Setup Type",
            ["Breakout", "Reversal", "Trend Following", "Support/Resistance", "Pattern"]
        )
        
        # Position Sizing
        st.subheader("Position Sizing")
        initial_capital = st.number_input("Initial Capital (₹)", value=100000.0, step=1000.0)
        risk_percent = st.number_input("Risk Per Trade (%)", value=1.0, max_value=5.0, step=0.1)

    with col2:
        # Trade Details
        st.subheader("Trade Details")
        symbol = st.text_input("Stock Symbol", placeholder="e.g., RELIANCE")
        trade_type = st.selectbox("Trade Type", ["Call Option", "Put Option", "Swing Trade"])
        entry_price = st.number_input("Entry Price (₹)", value=0.0, step=0.1)
        target_price = st.number_input("Target Price (₹)", value=0.0, step=0.1)
        stop_loss = st.number_input("Stop Loss (₹)", value=0.0, step=0.1)
        
        # Psychology Check
        st.subheader("Psychology Check")
        emotion = st.selectbox(
            "Current Emotional State",
            ["Confident & Calm", "Fearful", "Excited", "FOMO", "Revenge Trading Urge"]
        )

    # Trade Notes
    st.subheader("Trade Notes")
    setup_notes = st.text_area("Setup Analysis", height=100)
    risk_notes = st.text_area("Risk Management Notes", height=100)

    # Calculate position size
    if entry_price and stop_loss:
        position_size = calculate_position_size(initial_capital, risk_percent, entry_price, stop_loss)
        st.info(f"Recommended Position Size: {position_size} units")
        
        # Calculate R:R ratio
        if target_price:
            reward = abs(target_price - entry_price)
            risk = abs(entry_price - stop_loss)
            rr_ratio = reward / risk if risk != 0 else 0
            st.metric("Risk:Reward Ratio", f"{rr_ratio:.2f}")

    # Submit button
    if st.button("Log Trade"):
        if emotion in ["FOMO", "Revenge Trading Urge"]:
            st.error("⚠️ Trading not recommended in current psychological state!")
        else:
            # Add trade to dataframe
            new_trade = {
                'date': datetime.now(),
                'symbol': symbol,
                'trade_type': trade_type,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'target': target_price,
                'position_size': position_size,
                'setup_type': setup_type,
                'market_condition': market_condition,
                'psychology': emotion,
                'notes': setup_notes
            }
            st.session_state.trades = pd.concat([st.session_state.trades, pd.DataFrame([new_trade])], ignore_index=True)
            st.success("Trade logged successfully!")

with tabs[1]:
    st.header("📖 Trade Journal")
    if not st.session_state.trades.empty:
        st.dataframe(st.session_state.trades)
    else:
        st.info("No trades recorded yet. Start by logging your first trade!")

with tabs[2]:
    st.header("📊 Analytics Dashboard")
    if not st.session_state.trades.empty:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Best Trade", f"₹{st.session_state.trades['pnl'].max():.2f}")
        with col2:
            st.metric("Worst Trade", f"₹{st.session_state.trades['pnl'].min():.2f}")
        with col3:
            st.metric("Average Trade", f"₹{st.session_state.trades['pnl'].mean():.2f}")
            
        # Add more analytics visualizations
        setup_performance = st.session_state.trades.groupby('setup_type')['pnl'].mean()
        fig = px.bar(setup_performance, title='Setup Performance')
        st.plotly_chart(fig)
    else:
        st.info("Start logging trades to see analytics!")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ for traders who take journaling seriously")
