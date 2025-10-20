
import pandas as pd

def supertrend(df, period=7, multiplier=3):
    hl2 = (df['High'] + df['Low']) / 2
    df['ATR'] = df['High'] - df['Low']
    df['UpperBand'] = hl2 + (multiplier * df['ATR'])
    df['LowerBand'] = hl2 - (multiplier * df['ATR'])
    df['Supertrend'] = 0
    trend = True  # uptrend

    for i in range(1, len(df)):
        if df['Close'][i] > df['UpperBand'][i-1]:
            trend = True
        elif df['Close'][i] < df['LowerBand'][i-1]:
            trend = False

        df.at[i, 'Supertrend'] = df['LowerBand'][i] if trend else df['UpperBand'][i]
    return df

def generate_signals(df):
    df = supertrend(df)

    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()

    df['Signal'] = ''
    for i in range(1, len(df)):
        if df['EMA20'][i] > df['EMA50'][i] and df['EMA20'][i-1] <= df['EMA50'][i-1]:
            df.at[i, 'Signal'] = 'BUY'
        elif df['EMA20'][i] < df['EMA50'][i] and df['EMA20'][i-1] >= df['EMA50'][i-1]:
            df.at[i, 'Signal'] = 'SELL'

    # Stop loss and target logic
    df['StopLoss'] = df['Close'] * 0.99
    df['Target'] = df['Close'] * 1.02

    return df
