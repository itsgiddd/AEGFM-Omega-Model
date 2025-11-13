#!/usr/bin/env python3
"""
AEGFM-Ω Backtesting Script - Tests EA logic with realistic forex data
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class AEGFMBacktester:
    def __init__(self, num_candles=2000):
        self.num_candles = num_candles
        self.data = None
        self.trades = []

    def generate_realistic_data(self):
        """Generate realistic forex price movements"""
        print(f"Generating {self.num_candles} realistic forex candles...")

        # Start at realistic EURUSD price
        base_price = 1.0850

        # Generate realistic OHLC data with trends and volatility
        dates = [datetime.now() - timedelta(minutes=15*i) for i in range(self.num_candles)]
        dates.reverse()

        prices = [base_price]
        for i in range(1, self.num_candles):
            # Random walk with trend and mean reversion
            trend = 0.0001 * np.sin(i / 100)  # Cyclical trend
            noise = np.random.normal(0, 0.0005)  # Volatility
            mean_reversion = 0.0002 * (base_price - prices[-1])  # Pull to base

            change = trend + noise + mean_reversion
            prices.append(prices[-1] + change)

        # Create OHLC from prices
        data = []
        for i, price in enumerate(prices):
            noise = abs(np.random.normal(0, 0.0003))
            high = price + noise
            low = price - noise
            close = price + np.random.normal(0, 0.0002)
            open_price = prices[i-1] if i > 0 else price

            data.append({
                'Open': open_price,
                'High': max(high, open_price, close),
                'Low': min(low, open_price, close),
                'Close': close
            })

        self.data = pd.DataFrame(data, index=pd.DatetimeIndex(dates))
        print(f"✓ Generated {len(self.data)} realistic candles")

    def calculate_indicators(self):
        """Calculate all 14 indicators"""
        df = self.data.copy()

        # MA(50)
        df['MA50'] = df['Close'].rolling(window=50).mean()

        # RSI(14)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, 0.0001)  # Avoid division by zero
        df['RSI'] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

        # Bollinger Bands
        df['BB_middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
        df['BB_lower'] = df['BB_middle'] - (bb_std * 2)

        # ATR(14)
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(14).mean()

        # Stochastic
        low_min = df['Low'].rolling(window=5).min()
        high_max = df['High'].rolling(window=5).max()
        df['Stoch'] = 100 * (df['Close'] - low_min) / (high_max - low_min + 0.0001)
        df['Stoch'] = df['Stoch'].rolling(window=3).mean()

        # ADX(14) - Simplified
        plus_dm = df['High'].diff().clip(lower=0)
        minus_dm = -df['Low'].diff().clip(upper=0)
        atr = df['ATR'].replace(0, 0.0001)
        plus_di = 100 * (plus_dm.rolling(14).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(14).mean() / atr)
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 0.0001)
        df['ADX'] = dx.rolling(14).mean()

        # CCI(14)
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        sma_tp = tp.rolling(14).mean()
        mad = tp.rolling(14).apply(lambda x: np.abs(x - x.mean()).mean())
        df['CCI'] = (tp - sma_tp) / (0.015 * mad + 0.0001)

        self.data = df.dropna()
        print(f"✓ Calculated indicators, {len(self.data)} valid candles")

    def analyze_signals(self, idx):
        """Analyze all 14 signals - exact EA logic"""
        df = self.data
        row = df.iloc[idx]

        current_price = row['Close']
        ma50 = row['MA50']
        rsi = row['RSI']
        macd_main = row['MACD']
        macd_signal = row['MACD_signal']
        bb_upper = row['BB_upper']
        bb_middle = row['BB_middle']
        bb_lower = row['BB_lower']
        stoch = row['Stoch']
        adx = row['ADX']
        cci = row['CCI']
        atr = row['ATR']

        bullish = 0
        bearish = 0
        total = 0

        # Signal 1: MA position
        if current_price > ma50:
            bullish += 1
        else:
            bearish += 1
        total += 1

        # Signal 2: MA distance
        ma_distance = abs(current_price - ma50) / (atr + 0.0001)
        if 0.5 < ma_distance < 2.0:
            if current_price > ma50:
                bullish += 1
            else:
                bearish += 1
            total += 1

        # Signal 3: RSI
        if 30 < rsi < 50:
            bullish += 1
            total += 1
        elif 50 < rsi < 70:
            bearish += 1
            total += 1

        # Signal 4: MACD
        if macd_main > macd_signal and macd_main < 0:
            bullish += 1
            total += 1
        elif macd_main < macd_signal and macd_main > 0:
            bearish += 1
            total += 1

        # Signal 5: Bollinger Bands
        if current_price < bb_lower:
            bullish += 1
            total += 1
        elif current_price > bb_upper:
            bearish += 1
            total += 1
        elif current_price < bb_middle and (bb_middle - current_price) < (current_price - bb_lower):
            bullish += 1
            total += 1
        elif current_price > bb_middle and (current_price - bb_middle) < (bb_upper - current_price):
            bearish += 1
            total += 1

        # Signal 6: Stochastic
        if stoch < 20:
            bullish += 1
            total += 1
        elif stoch > 80:
            bearish += 1
            total += 1

        # Signal 7: ADX
        if adx >= 20:
            total += 1
            if current_price > ma50:
                bullish += 1
            else:
                bearish += 1
        elif adx >= 15:
            total += 1
            if current_price > ma50:
                bullish += 1
            else:
                bearish += 1

        # Signal 8: CCI
        if cci < -100:
            bullish += 1
            total += 1
        elif cci > 100:
            bearish += 1
            total += 1

        # Signal 9: Recent candles
        if idx >= 5:
            bullish_candles = sum([1 for i in range(5) if df.iloc[idx-i]['Close'] > df.iloc[idx-i]['Open']])
            if bullish_candles >= 4:
                bullish += 1
                total += 1
            elif bullish_candles <= 1:
                bearish += 1
                total += 1

        # Signals 10-12: Multi-timeframe (simplified)
        if current_price > ma50:
            bullish += 2
            total += 2
        else:
            bearish += 2
            total += 2

        # Signal 13: Higher TF RSI
        if 30 < rsi < 70:
            if rsi < 50:
                bullish += 1
                total += 1
            elif rsi > 50:
                bearish += 1
                total += 1

        # Signal 14: Higher TF ADX
        if adx >= 20:
            total += 1
            if current_price > ma50:
                bullish += 1
            else:
                bearish += 1

        return {
            'bullish': bullish,
            'bearish': bearish,
            'total': total,
            'adx': adx,
            'atr': atr,
            'volatility': atr / current_price,
            'current_price': current_price
        }

    def calculate_probability(self, signals):
        """Calculate probability - exact EA logic"""
        if signals['total'] == 0:
            return 0.50

        max_signals = max(signals['bullish'], signals['bearish'])
        confluence_ratio = max_signals / signals['total']

        base_prob = 0.50 + (confluence_ratio - 0.5) * 0.80

        adx_bonus = 0
        if signals['adx'] >= 25:
            adx_bonus = 0.08
        elif signals['adx'] >= 20:
            adx_bonus = 0.05

        conf_bonus = 0
        if confluence_ratio >= 0.85:
            conf_bonus = 0.10
        elif confluence_ratio >= 0.80:
            conf_bonus = 0.07
        elif confluence_ratio >= 0.75:
            conf_bonus = 0.05

        vol_adj = 0
        if signals['volatility'] < 0.01:
            vol_adj = 0.05
        elif signals['volatility'] < 0.015:
            vol_adj = 0.03
        elif signals['volatility'] > 0.025:
            vol_adj = -0.05

        probability = base_prob + adx_bonus + conf_bonus + vol_adj
        probability = max(0.60, min(0.98, probability))

        return probability

    def should_trade(self, signals, probability):
        """Check if trade should be taken"""
        max_signals = max(signals['bullish'], signals['bearish'])

        if max_signals < 5:
            return False, "Insufficient confluence"

        required_prob = 0.75

        spread_ratio = 0.1
        if spread_ratio > 0.3:
            required_prob += 0.05
        if signals['volatility'] > 0.03:
            required_prob += 0.05
        if signals['adx'] < 15:
            required_prob += 0.05

        confluence_ratio = max_signals / signals['total']
        if confluence_ratio >= 0.85 and signals['adx'] >= 25 and signals['volatility'] < 0.01:
            required_prob -= 0.05

        required_prob = max(0.70, min(0.95, required_prob))

        if probability < required_prob:
            return False, f"Probability {probability:.2%} < {required_prob:.2%}"

        return True, "All checks passed"

    def simulate_trade(self, idx, signals):
        """Simulate trade outcome"""
        df = self.data
        row = df.iloc[idx]

        direction = 'BUY' if signals['bullish'] > signals['bearish'] else 'SELL'
        entry_price = row['Close']
        atr = row['ATR']

        if direction == 'BUY':
            sl = entry_price - (1.0 * atr)
            tp = entry_price + (2.0 * atr)
        else:
            sl = entry_price + (1.0 * atr)
            tp = entry_price - (2.0 * atr)

        # Check next 100 candles
        for future_idx in range(idx + 1, min(idx + 100, len(df))):
            future_row = df.iloc[future_idx]

            if direction == 'BUY':
                if future_row['Low'] <= sl:
                    return 'LOSS', future_row.name
                if future_row['High'] >= tp:
                    return 'WIN', future_row.name
            else:
                if future_row['High'] >= sl:
                    return 'LOSS', future_row.name
                if future_row['Low'] <= tp:
                    return 'WIN', future_row.name

        return 'OPEN', None

    def run_backtest(self):
        """Run backtest"""
        print("\n" + "="*70)
        print("STARTING BACKTEST")
        print("="*70)

        wins = 0
        losses = 0
        open_trades = 0

        for idx in range(100, len(self.data), 30):  # Every 30 candles
            signals = self.analyze_signals(idx)
            probability = self.calculate_probability(signals)

            should_enter, reason = self.should_trade(signals, probability)

            if not should_enter:
                continue

            result, exit_time = self.simulate_trade(idx, signals)

            direction = 'BUY' if signals['bullish'] > signals['bearish'] else 'SELL'

            self.trades.append({
                'result': result,
                'direction': direction,
                'probability': probability,
                'confluence': f"{max(signals['bullish'], signals['bearish'])}/{signals['total']}",
                'adx': signals['adx']
            })

            if result == 'WIN':
                wins += 1
                print(f"✓ #{len(self.trades):2d} WIN  | {direction:4s} | Prob: {probability:5.1%} | Conf: {self.trades[-1]['confluence']:5s} | ADX: {signals['adx']:5.1f}")
            elif result == 'LOSS':
                losses += 1
                print(f"✗ #{len(self.trades):2d} LOSS | {direction:4s} | Prob: {probability:5.1%} | Conf: {self.trades[-1]['confluence']:5s} | ADX: {signals['adx']:5.1f}")
            else:
                open_trades += 1

        return wins, losses, open_trades

    def print_results(self, wins, losses, open_trades):
        """Print results"""
        total = wins + losses + open_trades
        closed_trades = wins + losses

        print("\n" + "="*70)
        print("BACKTEST RESULTS")
        print("="*70)
        print(f"Candles Analyzed: {self.num_candles}")
        print(f"Total Signals: {total}")
        print(f"Closed Trades: {closed_trades}")
        print(f"Open Trades: {open_trades}")
        print(f"Wins: {wins}")
        print(f"Losses: {losses}")

        if closed_trades > 0:
            win_rate = (wins / closed_trades) * 100
            print(f"\n{'='*70}")
            print(f"ACTUAL WIN RATE: {win_rate:.2f}%")
            print(f"{'='*70}")

            if win_rate >= 98:
                print("✓✓✓ TARGET ACHIEVED: 98%+ Accuracy ✓✓✓")
            elif win_rate >= 90:
                print("✓✓ EXCELLENT: 90%+ Accuracy (Close to target)")
            elif win_rate >= 80:
                print("✓ GOOD: 80%+ Accuracy (Needs optimization)")
            elif win_rate >= 70:
                print("⚠ ACCEPTABLE: 70%+ Accuracy (Significant gap from 98%)")
            else:
                print("✗ BELOW TARGET: < 70% Accuracy (Major adjustment needed)")

            expected_profit = (win_rate/100 * 2) - ((100-win_rate)/100 * 1)
            print(f"\nExpected Profit per Trade (1:2 R:R): {expected_profit:.2f}R")

            if expected_profit > 0:
                print(f"✓ Profitable system (positive expectancy)")
            else:
                print(f"✗ Losing system (negative expectancy)")

        else:
            print("\n✗ NO CLOSED TRADES - Cannot calculate win rate")
            print("   System may be TOO selective")

        print("="*70)

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║          AEGFM-Ω EA BACKTESTING SIMULATOR v1.0                  ║
║       Testing 14-Indicator Multi-Timeframe System                ║
║       Verifying 98% Accuracy Target                              ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    backtester = AEGFMBacktester(num_candles=2000)

    try:
        backtester.generate_realistic_data()
        backtester.calculate_indicators()
        wins, losses, open_trades = backtester.run_backtest()
        backtester.print_results(wins, losses, open_trades)

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
