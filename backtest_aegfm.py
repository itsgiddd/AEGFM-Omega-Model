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

    def calculate_momentum(self, idx, bars):
        """Calculate momentum (1st derivative of price)"""
        if idx + bars >= len(self.data):
            return 0

        current_price = self.data.iloc[idx]['Close']
        past_price = self.data.iloc[idx + bars]['Close']

        return current_price - past_price

    def calculate_velocity(self, idx, bars):
        """Calculate velocity (weighted directional speed)"""
        if idx + bars >= len(self.data):
            return 0

        total_weighted_change = 0
        total_weight = 0

        for i in range(bars - 1):
            if idx + i + 1 >= len(self.data):
                break

            weight = bars - i
            change = self.data.iloc[idx + i]['Close'] - self.data.iloc[idx + i + 1]['Close']

            total_weighted_change += change * weight
            total_weight += weight

        if total_weight == 0:
            return 0

        return total_weighted_change / total_weight

    def calculate_acceleration(self, idx, bars):
        """Calculate acceleration (2nd derivative)"""
        if idx + bars >= len(self.data):
            return 0

        half_bars = bars // 2

        if idx + half_bars >= len(self.data) or idx + bars >= len(self.data):
            return 0

        recent_momentum = self.data.iloc[idx]['Close'] - self.data.iloc[idx + half_bars]['Close']
        older_momentum = self.data.iloc[idx + half_bars]['Close'] - self.data.iloc[idx + bars]['Close']

        return recent_momentum - older_momentum

    def analyze_pattern_sequence(self, idx, bars):
        """Analyze pattern consistency"""
        if idx + bars >= len(self.data):
            return 0.5

        up_moves = 0
        down_moves = 0

        for i in range(bars - 1):
            if idx + i + 1 >= len(self.data):
                break

            if self.data.iloc[idx + i]['Close'] > self.data.iloc[idx + i + 1]['Close']:
                up_moves += 1
            elif self.data.iloc[idx + i]['Close'] < self.data.iloc[idx + i + 1]['Close']:
                down_moves += 1

        total_moves = up_moves + down_moves
        if total_moves == 0:
            return 0.5

        return max(up_moves, down_moves) / total_moves

    def is_market_trending(self, adx):
        """Detect if market is trending or ranging"""
        return adx >= 20

    def predict_next_move(self, idx, momentum, velocity, acceleration, pattern_score):
        """Predict direction based on market structure - ULTRA STRICT for 98% accuracy"""
        row = self.data.iloc[idx]
        adx = row['ADX']
        current_price = row['Close']
        ma50 = row['MA50']
        rsi = row['RSI']
        stoch = row['Stoch']
        cci = row['CCI']
        bb_upper = row['BB_upper']
        bb_lower = row['BB_lower']

        is_trending = self.is_market_trending(adx)

        # Extreme conditions
        extreme_oversold = (rsi < 30 or stoch < 20 or cci < -100 or current_price < bb_lower)
        extreme_overbought = (rsi > 70 or stoch > 80 or cci > 100 or current_price > bb_upper)

        current_tf_bullish = current_price > ma50

        bullish_score = 0
        bearish_score = 0

        if is_trending:
            # TRENDING: High selectivity
            # Factor 1: TF alignment (weight: 8)
            if current_tf_bullish:
                bullish_score += 8
            else:
                bearish_score += 8

            # Factor 2: Momentum + Velocity aligned (weight: 4)
            if momentum > 0 and velocity > 0:
                bullish_score += 4
            elif momentum < 0 and velocity < 0:
                bearish_score += 4

            # Bonus for acceleration (weight: 2)
            if acceleration > 0 and momentum > 0:
                bullish_score += 2
            elif acceleration > 0 and momentum < 0:
                bearish_score += 2

            # Factor 3: Pattern consistency (weight: 2)
            if pattern_score >= 0.65:
                if momentum > 0:
                    bullish_score += 2
                else:
                    bearish_score += 2

            # Minimum score
            if bullish_score < 12 and bearish_score < 12:
                return 0

        else:
            # RANGING: ONLY trade EXTREME reversals
            if not extreme_oversold and not extreme_overbought:
                return 0

            # Factor 1: Extreme + deceleration (weight: 6)
            if extreme_oversold and acceleration < 0:
                bullish_score += 6
            elif extreme_overbought and acceleration < 0:
                bearish_score += 6
            else:
                return 0

            # Factor 2: TF support/resistance (weight: 3)
            if current_tf_bullish and extreme_oversold:
                bullish_score += 3
            elif not current_tf_bullish and extreme_overbought:
                bearish_score += 3

            # Factor 3: Pattern consistency (weight: 2)
            if pattern_score >= 0.60:
                if extreme_oversold:
                    bullish_score += 2
                else:
                    bearish_score += 2

            # Minimum score
            if bullish_score < 8 and bearish_score < 8:
                return 0

        # Strict threshold
        if bullish_score > bearish_score + 3:
            return 1
        elif bearish_score > bullish_score + 3:
            return -1
        else:
            return 0

    def analyze_signals(self, idx, bars=20):
        """Analyze using PREDICTIVE ENGINE - exact EA logic"""
        df = self.data
        row = df.iloc[idx]

        atr = row['ATR']
        current_price = row['Close']

        # Calculate prediction factors
        momentum = self.calculate_momentum(idx, bars)
        velocity = self.calculate_velocity(idx, bars)
        acceleration = self.calculate_acceleration(idx, bars)
        pattern_score = self.analyze_pattern_sequence(idx, bars)

        momentum_strength = abs(momentum) / (atr + 0.0001)

        # Predict direction (now with market structure awareness)
        predicted_direction = self.predict_next_move(idx, momentum, velocity, acceleration, pattern_score)

        return {
            'momentum': momentum,
            'velocity': velocity,
            'acceleration': acceleration,
            'pattern_score': pattern_score,
            'momentum_strength': momentum_strength,
            'predicted_direction': predicted_direction,
            'atr': atr,
            'volatility': atr / current_price,
            'current_price': current_price
        }

    def calculate_probability(self, signals):
        """Calculate prediction confidence - exact EA logic"""
        confidence = 0.50  # Base 50%

        momentum_strength = signals['momentum_strength']
        momentum = signals['momentum']
        velocity = signals['velocity']
        acceleration = signals['acceleration']
        pattern_score = signals['pattern_score']
        atr = signals['atr']

        # Factor 1: Momentum strength (up to +20%)
        if momentum_strength > 2.0:
            confidence += 0.20
        elif momentum_strength > 1.5:
            confidence += 0.15
        elif momentum_strength > 1.0:
            confidence += 0.10
        elif momentum_strength > 0.5:
            confidence += 0.05

        # Factor 2: Velocity-Momentum alignment (up to +15%)
        velocity_aligned = (momentum > 0 and velocity > 0) or (momentum < 0 and velocity < 0)
        if velocity_aligned:
            velocity_strength = abs(velocity) / (atr + 0.0001)
            if velocity_strength > 0.001:
                confidence += 0.15
            elif velocity_strength > 0.0005:
                confidence += 0.10
            else:
                confidence += 0.05

        # Factor 3: Acceleration (up to +10%)
        acceleration_aligned = False
        if acceleration > 0 and momentum > 0 and velocity > 0:
            acceleration_aligned = True
        if acceleration > 0 and momentum < 0 and velocity < 0:
            acceleration_aligned = True

        if acceleration_aligned:
            confidence += 0.10
        elif abs(acceleration) < 0.00001:
            confidence += 0.05

        # Factor 4: Pattern consistency (up to +15%)
        if pattern_score >= 0.80:
            confidence += 0.15
        elif pattern_score >= 0.70:
            confidence += 0.12
        elif pattern_score >= 0.60:
            confidence += 0.08
        elif pattern_score >= 0.55:
            confidence += 0.04

        # Clamp to realistic range [50%, 98%]
        confidence = max(0.50, min(0.98, confidence))

        return confidence

    def should_trade(self, signals, probability):
        """Check if trade should be taken"""
        # Must have a clear prediction
        if signals['predicted_direction'] == 0:
            return False, "No clear prediction"

        # Minimum confidence threshold
        required_prob = 0.85

        if probability < required_prob:
            return False, f"Confidence {probability:.2%} < {required_prob:.2%}"

        return True, "Prediction confident"

    def simulate_trade(self, idx, signals):
        """Simulate trade outcome based on prediction"""
        df = self.data
        row = df.iloc[idx]

        direction = 'BUY' if signals['predicted_direction'] > 0 else 'SELL'
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
        """Run backtest with PREDICTIVE ENGINE"""
        print("\n" + "="*70)
        print("STARTING BACKTEST - PREDICTIVE ENGINE MODE")
        print("="*70)

        wins = 0
        losses = 0
        open_trades = 0

        for idx in range(100, len(self.data), 30):  # Every 30 candles
            signals = self.analyze_signals(idx, bars=20)
            probability = self.calculate_probability(signals)

            should_enter, reason = self.should_trade(signals, probability)

            if not should_enter:
                continue

            result, exit_time = self.simulate_trade(idx, signals)

            direction = 'BUY' if signals['predicted_direction'] > 0 else 'SELL'

            self.trades.append({
                'result': result,
                'direction': direction,
                'confidence': probability,
                'momentum': signals['momentum'],
                'velocity': signals['velocity'],
                'pattern_score': signals['pattern_score']
            })

            if result == 'WIN':
                wins += 1
                print(f"✓ #{len(self.trades):2d} WIN  | {direction:4s} | Conf: {probability:5.1%} | Mom: {signals['momentum']:7.5f} | Vel: {signals['velocity']:7.5f} | Pat: {signals['pattern_score']:4.2f}")
            elif result == 'LOSS':
                losses += 1
                print(f"✗ #{len(self.trades):2d} LOSS | {direction:4s} | Conf: {probability:5.1%} | Mom: {signals['momentum']:7.5f} | Vel: {signals['velocity']:7.5f} | Pat: {signals['pattern_score']:4.2f}")
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
║          AEGFM-Ω EA BACKTESTING SIMULATOR v2.0                  ║
║       Testing PREDICTIVE ENGINE: Momentum/Velocity/Accel         ║
║       Verifying 98% Accuracy Prediction Target                   ║
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
