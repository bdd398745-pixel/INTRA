import pandas as pd
import numpy as np

# ========== Helper Functions ========== #

def ATR(df, n=14):
    """Calculate Average True Range (ATR)."""
    df = df.copy()
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(window=n).mean()
    return df['ATR']


def supertrend(df, period=10, multiplier=3):
    """Calculate Supertrend indicator."""
    df = df.copy()
    hl2 = (df['High'] + df['Low']) / 2
    atr = ATR(df, n=period)

    upperband = hl2 + (multiplier * atr)
    lowerband = hl2 - (multiplier * atr)

    final_upperband = pd.Series(index=df.index)
    final_lowerband = pd.Series(index=df.index)
    direction = pd.Series(index=df.index)

    for i in range(len(df)):
        if i == 0:
            final_upperband.iloc[i] = upperband.iloc[i]
            final_lowerband.iloc[i] = lowerband.iloc[i]
            direction.iloc[i] = 1
        else:
            # Ensure all Series are aligned by index
            final_upperband.iloc[i] = (
                upperband.iloc[i] if (upperband.iloc[i] < final_upperband.iloc[i-1]) or (df['Close'].iloc[i-1] > final_upperband.iloc[i-1])
                else final_upperband.iloc[i-1]
            )

            final_lowerband.iloc[i] = (
                lowerband.iloc[i] if (lowerband.iloc[i] > final_lowerband.iloc[i-1]) or (df['Close'].iloc[i-1] < final_lowerband.iloc[i-1])
                else final_lowerband.iloc[i-1]
            )

            # Set trend direction
            if df['Close'].iloc[i-1] > final_upperband.iloc[i-1]:
                direction.iloc[i] = 1
            elif df['Close'].iloc[i-1] < final_lowerband.iloc[i-1]:
                direction.iloc[i] = -1
            else:
                direction.iloc[i] = direction.iloc[i-1]

    supertrend = np.where(direction == 1, final_lowerband, final_upperband)
    return pd.Series(supertrend, index=df.index), pd.Series(direction, index=df.index)


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
