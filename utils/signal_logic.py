import pandas as pd
import numpy as np
from .indicators import EMA, RSI, MACD, bollinger_bands, ATR, vwap

def supertrend(df, period=10, multiplier=3.0):
    hl2 = (df['High'] + df['Low']) / 2
    atrv = ATR(df, period)
    upperband = hl2 + (multiplier * atrv)
    lowerband = hl2 - (multiplier * atrv)

    final_upperband = upperband.copy()
    final_lowerband = lowerband.copy()
    supertrend = pd.Series(index=df.index)
    direction = pd.Series(1, index=df.index)

    for i in range(1, len(df)):
        if df['Close'].iat[i-1] <= final_upperband.iat[i-1]:
            final_upperband.iat[i] = min(upperband.iat[i], final_upperband.iat[i-1])
        else:
            final_upperband.iat[i] = upperband.iat[i]

        if df['Close'].iat[i-1] >= final_lowerband.iat[i-1]:
            final_lowerband.iat[i] = max(lowerband.iat[i], final_lowerband.iat[i-1])
        else:
            final_lowerband.iat[i] = lowerband.iat[i]

        if df['Close'].iat[i] <= final_upperband.iat[i]:
            supertrend.iat[i] = final_upperband.iat[i]
            direction.iat[i] = -1
        else:
            supertrend.iat[i] = final_lowerband.iat[i]
            direction.iat[i] = 1

    return supertrend, direction

def generate_signals(df, params):
    df = df.copy()
    df['EMA_short'] = EMA(df['Close'], params['ema_short'])
    df['EMA_long'] = EMA(df['Close'], params['ema_long'])
    df['RSI'] = RSI(df['Close'], params['rsi_period'])
    macd_line, macd_sig, macd_hist = MACD(df['Close'])
    df['MACD'], df['MACD_sig'], df['MACD_hist'] = macd_line, macd_sig, macd_hist
    df['SMA20'], df['BB_up'], df['BB_low'] = bollinger_bands(df['Close'], window=params['bb_window'])
    df['VWAP'] = vwap(df)
    df['ATR'] = ATR(df, n=params['atr_period'])
    df['Supertrend'], df['ST_dir'] = supertrend(df, period=params['st_period'], multiplier=params['st_mult'])
    df['vol_avg_20'] = df['Volume'].rolling(20).mean()
    df['vol_spike'] = df['Volume'] / (df['vol_avg_20'] + 1e-9)

    signals = []
    for i in range(len(df)):
        score, reasons = 0, []

        # Key logic components
        if df['EMA_short'].iat[i] > df['EMA_long'].iat[i]:
            score += 1; reasons.append('EMA Bullish')
        if df['MACD_hist'].iat[i] > 0:
            score += 1; reasons.append('MACD Positive')
        if df['Close'].iat[i] > df['VWAP'].iat[i]:
            score += 1; reasons.append('Above VWAP')
        if 40 < df['RSI'].iat[i] < 75:
            score += 1; reasons.append('RSI Favorable')
        if df['vol_spike'].iat[i] > params['vol_spike_threshold']:
            score += 1; reasons.append('Volume Spike')
        if df['ST_dir'].iat[i] == 1:
            score += 1; reasons.append('Supertrend Up')
        if df['Close'].iat[i] > df['BB_up'].iat[i]:
            score += 1; reasons.append('Bollinger Breakout')

        signal = None
        if score >= params['score_threshold']:
            if df['EMA_short'].iat[i] > df['EMA_long'].iat[i] and df['ST_dir'].iat[i] == 1:
                signal = 'BUY'
            elif df['EMA_short'].iat[i] < df['EMA_long'].iat[i] and df['ST_dir'].iat[i] == -1:
                signal = 'SELL'

        entry, sl, t1, t2 = None, None, None, None
        if signal:
            entry = df['Close'].iat[i]
            atr = df['ATR'].iat[i]
            if signal == 'BUY':
                sl = entry - params['sl_atr_mult'] * atr
                t1 = entry + params['rr1'] * (entry - sl)
                t2 = entry + params['rr2'] * (entry - sl)
            else:
                sl = entry + params['sl_atr_mult'] * atr
                t1 = entry - params['rr1'] * (sl - entry)
                t2 = entry - params['rr2'] * (sl - entry)

        signals.append({
            'timestamp': df.index[i],
            'signal': signal,
            'score': score,
            'reasons': '; '.join(reasons),
            'entry': entry,
            'stop_loss': sl,
            'target1': t1,
            'target2': t2
        })

    s = pd.DataFrame(signals).dropna(subset=['signal'])
    s.set_index('timestamp', inplace=True)
    return df, s
