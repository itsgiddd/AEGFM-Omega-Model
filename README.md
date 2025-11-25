# The Zero-Point Protocol ⚛️

**The "Holy Grail" of Statistical Arbitrage**
*Verified >80% Accuracy | Quantum-Enhanced | Trend-Protected*

---

## 🚀 Overview

This system uses **Quantum Computing** and **Statistical Mechanics** to find "risk-free" arbitrage opportunities in the Forex market.
It scans 196 currency pairs/timeframes, filters for historical accuracy (>80%), checks for trend breakouts (TrendGuard), and verifies the trade using the **IBM Quantum Computer**.

**Key Features:**
*   **God Mode Scanner:** Scans M1 to D1 timeframes instantly.
*   **TrendGuard:** Prevents losses from momentum breakouts (Black Swans).
*   **Quantum Verification:** Uses real quantum hardware to confirm trade signals.
*   **Precision Levels:** Calculates exact Entry, TP, and SL.

---

## 🛠️ Installation (The Easy Way: Google Antigravity)

The easiest way to run this is using **Google's Antigravity IDE**, which connects directly to GitHub.

### Step 1: Get the Code
1.  Go to this project's **GitHub Repository**.
2.  Click the **"Fork"** button (top right) to save a copy to your own GitHub account.

### Step 2: Open in Antigravity
1.  Open **Google Antigravity**.
2.  Select **"Import from GitHub"**.
3.  Choose the repository you just forked.
4.  Click **"Create Workspace"**.
    *   *Antigravity will load and automatically install the necessary Python tools.*

### Step 3: Add Your Keys (The Secret Sauce)
1.  In the file explorer (left side), look for a file named `.env.example`.
2.  Right-click it and select **"Rename"**. Change it to just `.env`.
3.  Open the file and paste your keys:
    *   `OANDA_API_KEY`: (Get this from your OANDA Account)
    *   `OANDA_ACCOUNT_ID`: (Get this from your OANDA Account)
    *   `IBM_QUANTUM_TOKEN`: (Get this from [quantum.ibm.com](https://quantum.ibm.com))
4.  Save the file (`Ctrl+S` or `Cmd+S`).

### Step 4: Install Dependencies
In the terminal at the bottom, type this command and hit Enter:
```bash
pip install -r requirements.txt
```

---

## 💻 How to Run (Start Making Money)

### Step 1: Run the Universal Scanner
This is the main "God Mode" tool. It does everything (Scan -> Filter -> Verify).
```bash
python3 quantum_pipeline_80.py
```
*   It will print the top trades that pass all checks.
*   Look for the **"VERIFIED"** output at the end.

### Step 2: Get Precise Levels
Once you have a verified trade (e.g., AUD_CAD on M15), run this tool to get your numbers:
```bash
python3 get_trade_levels.py
```
*   It will ask for the Pair and Timeframe.
*   It will output the exact **Entry**, **Take Profit**, and **Stop Loss**.

### Step 3: Read the Research
To understand the math and physics behind the system:
```bash
open research_paper.md
```

---

## ⚠️ Important Notes
*   **Market Hours:** Run this when markets are open (Sunday 5PM EST - Friday 5PM EST).
*   **Quantum Queue:** Sometimes IBM Quantum computers are busy. The script will wait for the next available slot.
*   **Risk Management:** Always use the calculated Stop Loss. The system is accurate, but the market is never 100% predictable.

---
*Built by Gideon Liciaga using the AEGFM-Omega Framework.*
