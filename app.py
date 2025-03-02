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
    status TEXT,
    setup_type TEXT,
    market_condition TEXT,
    psychology TEXT,
    notes TEXT,
    entry_screenshot BLOB,
    exit_screenshot BLOB,
    brokerage REAL,
    stt REAL,
    transaction_charges REAL,
    gst REAL,
    stamp_duty REAL,
    total_charges REAL,
    net_pnl REAL
)
""")
conn.commit()

# Page config
st.set_page_config(page_title="Professional Trading Journal", layout="wide")

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
            ws.add_image(ExcelImage(img), f'H{index+2}')
            
        if row['exit_screenshot']:
            img = Image.open(io.BytesIO(base64.b64decode(row['exit_screenshot'])))
            img.thumbnail((200, 200))
            ws.add_image(ExcelImage(img), f'I{index+2}')
    
    excel_file = "trade_journal.xlsx"
    wb.save(excel_file)
    return excel_file

# Main app
st.title("📈 Professional Trading Journal & Analytics")
st.markdown("---")

# Tabs setup
tabs = st.tabs(["📝 Trade Journal", "🧮 Position Calculator", "📊 Analytics", "⚙️ Settings"])

with tabs[0]:  # Trade Journal
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("🔍 Filter Trades")
        start_date = st.date_input("Start Date", datetime.today())
        end_date = st.date_input("End Date", datetime.today())
        selected_symbol = st.text_input("Filter by Symbol")
    
    with col2:
        st.subheader("📜 Trade History")
        query = """
            SELECT * FROM trades 
            WHERE date BETWEEN ? AND ?
            AND symbol LIKE ?
        """
        trades_df = pd.read_sql(query, conn, params=(
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            f"%{selected_symbol}%"
        ))
        
        if not trades_df.empty:
            for _, trade in trades_df.iterrows():
                with st.expander(f"{trade['symbol']} - {trade['date']} - {trade['status']}"):
                    cols = st.columns([3,1])
                    with cols[0]:
                        st.write(f"**Entry:** ₹{trade['entry_price']} | **Exit:** ₹{trade['exit_price']}")
                        st.write(f"**Size:** {trade['position_size']} | **Risk:** {trade['stop_loss']}")
                        st.write(f"**Net P&L:** ₹{trade['net_pnl']:,.2f}")
                        st.write(f"**Notes:** {trade['notes']}")
                    with cols[1]:
                        if trade['entry_screenshot']:
                            st.image(base64.b64decode(trade['entry_screenshot']), use_column_width=True)
                        if st.button("✏️ Edit", key=f"edit_{trade['id']}"):
                            st.session_state.edit_trade = trade
                        if st.button("🗑️ Delete", key=f"delete_{trade['id']}"):
                            c.execute("DELETE FROM trades WHERE id=?", (trade['id'],))
                            conn.commit()
                            st.rerun()
        else:
            st.info("No trades found for selected filters")

with tabs[1]:  # Position Calculator
    st.subheader("📐 Position Size Calculator")
    
    calc_col1, calc_col2 = st.columns(2)
    with calc_col1:
        st.markdown("### Long Position")
        long_entry = st.number_input("Entry Price", value=100.0, key="long_entry")
        long_stop = st.number_input("Stop Loss", value=80.0, key="long_stop")
        long_target = st.number_input("Target Price", value=150.0, key="long_target")
        long_risk = st.number_input("Risk (%)", value=2.0, key="long_risk")
        long_capital = st.number_input("Capital", value=100000.0, key="long_capital")
        
        if st.button("Calculate Long"):
            position_size = calculate_position_size(long_capital, long_risk, long_entry, long_stop, "Long")
            risk_amount = long_capital * (long_risk / 100)
            reward_risk = (long_target - long_entry) / (long_entry - long_stop)
            
            st.markdown("### Results")
            st.write(f"**Position Size:** {position_size}")
            st.write(f"**Risk Amount:** ₹{risk_amount:,.2f}")
            st.write(f"**Reward/Risk Ratio:** {reward_risk:.2f}:1")
    
    with calc_col2:
        st.markdown("### Short Position")
        short_entry = st.number_input("Entry Price", value=200.0, key="short_entry")
        short_stop = st.number_input("Stop Loss", value=220.0, key="short_stop")
        short_target = st.number_input("Target Price", value=140.0, key="short_target")
        short_risk = st.number_input("Risk (%)", value=2.0, key="short_risk")
        short_capital = st.number_input("Capital", value=50000.0, key="short_capital")
        
        if st.button("Calculate Short"):
            position_size = calculate_position_size(short_capital, short_risk, short_entry, short_stop, "Short")
            risk_amount = short_capital * (short_risk / 100)
            reward_risk = (short_entry - short_target) / (short_stop - short_entry)
            
            st.markdown("### Results")
            st.write(f"**Position Size:** {position_size}")
            st.write(f"**Risk Amount:** ₹{risk_amount:,.2f}")
            st.write(f"**Reward/Risk Ratio:** {reward_risk:.2f}:1")

with tabs[2]:  # Analytics
    st.subheader("📈 Performance Analytics")
    trades_df = pd.read_sql("SELECT * FROM trades", conn)
    
    # Debugging: Print columns to verify
    print(trades_df.columns)
    
    # Fallback for missing 'net_pnl'
    trades_df['net_pnl'] = trades_df.get('net_pnl', 0)
    
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
        st.plotly_chart(px.pie(trades_df, names='status', title='Trade Status Distribution'))
    else:
        st.info("No data available for analytics")

with tabs[3]:  # Settings/New Trade
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
            capital = st.number_input("Capital", value=100000.0)
            risk_percent = st.number_input("Risk (%)", value=1.0)
            status = st.selectbox("Status", ["Open", "Closed"])
            setup_type = st.selectbox("Setup Type", ["Breakout", "Reversal", "Trend"])
            market_condition = st.selectbox("Market Condition", ["Bullish", "Bearish", "Sideways"])
            psychology = st.selectbox("Psychology", ["Confident", "Fearful", "Revenge"])
            entry_screenshot = st.file_uploader("Entry Screenshot", type=["png", "jpg", "jpeg"])
            exit_screenshot = st.file_uploader("Exit Screenshot", type=["png", "jpg", "jpeg"])
        
        # Manual charges input
        st.subheader("💰 Trade Charges")
        brokerage = st.number_input("Brokerage", value=0.0)
        stt = st.number_input("STT", value=0.0)
        transaction_charges = st.number_input("Transaction Charges", value=0.0)
        gst = st.number_input("GST", value=0.0)
        stamp_duty = st.number_input("Stamp Duty", value=0.0)
        total_charges = brokerage + stt + transaction_charges + gst + stamp_duty
        st.write(f"**Total Charges:** ₹{total_charges:,.2f}")
        
        notes = st.text_area("Trade Notes")
        
        if st.form_submit_button("Save Trade"):
            position_size = calculate_position_size(capital, risk_percent, entry_price, stop_loss, trade_type)
            pnl = (exit_price - entry_price) * position_size if status == "Closed" else 0
            net_pnl = pnl - total_charges
            
            c.execute("""
                INSERT INTO trades (
                    date, symbol, trade_type, entry_price, exit_price,
                    stop_loss, target, position_size, status, setup_type,
                    market_condition, psychology, notes, entry_screenshot,
                    exit_screenshot, brokerage, stt, transaction_charges,
                    gst, stamp_duty, total_charges, net_pnl
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
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
                stt,
                transaction_charges,
                gst,
                stamp_duty,
                total_charges,
                net_pnl
            ))
            conn.commit()
            st.success("Trade saved successfully!")

# Edit Trade Modal
if 'edit_trade' in st.session_state:
    trade = st.session_state.edit_trade
    with st.form("edit_trade_form"):
        st.subheader("Edit Trade")
        
        col1, col2 = st.columns(2)
        with col1:
            new_entry = st.number_input("Entry Price", value=trade['entry_price'])
            new_exit = st.number_input("Exit Price", value=trade['exit_price'])
            new_stop = st.number_input("Stop Loss", value=trade['stop_loss'])
            new_target = st.number_input("Target", value=trade['target'])
        
        with col2:
            new_status = st.selectbox("Status", ["Open", "Closed"], index=0 if trade['status'] == "Open" else 1)
            new_notes = st.text_area("Notes", value=trade['notes'])
            new_brokerage = st.number_input("Brokerage", value=trade['brokerage'])
            new_stt = st.number_input("STT", value=trade['stt'])
        
        if st.form_submit_button("Save Changes"):
            c.execute("""
                UPDATE trades SET
                entry_price = ?,
                exit_price = ?,
                stop_loss = ?,
                target = ?,
                status = ?,
                notes = ?,
                brokerage = ?,
                stt = ?
                WHERE id = ?
            """, (
                new_entry,
                new_exit,
                new_stop,
                new_target,
                new_status,
                new_notes,
                new_brokerage,
                new_stt,
                trade['id']
            ))
            conn.commit()
            del st.session_state.edit_trade
            st.rerun()

# Footer
st.markdown("---")
st.markdown("© 2024 Trading Journal Pro | All rights reserved")

# Close connection
conn.close()
