import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import sqlite3
import io
from PIL import Image
from openpyxl import Workbook
from openpyxl.drawing.image import Image as ExcelImage

# Database configuration
DATABASE_URI = 'sqlite:///trading_data.db'  # SQLite database file
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
        market_condition = st.selectbox(
            "Market Condition",
            ["Bullish", "Bearish", "Sideways", "Volatile"]
        )
        setup_type = st.selectbox(
            "Setup Type",
            ["Breakout", "Reversal", "Trend Following", "Support/Resistance", "Pattern"]
        )

        # Position Size Calculation
        capital = st.number_input("Capital (₹)", min_value=0.0, step=1000.0)
        risk_percent = st.number_input("Risk Percentage (%)", min_value=0.0, max_value=100.0, value=1.0)
        entry_price = st.number_input("Entry Price (₹)", min_value=0.0, step=0.1)
        stop_loss = st.number_input("Stop Loss (₹)", min_value=0.0, step=0.1)
        
        if st.button("Calculate Position Size"):
            position_size = calculate_position_size(capital, risk_percent, entry_price, stop_loss)
            st.success(f"Calculated Position Size: {position_size} units")

    with col2:
        # Trade Details
        st.subheader("Trade Details")
        symbol = st.text_input("Symbol")
        trade_type = st.selectbox("Trade Type", ["Call Option", "Put Option", "Stock"])
        exit_price = st.number_input("Exit Price (₹)", min_value=0.0, step=0.1)
        
        if st.button("Submit Trade"):
            charges = calculate_charges(position_size, entry_price, exit_price, trade_type)
            net_pnl = calculate_pnl(position_size, entry_price, exit_price) - charges['total_charges']
            
            # Insert trade into database
            c.execute("""
            INSERT INTO trades (date, symbol, trade_type, entry_price, exit_price, stop_loss, target, position_size,
                                brokerage, stt, transaction_charges, gst, stamp_duty, total_charges, net_pnl,
                                setup_type, market_condition, psychology, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), symbol, trade_type, entry_price, exit_price,
                  stop_loss, None, position_size, charges['brokerage'], charges['stt'],
                  charges['transaction_charges'], charges['gst'], charges['stamp_duty'],
                  charges['total_charges'], net_pnl, setup_type, market_condition, None, None, 'Open'))
            conn.commit()
            st.success("Trade submitted successfully!")

with tabs[1]:
    st.header("📜 Trade Journal")
    trades_df = pd.read_sql("SELECT * FROM trades", conn)
    st.dataframe(trades_df)

with tabs[2]:
    st.header("📈 Analytics")
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

# Closing the database connection
conn.close()
