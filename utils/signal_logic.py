# signal_logic.py

import pandas as pd
import numpy as np

# ---------------- ATR ---------------- #
def ATR(df, period=14):
    """
    Average True Range (ATR) calculation
    """
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift(1))
    low_close = np.abs(df['Low'] - df['Close'].shift(1))
    
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(period, min_periods=1).mean()
    return atr

# ---------------- Supertrend ---------------- #
def supertrend(df, period=10, multiplier=3):
    """
    Supertrend calculation
    Returns: supertrend values, direction (1=up, -1=down)
    """
    df = df.copy()
    atr = ATR(df, period)
    hl2 = (df['High'] + df['Low']) / 2

    upperband = hl2 + multiplier * atr
    lowerband = hl2 - multiplier * atr

    st_values = []
    directions = []

    for i in range(len(df)):
        if i == 0:
            st_values.append(upperband.iloc[i])
            directions.append(1)  # initial direction up
            continue

        prev_direction = directions[i - 1]
        prev_upper = float(upperband.iloc[i - 1])
        prev_lower = float(lowerband.iloc[i - 1])
        curr_upper = float(upperband.iloc[i])
        curr_lower = float(lowerband.iloc[i])
        close = float(df['Close'].iloc[i])

        # Adjust bands based on previous direction
        if prev_direction == 1:
            upper = min(curr_upper, prev_upper)
            lower = curr_lower
        else:
            lower = max(curr_lower, prev_lower)
            upper = curr_upper

        # Determine current direction
        if close > upper:
            direction = 1
        elif close < lower:
            direction = -1
        else:
            direction = prev_direction

        st_val = lower if direction == 1 else upper

        st_values.append(st_val)
        directions.append(direction)

    return pd.Series(st_values, index=df.index), pd.Series(directions, index=df.index)

# ---------------- RSI ---------------- #
def RSI(df, period=14):
    """
    Relative Strength Index
    """
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period, min_periods=1).mean()
    avg_loss = loss.rolling(period, min_periods=1).mean()

    rs = avg_gain / (avg_loss + 1e-10)  # avoid division by zero
    rsi = 100 - (100 / (1 + rs))
    return rsi

# ---------------- MACD ---------------- #
def MACD(df, fast_period=12, slow_period=26, signal_period=9):
    """
    MACD and Signal line
    """
    ema_fast = df['Close'].ewm(span=fast_period, adjust=False).mean()
    ema_slow = df['Close'].ewm(span=slow_period, adjust=False).mean()

    macd = ema_fast - ema_slow
    signal = macd.ewm(span=signal_period, adjust=False).mean()
    return macd, signal

# ---------------- Generate Signals ---------------- #
def generate_signals(df, params=None):
    """
    Generates all indicators and buy/sell signals
    """
    if params is None:
        params = {}

    df = df.copy()

    # ATR
    df['ATR'] = ATR(df, period=params.get('atr_period', 14))

    # Supertrend
    df['Supertrend'], df['ST_dir'] = supertrend(
        df,
        period=params.get('st_period', 10),
        multiplier=params.get('st_multiplier', 3)
    )

    # RSI
    df['RSI'] = RSI(df, period=params.get('rsi_period', 14))

    # MACD
    df['MACD'], df['MACD_signal'] = MACD(df)

    # Buy/Sell signals
    df['Signal'] = np.where(df['ST_dir'] == 1, 'BUY', 'SELL')

    return df, df[['Close', 'Signal']]
