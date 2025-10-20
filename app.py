import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import io
from utils.signal_logic import generate_signals

st.set_page_config(layout="wide", page_title="Intraday Signal Finder")

st.title("📈 Intraday Buy/Sell Signal App")

ticker = st.text_input("Enter Stock Symbol (e.g. RELIANCE.NS)", value="RELIANCE.NS")
interval = st.selectbox("Interval", ["1m", "5m", "15m", "30m", "60m"])
fetch_btn = st.button("Fetch & Analyze")

params = {
    "ema_short": 9,
    "ema_long": 21,
    "rsi_period": 14,
    "bb_window": 20,
    "atr_period": 14,
    "st_period": 10,
    "st_mult": 3.0,
    "vol_spike_threshold": 1.5,
    "score_threshold": 5,
    "sl_atr_mult": 1.5,
    "rr1": 1.0,
    "rr2": 2.0,
}

if fetch_btn:
    st.info("Fetching 1-day intraday data...")
    df = yf.download(ticker, period="1d", interval=interval, progress=False)
    if df.empty:
        st.error("No intraday data found. Try another stock or interval.")
    else:
        analyzed_df, signals_df = generate_signals(df, params)

        # Plot
        fig = go.Figure(data=[go.Candlestick(
            x=analyzed_df.index,
            open=analyzed_df["Open"],
            high=analyzed_df["High"],
            low=analyzed_df["Low"],
            close=analyzed_df["Close"],
            name="Price"
        )])

        if not signals_df.empty:
            buy = signals_df[signals_df["signal"] == "BUY"]
            sell = signals_df[signals_df["signal"] == "SELL"]
            fig.add_trace(go.Scatter(x=buy.index, y=buy["entry"], mode="markers", marker_symbol="triangle-up", marker_color="green", name="BUY"))
            fig.add_trace(go.Scatter(x=sell.index, y=sell["entry"], mode="markers", marker_symbol="triangle-down", marker_color="red", name="SELL"))

        fig.update_layout(xaxis_rangeslider_visible=False, height=600, title=f"{ticker} ({interval}) Intraday Chart")
        st.plotly_chart(fig, use_container_width=True)

        # Signal Table
        st.subheader("📊 Signal Summary Table")
        if signals_df.empty:
            st.warning("No valid signals detected today.")
        else:
            st.dataframe(signals_df)
            csv_buf = io.StringIO()
            signals_df.to_csv(csv_buf)
            st.download_button("Download Signal Data", data=csv_buf.getvalue(), file_name=f"{ticker}_signals.csv", mime="text/csv")
