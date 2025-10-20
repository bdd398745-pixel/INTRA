import pandas as pd
import numpy as np

# === Technical Indicator Functions ===
def ATR(df, n=14):
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    return df['TR'].rolling(n).mean()

def supertrend(df, period=10, multiplier=3):
    atr = ATR(df, period)
    hl2 = (df['High'] + df['Low']) / 2
    upperband = hl2 + (multiplier * atr)
    lowerband = hl2 - (multiplier * atr)

    final_upperband = upperband.copy()
    final_lowerband = lowerband.copy()
    direction = pd.Series(1, index=df.index)

    for i in range(1, len(df)):
        if df['Close'].iloc[i - 1] > final_upperband.iloc[i - 1]:
            direction.iloc[i] = 1
        elif df['Close'].iloc[i - 1] < final_lowerband.iloc[i - 1]:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = direction.iloc[i - 1]

        if direction.iloc[i] == 1:
            final_lowerband.iloc[i] = max(lowerband.iloc[i], final_lowerband.iloc[i - 1])
        else:
            final_upperband.iloc[i] = min(upperband.iloc[i], final_upperband.iloc[i - 1])

    supertrend = np.where(direction == 1, final_lowerband, final_upperband)
    return pd.Series(supertrend, index=df.index), direction

# === Signal Generator ===
def generate_signals(df, params):
    df = df.copy()
    df['ATR'] = ATR(df, n=params['atr_period'])
    df['Supertrend'], df['ST_dir'] = supertrend(df, period=params['st_period'], multiplier=params['st_multiplier'])

    df['Signal'] = np.where(df['ST_dir'] == 1, 'BUY', 'SELL')

    # Extract latest signal rows
    signal_points = df[df['Signal'].shift(1) != df['Signal']].copy()
    signal_points['Entry_Price'] = signal_points['Close']
    signal_points['Stop_Loss'] = np.where(signal_points['Signal'] == 'BUY',
                                          signal_points['Entry_Price'] - signal_points['ATR'] * 1.5,
                                          signal_points['Entry_Price'] + signal_points['ATR'] * 1.5)
    signal_points['Target'] = np.where(signal_points['Signal'] == 'BUY',
                                       signal_points['Entry_Price'] + signal_points['ATR'] * 2,
                                       signal_points['Entry_Price'] - signal_points['ATR'] * 2)

    return df, signal_points[['Signal', 'Entry_Price', 'Stop_Loss', 'Target']]
