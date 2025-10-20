import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from utils.signal_logic import generate_signals

st.set_page_config(page_title="Intraday Stock Signals", layout="wide")

st.title("📈 Intraday Buy/Sell Signal App")
st.caption("For educational use only — not financial advice.")

ticker = st.text_input("Enter Stock Symbol (NSE, e.g., TCS.NS)", "TCS.NS")

interval = st.selectbox("Select Interval", ["5m", "15m", "30m", "60m"])
params = {"st_period": 10, "st_multiplier": 3}

if st.button("Get Signals"):
    with st.spinner("Fetching intraday data..."):
        df = yf.download(ticker, period="1d", interval=interval, progress=False)

    if df.empty:
        st.error("No intraday data found. Try another stock or interval.")
    else:
        analyzed_df, signals_df = generate_signals(df, params)

        # ---------- Plot ----------
        fig = go.Figure()

        fig.add_trace(go.Candlestick(
            x=analyzed_df.index,
            open=analyzed_df['Open'],
            high=analyzed_df['High'],
            low=analyzed_df['Low'],
            close=analyzed_df['Close'],
            name='Price'
        ))

        fig.add_trace(go.Scatter(
            x=analyzed_df.index,
            y=analyzed_df['Supertrend'],
            mode='lines',
            line=dict(color='orange', width=1.5),
            name='Supertrend'
        ))

        # BUY/SELL markers
        buys = analyzed_df[analyzed_df['Buy_Signal']]
        sells = analyzed_df[analyzed_df['Sell_Signal']]

        fig.add_trace(go.Scatter(
            x=buys.index, y=buys['Close'],
            mode='markers', name='BUY',
            marker=dict(color='green', size=10, symbol='triangle-up')
        ))

        fig.add_trace(go.Scatter(
            x=sells.index, y=sells['Close'],
            mode='markers', name='SELL',
            marker=dict(color='red', size=10, symbol='triangle-down')
        ))

        fig.update_layout(
            title=f"Intraday Signals for {ticker}",
            xaxis_title="Time",
            yaxis_title="Price (INR)",
            xaxis_rangeslider_visible=False,
            template="plotly_dark",
            height=700
        )

        st.plotly_chart(fig, use_container_width=True)

        # ---------- Signal Table ----------
        st.subheader("📊 Signal Summary")
        st.dataframe(signals_df.style.format({"Entry": "{:.2f}", "Stop_Loss": "{:.2f}", "Target": "{:.2f}", "RSI": "{:.2f}"}))
