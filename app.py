import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import requests
import io
import re
import xml.etree.ElementTree as ET
from statistics import mean, pstdev

# Page configuration
st.set_page_config(
    page_title="Algo Trading Suite - Market Scanner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark glassmorphism styling
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .signal-bullish { color: #00E676; font-weight: bold; }
    .signal-bearish { color: #FF5252; font-weight: bold; }
    .signal-neutral { color: #FFD600; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 8px;
        padding: 8px 16px;
    }
</style>
""", unsafe_allow_html=True)

NIFTY_50_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR", "ITC", 
    "SBIN", "BHARTIARTL", "KOTAKBANK", "LT", "AXISBANK", "ASIANPAINT", 
    "MARUTI", "SUNPHARMA", "TITAN", "BAJFINANCE", "ULTRACEMCO", 
    "NTPC", "POWERGRID", "TATASTEEL", "M&M", "ADANIENT", "ADANIPORTS", 
    "JSWSTEEL", "COALINDIA", "BAJAJFINSV", "SIEMENS", "GRASIM", "TECHM", 
    "HCLTECH", "ONGC", "WIPRO", "NESTLEIND", "DRREDDY", "CIPLA", 
    "EICHERMOT", "DIVISLAB", "HINDALCO", "APOLLOHOSP", "SBILIFE", "BPCL", 
    "BRITANNIA", "TATACONSUM", "HEROMOTOCO", "SHRIRAMFIN", "BEL", "TRENT"
]

def calc_pivots(h, l, c):
    p = round((h + l + c) / 3, 2)
    diff = h - l
    return {
        'R3': round(p + (1.000 * diff), 2), 'R2': round(p + (0.618 * diff), 2),
        'R1': round(p + (0.382 * diff), 2), 'Pivot': p,
        'S1': round(p - (0.382 * diff), 2), 'S2': round(p - (0.618 * diff), 2),
        'S3': round(p - (1.000 * diff), 2)
    }

def get_screener_fundamentals(symbol):
    result = {
        "Market Cap": "-", "P/E": "-", "Face Value": "-", "Debt to Equity": "-",
        "Sales Growth YoY": "-", "Promoter Holding": "-", "FII Holding": "-", "DII Holding": "-"
    }
    try:
        clean_sym = symbol.replace("&", "-").replace(" ", "-")
        url = f"https://www.screener.in/company/{clean_sym}/consolidated/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code != 200:
            resp = requests.get(f"https://www.screener.in/company/{clean_sym}/", headers=headers, timeout=5)
        
        if resp.status_code == 200:
            html = resp.text
            def _ratio(lbl):
                m = re.search(rf'{lbl}.*?class="number">([^<]+)</span>', html, re.I | re.DOTALL)
                return m.group(1).strip() if m else None
            
            mc = _ratio("Market Cap")
            if mc: result["Market Cap"] = f"₹{mc} Cr"
            pe = _ratio("Stock P/E")
            if pe: result["P/E"] = pe
            fv = _ratio("Face Value")
            if fv: result["Face Value"] = fv
            dte = _ratio("Debt to equity")
            if dte: result["Debt to Equity"] = dte
            
            tables = pd.read_html(io.StringIO(html))
            for tb in tables:
                fc = tb.columns[0]
                if tb[fc].astype(str).str.contains('Sales', na=False).any():
                    tb2 = tb.set_index(fc)
                    s_row = tb2[tb2.index.astype(str).str.contains('Sales', na=False)]
                    if not s_row.empty:
                        cols = [c for c in s_row.columns if str(c).upper() != 'TTM']
                        v = s_row.iloc[0][cols].tail(2)
                        if len(v) == 2:
                            p, c = float(str(v.iloc[0]).replace(',', '')), float(str(v.iloc[1]).replace(',', ''))
                            if p != 0:
                                g = ((c - p) / abs(p)) * 100
                                result["Sales Growth YoY"] = f"{'+' if g >= 0 else ''}{round(g, 1)}%"
                    break
    except Exception:
        pass
    return result

def get_news(symbol):
    headlines = []
    try:
        url = f"https://news.google.com/rss/search?q={symbol}+stock+india&hl=en-IN&gl=IN&ceid=IN:en"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            for item in root.findall(".//item")[:5]:
                t = item.find("title").text if item.find("title") is not None else ""
                d = item.find("pubDate").text if item.find("pubDate") is not None else ""
                l = item.find("link").text if item.find("link") is not None else "#"
                if t: headlines.append({"title": t, "date": d[:16], "link": l})
    except Exception:
        pass
    return headlines

# ==========================================
# APP LAYOUT
# ==========================================

st.title("📈 Indian Stock Market Algo-Scanner")
st.caption("🚀 Zero-Demat Mode: Free real-time technical analysis, Fibonacci pivots, Bollinger Bands, and fundamentals without broker login.")

mode = st.sidebar.radio("Navigation", ["🔍 Single Stock Deep Dive", "🚀 NIFTY 50 Universe Scanner"])

if mode == "🔍 Single Stock Deep Dive":
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        symbol = st.text_input("Enter NSE Stock Symbol:", value="RELIANCE").upper().strip()
    with col_btn:
        st.write("")
        st.write("")
        analyze_clicked = st.button("🚀 Analyze", use_container_width=True)

    if symbol:
        yf_ticker = f"{symbol}.NS"
        with st.spinner(f"Fetching data for {symbol}..."):
            ticker = yf.Ticker(yf_ticker)
            df = ticker.history(period="1y", interval="1d")
            
        if df.empty or len(df) < 5:
            st.error(f"Could not load data for symbol '{symbol}'. Please ensure it is a valid NSE ticker.")
        else:
            ltp = round(float(df['Close'].iloc[-1]), 2)
            prev_close = round(float(df['Close'].iloc[-2]), 2) if len(df) > 1 else ltp
            day_chg = round(((ltp - prev_close) / prev_close) * 100, 2)
            
            # EMA calculations
            closes = df['Close']
            ema50 = round(float(closes.ewm(span=50, adjust=False).mean().iloc[-1]), 2)
            ema200 = round(float(closes.ewm(span=min(200, len(closes)), adjust=False).mean().iloc[-1]), 2)
            
            # Bollinger Bands
            sma25 = round(float(closes.rolling(25).mean().iloc[-1]), 2)
            std25 = round(float(closes.rolling(25).std().iloc[-1]), 2)
            bb_upper = round(sma25 + 2 * std25, 2)
            bb_lower = round(sma25 - 2 * std25, 2)
            
            # 52-Week
            high_52 = round(float(df['High'].max()), 2)
            low_52 = round(float(df['Low'].min()), 2)
            
            # Pivots
            prev_h = float(df['High'].iloc[-2]) if len(df) > 1 else float(df['High'].iloc[-1])
            prev_l = float(df['Low'].iloc[-2]) if len(df) > 1 else float(df['Low'].iloc[-1])
            pivots = calc_pivots(prev_h, prev_l, prev_close)

            # Top Metrics
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("LTP (Last Traded Price)", f"₹{ltp}", f"{'+' if day_chg >= 0 else ''}{day_chg}%")
            m2.metric("50-Day EMA", f"₹{ema50}", f"{round(((ltp-ema50)/ema50)*100, 1)}% vs LTP")
            m3.metric("200-Day EMA", f"₹{ema200}", f"{round(((ltp-ema200)/ema200)*100, 1)}% vs LTP")
            m4.metric("52W Range", f"₹{low_52} - ₹{high_52}")

            st.subheader("📊 Price Chart & Indicators")
            chart_df = df[['Close']].tail(90).copy()
            chart_df['50 EMA'] = df['Close'].ewm(span=50, adjust=False).mean().tail(90)
            chart_df['BB Upper'] = (df['Close'].rolling(25).mean() + 2 * df['Close'].rolling(25).std()).tail(90)
            chart_df['BB Lower'] = (df['Close'].rolling(25).mean() - 2 * df['Close'].rolling(25).std()).tail(90)
            st.line_chart(chart_df)

            tab1, tab2, tab3 = st.tabs(["📐 Fibonacci Pivots & Bands", "🏢 Company Fundamentals", "📰 News"])
            
            with tab1:
                c1, c2 = st.columns(2)
                with c1:
                    st.write("**Daily Fibonacci Pivot Points**")
                    piv_df = pd.DataFrame(list(pivots.items()), columns=["Level", "Price (₹)"])
                    st.dataframe(piv_df, hide_index=True, use_container_width=True)
                with c2:
                    st.write("**Bollinger Bands (25-period)**")
                    st.write(f"- **Upper Band**: ₹{bb_upper}")
                    st.write(f"- **Middle SMA**: ₹{sma25}")
                    st.write(f"- **Lower Band**: ₹{bb_lower}")
                    if ltp > bb_upper:
                        st.markdown("<span class='signal-bullish'>🔥 Status: Breakout Above Upper Band</span>", unsafe_allow_html=True)
                    elif ltp < bb_lower:
                        st.markdown("<span class='signal-bearish'>❄️ Status: Oversold Below Lower Band</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("<span class='signal-neutral'>⚡ Status: Trading inside normal bands</span>", unsafe_allow_html=True)

            with tab2:
                fundamentals = get_screener_fundamentals(symbol)
                st.write("**Key Financial Ratios (Screener.in)**")
                f_cols = st.columns(4)
                f_keys = list(fundamentals.keys())
                for i, k in enumerate(f_keys):
                    f_cols[i % 4].metric(k, fundamentals[k])

            with tab3:
                news_items = get_news(symbol)
                if news_items:
                    for n in news_items:
                        st.markdown(f"- [{n['title']}]({n['link']}) *({n['date']})*")
                else:
                    st.info("No recent news found.")

elif mode == "🚀 NIFTY 50 Universe Scanner":
    st.write("Scan all 50 NIFTY constituent stocks for breakout & oversold momentum setups:")
    if st.button("▶️ Run NIFTY 50 Scan", type="primary"):
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, sym in enumerate(NIFTY_50_SYMBOLS):
            status_text.text(f"Scanning {sym} ({i+1}/{len(NIFTY_50_SYMBOLS)})...")
            progress_bar.progress((i + 1) / len(NIFTY_50_SYMBOLS))
            try:
                t = yf.Ticker(f"{sym}.NS")
                d = t.history(period="6mo", interval="1d")
                if not d.empty and len(d) >= 25:
                    c = d['Close']
                    last_p = round(float(c.iloc[-1]), 2)
                    prev_p = round(float(c.iloc[-2]), 2)
                    chg_pct = round(((last_p - prev_p) / prev_p) * 100, 2)
                    
                    e50 = round(float(c.ewm(span=50, adjust=False).mean().iloc[-1]), 2)
                    s25 = round(float(c.rolling(25).mean().iloc[-1]), 2)
                    sd25 = round(float(c.rolling(25).std().iloc[-1]), 2)
                    u_bb = round(s25 + 2 * sd25, 2)
                    l_bb = round(s25 - 2 * sd25, 2)
                    
                    bb_status = "Inside Normal"
                    if last_p > u_bb: bb_status = "🔥 Breakout (Above Upper BB)"
                    elif last_p < l_bb: bb_status = "❄️ Oversold (Below Lower BB)"
                    
                    results.append({
                        "Symbol": sym,
                        "LTP (₹)": last_p,
                        "Day %": chg_pct,
                        "50 EMA (₹)": e50,
                        "BB Status": bb_status
                    })
            except Exception:
                continue
                
        status_text.text("Scan complete!")
        if results:
            res_df = pd.DataFrame(results)
            st.dataframe(res_df, use_container_width=True)
            
            oversold_stocks = [r["Symbol"] for r in results if "Oversold" in r["BB Status"]]
            breakout_stocks = [r["Symbol"] for r in results if "Breakout" in r["BB Status"]]
            
            c1, c2 = st.columns(2)
            with c1:
                st.success(f"🔥 **Breakout Stocks:** {', '.join(breakout_stocks) if breakout_stocks else 'None'}")
            with c2:
                st.info(f"❄️ **Oversold Stocks (Support Bounce candidates):** {', '.join(oversold_stocks) if oversold_stocks else 'None'}")
