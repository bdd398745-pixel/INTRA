# signal_logic.py
import pandas as pd
import numpy as np

# =========================
# ATR Calculation
# =========================
def ATR(df, n=14):
    """
    Calculate Average True Range (ATR)
    Returns a 1D pandas Series
    """
    df = df.copy()
    df['H-L'] = df['High'] - df['Low']
    df['H-C'] = abs(df['High'] - df['Close'].shift(1))
    df['L-C'] = abs(df['Low'] - df['Close'].shift(1))
    
    tr = df[['H-L', 'H-C', 'L-C']].max(axis=1)  # True Range (Series)
    atr = tr.rolling(n, min_periods=1).mean()   # ATR (Series)
    return atr

# =========================
# Supertrend Calculation
# =========================
def supertrend(df, period=7, multiplier=3):
    """
    Calculate Supertrend and its direction
    Returns: supertrend_series, direction_series
    """
    df = df.copy()
    
    # Step 1: ATR
    df['ATR'] = ATR(df, n=period)
    
    # Step 2: Basic Bands
    hl2 = (df['High'] + df['Low']) / 2
    upperband = hl2 + multiplier * df['ATR']
    lowerband = hl2 - multiplier * df['ATR']
    
    # Step 3: Final Bands and Trend Direction
    final_upperband = upperband.copy()
    final_lowerband = lowerband.copy()
    supertrend = pd.Series(index=df.index)
    direction = pd.Series(1, index=df.index)  # 1 = uptrend, -1 = downtrend

    for i in range(1, len(df)):
        # Adjust final bands
        if df['Close'].iloc[i - 1] > final_upperband.iloc[i - 1]:
            direction.iloc[i] = 1
        elif df['Close'].iloc[i - 1] < final_lowerband.iloc[i - 1]:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = direction.iloc[i - 1]
        
        if direction.iloc[i] == 1:
            final_upperband.iloc[i] = max(upperband.iloc[i], final_upperband.iloc[i - 1])
        else:
            final_lowerband.iloc[i] = min(lowerband.iloc[i], final_lowerband.iloc[i - 1])
        
        # Supertrend value
        if direction.iloc[i] == 1:
            supertrend.iloc[i] = final_lowerband.iloc[i]
        else:
            supertrend.iloc[i] = final_upperband.iloc[i]
    
    # Fill first row
    supertrend.iloc[0] = hl2.iloc[0]

    return supertrend, direction

# =========================
# Signal Generator
# =========================
def generate_signals(df, params):
    """
    Generate buy/sell signals using Supertrend
    Returns analyzed_df, signals_df
    """
    df = df.copy()
    
    # Calculate ATR and Supertrend
    df['ATR'] = ATR(df, n=params['atr_period'])
    df['Supertrend'], df['ST_dir'] = supertrend(df, period=params['st_period'], multiplier=params['st_multiplier'])
    
    # Generate signals
    df['Signal'] = np.where(df['ST_dir'] == 1, 'BUY', 'SELL')
    
    # Optional: Only return relevant columns for signals
    signals_df = df[['Close', 'Supertrend', 'ST_dir', 'Signal']].copy()
    
    return df, signals_df
