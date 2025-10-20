
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from utils.signal_logic import generate_signals

st.set_page_config(page_title="Intraday Stock Signal App", layout="wide")

st.title("📈 Intraday Buy/Sell Signal App (India)")

# User input
symbol = st.text_input("Enter Stock Symbol (e.g. RELIANCE.NS):", "RELIANCE.NS")
interval = st.selectbox("Select Interval:", ["1d", "1h", "15m", "5m", "1m"], index=2)

if st.button("Get Signals"):
    df = yf.download(symbol, period="7d", interval=interval)
    if df.empty:
        st.error("No data found. Try again with a valid symbol or smaller interval.")
    else:
        df = generate_signals(df)

        # Plot candlestick + signals
        fig = go.Figure(data=[go.Candlestick(x=df.index,
                                             open=df['Open'],
                                             high=df['High'],
                                             low=df['Low'],
                                             close=df['Close'],
                                             name='Candlestick')])
        
        # Add buy/sell markers
        buys = df[df['Signal'] == 'BUY']
        sells = df[df['Signal'] == 'SELL']
        fig.add_trace(go.Scatter(x=buys.index, y=buys['Close'], mode='markers',
                                 marker=dict(symbol='triangle-up', color='green', size=10),
                                 name='Buy Signal'))
        fig.add_trace(go.Scatter(x=sells.index, y=sells['Close'], mode='markers',
                                 marker=dict(symbol='triangle-down', color='red', size=10),
                                 name='Sell Signal'))

        fig.update_layout(title=f"{symbol} - Intraday Chart with Buy/Sell Signals",
                          xaxis_title="Time",
                          yaxis_title="Price",
                          xaxis_rangeslider_visible=False)

        st.plotly_chart(fig, use_container_width=True)

        # Signal table
        signal_table = df[df['Signal'].isin(['BUY', 'SELL'])][['Signal', 'Close', 'StopLoss', 'Target']]
        st.subheader("📋 Trade Recommendations")
        st.dataframe(signal_table)
