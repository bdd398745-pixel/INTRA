import pandas as pd
import numpy as np

# ===== ATR Function =====
def ATR(df, n=14):
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift(1))
    low_close = abs(df['Low'] - df['Close'].shift(1))
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(n, min_periods=1).mean()
    return atr

# ===== Supertrend Function =====
def supertrend(df, period=10, multiplier=3):
    df = df.copy()
    atr = ATR(df, period)

    hl2 = (df['High'] + df['Low']) / 2

    upperband = hl2 + multiplier * atr
    lowerband = hl2 - multiplier * atr

    supertrend_values = []  # store supertrend values
    directions = []         # store trend direction

    for i in range(len(df)):
        if i == 0:
            supertrend_values.append(upperband.iloc[i])
            directions.append(1)  # initial trend
        else:
            # Adjust upper/lower bands
            if directions[i-1] == 1:
                upperband_i = min(upperband.iloc[i], upperband.iloc[i-1])
            else:
                upperband_i = upperband.iloc[i]

            if directions[i-1] == -1:
                lowerband_i = max(lowerband.iloc[i], lowerband.iloc[i-1])
            else:
                lowerband_i = lowerband.iloc[i]

            # Determine trend direction
            if df['Close'].iloc[i] > upperband_i:
                direction = 1
            elif df['Close'].iloc[i] < lowerband_i:
                direction = -1
            else:
                direction = directions[i-1]

            # Supertrend value based on trend
            supertrend_val = lowerband_i if direction == 1 else upperband_i

            # Append to lists
            supertrend_values.append(supertrend_val)
            directions.append(direction)

    # Convert lists to Series
    supertrend_series = pd.Series(supertrend_values, index=df.index)
    direction_series = pd.Series(directions, index=df.index)

    return supertrend_series, direction_series




def RSI(df, period=14):
    """Calculate Relative Strength Index."""
    df = df.copy()
    delta = df['Close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return pd.Series(rsi, index=df.index)


def MACD(df, fast=12, slow=26, signal=9):
    """Calculate MACD line and signal line."""
    df = df.copy()
    exp1 = df['Close'].ewm(span=fast, adjust=False).mean()
    exp2 = df['Close'].ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return pd.Series(macd, index=df.index), pd.Series(signal_line, index=df.index)


# ========== Main Function ========== #

def generate_signals(df, params):
    """Combine indicators to generate Buy/Sell/Exit signals."""
    df = df.copy().dropna().reset_index()

    # Calculate indicators
    df['ATR'] = ATR(df, n=params.get('atr_period', 14))
    df['Supertrend'], df['ST_dir'] = supertrend(df, period=params.get('st_period', 10), multiplier=params.get('st_mult', 3))
    df['RSI'] = RSI(df, period=params.get('rsi_period', 14))
    df['MACD'], df['MACD_signal'] = MACD(df)

    # Generate Buy/Sell signals
    df['Signal'] = None
    for i in range(1, len(df)):
        if (
            df['ST_dir'].iloc[i] == 1
            and df['RSI'].iloc[i] < 70
            and df['MACD'].iloc[i] > df['MACD_signal'].iloc[i]
            and df['Close'].iloc[i] > df['Supertrend'].iloc[i]
        ):
            df.loc[i, 'Signal'] = 'BUY'
        elif (
            df['ST_dir'].iloc[i] == -1
            and df['RSI'].iloc[i] > 30
            and df['MACD'].iloc[i] < df['MACD_signal'].iloc[i]
            and df['Close'].iloc[i] < df['Supertrend'].iloc[i]
        ):
            df.loc[i, 'Signal'] = 'SELL'

    # Calculate Stop Loss and Target (ATR-based)
    df['StopLoss'] = np.where(
        df['Signal'] == 'BUY', df['Close'] - df['ATR'] * 1.5,
        np.where(df['Signal'] == 'SELL', df['Close'] + df['ATR'] * 1.5, np.nan)
    )
    df['Target'] = np.where(
        df['Signal'] == 'BUY', df['Close'] + df['ATR'] * 2,
        np.where(df['Signal'] == 'SELL', df['Close'] - df['ATR'] * 2, np.nan)
    )

    # Create signal summary table
    signals_df = df.loc[df['Signal'].notnull(), ['Datetime', 'Signal', 'Close', 'StopLoss', 'Target']].reset_index(drop=True)
    signals_df.rename(columns={'Close': 'EntryPrice'}, inplace=True)

    return df, signals_df
