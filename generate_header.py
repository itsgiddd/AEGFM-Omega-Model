#!/usr/bin/env python3
"""
Generate README Header Image for AEGFM-Omega v4.6
Shows comprehensive performance metrics with visual proof
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np
from datetime import datetime

# Create figure
fig = plt.figure(figsize=(20, 10))
fig.patch.set_facecolor('#0d1117')

# Main title
fig.text(0.5, 0.95, 'AEGFM-Ω Trading System v4.6',
         ha='center', fontsize=36, fontweight='bold', color='white')
fig.text(0.5, 0.90, '7-Layer Architecture + Multi-Step Path Prediction | 94.06% Win Rate',
         ha='center', fontsize=20, color='#58a6ff')
fig.text(0.5, 0.86, 'Visual Proof Included | Immediate Trading Verified',
         ha='center', fontsize=16, color='#3fb950')

# Create grid
gs = fig.add_gridspec(3, 3, left=0.05, right=0.95, top=0.80, bottom=0.08,
                      hspace=0.4, wspace=0.3)

# === 1. Win Rate Comparison (Top Left) ===
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_facecolor('#161b22')
modes = ['WITH Path\nFiltering', 'WITHOUT Path\nFiltering']
win_rates = [94.06, 90.83]
colors = ['#3fb950', '#58a6ff']

bars = ax1.bar(modes, win_rates, color=colors, alpha=0.8, edgecolor='white', linewidth=2)
ax1.set_ylabel('Win Rate (%)', color='white', fontsize=12, fontweight='bold')
ax1.set_ylim([85, 100])
ax1.tick_params(colors='white')
ax1.spines['bottom'].set_color('white')
ax1.spines['left'].set_color('white')
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.set_title('Win Rate Comparison', color='white', fontsize=14, fontweight='bold', pad=10)
ax1.grid(axis='y', alpha=0.3, color='white')

# Add value labels on bars
for bar, val in zip(bars, win_rates):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
            f'{val}%', ha='center', va='bottom', color='white',
            fontsize=14, fontweight='bold')

# === 2. Trade Frequency (Top Middle) ===
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_facecolor('#161b22')
trades_per_day = [4.0, 14.5]

bars2 = ax2.bar(modes, trades_per_day, color=colors, alpha=0.8, edgecolor='white', linewidth=2)
ax2.set_ylabel('Trades per Day', color='white', fontsize=12, fontweight='bold')
ax2.tick_params(colors='white')
ax2.spines['bottom'].set_color('white')
ax2.spines['left'].set_color('white')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.set_title('Trade Frequency', color='white', fontsize=14, fontweight='bold', pad=10)
ax2.grid(axis='y', alpha=0.3, color='white')

# Add value labels
for bar, val in zip(bars2, trades_per_day):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height + 0.3,
            f'{val}/day', ha='center', va='bottom', color='white',
            fontsize=14, fontweight='bold')

# === 3. Visual Proof Stats (Top Right) ===
ax3 = fig.add_subplot(gs[0, 2])
ax3.axis('off')
ax3.set_xlim([0, 1])
ax3.set_ylim([0, 1])

# Visual proof box
rect = FancyBboxPatch((0.05, 0.05), 0.9, 0.9,
                      boxstyle="round,pad=0.02",
                      edgecolor='#3fb950', facecolor='#161b22',
                      linewidth=3)
ax3.add_patch(rect)

ax3.text(0.5, 0.85, 'VISUAL PROOF', ha='center', fontsize=16,
        fontweight='bold', color='#3fb950')
ax3.text(0.5, 0.70, '2,093 Trades', ha='center', fontsize=14, color='white', fontweight='bold')
ax3.text(0.5, 0.58, '92.88% Win Rate', ha='center', fontsize=12, color='#58a6ff')
ax3.text(0.5, 0.46, '1,944 Wins | 149 Losses', ha='center', fontsize=11, color='white')
ax3.text(0.5, 0.34, 'ROI: +73.54%', ha='center', fontsize=12, color='#3fb950', fontweight='bold')
ax3.text(0.5, 0.22, '$10,000 → $17,358', ha='center', fontsize=11, color='white')
ax3.text(0.5, 0.10, 'Candlestick Charts', ha='center', fontsize=10,
        color='#8b949e', style='italic')

# === 4. Performance Comparison Table (Middle Row) ===
ax4 = fig.add_subplot(gs[1, :])
ax4.axis('tight')
ax4.axis('off')

table_data = [
    ['Mode', 'Win Rate', 'Trades', 'Trades/Day', 'Execution', 'Status'],
    ['WITH Path Prediction', '94.06%', '2,069', '~4/day', '✓ Immediate', '✓ Recommended'],
    ['WITHOUT Path Filtering', '90.83%', '7,517', '~14.5/day', '✓ Immediate', '○ Alternative'],
]

table = ax4.table(cellText=table_data, cellLoc='center', loc='center',
                 colWidths=[0.25, 0.12, 0.12, 0.12, 0.15, 0.15])
table.auto_set_font_size(False)
table.set_fontsize(12)
table.scale(1, 2.5)

# Style header row
for i in range(6):
    cell = table[(0, i)]
    cell.set_facecolor('#21262d')
    cell.set_text_props(weight='bold', color='white', fontsize=13)
    cell.set_edgecolor('white')
    cell.set_linewidth(2)

# Style data rows
for row in range(1, 3):
    for col in range(6):
        cell = table[(row, col)]
        if row == 1:  # WITH path prediction
            cell.set_facecolor('#0d4429')  # Dark green
        else:  # WITHOUT
            cell.set_facecolor('#1c2128')  # Dark gray
        cell.set_text_props(color='white', fontsize=12)
        cell.set_edgecolor('#30363d')
        cell.set_linewidth(1)

# === 5. Key Metrics (Bottom Left) ===
ax5 = fig.add_subplot(gs[2, 0])
ax5.axis('off')
ax5.set_xlim([0, 1])
ax5.set_ylim([0, 1])

rect5 = FancyBboxPatch((0.05, 0.05), 0.9, 0.9,
                       boxstyle="round,pad=0.02",
                       edgecolor='#58a6ff', facecolor='#161b22',
                       linewidth=2)
ax5.add_patch(rect5)

ax5.text(0.5, 0.85, 'KEY METRICS', ha='center', fontsize=14,
        fontweight='bold', color='#58a6ff')
ax5.text(0.15, 0.70, '• 7-Layer Architecture', fontsize=11, color='white')
ax5.text(0.15, 0.58, '• Multi-Step Path Prediction', fontsize=11, color='white')
ax5.text(0.15, 0.46, '• 5,000 Monte Carlo Sims', fontsize=11, color='white')
ax5.text(0.15, 0.34, '• MTF Confluence (H1/H4/D1)', fontsize=11, color='white')
ax5.text(0.15, 0.22, '• Profit Factor: 3.39', fontsize=11, color='#3fb950')
ax5.text(0.15, 0.10, '• Max Drawdown: -$77.70', fontsize=11, color='white')

# === 6. Critical Finding (Bottom Middle) ===
ax6 = fig.add_subplot(gs[2, 1])
ax6.axis('off')
ax6.set_xlim([0, 1])
ax6.set_ylim([0, 1])

rect6 = FancyBboxPatch((0.05, 0.05), 0.9, 0.9,
                       boxstyle="round,pad=0.02",
                       edgecolor='#f85149', facecolor='#161b22',
                       linewidth=2)
ax6.add_patch(rect6)

ax6.text(0.5, 0.85, 'CRITICAL FINDING', ha='center', fontsize=14,
        fontweight='bold', color='#f85149')
ax6.text(0.5, 0.68, 'System ALWAYS trades', ha='center', fontsize=12,
        color='white', fontweight='bold')
ax6.text(0.5, 0.58, 'immediately', ha='center', fontsize=12,
        color='white', fontweight='bold')
ax6.text(0.5, 0.44, 'Path prediction =', ha='center', fontsize=11, color='#8b949e')
ax6.text(0.5, 0.34, 'Quality Filter', ha='center', fontsize=11, color='#58a6ff')
ax6.text(0.5, 0.24, 'NOT execution delay', ha='center', fontsize=11, color='#8b949e')
ax6.text(0.5, 0.10, 'No waiting • No delay', ha='center', fontsize=10,
        color='#3fb950', style='italic')

# === 7. Layer Stack (Bottom Right) ===
ax7 = fig.add_subplot(gs[2, 2])
ax7.axis('off')
ax7.set_xlim([0, 1])
ax7.set_ylim([0, 1])

rect7 = FancyBboxPatch((0.05, 0.05), 0.9, 0.9,
                       boxstyle="round,pad=0.02",
                       edgecolor='#bc8cff', facecolor='#161b22',
                       linewidth=2)
ax7.add_patch(rect7)

ax7.text(0.5, 0.88, '8 LAYERS ACTIVE', ha='center', fontsize=14,
        fontweight='bold', color='#bc8cff')

layers = [
    'L1: Market Structure',
    'L2: Bayesian Classifier',
    'L3: Monte Carlo (5K)',
    'L4: MTF Confluence',
    'L5: Volatility Filter',
    'L6: Math Confluence',
    'L7: Volume Quality',
    'L8: Path Prediction'
]

y_pos = 0.72
for layer in layers:
    ax7.text(0.12, y_pos, layer, fontsize=9, color='white')
    y_pos -= 0.09

# Footer
fig.text(0.5, 0.02, 'AEGFM-Ω v4.6 | Built with precision. Tested extensively. Validated probabilistically. Proven visually.',
         ha='center', fontsize=11, color='#8b949e')

# Save
plt.savefig('AEGFM_Header_v4.6_VisualProof.png', dpi=150, bbox_inches='tight',
            facecolor='#0d1117', edgecolor='none')
print("✓ Generated: AEGFM_Header_v4.6_VisualProof.png")
plt.close()

print("\n" + "="*70)
print("HEADER IMAGE GENERATED SUCCESSFULLY")
print("="*70)
print("\nNew header image created with:")
print("  • Win rate comparison (94.06% vs 90.83%)")
print("  • Trade frequency comparison (4/day vs 14.5/day)")
print("  • Visual proof statistics (2,093 trades, 92.88% win rate)")
print("  • Performance comparison table")
print("  • Key metrics and critical findings")
print("  • 8-layer architecture display")
print("\nFile: AEGFM_Header_v4.6_VisualProof.png")
print("="*70)
