import pandas as pd
import numpy as np

# ATR Calculation
def ATR(df, period=14):
    df = df.copy()
    df['H-L'] = df['High'] - df['Low']
    df['H-C'] = abs(df['High'] - df['Close'].shift(1))
    df['L-C'] = abs(df['Low'] - df['Close'].shift(1))
    tr = df[['H-L', 'H-C', 'L-C']].max(axis=1)
    atr = tr.rolling(period, min_periods=1).mean()
    return atr

# Supertrend Calculation
def supertrend(df, period=10, multiplier=3):
    df = df.copy()
    hl2 = (df['High'] + df['Low']) / 2
    atr = ATR(df, period)
    upperband = hl2 + multiplier * atr
    lowerband = hl2 - multiplier * atr

    st_values = []
    directions = []

    for i in range(len(df)):
        if i == 0:
            st_values.append(float(upperband.iloc[i]))
            directions.append(1)
            continue

        prev_st = st_values[-1]
        prev_direction = directions[-1]
        curr_upper = float(upperband.iloc[i])
        curr_lower = float(lowerband.iloc[i])
        close = float(df['Close'].iloc[i])

        if prev_direction == 1:
            curr_upper = min(curr_upper, prev_st)
        else:
            curr_lower = max(curr_lower, prev_st)

        if close > curr_upper:
            direction = 1
        elif close < curr_lower:
            direction = -1
        else:
            direction = prev_direction

        st_value = curr_lower if direction == -1 else curr_upper

        st_values.append(st_value)
        directions.append(direction)

    df['Supertrend'] = st_values
    df['ST_dir'] = directions
    return df['Supertrend'], df['ST_dir']

# RSI Calculation
def RSI(df, period=14):
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period, min_periods=1).mean()
    avg_loss = loss.rolling(period, min_periods=1).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi

# MACD Calculation
def MACD(df, fast=12, slow=26, signal=9):
    exp1 = df['Close'].ewm(span=fast, adjust=False).mean()
    exp2 = df['Close'].ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    macd_signal = macd.ewm(span=signal, adjust=False).mean()
    return macd, macd_signal

# Generate Signals
def generate_signals(df, params):
    df = df.copy()
    df['ATR'] = ATR(df, period=params.get('atr_period',14))
    df['Supertrend'], df['ST_dir'] = supertrend(
        df, period=params.get('st_period',10), multiplier=params.get('st_multiplier',3)
    )
    df['RSI'] = RSI(df, period=params.get('rsi_period',14))
    df['MACD'], df['MACD_signal'] = MACD(df)

    df['Signal'] = ""
    for i in range(len(df)):
        if df['ST_dir'].iloc[i] == 1:
            df.at[i, 'Signal'] = 'BUY'
        elif df['ST_dir'].iloc[i] == -1:
            df.at[i, 'Signal'] = 'SELL'

    # ATR-based StopLoss and Target
    df['StopLoss'] = np.where(
        df['Signal']=='BUY', df['Close'] - 1.5*df['ATR'],
        np.where(df['Signal']=='SELL', df['Close'] + 1.5*df['ATR'], np.nan)
    )
    df['Target'] = np.where(
        df['Signal']=='BUY', df['Close'] + 3*df['ATR'],
        np.where(df['Signal']=='SELL', df['Close'] - 3*df['ATR'], np.nan)
    )

    signals_df = df[['Close','Signal','StopLoss','Target','RSI','MACD','MACD_signal']]
    return df, signals_df
