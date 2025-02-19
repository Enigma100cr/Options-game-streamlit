import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import base64
import sqlite3
import io
from PIL import Image

# Database configuration
DATABASE_URI = 'sqlite:///trading_data.db'
conn = sqlite3.connect('trading_data.db')
c = conn.cursor()

# Create a table for storing trade data if it doesn't exist
c.execute("""
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    symbol TEXT,
    trade_type TEXT,
    entry_price REAL,
    exit_price REAL,
    stop_loss REAL,
    target REAL,
    position_size INTEGER,
    brokerage REAL,
    stt REAL,
    transaction_charges REAL,
    gst REAL,
    stamp_duty REAL,
    total_charges REAL,
    net_pnl REAL,
    setup_type TEXT,
    market_condition TEXT,
    psychology TEXT,
    notes TEXT,
    entry_screenshot BLOB,
    exit_screenshot BLOB,
    status TEXT
)
""")
conn.commit()

# Set page config
st.set_page_config(page_title="Options Trading Journal", layout="wide")

def calculate_position_size(capital, risk_percent, entry, stop_loss):
    risk_amount = capital * (risk_percent / 100)
    position_size = risk_amount / abs(entry - stop_loss)
    return round(position_size)

def calculate_pnl(position_size, entry_price, exit_price):
    return position_size * (exit_price - entry_price)

def calculate_charges(position_size, entry_price, exit_price, trade_type):
    turnover = position_size * (entry_price + exit_price)
    brokerage = min(turnover * 0.0003, 40)
   
    if trade_type in ["Call Option", "Put Option"]:
        stt = (position_size * exit_price) * 0.0005
    else:
        stt = turnover * 0.0001

    transaction_charges = turnover * 0.0000325
    gst = (brokerage + transaction_charges) * 0.18
    stamp_duty = (position_size * entry_price) * 0.00003
    total_charges = brokerage + stt + transaction_charges + gst + stamp_duty
   
    return {
        'brokerage': round(brokerage, 2),
        'stt': round(stt, 2),
        'transaction_charges': round(transaction_charges, 2),
        'gst': round(gst, 2),
        'stamp_duty': round(stamp_duty, 2),
        'total_charges': round(total_charges, 2)
    }

def get_image_base64(image_file):
    if image_file is not None:
        bytes_data = image_file.getvalue()
        return base64.b64encode(bytes_data).decode()
    return None

# Header
st.title("🚀 Advanced Options Trading Journal")
st.markdown("Track your trades, analyze performance, and improve your psychology")

# Sidebar for analytics
with st.sidebar:
    st.header("📊 Trading Statistics")
    trades_df = pd.read_sql("SELECT * FROM trades", conn)
    if not trades_df.empty:
        completed_trades = trades_df[trades_df['status'] == 'Closed']
        if not completed_trades.empty:
            total_trades = len(completed_trades)
            winning_trades = len(completed_trades[completed_trades['net_pnl'] > 0])
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            total_profit = completed_trades['net_pnl'].sum()
           
            st.metric("Total Trades", total_trades)
            st.metric("Win Rate", f"{win_rate:.2f}%")
            st.metric("Total P&L", f"₹{total_profit:,.2f}")
           
            # Show equity curve
            cumulative_pnl = completed_trades['net_pnl'].cumsum()
            fig = px.line(cumulative_pnl, title='Equity Curve')
            st.plotly_chart(fig)

# Main content
tabs = st.tabs(["Trade Entry", "Trade Journal", "Analytics"])

with tabs[0]:
    st.header("📝 Trade Entry Form")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Market Analysis
        st.subheader("Market Analysis")
        market_condition = st.selectbox("Market Condition", ["Bullish", "Bearish", "Sideways", "Volatile"])
        setup_type = st.selectbox("Setup Type", ["Breakout", "Reversal", "Trend Following", "Support/Resistance", "Pattern"])
    
    # Submit button
    if st.button("Log Trade"):
        st.success("Trade logged successfully with screenshots!")
