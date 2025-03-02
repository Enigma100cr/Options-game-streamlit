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
import hashlib
import re

# Database configuration
DATABASE_URI = 'sqlite:///trading_data.db'
conn = sqlite3.connect("trading_data.db", check_same_thread=False)
c = conn.cursor()

# Create tables
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
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

# Authentication functions
def create_user(email, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    try:
        c.execute("INSERT INTO users (email, password) VALUES (?, ?)", 
                 (email, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def verify_user(email, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT * FROM users WHERE email = ? AND password = ?",
             (email, hashed_password))
    return c.fetchone()

# Session state initialization
if 'user' not in st.session_state:
    st.session_state.user = None
if 'register' not in st.session_state:
    st.session_state.register = False

# Authentication flow
def show_auth():
    st.title("🔒 Trading Journal Authentication")
    
    if st.session_state.register:
        with st.form("Register"):
            st.subheader("Create New Account")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            reg_submitted = st.form_submit_button("Register")
            
            if reg_submitted:
                if not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
                    st.error("Please enter a valid email address")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    if create_user(new_email, new_password):
                        st.success("Account created! Please login")
                        st.session_state.register = False
                    else:
                        st.error("Email already exists")
        st.button("Already have an account? Login", on_click=lambda: st.session_state.update({"register": False}))
    else:
        with st.form("Login"):
            st.subheader("Login to Your Account")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                user = verify_user(email, password)
                if user:
                    st.session_state.user = {
                        "id": user[0],
                        "email": user[1]
                    }
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        st.button("Create new account", on_click=lambda: st.session_state.update({"register": True}))

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
if st.session_state.user is None:
    show_auth()
else:
    st.set_page_config(page_title="Professional Trading Journal", layout="wide")
    st.title(f"📈 {st.session_state.user['email']}'s Trading Journal")
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
                AND user_id = ?
            """
            trades_df = pd.read_sql(query, conn, params=(
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                f"%{selected_symbol}%",
                st.session_state.user['id']
            ))
            
            if not trades_df.empty:
                if st.button("📥 Download Excel"):
                    excel_file = save_to_excel(trades_df)
                    with open(excel_file, "rb") as f:
                        st.download_button(
                            label="⬇️ Download Excel File",
                            data=f,
                            file_name="trade_journal.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                
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
        trades_df = pd.read_sql("SELECT * FROM trades WHERE user_id = ?", 
                              conn, params=(st.session_state.user['id'],))
        
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
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    st.session_state.user['id'],
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
            
            if st.form_submit_button("Save Changes"):
                c.execute("""
                    UPDATE trades SET
                    entry_price = ?,
                    exit_price = ?,
                    stop_loss = ?,
                    target = ?,
                    status = ?,
                    notes = ?,
                    brokerage = ?
                    WHERE id = ?
                """, (
                    new_entry,
                    new_exit,
                    new_stop,
                    new_target,
                    new_status,
                    new_notes,
                    new_brokerage,
                    trade['id']
                ))
                conn.commit()
                del st.session_state.edit_trade
                st.rerun()

    # Footer
    st.markdown("---")
    st.markdown("© 2025 Trading Journal Pro | All rights reserved")
    if st.button("Logout"):
        st.session_state.user = None
        st.rerun()

# Close connection
conn.close()
