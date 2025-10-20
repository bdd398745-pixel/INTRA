import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from utils.signal_logic import generate_signals

st.set_page_config(page_title="Intraday Signal App", layout="wide")

st.title("📈 Intraday Stock Signal Dashboard")

# Sidebar parameters
st.sidebar.header("⚙️ Settings")

ticker = st.sidebar.text_input("Enter Stock Symbol (e.g. RELIANCE.NS)", "RELIANCE.NS")
interval = st.sidebar.selectbox("Select Interval", ["1m", "5m", "15m", "1h"])
st.sidebar.markdown("---")

params = {
    'atr_period': st.sidebar.slider("ATR Period", 5, 20, 10),
    'atr_multiplier': st.sidebar.slider("ATR Multiplier", 1.0, 5.0, 3.0),
    'st_period': st.sidebar.slider("Supertrend Period", 5, 20, 10),
    'st_multiplier': st.sidebar.slider("Supertrend Multiplier", 1.0, 5.0, 3.0)
}

st.sidebar.markdown("---")

if st.sidebar.button("📊 Generate Signals"):
    with st.spinner("Fetching data..."):
        df = yf.download(ticker, period="1d", interval=interval, progress=False)

    if df.empty:
        st.error("No intraday data found. Try another stock or interval.")
    else:
        analyzed_df, signals_df = generate_signals(df, params)

        # Plot Candlestick
        fig = go.Figure(data=[go.Candlestick(
            x=analyzed_df.index,
            open=analyzed_df['Open'],
            high=analyzed_df['High'],
            low=analyzed_df['Low'],
            close=analyzed_df['Close'],
            name='Candlestick'
        )])

        # Add Buy/Sell markers
        buys = analyzed_df[analyzed_df['Signal'] == 'BUY']
        sells = analyzed_df[analyzed_df['Signal'] == 'SELL']

        fig.add_trace(go.Scatter(x=buys.index, y=buys['Close'], mode='markers',
                                 marker=dict(symbol='triangle-up', color='green', size=10),
                                 name='BUY'))
        fig.add_trace(go.Scatter(x=sells.index, y=sells['Close'], mode='markers',
                                 marker=dict(symbol='triangle-down', color='red', size=10),
                                 name='SELL'))

        fig.update_layout(title=f"{ticker} - {interval} Chart",
                          xaxis_title="Time", yaxis_title="Price",
                          xaxis_rangeslider_visible=False, template="plotly_dark")

        st.plotly_chart(fig, use_container_width=True)
        st.subheader("📋 Latest Signals")
        st.dataframe(signals_df.tail(10))
