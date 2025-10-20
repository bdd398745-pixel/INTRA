import pandas as pd
import numpy as np

def EMA(series, span):
    return series.ewm(span=span, adjust=False).mean()

def RSI(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(alpha=1/period, adjust=False).mean()
    ma_down = down.ewm(alpha=1/period, adjust=False).mean()
    rs = ma_up / ma_down
    return 100 - (100 / (1 + rs))

def MACD(series, a=12, b=26, c=9):
    ema1 = series.ewm(span=a, adjust=False).mean()
    ema2 = series.ewm(span=b, adjust=False).mean()
    macd = ema1 - ema2
    sig = macd.ewm(span=c, adjust=False).mean()
    hist = macd - sig
    return macd, sig, hist

def bollinger_bands(series, window=20, nbdev=2):
    sma = series.rolling(window).mean()
    std = series.rolling(window).std()
    upper = sma + nbdev * std
    lower = sma - nbdev * std
    return sma, upper, lower

def ATR(df, n=14):
    high = df['High']
    low = df['Low']
    close = df['Close']
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/n, adjust=False).mean()
    return atr

def vwap(df):
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    return (tp * df['Volume']).cumsum() / df['Volume'].cumsum()
