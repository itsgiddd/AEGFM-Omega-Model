#!/usr/bin/env python3
"""
Visual Proof: Intermediate TP Strategy Comparison
Generates candlestick charts and performance dashboards comparing baseline vs intermediate TP.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from datetime import datetime, timedelta
import sys

# Import the backtester
from backtest_aegfm import AEGFMBacktester

def create_candlestick_chart(data, trades, title, filename, show_intermediate=False):
    """Create a candlestick chart with trade markers."""
    fig = plt.figure(figsize=(20, 12))
    gs = GridSpec(3, 1, height_ratios=[3, 1, 1], hspace=0.3)

    # Main candlestick chart
    ax1 = fig.add_subplot(gs[0])

    # Plot candlesticks (simplified - using close prices with high/low wicks)
    for idx in range(min(500, len(data))):  # Show first 500 candles
        row = data.iloc[idx]
        color = 'green' if row['Close'] >= row['Open'] else 'red'

        # Draw body
        ax1.plot([idx, idx], [row['Open'], row['Close']],
                color=color, linewidth=2, solid_capstyle='round')

        # Draw wicks
        ax1.plot([idx, idx], [row['Low'], row['High']],
                color=color, linewidth=0.5, alpha=0.5)

    # Mark trades
    win_trades = [t for t in trades if t['result'] == 'WIN']
    loss_trades = [t for t in trades if t['result'] == 'LOSS']
    intermediate_trades = [t for t in trades if t.get('intermediate_tp', False)]

    # Plot trade markers (using indices within first 500 candles)
    for trade in win_trades[:50]:  # Show first 50 trades
        if 'idx' in trade:
            idx = trade.get('idx', 0)
            if idx < 500:
                price = data.iloc[idx]['Close']
                marker = '^' if trade['direction'] == 'BUY' else 'v'
                color = 'lime' if trade.get('intermediate_tp', False) else 'green'
                size = 150 if trade.get('intermediate_tp', False) else 100
                ax1.scatter(idx, price, marker=marker, s=size, c=color,
                           edgecolors='black', linewidth=1, zorder=5,
                           label='WIN (Intermediate TP)' if trade.get('intermediate_tp', False) else 'WIN')

    for trade in loss_trades[:10]:  # Show first 10 losses
        if 'idx' in trade:
            idx = trade.get('idx', 0)
            if idx < 500:
                price = data.iloc[idx]['Close']
                marker = '^' if trade['direction'] == 'BUY' else 'v'
                ax1.scatter(idx, price, marker=marker, s=100, c='red',
                           edgecolors='black', linewidth=1, zorder=5, label='LOSS')

    ax1.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax1.set_ylabel('Price', fontsize=12)
    ax1.grid(True, alpha=0.3)

    # Remove duplicate labels
    handles, labels = ax1.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax1.legend(by_label.values(), by_label.keys(), loc='upper left', fontsize=10)

    # Equity curve
    ax2 = fig.add_subplot(gs[1])
    if len(trades) > 0:
        trade_numbers = list(range(1, len(trades) + 1))
        balances = [t['balance'] for t in trades]
        ax2.plot(trade_numbers, balances, linewidth=2, color='blue')
        ax2.fill_between(trade_numbers, 10000, balances, alpha=0.3, color='blue')
        ax2.axhline(y=10000, color='gray', linestyle='--', linewidth=1, alpha=0.5)
        ax2.set_ylabel('Balance ($)', fontsize=12)
        ax2.set_xlabel('Trade Number', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.set_title('Equity Curve', fontsize=12, fontweight='bold')

        # Add profit annotation
        final_profit = balances[-1] - 10000
        color = 'green' if final_profit > 0 else 'red'
        ax2.text(0.02, 0.95, f'Total Profit: ${final_profit:+,.2f}',
                transform=ax2.transAxes, fontsize=11, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor=color, alpha=0.3))

    # Win/Loss distribution
    ax3 = fig.add_subplot(gs[2])
    wins = len([t for t in trades if t['result'] == 'WIN'])
    losses = len([t for t in trades if t['result'] == 'LOSS'])

    bars = ax3.bar(['Wins', 'Losses'], [wins, losses], color=['green', 'red'], alpha=0.7)
    ax3.set_ylabel('Count', fontsize=12)
    ax3.set_title('Win/Loss Distribution', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y')

    # Add count labels on bars
    for bar in bars:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

    # Add win rate
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    ax3.text(0.98, 0.95, f'Win Rate: {win_rate:.2f}%',
            transform=ax3.transAxes, fontsize=12, fontweight='bold',
            verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))

    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"✓ Saved candlestick chart: {filename}")
    plt.close()

def create_comparison_dashboard(baseline_stats, intermediate_stats, filename):
    """Create a comprehensive comparison dashboard."""
    fig = plt.figure(figsize=(20, 14))
    gs = GridSpec(3, 2, hspace=0.3, wspace=0.3)

    # Title
    fig.suptitle('INTERMEDIATE TP STRATEGY COMPARISON\nBaseline vs Drawdown Reduction',
                fontsize=20, fontweight='bold', y=0.98)

    # 1. Win Rate Comparison
    ax1 = fig.add_subplot(gs[0, 0])
    categories = ['Baseline', 'Intermediate TP']
    win_rates = [baseline_stats['win_rate'], intermediate_stats['win_rate']]
    colors = ['#3498db', '#2ecc71']
    bars = ax1.bar(categories, win_rates, color=colors, alpha=0.8, edgecolor='black', linewidth=2)
    ax1.set_ylabel('Win Rate (%)', fontsize=12, fontweight='bold')
    ax1.set_title('Win Rate Comparison', fontsize=14, fontweight='bold', pad=15)
    ax1.set_ylim([90, 100])
    ax1.grid(True, alpha=0.3, axis='y')
    ax1.axhline(y=94, color='red', linestyle='--', linewidth=2, alpha=0.5, label='Original Target')
    ax1.axhline(y=98, color='gold', linestyle='--', linewidth=2, alpha=0.7, label='New Target')

    # Add value labels
    for i, (bar, rate) in enumerate(zip(bars, win_rates)):
        height = bar.get_height()
        improvement = win_rates[1] - win_rates[0] if i == 1 else 0
        label = f'{rate:.2f}%'
        if i == 1 and improvement > 0:
            label += f'\n(+{improvement:.2f}%)'
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                label, ha='center', va='bottom', fontsize=12, fontweight='bold')
    ax1.legend(loc='lower right', fontsize=10)

    # 2. Profit Comparison
    ax2 = fig.add_subplot(gs[0, 1])
    profits = [baseline_stats['profit'], intermediate_stats['profit']]
    bars = ax2.bar(categories, profits, color=colors, alpha=0.8, edgecolor='black', linewidth=2)
    ax2.set_ylabel('Total Profit ($)', fontsize=12, fontweight='bold')
    ax2.set_title('Profit Comparison', fontsize=14, fontweight='bold', pad=15)
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)

    for i, (bar, profit) in enumerate(zip(bars, profits)):
        height = bar.get_height()
        improvement = profits[1] - profits[0] if i == 1 else 0
        label = f'${profit:+,.2f}'
        if i == 1 and improvement > 0:
            pct_improvement = (improvement / profits[0] * 100) if profits[0] != 0 else 0
            label += f'\n(+${improvement:,.2f})\n(+{pct_improvement:.1f}%)'
        ax2.text(bar.get_x() + bar.get_width()/2., height + 20,
                label, ha='center', va='bottom', fontsize=11, fontweight='bold')

    # 3. Wins vs Losses
    ax3 = fig.add_subplot(gs[1, 0])
    x = np.arange(len(categories))
    width = 0.35
    wins = [baseline_stats['wins'], intermediate_stats['wins']]
    losses = [baseline_stats['losses'], intermediate_stats['losses']]

    bars1 = ax3.bar(x - width/2, wins, width, label='Wins', color='green', alpha=0.8, edgecolor='black')
    bars2 = ax3.bar(x + width/2, losses, width, label='Losses', color='red', alpha=0.8, edgecolor='black')

    ax3.set_ylabel('Count', fontsize=12, fontweight='bold')
    ax3.set_title('Wins vs Losses', fontsize=14, fontweight='bold', pad=15)
    ax3.set_xticks(x)
    ax3.set_xticklabels(categories)
    ax3.legend(fontsize=11)
    ax3.grid(True, alpha=0.3, axis='y')

    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom', fontsize=11, fontweight='bold')

    # 4. Drawdown Comparison
    ax4 = fig.add_subplot(gs[1, 1])
    drawdowns = [baseline_stats['avg_adverse'], intermediate_stats['avg_adverse']]
    bars = ax4.bar(categories, drawdowns, color=colors, alpha=0.8, edgecolor='black', linewidth=2)
    ax4.set_ylabel('Avg Adverse Movement', fontsize=12, fontweight='bold')
    ax4.set_title('Drawdown Comparison (Lower is Better)', fontsize=14, fontweight='bold', pad=15)
    ax4.grid(True, alpha=0.3, axis='y')

    for i, (bar, dd) in enumerate(zip(bars, drawdowns)):
        height = bar.get_height()
        reduction = (drawdowns[0] - drawdowns[1]) / drawdowns[0] * 100 if i == 1 and drawdowns[0] > 0 else 0
        label = f'{dd:.5f}'
        if i == 1 and reduction > 0:
            label += f'\n(-{reduction:.1f}%)'
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                label, ha='center', va='bottom', fontsize=11, fontweight='bold')

    # 5. Intermediate TP Statistics (if available)
    ax5 = fig.add_subplot(gs[2, :])
    ax5.axis('off')

    if intermediate_stats['intermediate_tps'] > 0:
        stats_text = f"""
INTERMEDIATE TP FEATURE IMPACT

• Total Intermediate TPs Placed: {intermediate_stats['intermediate_tps']}
• Total Re-entries Attempted: {intermediate_stats['reentries']}
• Successful Re-entries: {intermediate_stats['successful_reentries']}
• Re-entry Success Rate: {intermediate_stats['reentry_success_rate']:.1f}%
• Trades Using Feature: {intermediate_stats['trades_with_intermediate']} ({intermediate_stats['intermediate_usage_pct']:.1f}% of all trades)

KEY BENEFITS:
✓ Win Rate Improvement: +{intermediate_stats['win_rate'] - baseline_stats['win_rate']:.2f}%
✓ Profit Improvement: +${intermediate_stats['profit'] - baseline_stats['profit']:,.2f} (+{((intermediate_stats['profit'] - baseline_stats['profit']) / baseline_stats['profit'] * 100):.1f}%)
✓ Drawdown Reduction: {((baseline_stats['avg_adverse'] - intermediate_stats['avg_adverse']) / baseline_stats['avg_adverse'] * 100):.1f}%
✓ Losses Avoided: {baseline_stats['losses'] - intermediate_stats['losses']} trades converted from losses to wins

STRATEGY: When price moves {intermediate_stats.get('counter_move_atr', 0.75)}× ATR against position,
place intermediate TP to capture counter-move profit, then re-enter towards original target.
        """
    else:
        stats_text = "Intermediate TP feature not used in this backtest."

    ax5.text(0.5, 0.5, stats_text, transform=ax5.transAxes,
            fontsize=11, verticalalignment='center', horizontalalignment='center',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3, pad=1),
            family='monospace')

    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"✓ Saved comparison dashboard: {filename}")
    plt.close()

def main():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║      VISUAL PROOF: INTERMEDIATE TP STRATEGY COMPARISON          ║
║              Generating Charts and Dashboards                    ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    # Set seed for reproducible results
    np.random.seed(42)

    # Run baseline backtest
    print("\n" + "="*70)
    print("RUNNING BASELINE BACKTEST...")
    print("="*70)
    backtester_baseline = AEGFMBacktester(num_candles=5000, use_intermediate_tp=False)
    backtester_baseline.generate_realistic_data()
    backtester_baseline.calculate_indicators()

    # Store data before running backtest
    baseline_data = backtester_baseline.data.copy()

    wins_baseline, losses_baseline, _ = backtester_baseline.run_backtest()

    # Reset seed for same market conditions
    np.random.seed(42)

    # Run intermediate TP backtest
    print("\n" + "="*70)
    print("RUNNING INTERMEDIATE TP BACKTEST...")
    print("="*70)
    backtester_intermediate = AEGFMBacktester(num_candles=5000, use_intermediate_tp=True)
    backtester_intermediate.generate_realistic_data()
    backtester_intermediate.calculate_indicators()

    # Store data before running backtest
    intermediate_data = backtester_intermediate.data.copy()

    wins_intermediate, losses_intermediate, _ = backtester_intermediate.run_backtest()

    # Collect statistics
    baseline_stats = {
        'win_rate': (wins_baseline / (wins_baseline + losses_baseline) * 100) if (wins_baseline + losses_baseline) > 0 else 0,
        'wins': wins_baseline,
        'losses': losses_baseline,
        'profit': backtester_baseline.trades[-1]['balance'] - 10000 if len(backtester_baseline.trades) > 0 else 0,
        'avg_adverse': pd.DataFrame(backtester_baseline.trades)['max_adverse_move'].mean() if len(backtester_baseline.trades) > 0 else 0
    }

    intermediate_stats = {
        'win_rate': (wins_intermediate / (wins_intermediate + losses_intermediate) * 100) if (wins_intermediate + losses_intermediate) > 0 else 0,
        'wins': wins_intermediate,
        'losses': losses_intermediate,
        'profit': backtester_intermediate.trades[-1]['balance'] - 10000 if len(backtester_intermediate.trades) > 0 else 0,
        'avg_adverse': pd.DataFrame(backtester_intermediate.trades)['max_adverse_move'].mean() if len(backtester_intermediate.trades) > 0 else 0,
        'intermediate_tps': backtester_intermediate.total_intermediate_tps,
        'reentries': backtester_intermediate.total_reentries,
        'successful_reentries': backtester_intermediate.successful_reentries,
        'reentry_success_rate': (backtester_intermediate.successful_reentries / backtester_intermediate.total_reentries * 100) if backtester_intermediate.total_reentries > 0 else 0,
        'trades_with_intermediate': len([t for t in backtester_intermediate.trades if t.get('intermediate_tp', False)]),
        'intermediate_usage_pct': (len([t for t in backtester_intermediate.trades if t.get('intermediate_tp', False)]) / len(backtester_intermediate.trades) * 100) if len(backtester_intermediate.trades) > 0 else 0,
        'counter_move_atr': backtester_intermediate.counter_move_atr
    }

    # Generate visualizations
    print("\n" + "="*70)
    print("GENERATING VISUAL PROOF...")
    print("="*70)

    # 1. Baseline candlestick chart
    create_candlestick_chart(
        baseline_data,
        backtester_baseline.trades,
        'BASELINE STRATEGY (No Intermediate TP)\n' +
        f'Win Rate: {baseline_stats["win_rate"]:.2f}% | Profit: ${baseline_stats["profit"]:+,.2f}',
        'intermediate_tp_baseline_chart.png',
        show_intermediate=False
    )

    # 2. Intermediate TP candlestick chart
    create_candlestick_chart(
        intermediate_data,
        backtester_intermediate.trades,
        'INTERMEDIATE TP STRATEGY (Drawdown Reduction)\n' +
        f'Win Rate: {intermediate_stats["win_rate"]:.2f}% | Profit: ${intermediate_stats["profit"]:+,.2f}',
        'intermediate_tp_strategy_chart.png',
        show_intermediate=True
    )

    # 3. Comparison dashboard
    create_comparison_dashboard(
        baseline_stats,
        intermediate_stats,
        'intermediate_tp_comparison_dashboard.png'
    )

    print("\n" + "="*70)
    print("✓✓✓ VISUAL PROOF GENERATED SUCCESSFULLY ✓✓✓")
    print("="*70)
    print("\nGenerated files:")
    print("  1. intermediate_tp_baseline_chart.png")
    print("  2. intermediate_tp_strategy_chart.png")
    print("  3. intermediate_tp_comparison_dashboard.png")
    print("\n" + "="*70)

if __name__ == "__main__":
    try:
        # Check if matplotlib is installed
        import matplotlib
        main()
    except ImportError as e:
        print(f"\n✗ ERROR: Missing required package: {e}")
        print("Please install: pip3 install matplotlib")
        sys.exit(1)
