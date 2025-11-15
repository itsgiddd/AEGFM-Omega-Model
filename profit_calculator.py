#!/usr/bin/env python3
"""
AEGFM-Ω Profit Calculator
Calculate realistic profits based on backtest performance
"""

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# System Performance (from v4.3 backtest)
WIN_RATE = 0.90  # 90% target win rate
RISK_REWARD = 0.75 / 2.0  # Risk 2.0 ATR to make 0.75 ATR = 0.375
TRADES_PER_DAY = 19  # Based on 10,000 trades over 520 days

# Risk per trade (% of account)
RISK_PERCENT = 0.02  # 2% risk per trade

def calculate_expectancy():
    """Calculate expected profit per trade in R (risk units)"""
    win_amount = RISK_REWARD  # Win 0.375R
    loss_amount = -1.0  # Lose 1R

    expectancy = (WIN_RATE * win_amount) + ((1 - WIN_RATE) * loss_amount)
    return expectancy

def calculate_simple_profit(starting_capital, num_trades):
    """Calculate profit without compounding (fixed position size)"""
    risk_per_trade = starting_capital * RISK_PERCENT

    # Calculate wins and losses
    expected_wins = int(num_trades * WIN_RATE)
    expected_losses = num_trades - expected_wins

    # Calculate profit
    win_profit = expected_wins * (risk_per_trade * RISK_REWARD)
    loss_amount = expected_losses * risk_per_trade

    net_profit = win_profit - loss_amount
    final_balance = starting_capital + net_profit

    return {
        'trades': num_trades,
        'wins': expected_wins,
        'losses': expected_losses,
        'win_profit': win_profit,
        'loss_amount': loss_amount,
        'net_profit': net_profit,
        'final_balance': final_balance,
        'roi': (net_profit / starting_capital) * 100
    }

def calculate_compound_profit(starting_capital, num_trades, max_risk_per_trade=1000):
    """Calculate profit WITH compounding (position size grows with account)"""
    balance = starting_capital
    balance_history = [balance]

    expectancy = calculate_expectancy()

    for trade in range(num_trades):
        # Calculate position size (2% of current balance)
        risk_amount = min(balance * RISK_PERCENT, max_risk_per_trade)

        # Simulate trade outcome based on expectancy
        if np.random.random() < WIN_RATE:
            # Win
            profit = risk_amount * RISK_REWARD
            balance += profit
        else:
            # Loss
            balance -= risk_amount

        balance_history.append(balance)

        # Stop if account blows up
        if balance <= starting_capital * 0.5:
            print(f"⚠ WARNING: Large drawdown at trade {trade}")
            break

    return balance, balance_history

def simulate_multiple_runs(starting_capital, num_trades, runs=100):
    """Simulate multiple runs to get realistic range of outcomes"""
    final_balances = []

    for _ in range(runs):
        final_balance, _ = calculate_compound_profit(starting_capital, num_trades)
        final_balances.append(final_balance)

    return {
        'mean': np.mean(final_balances),
        'median': np.median(final_balances),
        'min': np.min(final_balances),
        'max': np.max(final_balances),
        'std': np.std(final_balances)
    }

# ============================================================
# MAIN ANALYSIS
# ============================================================

print("="*70)
print("AEGFM-Ω PROFIT CALCULATOR")
print("="*70)
print(f"System Performance: {WIN_RATE*100:.2f}% Win Rate")
print(f"Risk:Reward Ratio: 1 : {RISK_REWARD:.3f}")
print(f"Expected Trades: ~{TRADES_PER_DAY} per day")
print(f"Risk Per Trade: {RISK_PERCENT*100:.1f}% of account")

expectancy = calculate_expectancy()
print(f"\nExpected Profit: {expectancy:.4f}R per trade")
if expectancy > 0:
    print("✓ POSITIVE EXPECTANCY - System is profitable!")
else:
    print("✗ NEGATIVE EXPECTANCY - System loses money!")

# ============================================================
# SCENARIO 1: $1000 Account (No Compounding)
# ============================================================

print("\n" + "="*70)
print("SCENARIO 1: $1000 Account (NO COMPOUNDING - Fixed Position Size)")
print("="*70)

scenarios_1000 = [
    ("1 Week", 133),
    ("1 Month", 570),
    ("3 Months", 1710),
    ("6 Months", 3420),
    ("1 Year", 6935)
]

for period, trades in scenarios_1000:
    result = calculate_simple_profit(1000, trades)
    print(f"\n{period} ({trades:,} trades):")
    print(f"  Wins: {result['wins']:,} | Losses: {result['losses']:,}")
    print(f"  Win Profit: ${result['win_profit']:.2f}")
    print(f"  Loss Amount: ${result['loss_amount']:.2f}")
    print(f"  Net Profit: ${result['net_profit']:.2f}")
    print(f"  Final Balance: ${result['final_balance']:.2f}")
    print(f"  ROI: {result['roi']:.1f}%")

# ============================================================
# SCENARIO 2: $1000 Account (WITH Compounding)
# ============================================================

print("\n" + "="*70)
print("SCENARIO 2: $1000 Account (WITH COMPOUNDING - Position Grows)")
print("="*70)
print("⚠ Note: Compounding dramatically increases profits BUT also risk!")

for period, trades in scenarios_1000:
    stats = simulate_multiple_runs(1000, trades, runs=100)
    print(f"\n{period} ({trades:,} trades) - 100 simulations:")
    print(f"  Average Ending Balance: ${stats['mean']:.2f}")
    print(f"  Median: ${stats['median']:.2f}")
    print(f"  Best Case: ${stats['max']:.2f}")
    print(f"  Worst Case: ${stats['min']:.2f}")
    print(f"  Std Dev: ${stats['std']:.2f}")

# ============================================================
# SCENARIO 3: Different Account Sizes (1 Month, No Compounding)
# ============================================================

print("\n" + "="*70)
print("SCENARIO 3: Different Account Sizes (1 Month, NO COMPOUNDING)")
print("="*70)

account_sizes = [500, 1000, 2000, 5000, 10000, 25000, 50000]
trades_1_month = 570

for account in account_sizes:
    result = calculate_simple_profit(account, trades_1_month)
    print(f"\n${account:,} Account:")
    print(f"  Risk per trade: ${account * RISK_PERCENT:.2f}")
    print(f"  Net Profit: ${result['net_profit']:.2f}")
    print(f"  Final Balance: ${result['final_balance']:.2f}")
    print(f"  ROI: {result['roi']:.1f}%")

# ============================================================
# VISUALIZATION
# ============================================================

print("\n" + "="*70)
print("Generating visualization...")

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('AEGFM-Ω Profit Projections', fontsize=16, fontweight='bold')

# Plot 1: Account Growth Over Time (No Compounding)
ax1 = axes[0, 0]
starting_capital = 1000
trades_per_period = [0, 133, 570, 1710, 3420, 6935]
periods = ['Start', '1 Week', '1 Month', '3 Months', '6 Months', '1 Year']
balances = [starting_capital]

for trades in trades_per_period[1:]:
    result = calculate_simple_profit(starting_capital, trades)
    balances.append(result['final_balance'])

ax1.plot(periods, balances, marker='o', linewidth=3, markersize=10, color='#2ecc71')
ax1.fill_between(range(len(periods)), starting_capital, balances, alpha=0.3, color='#2ecc71')
ax1.axhline(y=starting_capital, color='gray', linestyle='--', alpha=0.5)
ax1.set_title('Account Growth: $1000 (No Compounding)', fontweight='bold')
ax1.set_ylabel('Account Balance ($)', fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.set_ylim(bottom=0)

# Add value labels
for i, (period, balance) in enumerate(zip(periods, balances)):
    ax1.text(i, balance + 200, f'${balance:.0f}', ha='center', fontweight='bold')

# Plot 2: Profit by Account Size (1 Month)
ax2 = axes[0, 1]
account_sizes = [500, 1000, 2000, 5000, 10000, 25000, 50000]
profits = []

for account in account_sizes:
    result = calculate_simple_profit(account, 570)
    profits.append(result['net_profit'])

ax2.bar(range(len(account_sizes)), profits, color='#3498db', alpha=0.8, edgecolor='black')
ax2.set_title('1-Month Profit by Account Size (No Compounding)', fontweight='bold')
ax2.set_ylabel('Net Profit ($)', fontweight='bold')
ax2.set_xticks(range(len(account_sizes)))
ax2.set_xticklabels([f'${s/1000:.0f}K' if s >= 1000 else f'${s}' for s in account_sizes], rotation=45)
ax2.grid(True, alpha=0.3, axis='y')

# Add value labels
for i, profit in enumerate(profits):
    ax2.text(i, profit + max(profits)*0.02, f'${profit:.0f}', ha='center', fontweight='bold', fontsize=9)

# Plot 3: Compounding Simulation (100 runs)
ax3 = axes[1, 0]
starting_capital = 1000
num_trades = 570  # 1 month

# Run 20 simulations for visualization
for run in range(20):
    _, history = calculate_compound_profit(starting_capital, num_trades)
    ax3.plot(history, alpha=0.3, color='#e74c3c', linewidth=1)

# Plot average
avg_balance, avg_history = calculate_compound_profit(starting_capital, num_trades)
ax3.plot(avg_history, color='#c0392b', linewidth=3, label=f'Sample Run (${avg_balance:.0f})')

ax3.axhline(y=starting_capital, color='gray', linestyle='--', alpha=0.5, label='Starting Capital')
ax3.set_title('Compounding Effect: $1000 over 1 Month (20 simulations)', fontweight='bold')
ax3.set_xlabel('Trade Number', fontweight='bold')
ax3.set_ylabel('Account Balance ($)', fontweight='bold')
ax3.legend(loc='upper left')
ax3.grid(True, alpha=0.3)

# Plot 4: ROI Comparison
ax4 = axes[1, 1]
periods_roi = ['1 Week', '1 Month', '3 Months', '6 Months', '1 Year']
trades_roi = [133, 570, 1710, 3420, 6935]
rois = []

for trades in trades_roi:
    result = calculate_simple_profit(1000, trades)
    rois.append(result['roi'])

colors = ['#27ae60' if roi > 0 else '#e74c3c' for roi in rois]
bars = ax4.bar(periods_roi, rois, color=colors, alpha=0.8, edgecolor='black')
ax4.set_title('ROI Over Time: $1000 Account (No Compounding)', fontweight='bold')
ax4.set_ylabel('Return on Investment (%)', fontweight='bold')
ax4.grid(True, alpha=0.3, axis='y')
ax4.axhline(y=0, color='black', linewidth=1)

# Add value labels
for bar, roi in zip(bars, rois):
    height = bar.get_height()
    ax4.text(bar.get_x() + bar.get_width()/2., height + (max(rois)*0.02),
             f'{roi:.1f}%', ha='center', fontweight='bold')

plt.tight_layout()

# Save figure
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f'AEGFM_Profit_Analysis_{timestamp}.png'
plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
print(f"✓ Visualization saved: {filename}")

# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "="*70)
print("KEY TAKEAWAYS")
print("="*70)
print("\n1. POSITIVE EXPECTANCY:")
print(f"   Every trade expects to make {expectancy:.4f}R profit")
print(f"   With 2% risk, that's ~{expectancy * RISK_PERCENT * 100:.3f}% account growth per trade")

print("\n2. $1000 ACCOUNT (Realistic Scenario):")
result_1month = calculate_simple_profit(1000, 570)
print(f"   1 Month: ${result_1month['net_profit']:.2f} profit ({result_1month['roi']:.1f}% ROI)")
result_1year = calculate_simple_profit(1000, 6935)
print(f"   1 Year: ${result_1year['net_profit']:.2f} profit ({result_1year['roi']:.1f}% ROI)")

print("\n3. COMPOUNDING WARNING:")
print("   ⚠ Compounding can 10x-100x your profits BUT:")
print("   - Requires perfect execution")
print("   - No account for slippage/spread")
print("   - Assumes unlimited liquidity")
print("   - Psychological pressure increases dramatically")

print("\n4. REALISTIC EXPECTATIONS:")
print(f"   With {WIN_RATE*100:.2f}% win rate, expect:")
print("   - Winning streaks of 10-20 trades")
print("   - Losing streaks of 2-3 trades")
print("   - Consistent but not explosive growth (without compounding)")
print("   - Potential for explosive growth (with compounding + risk)")

print("\n" + "="*70)
print("RECOMMENDATION:")
print("="*70)
print("Start with NO COMPOUNDING until you prove the system works for you.")
print("Then gradually increase position size as your account grows.")
print("Never risk more than 2% per trade to survive losing streaks!")
print("="*70)
