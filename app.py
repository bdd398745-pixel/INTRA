import streamlit as st
import yfinance as yf
import pandas as pd               # ← Add this import
import plotly.graph_objects as go
from utils.signal_logic import generate_signals
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from utils.signal_logic import generate_signals

# Streamlit App
st.title("Intraday Trading Signals")

# Sidebar inputs
ticker = st.sidebar.text_input("Ticker", value="AAPL")
interval = st.sidebar.selectbox("Interval", ["1m", "5m", "15m", "30m", "60m"])
params = {
    "atr_period": st.sidebar.number_input("ATR Period", min_value=1, value=14),
    "st_period": st.sidebar.number_input("Supertrend Period", min_value=1, value=10),
    "st_multiplier": st.sidebar.number_input("Supertrend Multiplier", min_value=1.0, value=3.0),
    "rsi_period": st.sidebar.number_input("RSI Period", min_value=1, value=14)
}

# Download intraday data
df = yf.download(ticker, period="1d", interval=interval, progress=False)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

# Keep only necessary columns and convert to float
df = df[['Open','High','Low','Close','Volume']].astype(float)

if df.empty:
    st.error("No intraday data found. Try another stock or interval.")
else:
    # Generate signals
    analyzed_df, signals_df = generate_signals(df, params)

    # Plot Candlestick
    fig = go.Figure(data=[go.Candlestick(
        x=analyzed_df.index,
        open=analyzed_df['Open'],
        high=analyzed_df['High'],
        low=analyzed_df['Low'],
        close=analyzed_df['Close'],
        name=ticker
    )])

    # Overlay Supertrend
    fig.add_trace(go.Scatter(
        x=analyzed_df.index, y=analyzed_df['Supertrend'], 
        line=dict(color='blue', width=1), name='Supertrend'
    ))

    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(signals_df)
