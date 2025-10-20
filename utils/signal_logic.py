import pandas as pd
import numpy as np

# ================= Supertrend =================
def supertrend(df, period=10, multiplier=3):
    hl2 = (df['High'] + df['Low']) / 2
    tr = np.maximum(df['High'] - df['Low'], 
                    np.maximum(abs(df['High'] - df['Close'].shift()), 
                               abs(df['Low'] - df['Close'].shift())))
    atr = tr.ewm(span=period, adjust=False).mean()

    upperband = hl2 + multiplier * atr
    lowerband = hl2 - multiplier * atr

    final_upperband = upperband.copy()
    final_lowerband = lowerband.copy()

    for i in range(1, len(df)):
        if df['Close'].iloc[i-1] > final_upperband.iloc[i-1]:
            final_upperband.iloc[i] = upperband.iloc[i]
        else:
            final_upperband.iloc[i] = min(upperband.iloc[i], final_upperband.iloc[i-1])

        if df['Close'].iloc[i-1] < final_lowerband.iloc[i-1]:
            final_lowerband.iloc[i] = lowerband.iloc[i]
        else:
            final_lowerband.iloc[i] = max(lowerband.iloc[i], final_lowerband.iloc[i-1])

    supertrend = pd.Series(index=df.index)
    direction = pd.Series(index=df.index)

    for i in range(len(df)):
        if df['Close'].iloc[i] > final_upperband.iloc[i]:
            supertrend.iloc[i] = final_lowerband.iloc[i]
            direction.iloc[i] = 1
        elif df['Close'].iloc[i] < final_lowerband.iloc[i]:
            supertrend.iloc[i] = final_upperband.iloc[i]
            direction.iloc[i] = -1
        else:
            supertrend.iloc[i] = supertrend.iloc[i-1] if i > 0 else final_upperband.iloc[i]
            direction.iloc[i] = direction.iloc[i-1] if i > 0 else 1

    return supertrend, direction


# ================= RSI =================
def RSI(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    RS = gain / (loss + 1e-10)
    return 100 - (100 / (1 + RS))


# ================= EMA =================
def EMA(series, period):
    return series.ewm(span=period, adjust=False).mean()


# ================= Signal Generation =================
def generate_signals(df, params):
    df['EMA9'] = EMA(df['Close'], 9)
    df['EMA21'] = EMA(df['Close'], 21)
    df['RSI'] = RSI(df['Close'], 14)
    df['Supertrend'], df['ST_dir'] = supertrend(df, period=params['st_period'], multiplier=params['st_multiplier'])
    df['vol_avg'] = df['Volume'].rolling(20).mean()
    df['vol_spike'] = df['Volume'] / (df['vol_avg'] + 1e-9)

    # BUY/SELL conditions
    df['Buy_Signal'] = (
        (df['EMA9'] > df['EMA21']) &
        (df['RSI'] < 60) &
        (df['Close'] > df['Supertrend']) &
        (df['vol_spike'] > 1.2)
    )

    df['Sell_Signal'] = (
        (df['EMA9'] < df['EMA21']) &
        (df['RSI'] > 40) &
        (df['Close'] < df['Supertrend']) &
        (df['vol_spike'] > 1.2)
    )

    # Signal summary table
    signals_df = df[(df['Buy_Signal']) | (df['Sell_Signal'])].copy()
    signals_df['Type'] = np.where(signals_df['Buy_Signal'], 'BUY', 'SELL')
    signals_df['Entry'] = signals_df['Close']
    signals_df['Stop_Loss'] = np.where(signals_df['Type']=='BUY',
                                       signals_df['Close']*0.99,
                                       signals_df['Close']*1.01)
    signals_df['Target'] = np.where(signals_df['Type']=='BUY',
                                    signals_df['Close']*1.02,
                                    signals_df['Close']*0.98)
    signals_df = signals_df[['Type', 'Entry', 'Stop_Loss', 'Target', 'RSI']]

    return df, signals_df
