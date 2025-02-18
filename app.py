import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from PIL import Image
import io
from datetime import datetime

# Database configuration
DATABASE_URI = 'sqlite:///trading_data.db'  # SQLite database file
engine = create_engine(DATABASE_URI)

# Create a table for storing trade data if it doesn't exist
with engine.connect() as conn:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_date TEXT,
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
        screenshot BLOB
    )
    """)

# Function to save trade data
def save_trade_data(trade_data):
    with engine.connect() as conn:
        conn.execute("""
        INSERT INTO trades (trade_date, symbol, trade_type, entry_price, exit_price, stop_loss, target, position_size,
                            brokerage, stt, transaction_charges, gst, stamp_duty, total_charges, net_pnl,
                            setup_type, market_condition, psychology, notes, screenshot)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, trade_data)

# Streamlit app layout
st.title("🚀 Trading Journal")

# Input fields for trade data
trade_date = st.date_input("Trade Date", datetime.today())
symbol = st.text_input("Symbol")
trade_type = st.selectbox("Trade Type", ["Call Option", "Put Option", "Swing Trade"])
entry_price = st.number_input("Entry Price (₹)", min_value=0.0, format="%.2f")
exit_price = st.number_input("Exit Price (₹)", min_value=0.0, format="%.2f")
stop_loss = st.number_input("Stop Loss (₹)", min_value=0.0, format="%.2f")
target = st.number_input("Target Price (₹)", min_value=0.0, format="%.2f")
position_size = st.number_input("Position Size", min_value=1)
brokerage = st.number_input("Brokerage (₹)", min_value=0.0, format="%.2f")
stt = st.number_input("STT (₹)", min_value=0.0, format="%.2f")
transaction_charges = st.number_input("Transaction Charges (₹)", min_value=0.0, format="%.2f")
gst = st.number_input("GST (₹)", min_value=0.0, format="%.2f")
stamp_duty = st.number_input("Stamp Duty (₹)", min_value=0.0, format="%.2f")
total_charges = brokerage + stt + transaction_charges + gst + stamp_duty
net_pnl = (exit_price - entry_price) * position_size - total_charges
setup_type = st.text_input("Setup Type")
market_condition = st.selectbox("Market Condition", ["Bullish", "Bearish", "Sideways", "Volatile"])
psychology = st.text_input("Psychology")
notes = st.text_area("Notes")

# Upload screenshot
screenshot = st.file_uploader("Upload Screenshot", type=["png", "jpg", "jpeg"])

if st.button("Save Trade"):
    if screenshot is not None:
        # Convert image to bytes
        image = Image.open(screenshot)
        image_bytes = io.BytesIO()
        image.save(image_bytes, format=image.format)
        image_bytes = image_bytes.getvalue()
        
        # Prepare trade data for saving
        trade_data = (
            str(trade_date), symbol, trade_type, entry_price, exit_price, stop_loss, target, position_size,
            brokerage, stt, transaction_charges, gst, stamp_duty, total_charges, net_pnl,
            setup_type, market_condition, psychology, notes, image_bytes
        )
        
        # Save trade data
        save_trade_data(trade_data)
        st.success("Trade data saved successfully!")
    else:
        st.error("Please upload a screenshot.")

# Display saved trades
st.subheader("Saved Trades")
with engine.connect() as conn:
    trades = pd.read_sql("SELECT * FROM trades", conn)
    st.dataframe(trades)

# Option to download trades as CSV
if st.button("Download Trades as CSV"):
    trades_df = pd.read_sql("SELECT * FROM trades", engine)
    trades_df.to_csv("trades.csv", index=False)
    st.success("Trades downloaded as trades.csv")
