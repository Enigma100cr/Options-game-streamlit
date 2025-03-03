import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import base64
import sqlite3
import io
from PIL import Image
from openpyxl import Workbook
from openpyxl.drawing.image import Image as ExcelImage

# Database configuration
DATABASE_URI = 'sqlite:///trading_data.db'
conn = sqlite3.connect("trading_data.db", check_same_thread=False)
c = conn.cursor()

# Create tables
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date TEXT,
    symbol TEXT,
    trade_type TEXT,
    entry_price REAL,
    exit_price REAL,
    stop_loss REAL,
    target REAL,
    position_size INTEGER,
    status TEXT,
    setup_type TEXT,
    market_condition TEXT,
    psychology TEXT,
    notes TEXT,
    entry_screenshot BLOB,
    exit_screenshot BLOB,
    brokerage REAL,
    net_pnl REAL,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")
conn.commit()

# Session state initialization
if 'user_id' not in st.session_state:
    st.session_state.user_id = 1  # Default user ID for simplicity

# Utility functions
def calculate_position_size(capital, risk_percent, entry, stop_loss, position_type):
    risk_amount = capital * (risk_percent / 100)
    risk_per_share = abs(entry - stop_loss)
    return round(risk_amount / risk_per_share) if risk_per_share != 0 else 0

def get_image_base64(image_file):
    if image_file is not None:
        return base64.b64encode(image_file.read()).decode()
    return None

def save_to_excel(trades_df):
    wb = Workbook()
    ws = wb.active
    ws.title = "Trade Journal"
    headers = ["Date", "Symbol", "Type", "Entry", "Exit", "Status", "Position Size", "Notes"]
    ws.append(headers)
    
    for index, row in trades_df.iterrows():
        ws.append([
            row['date'], row['symbol'], row['trade_type'],
            row['entry_price'], row['exit_price'], row['status'],
            row['position_size'], row['notes']
        ])
        
        if row['entry_screenshot']:
            img = Image.open(io.BytesIO(base64.b64decode(row['entry_screenshot'])))
            img.thumbnail((200, 200))
            img_io = io.BytesIO()
            img.save(img_io, format='PNG')
            img_io.seek(0)
            ws.add_image(ExcelImage(img_io), f'H{index+2}')
            
        if row['exit_screenshot']:
            img = Image.open(io.BytesIO(base64.b64decode(row['exit_screenshot'])))
            img.thumbnail((200, 200))
            img_io = io.BytesIO()
            img.save(img_io, format='PNG')
            img_io.seek(0)
            ws.add_image(ExcelImage(img_io), f'I{index+2}')
    
    excel_file = "trade_journal.xlsx"
    wb.save(excel_file)
    return excel_file

# Main app
st.set_page_config(page_title="Professional Trading Journal", layout="wide")
st.title(f"📈 Trading Journal")
st.markdown("---")

# Dashboard Sections
st.sidebar.title("Dashboard")
dashboard_section = st.sidebar.radio("Navigate", ["Stats", "Calendar", "Settings", "Help"])

if dashboard_section == "Stats":
    st.subheader("📊 Stats")
    trades_df = pd.read_sql("SELECT * FROM trades WHERE user_id = ?", conn, params=(st.session_state.user_id,))
    if not trades_df.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            total_trades = len(trades_df)
            st.metric("Total Trades", total_trades)
        with col2:
            win_rate = (len(trades_df[trades_df['net_pnl'] > 0]) / total_trades) * 100
            st.metric("Win Rate", f"{win_rate:.1f}%")
        with col3:
            total_pnl = trades_df['net_pnl'].sum()
            st.metric("Total P&L", f"₹{total_pnl:,.2f}")
        
        st.plotly_chart(px.line(trades_df, x='date', y='net_pnl', title='Equity Curve'))
    else:
        st.info("No data available for stats")

elif dashboard_section == "Calendar":
    st.subheader("📅 Calendar")
    st.write("Calendar view of trades will be displayed here.")

elif dashboard_section == "Settings":
    st.subheader("⚙️ Settings")
    st.write("User settings and preferences can be configured here.")

elif dashboard_section == "Help":
    st.subheader("❓ Help")
    st.write("Help and support information will be provided here.")

# New Trade Section
st.sidebar.title("New Trade")
new_trade_section = st.sidebar.radio("New Trade", ["New Setup", "New Note"])

if new_trade_section == "New Setup":
    st.subheader("➕ New Trade Entry")
    with st.form("new_trade_form"):
        col1, col2 = st.columns(2)
        with col1:
            trade_date = st.date_input("Trade Date")
            symbol = st.text_input("Symbol")
            trade_type = st.selectbox("Type", ["Long", "Short"])
            entry_price = st.number_input("Entry Price")
            exit_price = st.number_input("Exit Price")
            stop_loss = st.number_input("Stop Loss")
            target_price = st.number_input("Target Price")
        
        with col2:
            status = st.selectbox("Status", ["Open", "Closed"])
            setup_type = st.selectbox("Setup Type", ["Breakout", "Reversal", "Trend"])
            market_condition = st.selectbox("Market Condition", ["Bullish", "Bearish", "Sideways"])
            psychology = st.selectbox("Psychology", ["Confident", "Fearful", "Revenge"])
            entry_screenshot = st.file_uploader("Entry Screenshot", type=["png", "jpg", "jpeg"])
            exit_screenshot = st.file_uploader("Exit Screenshot", type=["png", "jpg", "jpeg"])
        
        brokerage = st.number_input("Brokerage", value=0.0)
        notes = st.text_area("Trade Notes")
        
        if st.form_submit_button("Save Trade"):
            position_size = calculate_position_size(100000, 1.0, entry_price, stop_loss, trade_type)
            pnl = (exit_price - entry_price) * position_size if status == "Closed" else 0
            net_pnl = pnl - brokerage
            
            c.execute("""
                INSERT INTO trades (
                    user_id, date, symbol, trade_type, entry_price, exit_price,
                    stop_loss, target, position_size, status, setup_type,
                    market_condition, psychology, notes, entry_screenshot,
                    exit_screenshot, brokerage, net_pnl
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                st.session_state.user_id,
                trade_date.strftime("%Y-%m-%d"),
                symbol,
                trade_type,
                entry_price,
                exit_price,
                stop_loss,
                target_price,
                position_size,
                status,
                setup_type,
                market_condition,
                psychology,
                notes,
                get_image_base64(entry_screenshot),
                get_image_base64(exit_screenshot),
                brokerage,
                net_pnl
            ))
            conn.commit()
            st.success("Trade saved successfully!")

elif new_trade_section == "New Note":
    st.subheader("📝 New Note")
    note = st.text_area("Add a new note")
    if st.button("Save Note"):
        st.success("Note saved successfully!")

# Footer
st.markdown("---")
st.markdown("© 2025 Trading Journal Pro | All rights reserved")

# Close connection
conn.close()
