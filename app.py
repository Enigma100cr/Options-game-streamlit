with tabs[1]:  # Position Calculator
    st.subheader("📐 Position Size Calculator")
    
    # Long Positions
    st.markdown("### Long Positions")
    col1, col2 = st.columns(2)
    with col1:
        long_entry = st.number_input("Entry Price (₹)", value=100.0, key="long_entry")
        long_stop = st.number_input("Stop Price (₹)", value=80.0, key="long_stop")
        long_target = st.number_input("Target Price (₹)", value=150.0, key="long_target")
    with col2:
        long_risk = st.number_input("Percent Risk (%)", value=2.0, key="long_risk")
        long_capital = st.number_input("Account Size (₹)", value=100000.0, key="long_capital")
    
    if st.button("Calculate Long"):
        position_size = calculate_position_size(long_capital, long_risk, long_entry, long_stop, "Long")
        cost_of_position = position_size * long_entry
        trade_risk = long_capital * (long_risk / 100)
        reward_risk = (long_target - long_entry) / (long_entry - long_stop)
        
        st.markdown("### Outputs")
        st.write(f"**Quantity to Buy:** {position_size}")
        st.write(f"**Cost of Position:** ₹{cost_of_position:,.2f}")
        st.write(f"**Trade Risk:** ₹{trade_risk:,.2f}")
        st.write(f"**Reward/Risk Ratio:** {reward_risk:.2f}")

    st.markdown("---")

    # Short Positions
    st.markdown("### Short Positions")
    col3, col4 = st.columns(2)
    with col3:
        short_entry = st.number_input("Entry Price (₹)", value=200.0, key="short_entry")
        short_stop = st.number_input("Stop Price (₹)", value=220.0, key="short_stop")
        short_target = st.number_input("Target Price (₹)", value=140.0, key="short_target")
    with col4:
        short_risk = st.number_input("Percent Risk (%)", value=2.0, key="short_risk")
        short_capital = st.number_input("Account Size (₹)", value=50000.0, key="short_capital")
    
    if st.button("Calculate Short"):
        position_size = calculate_position_size(short_capital, short_risk, short_entry, short_stop, "Short")
        cost_of_position = position_size * short_entry
        trade_risk = short_capital * (short_risk / 100)
        reward_risk = (short_entry - short_target) / (short_stop - short_entry)
        
        st.markdown("### Outputs")
        st.write(f"**Quantity to Sell:** {position_size}")
        st.write(f"**Cost of Position:** ₹{cost_of_position:,.2f}")
        st.write(f"**Trade Risk:** ₹{trade_risk:,.2f}")
        st.write(f"**Reward/Risk Ratio:** {reward_risk:.2f}")
