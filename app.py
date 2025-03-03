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
import calendar

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

def save_to_excel(trades_df, period):
    wb = Workbook()
    ws = wb.active
    ws.title = "Trade Journal"
    headers = ["Date", "Symbol", "Type", "Entry", "Exit", "Status", "Notes", "Entry Screenshot", "Exit Screenshot"]
    ws.append(headers)
    
    for index, row in trades_df.iterrows():
        entry_screenshot_link = f"=HYPERLINK(\"entry_{index}.png\", \"View Entry Screenshot\")" if row['entry_screenshot'] else ""
        exit_screenshot_link = f"=HYPERLINK(\"exit_{index}.png\", \"View Exit Screenshot\")" if row['exit_screenshot'] else ""
        
        ws.append([
            row['date'], row['symbol'], row['trade_type'],
            row['entry_price'], row['exit_price'], row['status'],
            row['notes'], entry_screenshot_link, exit_screenshot_link
        ])
    
    excel_file = f"trade_journal_{period}.xlsx"
    wb.save(excel_file)
    return excel_file

# Function to generate calendar view
def generate_calendar_view(trades_df, year, month):
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    st.subheader(f"📅 {month_name} {year} - Trade Calendar")
    
    # Create a DataFrame for the calendar
    calendar_df = pd.DataFrame(cal, columns=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    calendar_df = calendar_df.replace(0, "")  # Replace 0s with empty strings
    
    # Add trade data to the calendar
    for index, row in trades_df.iterrows():
        trade_date = datetime.strptime(row['date'], "%Y-%m-%d").date()
        if trade_date.year == year and trade_date.month == month:
            day = trade_date.day
            for i, week in enumerate(cal):
                if day in week:
                    row_idx = i
                    col_idx = week.index(day)
                    pnl = row['net_pnl']
                    color = "green" if pnl > 0 else "red"
                    calendar_df.iloc[row_idx, col_idx] = f"<span style='color: {color};'>{day}</span>"
    
    # Display the calendar
    st.markdown(calendar_df.to_html(escape=False), unsafe_allow_html=True)

# Main app
st.set_page_config(page_title="Professional Trading Journal", layout="wide")
st.title(f"📈 Trading Journal")
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
            st.session_state.user_id
        ))
        
        if not trades_df.empty:
            # Download Options
            st.subheader("📥 Download Options")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Download Day-wise"):
                    excel_file = save_to_excel(trades_df, "daywise")
                    with open(excel_file, "rb") as f:
                        st.download_button(
                            label="⬇️ Download Day-wise",
                            data=f,
                            file_name="trade_journal_daywise.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
            with col2:
                if st.button("Download Month-wise"):
                    excel_file = save_to_excel(trades_df, "monthwise")
                    with open(excel_file, "rb") as f:
                        st.download_button(
                            label="⬇️ Download Month-wise",
                            data=f,
                            file_name="trade_journal_monthwise.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
            with col3:
                if st.button("Download Year-wise"):
                    excel_file = save_to_excel(trades_df, "yearwise")
                    with open(excel_file, "rb") as f:
                        st.download_button(
                            label="⬇️ Download Year-wise",
                            data=f,
                            file_name="trade_journal_yearwise.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
            
            # Calendar View
            st.subheader("📅 Trade Calendar")
            selected_year = st.selectbox("Select Year", [2024, 2025])
            selected_month = st.selectbox("Select Month", list(range(1, 13)), format_func=lambda x: calendar.month_name[x])
            generate_calendar_view(trades_df, selected_year, selected_month)
            
            # Trade History Table
            for _, trade in trades_df.iterrows():
                with st.expander(f"{trade['symbol']} - {trade['date']} - {trade['status']}"):
                    cols = st.columns([3,1])
                    with cols[0]:
                        st.write(f"**Entry:** ₹{trade['entry_price']} | **Exit:** ₹{trade['exit_price']}")
                        st.write(f"**Net P&L:** ₹{trade['net_pnl']:,.2f}")
                        st.write(f"**Notes:** {trade['notes']}")
                    with cols[1]:
                        if trade['entry_screenshot']:
                            st.image(base64.b64decode(trade['entry_screenshot']), use_column_width=True)
                        if trade['exit_screenshot']:
                            st.image(base64.b64decode(trade['exit_screenshot']), use_column_width=True)
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
    st.subheader("📊 Performance Analytics")
    trades_df = pd.read_sql("SELECT * FROM trades WHERE user_id = ?", 
                          conn, params=(st.session_state.user_id,))
    
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
        
        # Equity Curve
        st.plotly_chart(px.line(trades_df, x='date', y='net_pnl', title='Equity Curve'))
        
        # Win Rate vs. Loss Rate
        win_loss_df = trades_df.groupby(trades_df['net_pnl'] > 0).size().reset_index(name='count')
        win_loss_df['result'] = win_loss_df['net_pnl'].apply(lambda x: 'Win' if x else 'Loss')
        st.plotly_chart(px.pie(win_loss_df, names='result', values='count', title='Win Rate vs. Loss Rate'))
        
        # P&L Distribution
        st.plotly_chart(px.histogram(trades_df, x='net_pnl', title='P&L Distribution'))
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
            # Correct P&L calculation based on trade type
            if trade_type == "Long":
                pnl = (exit_price - entry_price) * 1  # Position size removed from calculation
            else:  # Short
                pnl = (entry_price - exit_price) * 1  # Position size removed from calculation
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
                1,  # Position size set to 1 (not used in calculations)
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

# Close connection
conn.close()
