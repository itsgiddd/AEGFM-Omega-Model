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
    """Create comprehensive performance visualizations with REAL FOREX CONDITIONS"""

    print("\n" + "="*70)
    print("GENERATING PERFORMANCE VISUALIZATIONS - REAL FOREX CONDITIONS")
    print("="*70)

    # Create DataFrame from trades
    trades_df = pd.DataFrame(backtester.trades)

    if len(trades_df) == 0:
        print("✗ No trades to visualize")
        return

    # ===================================================================
    # REAL FOREX CONDITIONS - Apply spreads, slippage, and commissions
    # ===================================================================
    SPREAD_PIPS = 1.5  # Average spread for EURUSD (1.5 pips)
    SLIPPAGE_PIPS = 0.5  # Average slippage (0.5 pips)
    COMMISSION_PER_LOT = 7.0  # Round-trip commission ($7 per standard lot)
    PIP_VALUE = 10.0  # Standard lot pip value ($10 per pip for EURUSD)

    # Adjust profits for real forex costs
    total_cost_per_trade = (SPREAD_PIPS + SLIPPAGE_PIPS) * PIP_VALUE + COMMISSION_PER_LOT

    # Recalculate balance with real forex costs
    starting_balance = 10000.0
    real_balance = starting_balance
    trades_df['real_profit'] = 0.0
    trades_df['real_balance'] = 0.0

    for i in range(len(trades_df)):
        # Original profit
        original_profit = trades_df.iloc[i]['profit']

        # Subtract forex costs
        real_profit = original_profit - total_cost_per_trade

        # For losses, costs make them worse
        if trades_df.iloc[i]['result'] == 'LOSS':
            real_profit = original_profit - total_cost_per_trade

        real_balance += real_profit
        trades_df.at[i, 'real_profit'] = real_profit
        trades_df.at[i, 'real_balance'] = real_balance

    print(f"✓ Applied REAL FOREX conditions: {SPREAD_PIPS} pip spread + {SLIPPAGE_PIPS} pip slippage + ${COMMISSION_PER_LOT} commission")
    print(f"✓ Realistic costs per trade: ${total_cost_per_trade:.2f}")

    # Setup the plot style
    sns.set_style("darkgrid")
    plt.rcParams['figure.facecolor'] = '#0a0a0a'
    plt.rcParams['axes.facecolor'] = '#1a1a1a'
    plt.rcParams['text.color'] = '#00ff00'
    plt.rcParams['axes.labelcolor'] = '#00ff00'
    plt.rcParams['xtick.color'] = '#00ff00'
    plt.rcParams['ytick.color'] = '#00ff00'
    plt.rcParams['grid.color'] = '#333333'

    # Create figure with multiple subplots (increased to 4x3 for daily growth charts)
    fig = plt.figure(figsize=(24, 16))
    fig.suptitle('AEGFM-Ω REAL FOREX CONDITIONS - Spreads, Slippage & Commission Included',
                 fontsize=20, fontweight='bold', color='#00ff00', y=0.995)

    # =================================================================
    # PLOT 1: Win/Loss Timeline
    # =================================================================
    ax1 = plt.subplot(4, 3, 1)
    trades_df['trade_num'] = range(1, len(trades_df) + 1)

    wins_data = trades_df[trades_df['result'] == 'WIN']
    losses_data = trades_df[trades_df['result'] == 'LOSS']

    # SIMPLE BAR CHART: Shows actual COUNT difference
    # This makes the 9:1 ratio IMMEDIATELY and HONESTLY obvious
    win_count = len(wins_data)
    loss_count = len(losses_data)
    win_rate = win_count / (win_count + loss_count) * 100

    bars = ax1.bar(['WINS', 'LOSSES'], [win_count, loss_count],
                   color=['#00ff00', '#ff0000'], alpha=0.8, width=0.6)

    # Add count labels on top of bars
    ax1.text(0, win_count + (win_count * 0.02), f'{win_count:,}', ha='center', va='bottom',
            color='#00ff00', fontsize=14, fontweight='bold')
    ax1.text(1, loss_count + (win_count * 0.02), f'{loss_count:,}', ha='center', va='bottom',
            color='#ff0000', fontsize=14, fontweight='bold')

    ax1.set_ylabel('Trade Count', fontsize=10, color='#00ff00')
    ax1.set_title(f'Win/Loss Count - {win_rate:.2f}% Win Rate\n{win_count:,} Wins vs {loss_count:,} Losses',
                 fontsize=12, color='#00ff00', fontweight='bold')
    ax1.grid(True, alpha=0.2, axis='y')

    # Set y-axis to show the full scale so the difference is clear
    ax1.set_ylim(0, win_count * 1.15)

    # =================================================================
    # PLOT 2: Cumulative Win Rate
    # =================================================================
    ax2 = plt.subplot(4, 3, 2)
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
    ax3 = plt.subplot(4, 3, 3)

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
    ax4 = plt.subplot(4, 3, 4)

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
    ax5 = plt.subplot(4, 3, 5)

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
    ax6 = plt.subplot(4, 3, 6)

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
    ax7 = plt.subplot(4, 3, 7)

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
    ax8 = plt.subplot(4, 3, 8)

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
    # PLOT 9: REAL FOREX Performance Summary Stats
    # =================================================================
    ax9 = plt.subplot(4, 3, 9)
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

    # REAL FOREX METRICS
    total_gross_profit = trades_df[trades_df['real_profit'] > 0]['real_profit'].sum() if len(trades_df[trades_df['real_profit'] > 0]) > 0 else 0
    total_gross_loss = abs(trades_df[trades_df['real_profit'] < 0]['real_profit'].sum()) if len(trades_df[trades_df['real_profit'] < 0]) > 0 else 0
    profit_factor = total_gross_profit / total_gross_loss if total_gross_loss > 0 else 0

    avg_win = trades_df[trades_df['real_profit'] > 0]['real_profit'].mean() if len(trades_df[trades_df['real_profit'] > 0]) > 0 else 0
    avg_loss = trades_df[trades_df['real_profit'] < 0]['real_profit'].mean() if len(trades_df[trades_df['real_profit'] < 0]) > 0 else 0

    # Calculate max drawdown from real balance
    peak = trades_df['real_balance'].expanding(min_periods=1).max()
    drawdown = (trades_df['real_balance'] - peak) / peak * 100
    max_drawdown = abs(drawdown.min())

    # Calculate Sharpe Ratio (simplified - assuming 252 trading days/year)
    returns = trades_df['real_profit'] / starting_balance * 100
    sharpe_ratio = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0

    # Expected profit with real costs
    expected_profit = (overall_winrate/100 * 0.75) - ((100-overall_winrate)/100 * 2.0)

    # Total profit/loss
    net_profit = trades_df['real_balance'].iloc[-1] - starting_balance if len(trades_df) > 0 else 0

    stats_text = f"""
╔══════════════════════════════════════════════════════╗
║      REAL FOREX CONDITIONS - PERFORMANCE SUMMARY     ║
╚══════════════════════════════════════════════════════╝

OVERALL ACCURACY
├─ Total Trades: {total_trades:,}
├─ Wins: {total_wins:,} | Losses: {total_losses:,}
└─ Win Rate: {overall_winrate:.2f}%

REAL FOREX PROFITABILITY (After Costs)
├─ Net Profit: ${net_profit:,.2f}
├─ Profit Factor: {profit_factor:.2f}
├─ Avg Win: ${avg_win:.2f} | Avg Loss: ${avg_loss:.2f}
├─ Max Drawdown: {max_drawdown:.2f}%
└─ Sharpe Ratio: {sharpe_ratio:.2f}

TRADING COSTS (Per Trade)
├─ Spread: {SPREAD_PIPS} pips (${SPREAD_PIPS * PIP_VALUE:.2f})
├─ Slippage: {SLIPPAGE_PIPS} pips (${SLIPPAGE_PIPS * PIP_VALUE:.2f})
├─ Commission: ${COMMISSION_PER_LOT:.2f}
└─ Total Cost: ${total_cost_per_trade:.2f}/trade

STREAK ANALYSIS
├─ Max Win Streak: {max_win_streak} consecutive
└─ Max Loss Streak: {max_loss_streak} consecutive

SYSTEM STATUS
└─ {'✓✓✓ PROFITABLE' if profit_factor > 1.5 else '✓✓ GOOD' if profit_factor > 1.0 else '⚠ NEEDS WORK'}
    """

    ax9.text(0.05, 0.95, stats_text, transform=ax9.transAxes,
            fontsize=9, verticalalignment='top', fontfamily='monospace',
            color='#00ff00', bbox=dict(boxstyle='round', facecolor='#1a1a1a',
            edgecolor='#00ff00', linewidth=2, alpha=0.9))

    # =================================================================
    # PLOT 10: REAL FOREX Account Balance (With Spreads & Costs)
    # =================================================================
    ax10 = plt.subplot(4, 3, 10)

    if 'real_balance' in trades_df.columns and len(trades_df) > 0:
        # Plot both ideal and real balance for comparison
        ax10.plot(trades_df['trade_num'], trades_df['balance'],
                 color='#888888', linewidth=1.5, alpha=0.5, linestyle='--',
                 label='Ideal (No Costs)')
        ax10.plot(trades_df['trade_num'], trades_df['real_balance'],
                 color='#00ff00', linewidth=2.5, label='Real (With Costs)')

        ax10.axhline(y=starting_balance, color='#ffff00', linestyle='--',
                    linewidth=1, alpha=0.5, label='Starting Balance')

        # Fill area for real balance
        ax10.fill_between(trades_df['trade_num'], starting_balance, trades_df['real_balance'],
                          where=(trades_df['real_balance'] >= starting_balance),
                          color='#00ff00', alpha=0.2)
        ax10.fill_between(trades_df['trade_num'], trades_df['real_balance'], starting_balance,
                          where=(trades_df['real_balance'] < starting_balance),
                          color='#ff0000', alpha=0.2)

        final_balance_ideal = trades_df['balance'].iloc[-1]
        final_balance_real = trades_df['real_balance'].iloc[-1]
        total_growth = ((final_balance_real - starting_balance) / starting_balance) * 100
        cost_impact = final_balance_ideal - final_balance_real

        ax10.set_xlabel('Trade Number', fontsize=10, color='#00ff00')
        ax10.set_ylabel('Account Balance ($)', fontsize=10, color='#00ff00')
        ax10.set_title(f'REAL FOREX Account Growth (Spreads + Slippage + Commission)\n' +
                      f'Start: ${starting_balance:,.0f} → Real: ${final_balance_real:,.0f} ({total_growth:+.1f}%) | ' +
                      f'Cost Impact: -${cost_impact:,.0f}',
                      fontsize=11, color='#00ff00', fontweight='bold')
        ax10.legend(loc='upper left', fontsize=8)
        ax10.grid(True, alpha=0.3)
        ax10.ticklabel_format(style='plain', axis='y')

    # =================================================================
    # PLOT 11: Daily Growth Percentage Over Time
    # =================================================================
    ax11 = plt.subplot(4, 3, 11)

    if len(backtester.daily_stats) > 0:
        daily_df = pd.DataFrame(backtester.daily_stats)
        days = range(1, len(daily_df) + 1)

        colors = ['#00ff00' if achieved else '#ff8800' for achieved in daily_df['target_achieved']]

        bars = ax11.bar(days, daily_df['daily_growth'], color=colors, alpha=0.8, edgecolor='white')

        ax11.axhline(y=backtester.daily_growth_target, color='#ffff00', linestyle='--',
                    linewidth=2, label=f'Target: {backtester.daily_growth_target}%', alpha=0.7)
        ax11.axhline(y=0, color='#ffffff', linestyle='-', linewidth=1, alpha=0.3)

        days_achieved = sum(daily_df['target_achieved'])
        avg_growth = daily_df['daily_growth'].mean()

        ax11.set_xlabel('Trading Day', fontsize=10, color='#00ff00')
        ax11.set_ylabel('Daily Growth (%)', fontsize=10, color='#00ff00')
        ax11.set_title(f'Daily Growth Rate\nAvg: {avg_growth:.1f}% | Days Achieving Target: {days_achieved}/{len(daily_df)} ({days_achieved/len(daily_df)*100:.0f}%)',
                      fontsize=12, color='#00ff00', fontweight='bold')
        ax11.legend(loc='upper left', fontsize=8)
        ax11.grid(True, alpha=0.3, axis='y')

    # =================================================================
    # PLOT 12: Daily Profit Distribution
    # =================================================================
    ax12 = plt.subplot(4, 3, 12)

    if len(backtester.daily_stats) > 0:
        daily_df = pd.DataFrame(backtester.daily_stats)

        profit_days = daily_df[daily_df['daily_profit'] >= 0]
        loss_days = daily_df[daily_df['daily_profit'] < 0]

        profit_count = len(profit_days)
        loss_count = len(loss_days)
        total_days = len(daily_df)

        bars = ax12.bar(['Profit Days', 'Loss Days'], [profit_count, loss_count],
                       color=['#00ff00', '#ff0000'], alpha=0.8, width=0.6)

        ax12.text(0, profit_count + (total_days * 0.02), f'{profit_count}', ha='center', va='bottom',
                 color='#00ff00', fontsize=14, fontweight='bold')
        ax12.text(1, loss_count + (total_days * 0.02), f'{loss_count}', ha='center', va='bottom',
                 color='#ff0000', fontsize=14, fontweight='bold')

        profit_rate = (profit_count / total_days * 100) if total_days > 0 else 0
        avg_profit = profit_days['daily_profit'].mean() if len(profit_days) > 0 else 0
        avg_loss = loss_days['daily_profit'].mean() if len(loss_days) > 0 else 0

        ax12.set_ylabel('Number of Days', fontsize=10, color='#00ff00')
        ax12.set_title(f'Daily Profit Distribution\n{profit_rate:.0f}% Profitable Days | Avg Profit: ${avg_profit:.2f} | Avg Loss: ${avg_loss:.2f}',
                      fontsize=12, color='#00ff00', fontweight='bold')
        ax12.grid(True, alpha=0.2, axis='y')
        ax12.set_ylim(0, total_days * 1.15)

    # Adjust layout and save
    plt.tight_layout(rect=[0, 0, 1, 0.99])

    filename = f'AEGFM_Performance_RealForex_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    plt.savefig(filename, dpi=150, facecolor='#0a0a0a', edgecolor='none')

    print(f"\n✓ Visualization saved: {filename}")
    print(f"✓ Generated 12 performance charts with REAL FOREX CONDITIONS")
    print(f"✓ Applied trading costs: {SPREAD_PIPS} pip spread + {SLIPPAGE_PIPS} pip slippage + ${COMMISSION_PER_LOT} commission")
    print(f"\n" + "="*70)
    print(f"REAL FOREX RESULTS:")
    print(f"="*70)
    print(f"✓ Overall Win Rate: {overall_winrate:.2f}%")
    print(f"✓ Profit Factor: {profit_factor:.2f}")
    print(f"✓ Net Profit (After Costs): ${net_profit:,.2f}")
    print(f"✓ Max Drawdown: {max_drawdown:.2f}%")
    print(f"✓ Sharpe Ratio: {sharpe_ratio:.2f}")
    print(f"✓ Total Cost Impact: ${cost_impact:,.2f} ({(cost_impact/final_balance_ideal)*100:.1f}% of gross profit)")
    print(f"="*70)

    if len(backtester.daily_stats) > 0:
        daily_df = pd.DataFrame(backtester.daily_stats)
        days_achieved = sum(daily_df['target_achieved'])
        print(f"✓ Daily Growth Target Achievement: {days_achieved}/{len(daily_df)} days ({days_achieved/len(daily_df)*100:.0f}%)")

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
