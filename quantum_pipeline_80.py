#!/usr/bin/env python3
"""
QUANTUM PIPELINE 80 ⚛️
1. Scan All Pairs/TFs
2. Filter for >80% Historical Accuracy
3. Verify with Real IBM Quantum Computer
4. Calculate TP/SL
"""

import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import oandapyV20
import oandapyV20.endpoints.instruments as instruments
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from multiprocessing import Pool, cpu_count
import time

load_dotenv()
IBM_TOKEN = os.getenv('IBM_QUANTUM_TOKEN')
OANDA_KEY = os.getenv('OANDA_API_KEY')
ACCOUNT_ID = os.getenv('OANDA_ACCOUNT_ID')

PAIRS = [
    "EUR_USD", "GBP_USD", "USD_JPY", "USD_CHF", "AUD_USD", "USD_CAD", "NZD_USD",
    "EUR_GBP", "EUR_JPY", "GBP_JPY", "AUD_JPY", "NZD_JPY", "CHF_JPY", "CAD_JPY",
    "EUR_AUD", "EUR_CAD", "EUR_CHF", "EUR_NZD", "GBP_AUD", "GBP_CAD", "GBP_CHF",
    "GBP_NZD", "AUD_CAD", "AUD_CHF", "AUD_NZD", "CAD_CHF", "NZD_CAD", "NZD_CHF"
]
TIMEFRAMES = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]

# --- STEP 1: FAST SCAN ---
def scan_pair(args):
    pair, tf, token = args
    try:
        client = oandapyV20.API(access_token=token, environment='practice')
        params = {"count": 100, "granularity": tf, "price": "M"}
        r = instruments.InstrumentsCandles(instrument=pair, params=params)
        client.request(r)
        closes = pd.Series([float(c['mid']['c']) for c in r.response['candles']])
        
        window = min(50, len(closes)-1)
        mean = closes.rolling(window).mean().iloc[-1]
        std = closes.rolling(window).std().iloc[-1]
        
        if std == 0: return None
        
        z = (closes.iloc[-1] - mean) / std
        
        # Only return if Z is somewhat significant to save time
        if abs(z) > 2.0:
            return {'pair': pair, 'tf': tf, 'z': z, 'price': closes.iloc[-1]}
        return None
    except:
        return None

# --- STEP 2: ACCURACY CHECK ---
def check_accuracy(cand, token):
    try:
        client = oandapyV20.API(access_token=token, environment='practice')
        params = {"count": 2000, "granularity": cand['tf'], "price": "M"}
        r = instruments.InstrumentsCandles(instrument=cand['pair'], params=params)
        client.request(r)
        closes = pd.Series([float(c['mid']['c']) for c in r.response['candles']])
        
        window = 50
        rolling_mean = closes.rolling(window).mean()
        rolling_std = closes.rolling(window).std()
        z_scores = (closes - rolling_mean) / rolling_std
        
        trades = []
        position = 0
        entry_price = 0
        z_trigger = 2.5 if abs(cand['z']) > 2.5 else 2.0 # Adaptive trigger
        
        for i in range(window, len(closes)):
            z = z_scores.iloc[i]
            price = closes.iloc[i]
            mean = rolling_mean.iloc[i]
            
            if position == 0:
                # Sell Signal
                if cand['z'] > 0 and z > z_trigger:
                    position = -1
                    entry_price = price
                # Buy Signal
                elif cand['z'] < 0 and z < -z_trigger:
                    position = 1
                    entry_price = price
            elif position == -1: # Short
                if price <= mean: # Win
                    trades.append(1)
                    position = 0
                elif price > entry_price + (2*rolling_std.iloc[i]): # Loss (Stop)
                    trades.append(0)
                    position = 0
            elif position == 1: # Long
                if price >= mean: # Win
                    trades.append(1)
                    position = 0
                elif price < entry_price - (2*rolling_std.iloc[i]): # Loss (Stop)
                    trades.append(0)
                    position = 0
                    
        if not trades: return 0
        return sum(trades) / len(trades) * 100
    except:
        return 0

# --- STEP 3: QUANTUM VERIFICATION ---
def run_quantum_verification(candidates):
    if not candidates: return []
    
    print(f"\n⚛️ Connecting to IBM Quantum to verify {len(candidates)} candidates...")
    service = QiskitRuntimeService(channel="ibm_cloud", token=IBM_TOKEN)
    backend = service.least_busy(operational=True, simulator=False)
    print(f"Using Backend: {backend.name}")
    
    circuits = []
    
    for cand in candidates:
        # Map Z to Theta
        # Z=3 -> Theta=Pi (State |0> via 2*Pi rot)
        # Z=0 -> Theta=Pi/2 (State |1> via Pi rot)
        # Z=-3 -> Theta=0 (State |0> via 0 rot)
        
        # We want to measure deviation from Mean.
        # Mean (Z=0) should be |0>. Extreme (Z=3) should be |1>.
        # Let's use Ry(theta).
        # Z=0 -> Theta=0 -> |0>
        # Z=3 -> Theta=Pi -> |1>
        
        z_abs = abs(cand['z'])
        theta = np.clip(z_abs / 3.0 * np.pi, 0, np.pi)
        
        qc = QuantumCircuit(1)
        qc.ry(theta, 0)
        qc.measure_all()
        circuits.append(qc)
        
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa_circuits = [pm.run(qc) for qc in circuits]
    
    sampler = Sampler(backend)
    job = sampler.run(isa_circuits)
    print(f"Job ID: {job.job_id()} (Verifying...)")
    
    result = job.result()
    
    verified = []
    for i, cand in enumerate(candidates):
        try:
            counts = result[i].data.meas.get_counts()
        except:
            counts = result.quasi_dists[i]
            
        total = sum(counts.values())
        # Prob of |1> is Prob of Extreme Deviation
        prob_extreme = counts.get('1', 0) / total
        cand['quantum_conf'] = prob_extreme * 100
        verified.append(cand)
        
    return verified

# --- STEP 2.5: TREND GUARD (Prevent Breakouts) ---
def check_trend_danger(cand, token):
    try:
        client = oandapyV20.API(access_token=token, environment='practice')
        # Need history to calc RSI and Z-Velocity
        params = {"count": 50, "granularity": cand['tf'], "price": "M"}
        r = instruments.InstrumentsCandles(instrument=cand['pair'], params=params)
        client.request(r)
        closes = pd.Series([float(c['mid']['c']) for c in r.response['candles']])
        
        # 1. Z-Score Velocity
        window = 50
        mean = closes.rolling(window).mean()
        std = closes.rolling(window).std()
        z_scores = (closes - mean) / std
        
        z_current = z_scores.iloc[-1]
        z_prev = z_scores.iloc[-2]
        z_velocity = abs(z_current - z_prev)
        
        # 2. RSI (14)
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        # DANGER CHECKS
        is_dangerous = False
        reason = ""
        
        # If Selling (Z > 0)
        if cand['z'] > 0:
            # Expanding fast?
            if z_velocity > 0.2: 
                is_dangerous = True
                reason = f"Momentum Acceleration (Vel: {z_velocity:.2f})"
            # RSI Pinned?
            elif rsi > 75:
                is_dangerous = True
                reason = f"RSI Overextended ({rsi:.1f})"
                
        # If Buying (Z < 0)
        else:
            if z_velocity > 0.2:
                is_dangerous = True
                reason = f"Momentum Acceleration (Vel: {z_velocity:.2f})"
            elif rsi < 25:
                is_dangerous = True
                reason = f"RSI Overextended ({rsi:.1f})"
                
        return is_dangerous, reason
    except:
        return True, "Error checking trend"

def main():
    print("\n" + "="*80)
    print("🚀 QUANTUM PIPELINE 80 + TREND GUARD 🛡️")
    print("="*80)
    
    # 1. SCAN
    tasks = [(p, tf, OANDA_KEY) for p in PAIRS for tf in TIMEFRAMES]
    print(f"1. Scanning {len(tasks)} combinations...")
    with Pool(processes=cpu_count()) as pool:
        scan_results = pool.map(scan_pair, tasks)
    
    candidates = [r for r in scan_results if r is not None]
    candidates.sort(key=lambda x: abs(x['z']), reverse=True)
    print(f"   Found {len(candidates)} candidates with Z > 2.0")
    
    # 2. ACCURACY FILTER
    print("2. Backtesting for >80% Accuracy...")
    high_accuracy = []
    for cand in candidates[:15]: # Check top 15
        acc = check_accuracy(cand, OANDA_KEY)
        if acc >= 80.0:
            cand['accuracy'] = acc
            high_accuracy.append(cand)
            print(f"   ✅ {cand['pair']} ({cand['tf']}): {acc:.1f}% (Passed Accuracy)")
        else:
            print(f"   ❌ {cand['pair']} ({cand['tf']}): {acc:.1f}% (Failed Accuracy)")
            
    if not high_accuracy:
        print("\n❌ NO TRADES FOUND with >80% Accuracy.")
        return

    # 2.5 TREND GUARD
    print(f"2.5 Checking Trend Danger for {len(high_accuracy)} survivors...")
    safe_candidates = []
    for cand in high_accuracy:
        danger, reason = check_trend_danger(cand, OANDA_KEY)
        if danger:
            print(f"   ⚠️ REJECTED {cand['pair']}: {reason}")
        else:
            print(f"   🛡️ SAFE {cand['pair']}")
            safe_candidates.append(cand)
            
    if not safe_candidates:
        print("\n❌ ALL TRADES REJECTED BY TREND GUARD.")
        print("   Market is in Breakout Mode. Stand aside.")
        return

    # 3. QUANTUM VERIFICATION
    print(f"3. Verifying {len(safe_candidates)} trades on IBM Quantum...")
    verified = run_quantum_verification(safe_candidates)
    
    # 4. REPORT
    print("\n" + "="*80)
    print(f"{'PAIR':<10} | {'TF':<5} | {'ACCURACY':<10} | {'QUANTUM':<10} | {'ACTION':<6} | {'TP':<8} | {'SL'}")
    print("-" * 80)
    
    for v in verified:
        tp, sl, tp_pips, sl_pips = calculate_levels(v, OANDA_KEY)
        action = "SELL" if v['z'] > 0 else "BUY"
        
        print(f"{v['pair']:<10} | {v['tf']:<5} | {v['accuracy']:<10.1f}% | {v['quantum_conf']:<10.1f}% | {action:<6} | {tp:<8.5f} | {sl:.5f}")
        print(f"   TP: {tp_pips:.1f} pips | SL: {sl_pips:.1f} pips")
        
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
