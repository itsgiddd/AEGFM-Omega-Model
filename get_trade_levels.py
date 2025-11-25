#!/usr/bin/env python3
"""
GET TRADE LEVELS 🎯
Calculates precise TP/SL for any verified trade.
"""

import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import oandapyV20
import oandapyV20.endpoints.instruments as instruments

load_dotenv()
client = oandapyV20.API(access_token=os.getenv('OANDA_API_KEY'), environment='practice')

def get_levels():
    print("\n" + "="*60)
    print("🎯 TRADE LEVEL CALCULATOR")
    print("="*60)
    
    pair = input("Enter Pair (e.g., AUD_CAD): ").strip().upper()
    tf = input("Enter Timeframe (e.g., M15): ").strip().upper()
    window = 50
    
    print(f"\nFetching live data for {pair} ({tf})...")
    try:
        params = {"count": window + 10, "granularity": tf, "price": "M"}
        r = instruments.InstrumentsCandles(instrument=pair, params=params)
        client.request(r)
        closes = pd.Series([float(c['mid']['c']) for c in r.response['candles']])
        
        mean = closes.rolling(window).mean().iloc[-1]
        std = closes.rolling(window).std().iloc[-1]
        current_price = closes.iloc[-1]
        z_score = (current_price - mean) / std
        
        print("-" * 60)
        print(f"Current Price: {current_price:.5f}")
        print(f"Z-Score:       {z_score:.4f}")
        
        # Determine Action
        if z_score > 0:
            action = "SELL"
            tp = mean
            sl = current_price + (2.0 * std)
            tp_pips = (current_price - tp) * 10000
            sl_pips = (sl - current_price) * 10000
        else:
            action = "BUY"
            tp = mean
            sl = current_price - (2.0 * std)
            tp_pips = (tp - current_price) * 10000
            sl_pips = (current_price - sl) * 10000
            
        print(f"Action:        {action}")
        print("-" * 60)
        print(f"✅ TAKE PROFIT: {tp:.5f} ({tp_pips:.1f} Pips)")
        print(f"🛑 STOP LOSS:   {sl:.5f} ({sl_pips:.1f} Pips)")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Check your spelling or API connection.")

if __name__ == "__main__":
    get_levels()
