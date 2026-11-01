import os
import io
import re
import sys
import time
import requests
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from statistics import mean, pstdev

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

try:
    import yfinance as yf
except ImportError:
    print("Error: yfinance is not installed. Please run: pip install yfinance")
    sys.exit(1)

# Preset NIFTY 50 Stock Universe
NIFTY_50_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR", "ITC", 
    "SBIN", "BHARTIARTL", "KOTAKBANK", "LT", "AXISBANK", "ASIANPAINT", 
    "MARUTI", "SUNPHARMA", "TITAN", "BAJFINANCE", "TATAMOTORS", "ULTRACEMCO", 
    "NTPC", "POWERGRID", "TATASTEEL", "M&M", "ADANIENT", "ADANIPORTS", 
    "JSWSTEEL", "COALINDIA", "BAJAJFINSV", "SIEMENS", "GRASIM", "TECHM", 
    "HCLTECH", "ONGC", "WIPRO", "NESTLEIND", "DRREDDY", "CIPLA", 
    "EICHERMOT", "DIVISLAB", "HINDALCO", "APOLLOHOSP", "SBILIFE", "BPCL", 
    "LTIM", "BRITANNIA", "TATACONSUM", "HEROMOTOCO", "SHRIRAMFIN", "BEL", "TRENT"
]

# ==============================================================================
# TECHNICAL ANALYSIS ENGINE (Calculations)
# ==============================================================================

def calc_pivots(h, l, c):
    """Calculates standard Fibonacci Pivot levels."""
    p = round((h + l + c) / 3, 2)
    diff = h - l
    return {
        'r3': round(p + (1.000 * diff), 2),
        'r2': round(p + (0.618 * diff), 2),
        'r1': round(p + (0.382 * diff), 2),
        'p': p,
        's1': round(p - (0.382 * diff), 2),
        's2': round(p - (0.618 * diff), 2),
        's3': round(p - (1.000 * diff), 2)
    }

def calc_bb(closes, ltp):
    """Calculates 25-period Bollinger Bands & position relative to LTP."""
    if len(closes) < 25:
        return 0.0, 0.0, "N/A", "-"
    sma = mean(closes[-25:])
    std = pstdev(closes[-25:])
    upper = round(sma + (2 * std), 2)
    lower = round(sma - (2 * std), 2)
    
    status, pct_str = "Within BB", "-"
    if upper > 0 and lower > 0:
        if ltp > upper:
            pct = round(((ltp - upper) / upper) * 100, 2)
            status = "🔥 Above Upper Band (Breakout)"
            pct_str = f"+{pct}%"
        elif ltp < lower:
            pct = round(((lower - ltp) / lower) * 100, 2)
            status = "❄️ Below Lower Band (Oversold)"
            pct_str = f"-{pct}%"
        else:
            status = "⚡ Inside Normal Bands"
            pct_str = "0.0%"
    return upper, lower, status, pct_str

def build_range_bar(low, high, current, width=15):
    """Builds a visual Unicode position bar [Low ──🔘───── High]."""
    try:
        lo, hi = min(low, high), max(low, high)
        if hi == lo:
            ratio = 0.5
        else:
            ratio = (current - lo) / (hi - lo)
        ratio = max(0.0, min(1.0, ratio))
        pos = int(round(ratio * (width - 1)))
        bar = ["─"] * width
        bar[pos] = "🔘"
        return f"[{''.join(bar)}]"
    except Exception:
        return "[───────────────]"

def calc_ema_metrics(daily_closes, weekly_closes, ltp):
    """Calculates 50/200-period Daily & Weekly EMAs vs LTP."""
    def _ema(closes, period):
        if len(closes) < 10:
            return None
        s = pd.Series(closes, dtype="float64")
        span = min(period, len(s))
        return round(float(s.ewm(span=span, adjust=False).mean().iloc[-1]), 2)

    def _fmt(val, ltp_):
        if not val:
            return "-"
        pct = round(((ltp_ - val) / val) * 100, 2)
        sign = "+" if pct >= 0 else ""
        return f"₹{val} ({sign}{pct}%)"

    dema50 = _ema(daily_closes, 50)
    dema200 = _ema(daily_closes, 200)
    wema50 = _ema(weekly_closes, 50)
    wema200 = _ema(weekly_closes, 200)

    # Signal
    trend = "Neutral"
    if dema50 and dema200:
        if ltp > dema50 > dema200:
            trend = "🟢 Strong Bullish (Above 50 & 200 EMA)"
        elif ltp < dema50 < dema200:
            trend = "🔴 Strong Bearish (Below 50 & 200 EMA)"
        elif ltp > dema50:
            trend = "🟡 Mild Bullish (Above 50 EMA)"
        else:
            trend = "🟠 Mild Bearish (Below 50 EMA)"

    return {
        "dema50_str": _fmt(dema50, ltp),
        "dema200_str": _fmt(dema200, ltp),
        "wema50_str": _fmt(wema50, ltp),
        "wema200_str": _fmt(wema200, ltp),
        "dema200_raw": dema200,
        "trend": trend
    }

def calc_price_projections(daily_closes, ltp, dema200_raw):
    """Lightweight statistical projections for 1M / 6M / 1Y horizons."""
    try:
        closes = daily_closes[-252:] if len(daily_closes) >= 30 else daily_closes
        s = pd.Series(closes, dtype="float64")
        if len(s) < 10:
            return None
        returns = s.pct_change().dropna()
        mu = float(returns.mean())
        horizons = {"1 Month (21d)": 21, "6 Months (126d)": 126, "1 Year (252d)": 252}
        projections = {}
        for label, days in horizons.items():
            drift = ltp * ((1 + mu) ** days)
            target = (0.7 * drift) + (0.3 * dema200_raw) if dema200_raw else drift
            pct = ((target - ltp) / ltp) * 100
            sign = "+" if pct >= 0 else ""
            projections[label] = f"₹{round(target, 2)} ({sign}{round(pct, 1)}%)"
        return projections
    except Exception:
        return None

# ==============================================================================
# FUNDAMENTALS & NEWS PARSERS (Screener.in & Google News RSS)
# ==============================================================================

def get_screener_fundamentals(symbol):
    """Scrapes financial ratios and shareholding patterns from Screener.in."""
    result = {
        "market_cap": "-", "pe": "-", "face_value": "-", "debt_to_eq": "-",
        "sales_growth": "-", "promoter_hold": "-", "fii_hold": "-", "dii_hold": "-"
    }
    try:
        clean_sym = symbol.replace("&", "-").replace(" ", "-")
        urls = [
            f"https://www.screener.in/company/{clean_sym}/consolidated/",
            f"https://www.screener.in/company/{clean_sym}/"
        ]
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        html_text, tables = "", []

        for url in urls:
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                html_text = resp.text
                try:
                    tables = pd.read_html(io.StringIO(html_text))
                    if tables:
                        break
                except Exception:
                    continue

        if not html_text:
            return result

        def _ratio(label):
            m = re.search(rf'{label}.*?class="number">([^<]+)</span>', html_text, re.IGNORECASE | re.DOTALL)
            return m.group(1).strip() if m else None

        mc = _ratio("Market Cap")
        if mc: result["market_cap"] = f"₹{mc} Cr"

        pe = _ratio("Stock P/E")
        if pe: result["pe"] = pe

        fv = _ratio("Face Value")
        if fv: result["face_value"] = fv

        dte = _ratio("Debt to equity")
        if dte: result["debt_to_eq"] = dte

        # Sales Growth
        for tb in tables:
            first_col = tb.columns[0]
            if tb[first_col].astype(str).str.contains('Sales', na=False, regex=False).any():
                tb2 = tb.set_index(first_col)
                sales_row = tb2[tb2.index.astype(str).str.contains('Sales', na=False, regex=False)]
                if not sales_row.empty:
                    cols = [c for c in sales_row.columns if str(c).upper() != 'TTM']
                    vals = sales_row.iloc[0][cols].tail(2)
                    if len(vals) == 2:
                        try:
                            prev = float(str(vals.iloc[0]).replace(',', '').strip())
                            curr = float(str(vals.iloc[1]).replace(',', '').strip())
                            if prev != 0:
                                growth = ((curr - prev) / abs(prev)) * 100
                                sign = "+" if growth >= 0 else ""
                                result["sales_growth"] = f"{sign}{round(growth, 2)}%"
                        except Exception:
                            pass
                break

        # Shareholding
        for tb in tables:
            first_col = tb.columns[0]
            col_vals = tb[first_col].astype(str)
            if col_vals.str.contains('Promoter', na=False, regex=False).any() and \
               col_vals.str.contains('FII', na=False, regex=False).any():
                tb2 = tb.set_index(first_col)

                def _hold(label):
                    row = tb2[tb2.index.astype(str).str.contains(label, na=False, regex=False)]
                    if row.empty: return "-"
                    vals = row.iloc[0].dropna()
                    if len(vals) < 2: return "-"
                    try:
                        curr = float(str(vals.iloc[-1]).replace('%', '').strip())
                        prev = float(str(vals.iloc[-2]).replace('%', '').strip())
                        chg = round(curr - prev, 2)
                        return f"{curr}% ({'+' if chg >= 0 else ''}{chg}%)"
                    except Exception:
                        return "-"

                result["promoter_hold"] = _hold("Promoter")
                result["fii_hold"] = _hold("FII")
                result["dii_hold"] = _hold("DII")
                break

    except Exception:
        pass
    return result

def get_stock_news(symbol, limit=3):
    """Fetches recent news headlines via Google News RSS."""
    headlines = []
    try:
        url = f"https://news.google.com/rss/search?q={symbol}+stock+india&hl=en-IN&gl=IN&ceid=IN:en"
        resp = requests.get(url, timeout=6)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            for item in root.findall(".//item")[:limit]:
                title = item.find("title").text if item.find("title") is not None else ""
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                if title:
                    short_date = pub_date[:16] if pub_date else ""
                    headlines.append(f"• {title} ({short_date})")
    except Exception:
        pass
    return headlines

# ==============================================================================
# STOCK ANALYSIS PIPELINE (Free yfinance Engine)
# ==============================================================================

def analyze_stock(symbol, include_extras=True):
    """Fetches real-time price & candles via yfinance and performs full technical & fundamental analysis."""
    clean_sym = symbol.upper().replace(".NS", "")
    yf_ticker = f"{clean_sym}.NS"
    
    try:
        ticker = yf.Ticker(yf_ticker)
        # Fetch daily history (1 year)
        df_daily = ticker.history(period="1y", interval="1d")
        if df_daily.empty or len(df_daily) < 5:
            return None, f"Could not fetch data for {symbol} on NSE. Verify symbol name."

        # Fetch weekly history
        df_weekly = ticker.history(period="2y", interval="1wk")
    except Exception as e:
        return None, f"Network/data error for {symbol}: {e}"

    ltp = round(float(df_daily['Close'].iloc[-1]), 2)
    prev_close = round(float(df_daily['Close'].iloc[-2]), 2) if len(df_daily) > 1 else ltp
    day_chg = round(((ltp - prev_close) / prev_close) * 100, 2)
    day_chg_sign = "+" if day_chg >= 0 else ""

    # Previous Day High, Low, Close for Pivots
    prev_h = float(df_daily['High'].iloc[-2]) if len(df_daily) > 1 else float(df_daily['High'].iloc[-1])
    prev_l = float(df_daily['Low'].iloc[-2]) if len(df_daily) > 1 else float(df_daily['Low'].iloc[-1])
    prev_c = prev_close
    pivots = calc_pivots(prev_h, prev_l, prev_c)

    # 52-Week High & Low
    high_52w = round(float(df_daily['High'].max()), 2)
    low_52w = round(float(df_daily['Low'].min()), 2)
    range_bar = build_range_bar(low_52w, high_52w, ltp)

    # Bollinger Bands
    daily_closes = df_daily['Close'].tolist()
    upper_bb, lower_bb, bb_status, bb_pct = calc_bb(daily_closes, ltp)

    # EMAs
    weekly_closes = df_weekly['Close'].tolist() if not df_weekly.empty else daily_closes
    ema_data = calc_ema_metrics(daily_closes, weekly_closes, ltp)

    # Price Projections
    projections = calc_price_projections(daily_closes, ltp, ema_data.get("dema200_raw"))

    # Fundamentals & News (only if requested)
    fundamentals = get_screener_fundamentals(clean_sym) if include_extras else {
        "market_cap": "-", "pe": "-", "face_value": "-", "debt_to_eq": "-",
        "sales_growth": "-", "promoter_hold": "-", "fii_hold": "-", "dii_hold": "-"
    }
    news = get_stock_news(clean_sym) if include_extras else []

    analysis = {
        "symbol": clean_sym,
        "ltp": ltp,
        "day_change": f"{day_chg_sign}{day_chg}%",
        "pivots": pivots,
        "52w_high": high_52w,
        "52w_low": low_52w,
        "range_bar": range_bar,
        "bb_upper": upper_bb,
        "bb_lower": lower_bb,
        "bb_status": bb_status,
        "bb_pct": bb_pct,
        "ema_data": ema_data,
        "projections": projections,
        "fundamentals": fundamentals,
        "news": news
    }
    return analysis, None

# ==============================================================================
# DISPLAY & FORMATTING
# ==============================================================================

def print_stock_card(data):
    """Prints a beautiful terminal card for a analyzed stock."""
    sym = data["symbol"]
    ltp = data["ltp"]
    chg = data["day_change"]
    piv = data["pivots"]
    ema = data["ema_data"]
    fund = data["fundamentals"]
    
    print("\n" + "═" * 70)
    print(f" 📈 {sym} | LTP: ₹{ltp} ({chg})")
    print("═" * 70)
    
    # 52W Range & Trend
    print(f" 🎯 Trend Signal:  {ema['trend']}")
    print(f" 📊 52W Range:     ₹{data['52w_low']}  {data['range_bar']}  ₹{data['52w_high']}")
    print(f" ⚡ Bollinger Band: Upper: ₹{data['bb_upper']} | Lower: ₹{data['bb_lower']} -> {data['bb_status']}")
    
    # Pivots Table
    print("\n 📐 Fibonacci Pivots (Daily):")
    print(f"    R3: ₹{piv['r3']}   |   R2: ₹{piv['r2']}   |   R1: ₹{piv['r1']}")
    print(f"    Pivot: ₹{piv['p']}")
    print(f"    S1: ₹{piv['s1']}   |   S2: ₹{piv['s2']}   |   S3: ₹{piv['s3']}")
    
    # Moving Averages
    print("\n 📉 Exponential Moving Averages (EMA):")
    print(f"    Daily 50 EMA:  {ema['dema50_str']}  |  Daily 200 EMA:  {ema['dema200_str']}")
    print(f"    Weekly 50 EMA: {ema['wema50_str']}  |  Weekly 200 EMA: {ema['wema200_str']}")
    
    # Price Projections
    if data["projections"]:
        print("\n 🔮 Statistical Projections (Drift + 200-EMA mean reversion):")
        for k, v in data["projections"].items():
            print(f"    {k:18}: {v}")
            
    # Fundamentals
    print("\n 🏢 Fundamental Metrics (Screener.in):")
    print(f"    Market Cap: {fund['market_cap']}  |  P/E: {fund['pe']}  |  Face Value: {fund['face_value']}")
    print(f"    Debt/Eq: {fund['debt_to_eq']}  |  YoY Sales Growth: {fund['sales_growth']}")
    print(f"    Shareholding: Promoter: {fund['promoter_hold']} | FII: {fund['fii_hold']} | DII: {fund['dii_hold']}")
    
    # News
    if data["news"]:
        print("\n 📰 Latest News Headlines:")
        for n in data["news"]:
            print(f"    {n}")
    print("═" * 70 + "\n")

def run_nifty50_scan():
    """Scans all 50 stocks in the NIFTY 50 universe and highlights breakout and key momentum setups."""
    print("\n" + "=" * 75)
    print(f" 🚀 SCANNING NIFTY 50 UNIVERSE (Free Data Mode - Zero Demat Required)")
    print("=" * 75)
    print(f"{'SYMBOL':<12} {'LTP (₹)':<10} {'DAY %':<10} {'50 EMA':<15} {'BOLLINGER BAND':<25}")
    print("-" * 75)
    
    breakouts = []
    oversold = []
    
    for i, symbol in enumerate(NIFTY_50_SYMBOLS):
        try:
            analysis, err = analyze_stock(symbol, include_extras=False)
            if not analysis:
                continue
            
            sym = analysis["symbol"]
            ltp = analysis["ltp"]
            chg = analysis["day_change"]
            ema_str = analysis["ema_data"]["dema50_str"]
            bb_st = analysis["bb_status"]
            
            print(f"{sym:<12} {ltp:<10} {chg:<10} {ema_str:<15} {bb_st:<25}")
            
            if "Breakout" in bb_st:
                breakouts.append(sym)
            elif "Oversold" in bb_st:
                oversold.append(sym)
        except Exception:
            continue

    print("=" * 75)
    print("\n🎯 SCAN SUMMARY:")
    print(f"🔥 Upper Bollinger Breakouts: {', '.join(breakouts) if breakouts else 'None'}")
    print(f"❄️ Oversold / Lower Band:     {', '.join(oversold) if oversold else 'None'}")
    print("=" * 75 + "\n")

# ==============================================================================
# MAIN INTERACTIVE MENU
# ==============================================================================

def main():
    print("""
======================================================================
  📈 ALGO TRADING SUITE - FREE MARKET SCANNER (ZERO-DEMAT MODE)
======================================================================
  • No Broker Login Required (Zerodha/Upstox not needed)
  • Real-Time Market Data via Yahoo Finance (yfinance)
  • Fibonacci Pivots, 25-BB, 50/200-EMA, 52W Range
  • Financials via Screener.in & Live News via Google RSS
======================================================================
    """)
    
    if len(sys.argv) > 1:
        # Direct CLI argument mode, e.g. "python free_market_scanner.py RELIANCE"
        arg = sys.argv[1].upper()
        if arg in ["--SCAN", "SCAN", "NIFTY50", "ALL"]:
            run_nifty50_scan()
        else:
            print(f"Fetching full analysis for {arg}...")
            analysis, err = analyze_stock(arg)
            if analysis:
                print_stock_card(analysis)
            else:
                print(f"❌ {err}")
        return

    while True:
        print("\nChoose an option:")
        print("  1. 🔍 Analyze a Specific Stock (e.g. RELIANCE, TCS, INFY, TATAMOTORS)")
        print("  2. 🚀 Run Full NIFTY 50 Universe Scan")
        print("  3. ❌ Exit")
        
        try:
            choice = input("\nEnter your choice (1/2/3): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting. Happy trading!")
            break
            
        if choice == "1":
            stock = input("Enter Stock Symbol (e.g., RELIANCE, TCS, SBIN): ").strip().upper()
            if stock:
                print(f"\nAnalyzing {stock}...")
                analysis, err = analyze_stock(stock)
                if analysis:
                    print_stock_card(analysis)
                else:
                    print(f"\n❌ {err}")
        elif choice == "2":
            run_nifty50_scan()
        elif choice == "3":
            print("\nExiting. Happy trading!")
            break
        else:
            print("Invalid selection. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
