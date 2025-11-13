//+------------------------------------------------------------------+
//|                                              AEGFM_Omega_EA.mq5 |
//|                        Advanced Trading System with 75% Target |
//|                          IMMEDIATE TRADING MODE ENABLED         |
//+------------------------------------------------------------------+
#property copyright "AEGFM-Ω Trading System"
#property link      ""
#property version   "1.10"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\AccountInfo.mqh>

//--- Input Parameters
input group "=== IMMEDIATE TRADING ==="
input bool InpImmediateTrade = true;            // ✓ Trade Immediately on Load
input bool InpAggressiveMode = true;            // ✓ Aggressive Entry (No Pattern Required)

input group "=== Risk Management ==="
input double InpRiskPercent = 4.0;              // Risk Per Trade (%)
input double InpMaxLossPercent = 0.25;          // Max Loss Per Trade (% of equity)
input double InpKellyFraction = 0.4;            // Fractional Kelly
input double InpMinProbability = 0.60;          // Minimum Probability (60% for immediate mode)

input group "=== Entry Settings ==="
input int InpATRPeriod = 14;                    // ATR Period
input double InpStopATRMultiplier = 1.0;        // Stop Loss (ATR multiplier)
input double InpTargetATRMultiplier = 2.0;      // Take Profit (ATR multiplier)
input int InpMinBarsForPattern = 30;            // Minimum Bars for Pattern

input group "=== Pattern Detection ==="
input double InpPatternTolerance = 0.02;        // Pattern Level Tolerance (ATR fraction)
input double InpNecklineTolerance = 0.03;       // Neckline Tolerance (ATR fraction)
input int InpSwingLookback = 5;                 // Swing Point Lookback

input group "=== Trade Management ==="
input bool InpUseBreakeven = true;              // Move to Breakeven
input double InpBreakevenATR = 1.5;             // Breakeven Trigger (ATR)
input int InpMagicNumber = 123456;              // Magic Number
input string InpTradeComment = "AEGFM-Ω";       // Trade Comment

input group "=== Time Filters ==="
input bool InpUseTimeFilter = false;            // Use Time Filter
input int InpStartHour = 0;                     // Start Hour (Server Time)
input int InpEndHour = 23;                      // End Hour (Server Time)

//--- Global Variables
CTrade trade;
CPositionInfo positionInfo;
CAccountInfo accountInfo;

// Pattern detection arrays
double high[], low[], close[], open[];
datetime time[];

// Indicator handles
int atrHandle;
int maHandle;  // Moving average for trend

// Immediate trading flag
bool initialTradeExecuted = false;
bool isFirstTick = true;

// Structure for detected patterns
struct PatternInfo {
    string type;
    double entry;
    double stop;
    double target;
    double quality;
    datetime detectTime;
    bool isValid;
};

PatternInfo currentPattern;

// Trade statistics
int totalTrades = 0;
int winningTrades = 0;
double currentEquity = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit() {
    Print("═══════════════════════════════════════════════════");
    Print("  AEGFM-Ω Expert Advisor Initialized");
    Print("  IMMEDIATE TRADING MODE: ", (InpImmediateTrade ? "ON" : "OFF"));
    Print("  AGGRESSIVE MODE: ", (InpAggressiveMode ? "ON" : "OFF"));
    Print("  Target Accuracy: ", InpMinProbability * 100, "%");
    Print("  Risk Per Trade: ", InpRiskPercent, "%");
    Print("═══════════════════════════════════════════════════");

    // Initialize trade object
    trade.SetExpertMagicNumber(InpMagicNumber);
    trade.SetDeviationInPoints(10);
    trade.SetTypeFilling(ORDER_FILLING_FOK);
    trade.SetAsyncMode(false);

    // Initialize ATR indicator
    atrHandle = iATR(_Symbol, _Period, InpATRPeriod);
    if(atrHandle == INVALID_HANDLE) {
        Print("Error creating ATR indicator!");
        return(INIT_FAILED);
    }

    // Initialize MA for trend detection
    maHandle = iMA(_Symbol, _Period, 50, 0, MODE_SMA, PRICE_CLOSE);
    if(maHandle == INVALID_HANDLE) {
        Print("Error creating MA indicator!");
        return(INIT_FAILED);
    }

    // Initialize pattern structure
    ResetPattern();

    // Set array as series
    ArraySetAsSeries(high, true);
    ArraySetAsSeries(low, true);
    ArraySetAsSeries(close, true);
    ArraySetAsSeries(open, true);
    ArraySetAsSeries(time, true);

    currentEquity = accountInfo.Balance();
    initialTradeExecuted = false;
    isFirstTick = true;

    if(InpImmediateTrade) {
        Print("⚡ IMMEDIATE TRADING ENABLED - Will analyze and trade on first tick!");
    }

    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason) {
    Print("═══════════════════════════════════════════════════");
    Print("  AEGFM-Ω EA Stopped");
    Print("  Total Trades: ", totalTrades);
    Print("  Winning Trades: ", winningTrades);
    if(totalTrades > 0) {
        Print("  Win Rate: ", NormalizeDouble((double)winningTrades/totalTrades * 100, 2), "%");
    }
    Print("═══════════════════════════════════════════════════");

    IndicatorRelease(atrHandle);
    IndicatorRelease(maHandle);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick() {
    // Update market data
    if(!UpdateMarketData()) return;

    // IMMEDIATE TRADING MODE - Execute on first tick
    if(InpImmediateTrade && isFirstTick && !initialTradeExecuted) {
        Print("⚡⚡⚡ IMMEDIATE TRADING MODE ACTIVATED ⚡⚡⚡");
        Print("Analyzing current market conditions...");

        isFirstTick = false;

        if(!HasOpenPosition()) {
            ExecuteImmediateTrade();
            initialTradeExecuted = true;
        }

        return;
    }

    // Check if new bar (for regular pattern detection)
    static datetime lastBar = 0;
    if(time[0] == lastBar && !InpImmediateTrade) return;
    lastBar = time[0];

    // Check time filter
    if(InpUseTimeFilter && !IsTimeToTrade()) return;

    // Manage existing positions
    ManageOpenPositions();

    // If no position, look for entry (regular mode)
    if(!HasOpenPosition() && !InpImmediateTrade) {
        AnalyzeMarket();
    }
}

//+------------------------------------------------------------------+
//| Execute immediate trade based on current market conditions       |
//+------------------------------------------------------------------+
void ExecuteImmediateTrade() {
    Print("════════════════════════════════════════════════════════════");
    Print("  IMMEDIATE MARKET ANALYSIS");
    Print("════════════════════════════════════════════════════════════");

    double atr = GetATR(0);
    if(atr <= 0) {
        Print("✗ Cannot calculate ATR, aborting immediate trade");
        return;
    }

    double currentPrice = close[0];
    double ma50 = GetMA(0);

    // Calculate market conditions
    double momentum = CalculateMomentum();
    double volatility = atr / currentPrice;
    double trendStrength = CalculateTrendStrength();

    // Determine direction from multiple signals
    int bullishSignals = 0;
    int bearishSignals = 0;

    // Signal 1: Price vs MA
    if(currentPrice > ma50) bullishSignals++;
    else bearishSignals++;

    // Signal 2: Momentum
    if(momentum > 0) bullishSignals++;
    else bearishSignals++;

    // Signal 3: Recent candles
    int recentBullish = 0;
    for(int i = 0; i < 5; i++) {
        if(close[i] > open[i]) recentBullish++;
    }
    if(recentBullish >= 3) bullishSignals++;
    else if(recentBullish <= 2) bearishSignals++;

    // Signal 4: Trend strength
    if(trendStrength > 0.5) {
        if(currentPrice > ma50) bullishSignals++;
        else bearishSignals++;
    }

    // Calculate immediate probability
    double probability = CalculateImmediateProbability(momentum, volatility, trendStrength,
                                                       bullishSignals, bearishSignals);

    Print("─────────────────────────────────────────────────────────────");
    Print("  Market Analysis:");
    Print("  Current Price: ", currentPrice);
    Print("  MA(50): ", ma50);
    Print("  Momentum: ", NormalizeDouble(momentum, 5));
    Print("  Volatility: ", NormalizeDouble(volatility * 100, 3), "%");
    Print("  Trend Strength: ", NormalizeDouble(trendStrength, 3));
    Print("  Bullish Signals: ", bullishSignals);
    Print("  Bearish Signals: ", bearishSignals);
    Print("  Calculated Probability: ", NormalizeDouble(probability * 100, 2), "%");
    Print("─────────────────────────────────────────────────────────────");

    // Determine trade direction
    bool goLong = bullishSignals > bearishSignals;
    string direction = goLong ? "LONG" : "SHORT";

    // In aggressive mode, trade even with low probability
    if(InpAggressiveMode || probability >= InpMinProbability) {

        double entry = currentPrice;
        double stop, target;

        if(goLong) {
            stop = entry - (InpStopATRMultiplier * atr);
            target = entry + (InpTargetATRMultiplier * atr);
        } else {
            stop = entry + (InpStopATRMultiplier * atr);
            target = entry - (InpTargetATRMultiplier * atr);
        }

        double riskReward = MathAbs(target - entry) / MathAbs(entry - stop);
        double lotSize = CalculatePositionSize(probability, riskReward, MathAbs(entry - stop));

        if(lotSize < SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN)) {
            Print("✗ Position size too small, cannot trade");
            return;
        }

        Print("════════════════════════════════════════════════════════════");
        Print("  ⚡ IMMEDIATE TRADE EXECUTION ⚡");
        Print("  Direction: ", direction);
        Print("  Entry: ", entry);
        Print("  Stop: ", stop);
        Print("  Target: ", target);
        Print("  Probability: ", NormalizeDouble(probability * 100, 2), "%");
        Print("  R:R: 1:", NormalizeDouble(riskReward, 2));
        Print("  Lot Size: ", lotSize);
        Print("════════════════════════════════════════════════════════════");

        // Normalize prices
        stop = NormalizeDouble(stop, _Digits);
        target = NormalizeDouble(target, _Digits);

        // Execute trade
        bool success = false;
        if(goLong) {
            success = trade.Buy(lotSize, _Symbol, 0, stop, target, InpTradeComment + " [IMMEDIATE]");
        } else {
            success = trade.Sell(lotSize, _Symbol, 0, stop, target, InpTradeComment + " [IMMEDIATE]");
        }

        if(success) {
            totalTrades++;
            Print("✓✓✓ IMMEDIATE TRADE PLACED SUCCESSFULLY ✓✓✓");
            Print("  Ticket: ", trade.ResultOrder());
            Print("  Filled at: ", trade.ResultPrice());
        } else {
            Print("✗✗✗ IMMEDIATE TRADE FAILED ✗✗✗");
            Print("  Error: ", GetLastError());
        }

    } else {
        Print("✗ Probability (", NormalizeDouble(probability * 100, 2), "%) below minimum (",
              NormalizeDouble(InpMinProbability * 100, 2), "%)");
        Print("  Enable Aggressive Mode to trade anyway");
    }
}

//+------------------------------------------------------------------+
//| Calculate momentum from recent price action                      |
//+------------------------------------------------------------------+
double CalculateMomentum() {
    int periods = 20;
    if(ArraySize(close) < periods) return 0;

    double priceChange = close[0] - close[periods-1];
    double percentChange = priceChange / close[periods-1];

    return percentChange;
}

//+------------------------------------------------------------------+
//| Calculate trend strength (0 to 1)                                |
//+------------------------------------------------------------------+
double CalculateTrendStrength() {
    int periods = 20;
    if(ArraySize(close) < periods) return 0.5;

    // Count how many closes are above/below MA
    double ma = GetMA(0);
    int aboveMA = 0;

    for(int i = 0; i < periods; i++) {
        if(close[i] > ma) aboveMA++;
    }

    // Strength is how consistently price stays on one side of MA
    double consistency = MathAbs((double)aboveMA / periods - 0.5) * 2;

    return consistency;
}

//+------------------------------------------------------------------+
//| Calculate immediate probability                                  |
//+------------------------------------------------------------------+
double CalculateImmediateProbability(double momentum, double volatility,
                                     double trendStrength, int bullSignals, int bearSignals) {
    // Base probability from signal ratio
    int totalSignals = bullSignals + bearSignals;
    if(totalSignals == 0) return 0.50;

    double winningSignals = MathMax(bullSignals, bearSignals);
    double baseProbability = winningSignals / totalSignals;

    // Adjust for momentum (strong momentum increases probability)
    double momentumBonus = MathAbs(momentum) * 100 * 0.05;  // Up to 5% bonus
    momentumBonus = MathMin(momentumBonus, 0.05);

    // Adjust for trend strength (strong trend increases probability)
    double trendBonus = trendStrength * 0.10;  // Up to 10% bonus

    // Penalty for high volatility (uncertainty)
    double volPenalty = MathMin(volatility * 50, 0.05);  // Up to 5% penalty

    // Calculate final probability
    double probability = baseProbability + momentumBonus + trendBonus - volPenalty;

    // Ensure in range [0.50, 0.95]
    probability = MathMax(0.50, MathMin(0.95, probability));

    return probability;
}

//+------------------------------------------------------------------+
//| Get MA value                                                      |
//+------------------------------------------------------------------+
double GetMA(int shift) {
    double maBuffer[];
    ArraySetAsSeries(maBuffer, true);

    if(CopyBuffer(maHandle, 0, shift, 1, maBuffer) <= 0) {
        return close[shift];  // Fallback to price
    }

    return maBuffer[0];
}

//+------------------------------------------------------------------+
//| Update market data arrays                                        |
//+------------------------------------------------------------------+
bool UpdateMarketData() {
    int bars = 200; // Lookback period

    if(CopyHigh(_Symbol, _Period, 0, bars, high) <= 0) return false;
    if(CopyLow(_Symbol, _Period, 0, bars, low) <= 0) return false;
    if(CopyClose(_Symbol, _Period, 0, bars, close) <= 0) return false;
    if(CopyOpen(_Symbol, _Period, 0, bars, open) <= 0) return false;
    if(CopyTime(_Symbol, _Period, 0, bars, time) <= 0) return false;

    return true;
}

//+------------------------------------------------------------------+
//| Check if time to trade                                           |
//+------------------------------------------------------------------+
bool IsTimeToTrade() {
    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);
    return (dt.hour >= InpStartHour && dt.hour < InpEndHour);
}

//+------------------------------------------------------------------+
//| Check if there's an open position                                |
//+------------------------------------------------------------------+
bool HasOpenPosition() {
    for(int i = PositionsTotal() - 1; i >= 0; i--) {
        if(positionInfo.SelectByIndex(i)) {
            if(positionInfo.Symbol() == _Symbol &&
               positionInfo.Magic() == InpMagicNumber) {
                return true;
            }
        }
    }
    return false;
}

//+------------------------------------------------------------------+
//| Manage open positions (breakeven, trailing, etc.)                |
//+------------------------------------------------------------------+
void ManageOpenPositions() {
    for(int i = PositionsTotal() - 1; i >= 0; i--) {
        if(positionInfo.SelectByIndex(i)) {
            if(positionInfo.Symbol() == _Symbol &&
               positionInfo.Magic() == InpMagicNumber) {

                // Move to breakeven
                if(InpUseBreakeven) {
                    MoveToBreakeven();
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Move stop loss to breakeven                                      |
//+------------------------------------------------------------------+
void MoveToBreakeven() {
    double atr = GetATR(0);
    double openPrice = positionInfo.PriceOpen();
    double currentSL = positionInfo.StopLoss();
    double currentPrice = positionInfo.PriceCurrent();

    if(positionInfo.Type() == POSITION_TYPE_BUY) {
        double triggerPrice = openPrice + InpBreakevenATR * atr;

        if(currentPrice >= triggerPrice && currentSL < openPrice) {
            double newSL = openPrice + 10 * _Point;
            if(trade.PositionModify(positionInfo.Ticket(), newSL, positionInfo.TakeProfit())) {
                Print("✓ Stop moved to breakeven for BUY at ", newSL);
            }
        }
    }
    else if(positionInfo.Type() == POSITION_TYPE_SELL) {
        double triggerPrice = openPrice - InpBreakevenATR * atr;

        if(currentPrice <= triggerPrice && (currentSL > openPrice || currentSL == 0)) {
            double newSL = openPrice - 10 * _Point;
            if(trade.PositionModify(positionInfo.Ticket(), newSL, positionInfo.TakeProfit())) {
                Print("✓ Stop moved to breakeven for SELL at ", newSL);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Main market analysis function (pattern-based)                    |
//+------------------------------------------------------------------+
void AnalyzeMarket() {
    // Reset pattern
    ResetPattern();

    double atr = GetATR(0);
    if(atr <= 0) return;

    // Find swing points
    int swingHighs[], swingLows[];
    FindSwingPoints(swingHighs, swingLows);

    // Try to detect patterns
    bool patternFound = false;

    if(!patternFound && ArraySize(swingLows) >= 2) {
        patternFound = DetectDoubleBottom(swingLows, atr);
    }

    if(!patternFound && ArraySize(swingHighs) >= 2) {
        patternFound = DetectDoubleTop(swingHighs, atr);
    }

    if(!patternFound && ArraySize(swingHighs) >= 3) {
        patternFound = DetectHeadAndShoulders(swingHighs, atr);
    }

    if(!patternFound && ArraySize(swingLows) >= 3) {
        patternFound = DetectInverseHeadAndShoulders(swingLows, atr);
    }

    if(!patternFound) {
        patternFound = DetectTriangle(atr);
    }

    if(patternFound && currentPattern.isValid) {
        double probability = CalculateProbability();

        if(probability >= InpMinProbability) {
            Print("═══════════════════════════════════════════════════");
            Print("✓ PATTERN DETECTED: ", currentPattern.type);
            Print("  Entry: ", currentPattern.entry);
            Print("  Stop: ", currentPattern.stop);
            Print("  Target: ", currentPattern.target);
            Print("  Quality: ", NormalizeDouble(currentPattern.quality * 100, 2), "%");
            Print("  Probability: ", NormalizeDouble(probability * 100, 2), "%");
            Print("═══════════════════════════════════════════════════");

            ExecuteTrade(probability);
        }
    }
}

//+------------------------------------------------------------------+
//| Find swing highs and swing lows                                  |
//+------------------------------------------------------------------+
void FindSwingPoints(int &swingHighs[], int &swingLows[]) {
    ArrayResize(swingHighs, 0);
    ArrayResize(swingLows, 0);

    int lookback = InpSwingLookback;
    int bars = ArraySize(high);

    for(int i = lookback; i < bars - lookback; i++) {
        bool isSwingHigh = true;
        for(int j = i - lookback; j <= i + lookback; j++) {
            if(j != i && high[j] >= high[i]) {
                isSwingHigh = false;
                break;
            }
        }
        if(isSwingHigh) {
            ArrayResize(swingHighs, ArraySize(swingHighs) + 1);
            swingHighs[ArraySize(swingHighs) - 1] = i;
        }

        bool isSwingLow = true;
        for(int j = i - lookback; j <= i + lookback; j++) {
            if(j != i && low[j] <= low[i]) {
                isSwingLow = false;
                break;
            }
        }
        if(isSwingLow) {
            ArrayResize(swingLows, ArraySize(swingLows) + 1);
            swingLows[ArraySize(swingLows) - 1] = i;
        }
    }
}

//+------------------------------------------------------------------+
//| Detect Double Bottom pattern                                     |
//+------------------------------------------------------------------+
bool DetectDoubleBottom(int &swingLows[], double atr) {
    int size = ArraySize(swingLows);
    if(size < 2) return false;

    int idx1 = swingLows[size - 2];
    int idx2 = swingLows[size - 1];

    double low1 = low[idx1];
    double low2 = low[idx2];

    double tolerance = InpPatternTolerance * atr;
    if(MathAbs(low1 - low2) > tolerance) return false;

    double neckline = 0;
    for(int i = idx2; i <= idx1; i++) {
        if(high[i] > neckline) neckline = high[i];
    }

    double neckTolerance = InpNecklineTolerance * atr;
    if(neckline - MathMax(low1, low2) < neckTolerance) return false;

    if(close[0] < neckline - tolerance) return false;

    currentPattern.type = "Double Bottom";
    currentPattern.entry = neckline;
    currentPattern.stop = MathMin(low1, low2) - InpStopATRMultiplier * atr;
    currentPattern.target = neckline + (neckline - MathMin(low1, low2));
    currentPattern.quality = 1.0 - MathAbs(low1 - low2) / atr;
    currentPattern.detectTime = time[0];
    currentPattern.isValid = true;

    return true;
}

//+------------------------------------------------------------------+
//| Detect Double Top pattern                                        |
//+------------------------------------------------------------------+
bool DetectDoubleTop(int &swingHighs[], double atr) {
    int size = ArraySize(swingHighs);
    if(size < 2) return false;

    int idx1 = swingHighs[size - 2];
    int idx2 = swingHighs[size - 1];

    double high1 = high[idx1];
    double high2 = high[idx2];

    double tolerance = InpPatternTolerance * atr;
    if(MathAbs(high1 - high2) > tolerance) return false;

    double neckline = DBL_MAX;
    for(int i = idx2; i <= idx1; i++) {
        if(low[i] < neckline) neckline = low[i];
    }

    double neckTolerance = InpNecklineTolerance * atr;
    if(MathMin(high1, high2) - neckline < neckTolerance) return false;

    if(close[0] > neckline + tolerance) return false;

    currentPattern.type = "Double Top";
    currentPattern.entry = neckline;
    currentPattern.stop = MathMax(high1, high2) + InpStopATRMultiplier * atr;
    currentPattern.target = neckline - (MathMax(high1, high2) - neckline);
    currentPattern.quality = 1.0 - MathAbs(high1 - high2) / atr;
    currentPattern.detectTime = time[0];
    currentPattern.isValid = true;

    return true;
}

//+------------------------------------------------------------------+
//| Detect Head & Shoulders pattern                                  |
//+------------------------------------------------------------------+
bool DetectHeadAndShoulders(int &swingHighs[], double atr) {
    int size = ArraySize(swingHighs);
    if(size < 3) return false;

    int idxL = swingHighs[size - 3];
    int idxH = swingHighs[size - 2];
    int idxR = swingHighs[size - 1];

    double highL = high[idxL];
    double highH = high[idxH];
    double highR = high[idxR];

    double tolerance = InpPatternTolerance * atr;

    if(highH - highL < tolerance || highH - highR < tolerance) return false;
    if(MathAbs(highL - highR) > tolerance) return false;

    double neckline = DBL_MAX;
    for(int i = idxR; i <= idxL; i++) {
        if(low[i] < neckline) neckline = low[i];
    }

    if(close[0] > neckline + tolerance) return false;

    currentPattern.type = "Head & Shoulders";
    currentPattern.entry = neckline;
    currentPattern.stop = MathMax(MathMax(highL, highH), highR) + InpStopATRMultiplier * atr;
    currentPattern.target = neckline - (highH - neckline);
    currentPattern.quality = 1.0 - MathAbs(highL - highR) / atr;
    currentPattern.detectTime = time[0];
    currentPattern.isValid = true;

    return true;
}

//+------------------------------------------------------------------+
//| Detect Inverse Head & Shoulders                                  |
//+------------------------------------------------------------------+
bool DetectInverseHeadAndShoulders(int &swingLows[], double atr) {
    int size = ArraySize(swingLows);
    if(size < 3) return false;

    int idxL = swingLows[size - 3];
    int idxH = swingLows[size - 2];
    int idxR = swingLows[size - 1];

    double lowL = low[idxL];
    double lowH = low[idxH];
    double lowR = low[idxR];

    double tolerance = InpPatternTolerance * atr;

    if(lowL - lowH < tolerance || lowR - lowH < tolerance) return false;
    if(MathAbs(lowL - lowR) > tolerance) return false;

    double neckline = 0;
    for(int i = idxR; i <= idxL; i++) {
        if(high[i] > neckline) neckline = high[i];
    }

    if(close[0] < neckline - tolerance) return false;

    currentPattern.type = "Inverse H&S";
    currentPattern.entry = neckline;
    currentPattern.stop = MathMin(MathMin(lowL, lowH), lowR) - InpStopATRMultiplier * atr;
    currentPattern.target = neckline + (neckline - lowH);
    currentPattern.quality = 1.0 - MathAbs(lowL - lowR) / atr;
    currentPattern.detectTime = time[0];
    currentPattern.isValid = true;

    return true;
}

//+------------------------------------------------------------------+
//| Detect Triangle pattern                                          |
//+------------------------------------------------------------------+
bool DetectTriangle(double atr) {
    int window = InpMinBarsForPattern;
    if(ArraySize(high) < window) return false;

    double upperSlope, lowerSlope;
    double upperIntercept, lowerIntercept;

    CalculateTrendline(high, window, upperSlope, upperIntercept);
    CalculateTrendline(low, window, lowerSlope, lowerIntercept);

    if(upperSlope >= 0 || lowerSlope <= 0) return false;

    double upperBound = upperSlope * 0 + upperIntercept;
    double lowerBound = lowerSlope * 0 + lowerIntercept;

    double range = upperBound - lowerBound;
    if(range <= 0) return false;

    double poleHeight = high[window] - low[window];

    currentPattern.type = "Symmetrical Triangle";
    currentPattern.entry = upperBound;
    currentPattern.stop = lowerBound - InpStopATRMultiplier * atr;
    currentPattern.target = upperBound + poleHeight;
    currentPattern.quality = 0.7;
    currentPattern.detectTime = time[0];
    currentPattern.isValid = true;

    return true;
}

//+------------------------------------------------------------------+
//| Calculate simple linear trendline                                |
//+------------------------------------------------------------------+
void CalculateTrendline(double &prices[], int window, double &slope, double &intercept) {
    double sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;

    for(int i = 0; i < window; i++) {
        double x = i;
        double y = prices[i];

        sumX += x;
        sumY += y;
        sumXY += x * y;
        sumX2 += x * x;
    }

    double n = window;
    slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    intercept = (sumY - slope * sumX) / n;
}

//+------------------------------------------------------------------+
//| Calculate probability of success (pattern-based)                 |
//+------------------------------------------------------------------+
double CalculateProbability() {
    double qualityScore = currentPattern.quality;

    double momentum = (close[0] - close[10]) / close[10];
    double momentumScore = (momentum > 0) ? MathMin(momentum * 100, 1.0) : 0.0;

    double atr = GetATR(0);
    double atrRatio = atr / close[0];
    double volScore = 1.0 - MathMin(atrRatio * 50, 1.0);

    double rr = MathAbs(currentPattern.target - currentPattern.entry) /
                MathAbs(currentPattern.entry - currentPattern.stop);
    double rrScore = MathMin(rr / 3.0, 1.0);

    double probability = (qualityScore * 0.4) +
                        (momentumScore * 0.2) +
                        (volScore * 0.2) +
                        (rrScore * 0.2);

    probability = MathMax(probability, 0.5);

    if(StringFind(currentPattern.type, "Double") >= 0) {
        probability += 0.05;
    }
    if(StringFind(currentPattern.type, "H&S") >= 0 ||
       StringFind(currentPattern.type, "Shoulders") >= 0) {
        probability += 0.08;
    }

    return MathMin(probability, 0.99);
}

//+------------------------------------------------------------------+
//| Execute trade based on pattern                                   |
//+------------------------------------------------------------------+
void ExecuteTrade(double probability) {
    double atr = GetATR(0);
    double currentPrice = close[0];

    bool isBullish = (currentPrice < currentPattern.entry &&
                     (StringFind(currentPattern.type, "Bottom") >= 0 ||
                      StringFind(currentPattern.type, "Inverse") >= 0));

    double riskReward = MathAbs(currentPattern.target - currentPattern.entry) /
                       MathAbs(currentPattern.entry - currentPattern.stop);

    double lotSize = CalculatePositionSize(probability, riskReward,
                                          MathAbs(currentPattern.entry - currentPattern.stop));

    if(lotSize < SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN)) {
        Print("Position size too small, skipping trade");
        return;
    }

    double entryPrice = NormalizeDouble(currentPattern.entry, _Digits);
    double stopLoss = NormalizeDouble(currentPattern.stop, _Digits);
    double takeProfit = NormalizeDouble(currentPattern.target, _Digits);

    bool success = false;

    if(isBullish) {
        if(entryPrice > currentPrice) {
            success = trade.BuyStop(lotSize, entryPrice, _Symbol, stopLoss, takeProfit,
                                   ORDER_TIME_GTC, 0, InpTradeComment);
        } else {
            success = trade.Buy(lotSize, _Symbol, 0, stopLoss, takeProfit, InpTradeComment);
        }
    } else {
        if(entryPrice < currentPrice) {
            success = trade.SellStop(lotSize, entryPrice, _Symbol, stopLoss, takeProfit,
                                    ORDER_TIME_GTC, 0, InpTradeComment);
        } else {
            success = trade.Sell(lotSize, _Symbol, 0, stopLoss, takeProfit, InpTradeComment);
        }
    }

    if(success) {
        totalTrades++;
        Print("→ ORDER PLACED: ", (isBullish ? "BUY" : "SELL"), " ", lotSize, " lots");
        Print("  Probability: ", NormalizeDouble(probability * 100, 2), "%");
        Print("  R:R: 1:", NormalizeDouble(riskReward, 2));
    } else {
        Print("✗ Order failed: ", GetLastError());
    }
}

//+------------------------------------------------------------------+
//| Calculate position size using fractional Kelly                   |
//+------------------------------------------------------------------+
double CalculatePositionSize(double probability, double rewardRiskRatio, double stopDistance) {
    double equity = accountInfo.Balance();

    double kellyF = probability - (1 - probability) / rewardRiskRatio;
    if(kellyF <= 0) return 0;

    double f = InpKellyFraction * kellyF;

    double riskAmount = MathMin(
        equity * (InpRiskPercent / 100.0),
        equity * (InpMaxLossPercent / 100.0)
    );

    double pointValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
    double stopPoints = stopDistance / _Point;

    double lotSize = riskAmount / (stopPoints * pointValue);

    double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
    double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
    double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);

    lotSize = MathFloor(lotSize / lotStep) * lotStep;
    lotSize = MathMax(minLot, MathMin(maxLot, lotSize));

    return lotSize;
}

//+------------------------------------------------------------------+
//| Get ATR value                                                     |
//+------------------------------------------------------------------+
double GetATR(int shift) {
    double atrBuffer[];
    ArraySetAsSeries(atrBuffer, true);

    if(CopyBuffer(atrHandle, 0, shift, 1, atrBuffer) <= 0) {
        return 0;
    }

    return atrBuffer[0];
}

//+------------------------------------------------------------------+
//| Reset pattern structure                                          |
//+------------------------------------------------------------------+
void ResetPattern() {
    currentPattern.type = "";
    currentPattern.entry = 0;
    currentPattern.stop = 0;
    currentPattern.target = 0;
    currentPattern.quality = 0;
    currentPattern.detectTime = 0;
    currentPattern.isValid = false;
}

//+------------------------------------------------------------------+
//| Trade event handler                                              |
//+------------------------------------------------------------------+
void OnTrade() {
    HistorySelect(0, TimeCurrent());

    int total = HistoryDealsTotal();
    for(int i = total - 1; i >= 0; i--) {
        ulong ticket = HistoryDealGetTicket(i);

        if(HistoryDealGetInteger(ticket, DEAL_MAGIC) == InpMagicNumber &&
           HistoryDealGetString(ticket, DEAL_SYMBOL) == _Symbol) {

            ENUM_DEAL_ENTRY entry = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(ticket, DEAL_ENTRY);

            if(entry == DEAL_ENTRY_OUT) {
                double profit = HistoryDealGetDouble(ticket, DEAL_PROFIT);

                if(profit > 0) {
                    winningTrades++;
                }

                break;
            }
        }
    }
}
//+------------------------------------------------------------------+
