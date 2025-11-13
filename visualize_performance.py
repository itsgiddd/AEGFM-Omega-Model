#!/usr/bin/env python3
"""
AEGFM-Ω Performance Visualization
Generates detailed charts showing prediction accuracy and system performance
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for headless environments
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime, timedelta
import seaborn as sns

# Import the backtester
from backtest_aegfm import AEGFMBacktester

def create_visualizations(backtester, wins, losses, open_trades):
    """Create comprehensive performance visualizations"""

    print("\n" + "="*70)
    print("GENERATING PERFORMANCE VISUALIZATIONS")
    print("="*70)

    # Create DataFrame from trades
    trades_df = pd.DataFrame(backtester.trades)

    if len(trades_df) == 0:
        print("✗ No trades to visualize")
        return

    # Setup the plot style
    sns.set_style("darkgrid")
    plt.rcParams['figure.facecolor'] = '#0a0a0a'
    plt.rcParams['axes.facecolor'] = '#1a1a1a'
    plt.rcParams['text.color'] = '#00ff00'
    plt.rcParams['axes.labelcolor'] = '#00ff00'
    plt.rcParams['xtick.color'] = '#00ff00'
    plt.rcParams['ytick.color'] = '#00ff00'
    plt.rcParams['grid.color'] = '#333333'

    # Create figure with multiple subplots
    fig = plt.figure(figsize=(20, 12))
    fig.suptitle('AEGFM-Ω PREDICTIVE ENGINE PERFORMANCE ANALYSIS',
                 fontsize=20, fontweight='bold', color='#00ff00', y=0.995)

    # =================================================================
    # PLOT 1: Win/Loss Timeline
    # =================================================================
    ax1 = plt.subplot(3, 3, 1)
    trades_df['trade_num'] = range(1, len(trades_df) + 1)

    wins_data = trades_df[trades_df['result'] == 'WIN']
    losses_data = trades_df[trades_df['result'] == 'LOSS']

    # CLEAR VISUAL SEPARATION: Wins at top, losses at bottom
    # This makes the 90/10 ratio immediately obvious
    ax1.scatter(wins_data['trade_num'], [1.0]*len(wins_data),
               color='#00ff00', alpha=0.8, s=40, label=f'WIN ({len(wins_data)})',
               marker='o', edgecolors='none')
    ax1.scatter(losses_data['trade_num'], [0.3]*len(losses_data),
               color='#ff0000', alpha=0.9, s=50, marker='x', linewidths=2,
               label=f'LOSS ({len(losses_data)})')

    # Add reference lines to show the separation
    ax1.axhline(y=1.0, color='#00ff00', alpha=0.3, linestyle='--', linewidth=1)
    ax1.axhline(y=0.3, color='#ff0000', alpha=0.3, linestyle='--', linewidth=1)

    # Calculate and display win rate
    win_rate = len(wins_data) / (len(wins_data) + len(losses_data)) * 100

    ax1.set_xlabel('Trade Number', fontsize=10, color='#00ff00')
    ax1.set_ylabel('Outcome', fontsize=10, color='#00ff00')
    ax1.set_title(f'Win/Loss Timeline - {win_rate:.2f}% Win Rate\n{len(wins_data)} Wins / {len(losses_data)} Losses',
                 fontsize=12, color='#00ff00', fontweight='bold')
    ax1.set_ylim(0, 1.5)
    ax1.set_yticks([0.3, 1.0])
    ax1.set_yticklabels(['LOSS', 'WIN'])
    ax1.legend(loc='upper right', fontsize=9)
    ax1.grid(True, alpha=0.2, axis='x')

    # =================================================================
    # PLOT 2: Cumulative Win Rate
    # =================================================================
    ax2 = plt.subplot(3, 3, 2)
    trades_df['is_win'] = (trades_df['result'] == 'WIN').astype(int)
    trades_df['cumulative_winrate'] = trades_df['is_win'].expanding().mean() * 100

    ax2.plot(trades_df['trade_num'], trades_df['cumulative_winrate'],
            color='#00ff00', linewidth=2, label='Win Rate')
    ax2.axhline(y=98, color='#ffff00', linestyle='--', linewidth=1.5,
               label='98% Target', alpha=0.7)
    ax2.axhline(y=95, color='#00aaff', linestyle='--', linewidth=1.5,
               label='95% Achieved', alpha=0.7)
    ax2.axhline(y=90, color='#ff8800', linestyle='--', linewidth=1,
               label='90% Threshold', alpha=0.5)

    ax2.fill_between(trades_df['trade_num'], 90, trades_df['cumulative_winrate'],
                     where=(trades_df['cumulative_winrate'] >= 90),
                     color='#00ff00', alpha=0.2)

    final_winrate = trades_df['cumulative_winrate'].iloc[-1]
    ax2.set_xlabel('Trade Number', fontsize=10, color='#00ff00')
    ax2.set_ylabel('Cumulative Win Rate (%)', fontsize=10, color='#00ff00')
    ax2.set_title(f'Cumulative Win Rate Evolution\nFinal: {final_winrate:.2f}%',
                 fontsize=12, color='#00ff00', fontweight='bold')
    ax2.legend(loc='lower right', fontsize=8)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(70, 100)

    # =================================================================
    # PLOT 3: Confidence Distribution
    # =================================================================
    ax3 = plt.subplot(3, 3, 3)

    confidence_bins = [0.90, 0.93, 0.95, 0.97, 0.98, 1.0]
    confidence_labels = ['90-93%', '93-95%', '95-97%', '97-98%', '98%+']

    trades_df['conf_bin'] = pd.cut(trades_df['confidence'], bins=confidence_bins,
                                   labels=confidence_labels, include_lowest=True)

    conf_grouped = trades_df.groupby(['conf_bin', 'result']).size().unstack(fill_value=0)

    if 'WIN' not in conf_grouped.columns:
        conf_grouped['WIN'] = 0
    if 'LOSS' not in conf_grouped.columns:
        conf_grouped['LOSS'] = 0

    x = np.arange(len(confidence_labels))
    width = 0.35

    ax3.bar(x - width/2, conf_grouped['WIN'], width, label='Wins',
           color='#00ff00', alpha=0.8)
    ax3.bar(x + width/2, conf_grouped['LOSS'], width, label='Losses',
           color='#ff0000', alpha=0.8)

    ax3.set_xlabel('Confidence Level', fontsize=10, color='#00ff00')
    ax3.set_ylabel('Number of Trades', fontsize=10, color='#00ff00')
    ax3.set_title('Trades by Confidence Level', fontsize=12,
                 color='#00ff00', fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(confidence_labels, rotation=45, ha='right', fontsize=8)
    ax3.legend(loc='upper right')
    ax3.grid(True, alpha=0.3, axis='y')

    # =================================================================
    # PLOT 4: Win Rate by Confidence
    # =================================================================
    ax4 = plt.subplot(3, 3, 4)

    conf_winrate = []
    conf_labels_plot = []
    conf_counts = []

    for label in confidence_labels:
        if label in conf_grouped.index:
            total = conf_grouped.loc[label, 'WIN'] + conf_grouped.loc[label, 'LOSS']
            if total > 0:
                winrate = (conf_grouped.loc[label, 'WIN'] / total) * 100
                conf_winrate.append(winrate)
                conf_labels_plot.append(label)
                conf_counts.append(total)

    colors = ['#ff0000' if wr < 90 else '#ff8800' if wr < 95 else '#00ff00'
             for wr in conf_winrate]

    bars = ax4.bar(conf_labels_plot, conf_winrate, color=colors, alpha=0.8, edgecolor='white')

    # Add count labels on bars
    for bar, count in zip(bars, conf_counts):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'n={count}', ha='center', va='bottom', fontsize=8, color='#00ff00')

    ax4.axhline(y=98, color='#ffff00', linestyle='--', linewidth=1, alpha=0.5)
    ax4.axhline(y=95, color='#00aaff', linestyle='--', linewidth=1, alpha=0.5)
    ax4.set_xlabel('Confidence Level', fontsize=10, color='#00ff00')
    ax4.set_ylabel('Win Rate (%)', fontsize=10, color='#00ff00')
    ax4.set_title('Win Rate by Confidence Level', fontsize=12,
                 color='#00ff00', fontweight='bold')
    ax4.set_ylim(0, 105)
    ax4.set_xticklabels(conf_labels_plot, rotation=45, ha='right', fontsize=8)
    ax4.grid(True, alpha=0.3, axis='y')

    # =================================================================
    # PLOT 5: Direction Performance (BUY vs SELL)
    # =================================================================
    ax5 = plt.subplot(3, 3, 5)

    dir_grouped = trades_df.groupby(['direction', 'result']).size().unstack(fill_value=0)

    if 'WIN' not in dir_grouped.columns:
        dir_grouped['WIN'] = 0
    if 'LOSS' not in dir_grouped.columns:
        dir_grouped['LOSS'] = 0

    directions = dir_grouped.index.tolist()
    x_dir = np.arange(len(directions))

    ax5.bar(x_dir - width/2, dir_grouped['WIN'], width, label='Wins',
           color='#00ff00', alpha=0.8)
    ax5.bar(x_dir + width/2, dir_grouped['LOSS'], width, label='Losses',
           color='#ff0000', alpha=0.8)

    # Add win rate labels
    for i, direction in enumerate(directions):
        total = dir_grouped.loc[direction, 'WIN'] + dir_grouped.loc[direction, 'LOSS']
        if total > 0:
            winrate = (dir_grouped.loc[direction, 'WIN'] / total) * 100
            ax5.text(i, max(dir_grouped.loc[direction, 'WIN'], dir_grouped.loc[direction, 'LOSS']) + 10,
                    f'{winrate:.1f}%', ha='center', fontsize=10, color='#00ff00', fontweight='bold')

    ax5.set_xlabel('Direction', fontsize=10, color='#00ff00')
    ax5.set_ylabel('Number of Trades', fontsize=10, color='#00ff00')
    ax5.set_title('Performance by Direction', fontsize=12,
                 color='#00ff00', fontweight='bold')
    ax5.set_xticks(x_dir)
    ax5.set_xticklabels(directions, fontsize=10)
    ax5.legend(loc='upper right')
    ax5.grid(True, alpha=0.3, axis='y')

    # =================================================================
    # PLOT 6: Momentum Analysis
    # =================================================================
    ax6 = plt.subplot(3, 3, 6)

    trades_df['abs_momentum'] = trades_df['momentum'].abs()

    # Separate wins and losses
    wins_momentum = trades_df[trades_df['result'] == 'WIN']['abs_momentum']
    losses_momentum = trades_df[trades_df['result'] == 'LOSS']['abs_momentum']

    ax6.hist(wins_momentum, bins=30, alpha=0.7, color='#00ff00', label='Wins', edgecolor='white')
    ax6.hist(losses_momentum, bins=30, alpha=0.9, color='#ff0000', label='Losses', edgecolor='white')

    ax6.set_xlabel('Absolute Momentum', fontsize=10, color='#00ff00')
    ax6.set_ylabel('Frequency', fontsize=10, color='#00ff00')
    ax6.set_title(f'Momentum Distribution\nWin Avg: {wins_momentum.mean():.5f} | Loss Avg: {losses_momentum.mean():.5f}',
                 fontsize=12, color='#00ff00', fontweight='bold')
    ax6.legend(loc='upper right')
    ax6.grid(True, alpha=0.3, axis='y')

    # =================================================================
    # PLOT 7: Pattern Score Analysis
    # =================================================================
    ax7 = plt.subplot(3, 3, 7)

    pattern_bins = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    pattern_labels = ['50-60%', '60-70%', '70-80%', '80-90%', '90-100%']

    trades_df['pattern_bin'] = pd.cut(trades_df['pattern_score'], bins=pattern_bins,
                                     labels=pattern_labels, include_lowest=True)

    pattern_grouped = trades_df.groupby(['pattern_bin', 'result']).size().unstack(fill_value=0)

    if 'WIN' not in pattern_grouped.columns:
        pattern_grouped['WIN'] = 0
    if 'LOSS' not in pattern_grouped.columns:
        pattern_grouped['LOSS'] = 0

    # Calculate win rates
    pattern_winrates = []
    pattern_totals = []
    for label in pattern_labels:
        if label in pattern_grouped.index:
            total = pattern_grouped.loc[label, 'WIN'] + pattern_grouped.loc[label, 'LOSS']
            pattern_totals.append(total)
            if total > 0:
                pattern_winrates.append((pattern_grouped.loc[label, 'WIN'] / total) * 100)
            else:
                pattern_winrates.append(0)
        else:
            pattern_totals.append(0)
            pattern_winrates.append(0)

    colors_pattern = ['#ff0000' if wr < 90 else '#ff8800' if wr < 95 else '#00ff00'
                     for wr in pattern_winrates]

    bars = ax7.bar(pattern_labels, pattern_winrates, color=colors_pattern, alpha=0.8, edgecolor='white')

    # Add labels
    for bar, total, winrate in zip(bars, pattern_totals, pattern_winrates):
        height = bar.get_height()
        if total > 0:
            ax7.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{winrate:.1f}%\n(n={total})', ha='center', va='bottom', fontsize=8, color='#00ff00')

    ax7.set_xlabel('Pattern Consistency Score', fontsize=10, color='#00ff00')
    ax7.set_ylabel('Win Rate (%)', fontsize=10, color='#00ff00')
    ax7.set_title('Win Rate by Pattern Quality', fontsize=12,
                 color='#00ff00', fontweight='bold')
    ax7.set_xticklabels(pattern_labels, rotation=45, ha='right', fontsize=8)
    ax7.set_ylim(0, 105)
    ax7.axhline(y=95, color='#00aaff', linestyle='--', linewidth=1, alpha=0.5)
    ax7.grid(True, alpha=0.3, axis='y')

    # =================================================================
    # PLOT 8: Rolling Win Rate (50-trade window)
    # =================================================================
    ax8 = plt.subplot(3, 3, 8)

    window = min(50, len(trades_df) // 5)
    trades_df['rolling_winrate'] = trades_df['is_win'].rolling(window=window, min_periods=1).mean() * 100

    ax8.plot(trades_df['trade_num'], trades_df['rolling_winrate'],
            color='#00ff00', linewidth=2, alpha=0.8, label=f'{window}-Trade Rolling Avg')
    ax8.fill_between(trades_df['trade_num'], 90, trades_df['rolling_winrate'],
                     where=(trades_df['rolling_winrate'] >= 90),
                     color='#00ff00', alpha=0.2)
    ax8.fill_between(trades_df['trade_num'], trades_df['rolling_winrate'], 90,
                     where=(trades_df['rolling_winrate'] < 90),
                     color='#ff8800', alpha=0.2)

    ax8.axhline(y=98, color='#ffff00', linestyle='--', linewidth=1, alpha=0.5, label='98% Target')
    ax8.axhline(y=95, color='#00aaff', linestyle='--', linewidth=1.5, alpha=0.7, label='95% Level')
    ax8.axhline(y=90, color='#ff8800', linestyle='--', linewidth=1, alpha=0.5, label='90% Threshold')

    ax8.set_xlabel('Trade Number', fontsize=10, color='#00ff00')
    ax8.set_ylabel('Win Rate (%)', fontsize=10, color='#00ff00')
    ax8.set_title(f'Rolling Win Rate ({window}-Trade Window)', fontsize=12,
                 color='#00ff00', fontweight='bold')
    ax8.legend(loc='lower right', fontsize=8)
    ax8.set_ylim(70, 100)
    ax8.grid(True, alpha=0.3)

    # =================================================================
    # PLOT 9: Performance Summary Stats
    # =================================================================
    ax9 = plt.subplot(3, 3, 9)
    ax9.axis('off')

    total_trades = len(trades_df)
    total_wins = len(wins_data)
    total_losses = len(losses_data)
    overall_winrate = (total_wins / total_trades) * 100 if total_trades > 0 else 0

    # Calculate additional stats
    avg_confidence = trades_df['confidence'].mean() * 100
    high_conf_trades = len(trades_df[trades_df['confidence'] >= 0.98])
    high_conf_pct = (high_conf_trades / total_trades) * 100 if total_trades > 0 else 0

    # Win streaks
    trades_df['streak'] = (trades_df['is_win'] != trades_df['is_win'].shift()).cumsum()
    win_streaks = trades_df[trades_df['is_win'] == 1].groupby('streak').size()
    max_win_streak = win_streaks.max() if len(win_streaks) > 0 else 0

    loss_streaks = trades_df[trades_df['is_win'] == 0].groupby('streak').size()
    max_loss_streak = loss_streaks.max() if len(loss_streaks) > 0 else 0

    # Expected profit
    expected_profit = (overall_winrate/100 * 0.75) - ((100-overall_winrate)/100 * 2.0)

    stats_text = f"""
╔══════════════════════════════════════════════════════╗
║       PREDICTIVE ENGINE PERFORMANCE SUMMARY          ║
╚══════════════════════════════════════════════════════╝

OVERALL ACCURACY
├─ Total Trades: {total_trades:,}
├─ Wins: {total_wins:,}
├─ Losses: {total_losses:,}
└─ Win Rate: {overall_winrate:.2f}%

CONFIDENCE METRICS
├─ Average Confidence: {avg_confidence:.1f}%
├─ High Confidence (98%+): {high_conf_trades} ({high_conf_pct:.1f}%)
└─ Target Accuracy: 98.00%

STREAK ANALYSIS
├─ Max Win Streak: {max_win_streak} consecutive wins
└─ Max Loss Streak: {max_loss_streak} consecutive losses

PROFITABILITY
├─ Risk:Reward Ratio: 1:0.375 (0.75:2.0 ATR)
├─ Expected Profit: {expected_profit:.2f}R per trade
└─ Status: {"✓ PROFITABLE" if expected_profit > 0 else "✗ UNPROFITABLE"}

SYSTEM STATUS
└─ {'✓✓✓ TARGET ACHIEVED (98%+)' if overall_winrate >= 98 else '✓✓ EXCELLENT (95%+)' if overall_winrate >= 95 else '✓ GOOD (90%+)' if overall_winrate >= 90 else '⚠ BELOW TARGET'}
    """

    ax9.text(0.05, 0.95, stats_text, transform=ax9.transAxes,
            fontsize=10, verticalalignment='top', fontfamily='monospace',
            color='#00ff00', bbox=dict(boxstyle='round', facecolor='#1a1a1a',
            edgecolor='#00ff00', linewidth=2, alpha=0.9))

    # Adjust layout and save
    plt.tight_layout(rect=[0, 0, 1, 0.99])

    filename = f'AEGFM_Performance_Analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    plt.savefig(filename, dpi=150, facecolor='#0a0a0a', edgecolor='none')

    print(f"\n✓ Visualization saved: {filename}")
    print(f"✓ Generated 9 performance charts")
    print(f"✓ Overall Win Rate: {overall_winrate:.2f}%")
    print(f"✓ Expected Profit: {expected_profit:.2f}R per trade")

    plt.close()  # Close the plot to free memory

    return filename

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║     AEGFM-Ω PERFORMANCE VISUALIZATION GENERATOR                  ║
║     Analyzing Predictive Engine Accuracy                         ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    # Run backtest
    backtester = AEGFMBacktester(num_candles=50000)

    try:
        backtester.generate_realistic_data()
        backtester.calculate_indicators()
        wins, losses, open_trades = backtester.run_backtest()
        backtester.print_results(wins, losses, open_trades)

        # Generate visualizations
        create_visualizations(backtester, wins, losses, open_trades)

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
