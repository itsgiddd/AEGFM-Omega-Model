#!/usr/bin/env python3
"""
Technical Dashboard Generator for AEGFM-Ω Trading System
Generates comprehensive technical analysis dashboard with advanced metrics.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Rectangle
from datetime import datetime, timedelta
import sys

# Import the backtester
from backtest_aegfm import AEGFMBacktester

def calculate_sharpe_ratio(returns, risk_free_rate=0.02):
    """Calculate Sharpe Ratio"""
    if len(returns) == 0 or returns.std() == 0:
        return 0
    excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
    return np.sqrt(252) * excess_returns.mean() / returns.std()

def calculate_sortino_ratio(returns, risk_free_rate=0.02):
    """Calculate Sortino Ratio (only considers downside deviation)"""
    if len(returns) == 0:
        return 0
    excess_returns = returns - (risk_free_rate / 252)
    downside_returns = returns[returns < 0]
    if len(downside_returns) == 0 or downside_returns.std() == 0:
        return 0
    return np.sqrt(252) * excess_returns.mean() / downside_returns.std()

def calculate_calmar_ratio(returns, max_drawdown):
    """Calculate Calmar Ratio (annual return / max drawdown)"""
    if max_drawdown == 0:
        return 0
    annual_return = returns.mean() * 252
    return annual_return / abs(max_drawdown)

def calculate_max_drawdown(equity_curve):
    """Calculate maximum drawdown"""
    peak = equity_curve.expanding(min_periods=1).max()
    drawdown = (equity_curve - peak) / peak
    return drawdown.min()

def calculate_win_rate_by_time(trades_df):
    """Calculate win rate by hour of day"""
    if 'entry_time' not in trades_df.columns or len(trades_df) == 0:
        return None

    # Simulated entry times based on index
    trades_df['hour'] = trades_df.index % 24
    hourly_stats = trades_df.groupby('hour').agg({
        'result': lambda x: (x == 'WIN').sum() / len(x) * 100 if len(x) > 0 else 0
    })
    return hourly_stats

def create_technical_dashboard(backtester, title, filename):
    """Create comprehensive technical dashboard"""

    if len(backtester.trades) == 0:
        print(f"⚠ No trades to analyze for {title}")
        return

    trades_df = pd.DataFrame(backtester.trades)

    # Calculate returns
    trades_df['returns'] = trades_df['profit'] / trades_df['balance'].shift(1).fillna(10000)
    trades_df['cumulative_returns'] = (1 + trades_df['returns']).cumprod() - 1

    # Create figure with complex layout
    fig = plt.figure(figsize=(24, 16))
    gs = gridspec.GridSpec(4, 3, hspace=0.35, wspace=0.3,
                          height_ratios=[1.2, 1, 1, 0.8])

    # Main title
    fig.suptitle(f'TECHNICAL DASHBOARD: {title}',
                fontsize=22, fontweight='bold', y=0.98)

    # ===== 1. EQUITY CURVE WITH DRAWDOWN =====
    ax1 = fig.add_subplot(gs[0, :])

    equity = trades_df['balance'].values
    peak = pd.Series(equity).expanding(min_periods=1).max()
    drawdown = (equity - peak) / peak * 100

    # Plot equity
    ax1_main = ax1
    ax1_main.plot(range(len(equity)), equity, linewidth=2.5, color='#2E86DE', label='Equity')
    ax1_main.fill_between(range(len(equity)), 10000, equity, alpha=0.3, color='#2E86DE')
    ax1_main.axhline(y=10000, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax1_main.set_ylabel('Equity ($)', fontsize=12, fontweight='bold')
    ax1_main.set_title('Equity Curve & Drawdown', fontsize=14, fontweight='bold', pad=15)
    ax1_main.grid(True, alpha=0.3)
    ax1_main.legend(loc='upper left', fontsize=10)

    # Drawdown on secondary axis
    ax1_dd = ax1_main.twinx()
    ax1_dd.fill_between(range(len(drawdown)), 0, drawdown, alpha=0.4, color='red', label='Drawdown %')
    ax1_dd.set_ylabel('Drawdown (%)', fontsize=12, fontweight='bold', color='red')
    ax1_dd.tick_params(axis='y', labelcolor='red')
    ax1_dd.legend(loc='upper right', fontsize=10)

    ax1_main.set_xlabel('Trade Number', fontsize=12)

    # ===== 2. RISK METRICS PANEL =====
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.axis('off')

    # Calculate advanced metrics
    returns = trades_df['returns'].dropna()
    max_dd = calculate_max_drawdown(pd.Series(equity))
    sharpe = calculate_sharpe_ratio(returns)
    sortino = calculate_sortino_ratio(returns)
    calmar = calculate_calmar_ratio(returns, max_dd)

    total_return = (equity[-1] - 10000) / 10000 * 100
    wins = len(trades_df[trades_df['result'] == 'WIN'])
    losses = len(trades_df[trades_df['result'] == 'LOSS'])
    win_rate = wins / (wins + losses) * 100 if (wins + losses) > 0 else 0

    # Average win/loss
    avg_win = trades_df[trades_df['result'] == 'WIN']['profit'].mean()
    avg_loss = trades_df[trades_df['result'] == 'LOSS']['profit'].mean()
    profit_factor = abs(avg_win * wins / (avg_loss * losses)) if losses > 0 and avg_loss != 0 else float('inf')

    metrics_text = f"""
RISK-ADJUSTED METRICS

Total Return:      {total_return:+.2f}%
Max Drawdown:      {max_dd*100:.2f}%
Sharpe Ratio:      {sharpe:.3f}
Sortino Ratio:     {sortino:.3f}
Calmar Ratio:      {calmar:.3f}

PERFORMANCE METRICS

Win Rate:          {win_rate:.2f}%
Total Trades:      {len(trades_df)}
Wins:              {wins}
Losses:            {losses}

PROFIT METRICS

Avg Win:           ${avg_win:.2f}
Avg Loss:          ${avg_loss:.2f}
Profit Factor:     {profit_factor:.2f}
Expectancy:        ${trades_df['profit'].mean():.2f}
    """

    ax2.text(0.05, 0.95, metrics_text, transform=ax2.transAxes,
            fontsize=10, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3, pad=1))

    # ===== 3. RETURN DISTRIBUTION =====
    ax3 = fig.add_subplot(gs[1, 1])

    returns_pct = trades_df['returns'] * 100
    ax3.hist(returns_pct, bins=30, color='steelblue', alpha=0.7, edgecolor='black')
    ax3.axvline(x=returns_pct.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {returns_pct.mean():.2f}%')
    ax3.axvline(x=0, color='black', linestyle='-', linewidth=1, alpha=0.5)
    ax3.set_xlabel('Return (%)', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Frequency', fontsize=11, fontweight='bold')
    ax3.set_title('Return Distribution', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y')
    ax3.legend(fontsize=9)

    # ===== 4. WIN/LOSS STREAK ANALYSIS =====
    ax4 = fig.add_subplot(gs[1, 2])

    # Calculate streaks
    trades_df['win'] = (trades_df['result'] == 'WIN').astype(int)
    trades_df['streak'] = (trades_df['win'] != trades_df['win'].shift()).cumsum()
    streaks = trades_df.groupby('streak').agg({
        'win': ['first', 'count']
    })
    streaks.columns = ['is_win', 'length']

    win_streaks = streaks[streaks['is_win'] == 1]['length']
    loss_streaks = streaks[streaks['is_win'] == 0]['length']

    max_win_streak = win_streaks.max() if len(win_streaks) > 0 else 0
    max_loss_streak = loss_streaks.max() if len(loss_streaks) > 0 else 0
    avg_win_streak = win_streaks.mean() if len(win_streaks) > 0 else 0
    avg_loss_streak = loss_streaks.mean() if len(loss_streaks) > 0 else 0

    streak_data = [
        ['Max Win Streak', max_win_streak, 'green'],
        ['Avg Win Streak', avg_win_streak, 'lightgreen'],
        ['Max Loss Streak', max_loss_streak, 'red'],
        ['Avg Loss Streak', avg_loss_streak, 'lightcoral']
    ]

    labels = [s[0] for s in streak_data]
    values = [s[1] for s in streak_data]
    colors = [s[2] for s in streak_data]

    bars = ax4.barh(labels, values, color=colors, alpha=0.7, edgecolor='black')
    ax4.set_xlabel('Streak Length', fontsize=11, fontweight='bold')
    ax4.set_title('Win/Loss Streaks', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='x')

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, values)):
        ax4.text(val + 0.1, i, f'{val:.1f}', va='center', fontsize=10, fontweight='bold')

    # ===== 5. CUMULATIVE PROFIT BY DIRECTION =====
    ax5 = fig.add_subplot(gs[2, 0])

    trades_df['cumulative_profit'] = trades_df['profit'].cumsum()
    buy_trades = trades_df[trades_df['direction'] == 'BUY'].copy()
    sell_trades = trades_df[trades_df['direction'] == 'SELL'].copy()

    if len(buy_trades) > 0:
        buy_trades['buy_cumulative'] = buy_trades['profit'].cumsum()
        ax5.plot(buy_trades.index, buy_trades['buy_cumulative'],
                linewidth=2, color='green', marker='o', markersize=3, label='BUY Trades', alpha=0.7)

    if len(sell_trades) > 0:
        sell_trades['sell_cumulative'] = sell_trades['profit'].cumsum()
        ax5.plot(sell_trades.index, sell_trades['sell_cumulative'],
                linewidth=2, color='red', marker='s', markersize=3, label='SELL Trades', alpha=0.7)

    ax5.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5)
    ax5.set_xlabel('Trade Number', fontsize=11, fontweight='bold')
    ax5.set_ylabel('Cumulative Profit ($)', fontsize=11, fontweight='bold')
    ax5.set_title('Cumulative Profit by Direction', fontsize=12, fontweight='bold')
    ax5.grid(True, alpha=0.3)
    ax5.legend(fontsize=10)

    # ===== 6. INTERMEDIATE TP IMPACT =====
    ax6 = fig.add_subplot(gs[2, 1])
    ax6.axis('off')

    if 'intermediate_tp' in trades_df.columns:
        with_intermediate = trades_df[trades_df['intermediate_tp'] == True]
        without_intermediate = trades_df[trades_df['intermediate_tp'] == False]

        int_win_rate = (with_intermediate['result'] == 'WIN').sum() / len(with_intermediate) * 100 if len(with_intermediate) > 0 else 0
        no_int_win_rate = (without_intermediate['result'] == 'WIN').sum() / len(without_intermediate) * 100 if len(without_intermediate) > 0 else 0

        int_avg_profit = with_intermediate['profit'].mean() if len(with_intermediate) > 0 else 0
        no_int_avg_profit = without_intermediate['profit'].mean() if len(without_intermediate) > 0 else 0

        int_text = f"""
INTERMEDIATE TP ANALYSIS

Trades with Intermediate TP:    {len(with_intermediate)}
  • Win Rate:                    {int_win_rate:.2f}%
  • Avg Profit:                  ${int_avg_profit:.2f}
  • Avg Drawdown:                {with_intermediate['max_adverse_move'].mean():.5f}

Trades without Intermediate TP:  {len(without_intermediate)}
  • Win Rate:                    {no_int_win_rate:.2f}%
  • Avg Profit:                  ${no_int_avg_profit:.2f}
  • Avg Drawdown:                {without_intermediate['max_adverse_move'].mean():.5f}

Re-entry Statistics:
  • Total Re-entries:            {trades_df['reentries'].sum():.0f}
  • Avg Re-entries per trade:    {trades_df['reentries'].mean():.2f}

IMPACT:
  • Win Rate Δ:                  {int_win_rate - no_int_win_rate:+.2f}%
  • Avg Profit Δ:                ${int_avg_profit - no_int_avg_profit:+.2f}
        """
    else:
        int_text = "Intermediate TP data not available"

    ax6.text(0.05, 0.95, int_text, transform=ax6.transAxes,
            fontsize=10, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.3, pad=1))

    # ===== 7. ROLLING METRICS =====
    ax7 = fig.add_subplot(gs[2, 2])

    window = min(20, len(trades_df) // 2)
    if window > 5:
        rolling_returns = trades_df['returns'].rolling(window=window).mean() * 100
        rolling_sharpe = trades_df['returns'].rolling(window=window).apply(
            lambda x: calculate_sharpe_ratio(x) if len(x) > 0 else 0
        )

        ax7_1 = ax7
        color = 'tab:blue'
        ax7_1.plot(rolling_returns.index, rolling_returns, color=color, linewidth=2, label='Rolling Return %')
        ax7_1.set_xlabel('Trade Number', fontsize=11, fontweight='bold')
        ax7_1.set_ylabel('Rolling Return (%)', color=color, fontsize=11, fontweight='bold')
        ax7_1.tick_params(axis='y', labelcolor=color)
        ax7_1.grid(True, alpha=0.3)
        ax7_1.legend(loc='upper left', fontsize=9)

        ax7_2 = ax7_1.twinx()
        color = 'tab:red'
        ax7_2.plot(rolling_sharpe.index, rolling_sharpe, color=color, linewidth=2, label='Rolling Sharpe', alpha=0.7)
        ax7_2.set_ylabel('Rolling Sharpe Ratio', color=color, fontsize=11, fontweight='bold')
        ax7_2.tick_params(axis='y', labelcolor=color)
        ax7_2.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.3)
        ax7_2.legend(loc='upper right', fontsize=9)

        ax7_1.set_title(f'Rolling Metrics (Window={window})', fontsize=12, fontweight='bold')
    else:
        ax7.text(0.5, 0.5, 'Insufficient data for rolling metrics',
                ha='center', va='center', transform=ax7.transAxes, fontsize=12)
        ax7.axis('off')

    # ===== 8. PROFIT/LOSS DISTRIBUTION =====
    ax8 = fig.add_subplot(gs[3, 0])

    profit_bins = [-float('inf'), -20, -10, 0, 10, 20, float('inf')]
    profit_labels = ['< -$20', '-$20 to -$10', '-$10 to $0', '$0 to $10', '$10 to $20', '> $20']
    trades_df['profit_bin'] = pd.cut(trades_df['profit'], bins=profit_bins, labels=profit_labels)

    profit_dist = trades_df['profit_bin'].value_counts().sort_index()
    colors_pl = ['darkred', 'red', 'lightcoral', 'lightgreen', 'green', 'darkgreen']

    ax8.bar(range(len(profit_dist)), profit_dist.values, color=colors_pl, alpha=0.7, edgecolor='black')
    ax8.set_xticks(range(len(profit_dist)))
    ax8.set_xticklabels(profit_dist.index, rotation=45, ha='right', fontsize=9)
    ax8.set_ylabel('Count', fontsize=11, fontweight='bold')
    ax8.set_title('Profit/Loss Distribution', fontsize=12, fontweight='bold')
    ax8.grid(True, alpha=0.3, axis='y')

    # ===== 9. WIN RATE BY TRADE NUMBER =====
    ax9 = fig.add_subplot(gs[3, 1])

    bin_size = max(10, len(trades_df) // 10)
    trades_df['trade_bin'] = (trades_df.index // bin_size) * bin_size
    win_rate_by_bin = trades_df.groupby('trade_bin').apply(
        lambda x: (x['result'] == 'WIN').sum() / len(x) * 100 if len(x) > 0 else 0
    )

    ax9.plot(win_rate_by_bin.index, win_rate_by_bin.values, marker='o', linewidth=2, markersize=6, color='purple')
    ax9.axhline(y=win_rate, color='red', linestyle='--', linewidth=2, alpha=0.5, label=f'Overall: {win_rate:.1f}%')
    ax9.set_xlabel('Trade Number', fontsize=11, fontweight='bold')
    ax9.set_ylabel('Win Rate (%)', fontsize=11, fontweight='bold')
    ax9.set_title(f'Win Rate by Trade Group (bins of {bin_size})', fontsize=12, fontweight='bold')
    ax9.grid(True, alpha=0.3)
    ax9.legend(fontsize=9)
    ax9.set_ylim([0, 105])

    # ===== 10. CONFIDENCE VS RESULT =====
    ax10 = fig.add_subplot(gs[3, 2])

    if 'confidence' in trades_df.columns:
        wins_conf = trades_df[trades_df['result'] == 'WIN']['confidence'] * 100
        losses_conf = trades_df[trades_df['result'] == 'LOSS']['confidence'] * 100

        ax10.violinplot([wins_conf, losses_conf], positions=[1, 2],
                       showmeans=True, showmedians=True)
        ax10.set_xticks([1, 2])
        ax10.set_xticklabels(['Wins', 'Losses'], fontsize=11)
        ax10.set_ylabel('Confidence (%)', fontsize=11, fontweight='bold')
        ax10.set_title('Confidence Distribution by Result', fontsize=12, fontweight='bold')
        ax10.grid(True, alpha=0.3, axis='y')

        # Add statistics text
        ax10.text(1, wins_conf.min() - 1, f'μ={wins_conf.mean():.1f}%', ha='center', fontsize=9)
        ax10.text(2, losses_conf.min() - 1, f'μ={losses_conf.mean():.1f}%', ha='center', fontsize=9)
    else:
        ax10.text(0.5, 0.5, 'Confidence data not available',
                ha='center', va='center', transform=ax10.transAxes, fontsize=12)
        ax10.axis('off')

    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"✓ Saved technical dashboard: {filename}")
    plt.close()

def main():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║     TECHNICAL DASHBOARD GENERATOR - AEGFM-Ω TRADING SYSTEM      ║
║            Advanced Analytics & Risk Metrics                     ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    # Set seed for reproducible results
    np.random.seed(42)

    # Run intermediate TP backtest (the superior strategy)
    print("\n" + "="*70)
    print("RUNNING BACKTEST WITH INTERMEDIATE TP...")
    print("="*70)

    backtester = AEGFMBacktester(num_candles=5000, use_intermediate_tp=True)
    backtester.generate_realistic_data()
    backtester.calculate_indicators()
    wins, losses, _ = backtester.run_backtest()

    print(f"\n✓ Backtest completed: {wins} wins, {losses} losses")
    print(f"✓ Win Rate: {wins/(wins+losses)*100:.2f}%")

    # Generate technical dashboard
    print("\n" + "="*70)
    print("GENERATING TECHNICAL DASHBOARD...")
    print("="*70)

    create_technical_dashboard(
        backtester,
        'AEGFM-Ω with Intermediate TP (v4.6)',
        'technical_dashboard_intermediate_tp.png'
    )

    print("\n" + "="*70)
    print("✓✓✓ TECHNICAL DASHBOARD GENERATED SUCCESSFULLY ✓✓✓")
    print("="*70)
    print("\nGenerated file: technical_dashboard_intermediate_tp.png")
    print("\n" + "="*70)

if __name__ == "__main__":
    try:
        import matplotlib
        main()
    except ImportError as e:
        print(f"\n✗ ERROR: Missing required package: {e}")
        print("Please install: pip3 install matplotlib numpy pandas")
        sys.exit(1)
