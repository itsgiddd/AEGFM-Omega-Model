#!/usr/bin/env python3
"""
AEGFM $20 to $1 Million AGGRESSIVE Challenge
=============================================

Uses AGGRESSIVE position sizing to target 50% daily growth.
- Higher risk per trade (5-10% instead of 0.2%)
- Larger lot sizes that scale with balance
- Goal: Reach $1M in ~27 days instead of 4,531 days

Author: AEGFM Team
Date: 2025-11-18
"""

import numpy as np
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime
import sys

# Import the main backtester
from backtest_aegfm import AEGFMBacktester


@dataclass
class ForexPair:
    """Forex pair configuration"""
    symbol: str
    base_price: float
    spread_pips: float
    pip_value: float = 0.0001


class AggressiveMultiPairBacktester:
    """
    AGGRESSIVE backtester targeting 50% daily growth.
    Uses much larger position sizes.
    """

    def __init__(
        self,
        starting_balance: float = 20.0,
        target_balance: float = 1_000_000.0,
        risk_multiplier: float = 25.0,  # 25x more aggressive than conservative
        use_intermediate_tp: bool = True
    ):
        """
        Initialize aggressive backtester.

        Args:
            starting_balance: Starting account balance ($20)
            target_balance: Target balance ($1,000,000)
            risk_multiplier: How much more aggressive than base (25x = 5% risk vs 0.2%)
            use_intermediate_tp: Use intermediate TP strategy
        """
        self.starting_balance = starting_balance
        self.target_balance = target_balance
        self.risk_multiplier = risk_multiplier
        self.use_intermediate_tp = use_intermediate_tp

        # Initialize forex pairs
        self.forex_pairs = self._initialize_forex_pairs()

        # Track statistics
        self.total_trades = 0
        self.total_wins = 0
        self.total_losses = 0
        self.current_balance = starting_balance
        self.balance_history = [starting_balance]
        self.daily_history = []

    def _initialize_forex_pairs(self) -> List[ForexPair]:
        """Initialize major forex pairs"""
        return [
            # Major pairs
            ForexPair("EURUSD", 1.0850, 1.0),
            ForexPair("GBPUSD", 1.2650, 1.2),
            ForexPair("USDJPY", 149.50, 1.0, pip_value=0.01),
            ForexPair("USDCHF", 0.8850, 1.2),
            ForexPair("AUDUSD", 0.6550, 1.0),
            ForexPair("USDCAD", 1.3650, 1.2),
            ForexPair("NZDUSD", 0.6050, 1.5),

            # Cross pairs
            ForexPair("EURGBP", 0.8580, 1.5),
            ForexPair("EURJPY", 162.00, 1.5, pip_value=0.01),
            ForexPair("GBPJPY", 188.50, 2.0, pip_value=0.01),
            ForexPair("EURAUD", 1.6550, 2.0),
            ForexPair("EURCHF", 0.9600, 1.8),
            ForexPair("AUDJPY", 97.80, 1.5, pip_value=0.01),
            ForexPair("GBPAUD", 1.9300, 2.5),
            ForexPair("NZDJPY", 90.50, 2.0, pip_value=0.01),
        ]

    def run_aggressive_challenge(self):
        """
        Run the AGGRESSIVE $20 to $1M challenge.
        Targets 50% daily growth through larger position sizes.
        """
        print("=" * 80)
        print("AEGFM OMEGA: AGGRESSIVE $20 TO $1 MILLION CHALLENGE")
        print("=" * 80)
        print(f"\nStarting Balance: ${self.starting_balance:,.2f}")
        print(f"Target Balance: ${self.target_balance:,.2f}")
        print(f"Risk Multiplier: {self.risk_multiplier}x (AGGRESSIVE)")
        print(f"Forex Pairs: {len(self.forex_pairs)}")
        print(f"Strategy: 7-Layer AEGFM with Aggressive Position Sizing")
        print(f"Daily Target: 50% growth per day")
        print("\n" + "=" * 80)

        day_count = 0
        pair_index = 0
        max_days = 50  # Safety limit

        while self.current_balance < self.target_balance and day_count < max_days:
            day_count += 1
            day_starting_balance = self.current_balance

            # Trade on each pair during the day
            day_trades = 0
            day_wins = 0
            day_losses = 0

            print(f"\n{'=' * 80}")
            print(f"DAY {day_count} - Starting Balance: ${self.current_balance:,.2f}")
            print(f"{'=' * 80}")

            # Trade multiple pairs per day
            pairs_per_day = 3  # Trade 3 different pairs per day

            for i in range(pairs_per_day):
                if self.current_balance >= self.target_balance:
                    break

                pair = self.forex_pairs[pair_index % len(self.forex_pairs)]
                pair_index += 1

                result = self._run_aggressive_pair_backtest(pair, day_count)

                if result:
                    profit = result['net_profit']
                    self.current_balance += profit
                    self.balance_history.append(self.current_balance)

                    day_trades += result['total_trades']
                    day_wins += result['winning_trades']
                    day_losses += result['losing_trades']

                    self.total_trades += result['total_trades']
                    self.total_wins += result['winning_trades']
                    self.total_losses += result['losing_trades']

            # Calculate daily performance
            day_profit = self.current_balance - day_starting_balance
            day_growth_pct = (day_profit / day_starting_balance) * 100 if day_starting_balance > 0 else 0

            self.daily_history.append({
                'day': day_count,
                'starting': day_starting_balance,
                'ending': self.current_balance,
                'profit': day_profit,
                'growth_pct': day_growth_pct,
                'trades': day_trades,
                'wins': day_wins,
                'losses': day_losses
            })

            # Print daily summary
            target_emoji = "🎯" if day_growth_pct >= 50 else "📊"
            print(f"\n{target_emoji} Day {day_count} Summary:")
            print(f"  Growth: {day_growth_pct:+.2f}% | Profit: ${day_profit:+,.2f}")
            print(f"  Ending Balance: ${self.current_balance:,.2f}")
            print(f"  Trades: {day_trades} (W:{day_wins} L:{day_losses})")

            # Check if target reached
            if self.current_balance >= self.target_balance:
                print("\n" + "🎯" * 40)
                print(f"TARGET REACHED on Day {day_count}! ${self.current_balance:,.2f}")
                print("🎯" * 40)
                break

        # Final report
        self._print_final_report()

    def _run_aggressive_pair_backtest(self, pair: ForexPair, day: int) -> Dict:
        """
        Run aggressive backtest on a single pair for one day.
        """
        try:
            print(f"\n  [{pair.symbol}] Trading with ${self.current_balance:,.2f}...")

            # Create custom aggressive backtester
            backtester = AEGFMBacktester(
                num_candles=500,  # One day of 15min candles = 96, use 500 for more opportunities
                daily_growth_target=50.0,
                use_intermediate_tp=self.use_intermediate_tp,
                starting_balance=self.current_balance
            )

            # Adjust base price and spread
            backtester.base_price = pair.base_price
            backtester.spread = pair.spread_pips * pair.pip_value

            # Generate data and run backtest
            backtester.generate_realistic_data()
            backtester.calculate_indicators()

            # OVERRIDE position sizing in the trades to be AGGRESSIVE
            # We'll modify the lot size calculation by monkey-patching
            original_run = backtester.run_backtest

            def aggressive_run_backtest():
                """Modified backtest with aggressive position sizing"""
                wins, losses, open_trades = original_run()

                # Recalculate profits with aggressive sizing
                if len(backtester.trades) > 0:
                    # Apply risk multiplier to all trades retroactively
                    for trade in backtester.trades:
                        # Multiply the profit/loss by risk multiplier
                        original_balance_change = trade['balance'] - self.current_balance
                        trade['balance'] = self.current_balance + (original_balance_change * self.risk_multiplier)

                return wins, losses, open_trades

            # Use aggressive version
            wins, losses, open_trades = aggressive_run_backtest()

            total_trades = wins + losses
            if total_trades == 0:
                print(f"    No trades found")
                return None

            win_rate = (wins / total_trades) * 100

            # Calculate profit with aggressive multiplier
            if len(backtester.trades) > 0:
                final_balance = backtester.trades[-1]['balance']
                net_profit = final_balance - self.current_balance
            else:
                net_profit = 0

            print(f"    Trades: {total_trades} | W/L: {wins}/{losses} | " +
                  f"Win Rate: {win_rate:.1f}% | Profit: ${net_profit:+,.2f}")

            return {
                'pair': pair.symbol,
                'total_trades': total_trades,
                'winning_trades': wins,
                'losing_trades': losses,
                'net_profit': net_profit,
                'win_rate': win_rate
            }

        except Exception as e:
            print(f"    Error: {str(e)}")
            return None

    def _print_final_report(self):
        """Print comprehensive final report"""
        print("\n" + "=" * 80)
        print("FINAL REPORT: AGGRESSIVE $20 TO $1 MILLION CHALLENGE")
        print("=" * 80)

        final_balance = self.current_balance
        total_profit = final_balance - self.starting_balance
        roi_pct = ((final_balance - self.starting_balance) / self.starting_balance) * 100
        growth_multiple = final_balance / self.starting_balance

        print(f"\n📊 ACCOUNT PERFORMANCE")
        print(f"{'─' * 80}")
        print(f"Starting Balance:     ${self.starting_balance:>15,.2f}")
        print(f"Final Balance:        ${final_balance:>15,.2f}")
        print(f"Total Profit:         ${total_profit:>15,.2f}")
        print(f"ROI:                  {roi_pct:>15,.2f}%")
        print(f"Growth Multiple:      {growth_multiple:>15,.2f}x")

        print(f"\n📈 TRADING STATISTICS")
        print(f"{'─' * 80}")
        print(f"Total Trades:         {self.total_trades:>15,}")
        print(f"Winning Trades:       {self.total_wins:>15,}")
        print(f"Losing Trades:        {self.total_losses:>15,}")
        if self.total_trades > 0:
            win_rate = (self.total_wins / self.total_trades) * 100
            print(f"Win Rate:             {win_rate:>14.2f}%")
            avg_profit = total_profit / self.total_trades
            print(f"Avg Profit/Trade:     ${avg_profit:>14,.2f}")

        print(f"\n⏱️  TIME METRICS")
        print(f"{'─' * 80}")
        days = len(self.daily_history)
        print(f"Total Trading Days:   {days:>15,}")

        if days > 0:
            print(f"\n📅 DAILY PERFORMANCE BREAKDOWN")
            print(f"{'─' * 80}")
            days_hit_50 = sum(1 for d in self.daily_history if d['growth_pct'] >= 50)
            avg_daily_growth = sum(d['growth_pct'] for d in self.daily_history) / days

            print(f"Days hitting 50%+ :   {days_hit_50:>15,} ({days_hit_50/days*100:.1f}%)")
            print(f"Avg Daily Growth:     {avg_daily_growth:>14.2f}%")

            print(f"\n{'Day':<5} {'Starting':<15} {'Ending':<15} {'Growth':<10} {'Trades':<8} {'Win Rate'}")
            print(f"{'─' * 80}")
            for day_data in self.daily_history:
                day_wr = (day_data['wins'] / day_data['trades'] * 100) if day_data['trades'] > 0 else 0
                emoji = "🎯" if day_data['growth_pct'] >= 50 else "📊"
                print(f"{emoji} {day_data['day']:<3} ${day_data['starting']:>12,.2f} ${day_data['ending']:>12,.2f} "
                      f"{day_data['growth_pct']:>7.2f}%  {day_data['trades']:>6}  {day_wr:>6.1f}%")

        if final_balance >= self.target_balance:
            print(f"\n{'🎉' * 40}")
            print(f"SUCCESS! Turned ${self.starting_balance:.2f} into ${final_balance:,.2f}")
            print(f"Target of ${self.target_balance:,.0f} REACHED in {days} days!")
            print(f"{'🎉' * 40}")
        else:
            print(f"\n⚠️  Challenge incomplete: ${final_balance:,.2f} / ${self.target_balance:,.0f}")

        print("\n" + "=" * 80)


def main():
    """Run the aggressive $20 to $1 million backtest"""

    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                   AEGFM AGGRESSIVE TRADING CHALLENGE                     ║
║                  $20 to $1,000,000 in ~27 Days                          ║
║                                                                          ║
║  WARNING: Uses 25x more aggressive position sizing than conservative     ║
║           Higher risk, higher reward - targets 50% daily growth          ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)

    # Create and run aggressive backtester
    backtester = AggressiveMultiPairBacktester(
        starting_balance=20.0,
        target_balance=1_000_000.0,
        risk_multiplier=25.0,  # 25x more aggressive
        use_intermediate_tp=True
    )

    try:
        backtester.run_aggressive_challenge()
    except KeyboardInterrupt:
        print("\n\nBacktest interrupted by user.")
        backtester._print_final_report()
    except Exception as e:
        print(f"\nError during backtest: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
