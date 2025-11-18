#!/usr/bin/env python3
"""
AEGFM $20 to $1 Million Challenge Backtest
==========================================

Tests the AEGFM Omega trading strategy starting with $20 and trading
on all major forex pairs to see how long it takes to reach $1,000,000.

Author: AEGFM Team
Date: 2025-11-18
"""

import numpy as np
from typing import Dict, List, Tuple
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
    pip_value: float = 0.0001  # Standard for most pairs


class MultiPairBacktester:
    """
    Backtests AEGFM strategy across multiple forex pairs simultaneously
    with compound growth from $20 to $1 million.
    """

    def __init__(
        self,
        starting_balance: float = 20.0,
        target_balance: float = 1_000_000.0,
        num_candles: int = 5000,
        use_intermediate_tp: bool = True,
        daily_growth_target: float = 50.0
    ):
        """
        Initialize multi-pair backtester.

        Args:
            starting_balance: Starting account balance ($20)
            target_balance: Target balance ($1,000,000)
            num_candles: Number of candles per pair
            use_intermediate_tp: Use intermediate TP strategy
            daily_growth_target: Daily growth target %
        """
        self.starting_balance = starting_balance
        self.target_balance = target_balance
        self.num_candles = num_candles
        self.use_intermediate_tp = use_intermediate_tp
        self.daily_growth_target = daily_growth_target

        # Initialize forex pairs with realistic spreads
        self.forex_pairs = self._initialize_forex_pairs()

        # Track overall statistics
        self.total_trades = 0
        self.total_wins = 0
        self.total_losses = 0
        self.current_balance = starting_balance
        self.balance_history = [starting_balance]
        self.trade_history = []

    def _initialize_forex_pairs(self) -> List[ForexPair]:
        """Initialize all major forex pairs with realistic configurations"""
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

    def run_challenge(self):
        """
        Run the $20 to $1M challenge.

        Trades on all forex pairs in rotation until target is reached.
        """
        print("=" * 80)
        print("AEGFM OMEGA: $20 TO $1 MILLION CHALLENGE")
        print("=" * 80)
        print(f"\nStarting Balance: ${self.starting_balance:,.2f}")
        print(f"Target Balance: ${self.target_balance:,.2f}")
        print(f"Forex Pairs: {len(self.forex_pairs)}")
        print(f"Strategy: 7-Layer AEGFM with {'Intermediate TP' if self.use_intermediate_tp else 'Standard TP'}")
        print(f"Candles per Pair: {self.num_candles:,}")
        print("\n" + "=" * 80)

        pair_index = 0
        total_iterations = 0
        max_iterations = 1000  # Safety limit

        while self.current_balance < self.target_balance and total_iterations < max_iterations:
            # Select next pair in rotation
            pair = self.forex_pairs[pair_index % len(self.forex_pairs)]

            # Run backtest on this pair
            print(f"\n[Iteration {total_iterations + 1}] Trading {pair.symbol} with ${self.current_balance:,.2f}")

            result = self._run_pair_backtest(pair)

            if result:
                # Update balance
                profit = result['net_profit']
                self.current_balance += profit
                self.balance_history.append(self.current_balance)

                # Update statistics
                self.total_trades += result['total_trades']
                self.total_wins += result['winning_trades']
                self.total_losses += result['losing_trades']

                # Track milestone
                if len(self.balance_history) % 10 == 0 or self.current_balance >= self.target_balance:
                    self._print_milestone()

                # Check if target reached
                if self.current_balance >= self.target_balance:
                    print("\n" + "🎯" * 40)
                    print(f"TARGET REACHED! ${self.current_balance:,.2f}")
                    print("🎯" * 40)
                    break

            pair_index += 1
            total_iterations += 1

        # Final report
        self._print_final_report()

    def _run_pair_backtest(self, pair: ForexPair) -> Dict:
        """
        Run backtest on a single forex pair.

        Args:
            pair: ForexPair configuration

        Returns:
            Dictionary with backtest results
        """
        try:
            # Create backtester for this pair
            backtester = AEGFMBacktester(
                num_candles=self.num_candles,
                daily_growth_target=self.daily_growth_target,
                use_intermediate_tp=self.use_intermediate_tp,
                starting_balance=self.current_balance  # Pass current balance
            )

            # Adjust base price and spread for this pair
            backtester.base_price = pair.base_price
            backtester.spread = pair.spread_pips * pair.pip_value

            # Generate fresh data for this pair
            backtester.generate_realistic_data()
            backtester.calculate_indicators()

            # Run backtest - returns (wins, losses, open_trades)
            wins, losses, open_trades = backtester.run_backtest()

            # Calculate metrics
            total_trades = wins + losses
            if total_trades == 0:
                return None

            win_rate = (wins / total_trades) * 100

            # Calculate profit from the trades
            if len(backtester.trades) > 0:
                # Get final balance from last trade
                final_balance = backtester.trades[-1]['balance']
                net_profit = final_balance - self.current_balance
            else:
                net_profit = 0

            print(f"  Trades: {total_trades} | Wins: {wins} | Losses: {losses} | " +
                  f"Win Rate: {win_rate:.2f}% | Profit: ${net_profit:,.2f}")

            return {
                'pair': pair.symbol,
                'total_trades': total_trades,
                'winning_trades': wins,
                'losing_trades': losses,
                'net_profit': net_profit,
                'win_rate': win_rate
            }

        except Exception as e:
            print(f"  Error running {pair.symbol}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _print_milestone(self):
        """Print milestone progress update"""
        growth_multiple = self.current_balance / self.starting_balance
        progress_pct = (self.current_balance / self.target_balance) * 100

        print(f"\n{'=' * 80}")
        print(f"MILESTONE: Balance = ${self.current_balance:,.2f} ({growth_multiple:.2f}x growth)")
        print(f"Progress: {progress_pct:.2f}% to target")
        print(f"Total Trades: {self.total_trades:,} | Win Rate: {self._calculate_win_rate():.2f}%")
        print(f"{'=' * 80}")

    def _calculate_win_rate(self) -> float:
        """Calculate overall win rate"""
        if self.total_trades == 0:
            return 0.0
        return (self.total_wins / self.total_trades) * 100

    def _print_final_report(self):
        """Print comprehensive final report"""
        print("\n" + "=" * 80)
        print("FINAL REPORT: $20 TO $1 MILLION CHALLENGE")
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
        print(f"Win Rate:             {self._calculate_win_rate():>14.2f}%")

        avg_profit_per_trade = total_profit / self.total_trades if self.total_trades > 0 else 0
        print(f"Avg Profit/Trade:     ${avg_profit_per_trade:>14,.2f}")

        print(f"\n🎯 FOREX PAIRS TRADED")
        print(f"{'─' * 80}")
        print(f"Total Pairs:          {len(self.forex_pairs):>15,}")
        print(f"Pairs List:           {', '.join([p.symbol for p in self.forex_pairs])}")

        print(f"\n⏱️  TIME METRICS")
        print(f"{'─' * 80}")
        iterations = len(self.balance_history) - 1
        print(f"Total Iterations:     {iterations:>15,}")
        print(f"Trades per Iteration: {self.total_trades / iterations if iterations > 0 else 0:>14.2f}")

        # Balance growth checkpoints
        print(f"\n💰 BALANCE GROWTH MILESTONES")
        print(f"{'─' * 80}")
        milestones = [100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000]

        for milestone in milestones:
            trades_to_milestone = None
            for i, balance in enumerate(self.balance_history):
                if balance >= milestone:
                    # Count trades up to this point (rough estimate)
                    trades_to_milestone = int((i / len(self.balance_history)) * self.total_trades)
                    print(f"${milestone:>10,} reached after ~{trades_to_milestone:>6,} trades")
                    break
            if not trades_to_milestone and final_balance < milestone:
                break

        # Success message
        if final_balance >= self.target_balance:
            print(f"\n{'🎉' * 40}")
            print(f"SUCCESS! Turned ${self.starting_balance:.2f} into ${final_balance:,.2f}")
            print(f"Target of ${self.target_balance:,.0f} REACHED in {self.total_trades:,} trades!")
            print(f"{'🎉' * 40}")
        else:
            print(f"\n⚠️  Challenge incomplete: ${final_balance:,.2f} / ${self.target_balance:,.0f}")

        print("\n" + "=" * 80)


def main():
    """Run the $20 to $1 million backtest challenge"""

    # Configuration
    STARTING_BALANCE = 20.0
    TARGET_BALANCE = 1_000_000.0
    NUM_CANDLES = 3000  # 3000 candles per pair per iteration
    USE_INTERMEDIATE_TP = True  # Use the improved ITP strategy
    DAILY_GROWTH_TARGET = 50.0

    # Create and run backtester
    backtester = MultiPairBacktester(
        starting_balance=STARTING_BALANCE,
        target_balance=TARGET_BALANCE,
        num_candles=NUM_CANDLES,
        use_intermediate_tp=USE_INTERMEDIATE_TP,
        daily_growth_target=DAILY_GROWTH_TARGET
    )

    # Run the challenge
    try:
        backtester.run_challenge()
    except KeyboardInterrupt:
        print("\n\nBacktest interrupted by user.")
        backtester._print_final_report()
    except Exception as e:
        print(f"\nError during backtest: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
