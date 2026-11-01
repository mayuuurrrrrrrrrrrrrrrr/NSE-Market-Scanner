import os
import time
import requests
import html
from dotenv import load_dotenv
from free_market_scanner import analyze_stock, NIFTY_50_SYMBOLS

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or "8907211670:AAHipPtOpXLetDzsU8vODEhewM_noSbasBo"
ADMIN_CHAT_ID = os.getenv("TELEGRAM_CHAT_IDS_01") or "8528995878"

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_telegram_message(chat_id, text, parse_mode="HTML"):
    """Sends a formatted message to a Telegram chat."""
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

def format_telegram_stock_card(data):
    """Formats a rich HTML card for Telegram messages."""
    sym = data["symbol"]
    ltp = data["ltp"]
    chg = data["day_change"]
    piv = data["pivots"]
    ema = data["ema_data"]
    fund = data["fundamentals"]
    
    msg = [
        f"📊 <b>{sym} | ₹{ltp} ({chg})</b>",
        "━━━━━━━━━━━━━━━━━━━━━",
        f"🎯 <b>Trend Signal:</b> {ema['trend']}",
        f"📊 <b>52W Range:</b> ₹{data['52w_low']} {data['range_bar']} ₹{data['52w_high']}",
        f"⚡ <b>Bollinger Band:</b> {data['bb_status']}",
        f"   • Upper: ₹{data['bb_upper']} | Lower: ₹{data['bb_lower']}",
        "",
        "📐 <b>Fibonacci Pivots (Daily):</b>",
        f"   • R3: ₹{piv['r3']} | R2: ₹{piv['r2']} | R1: ₹{piv['r1']}",
        f"   • <b>Pivot: ₹{piv['p']}</b>",
        f"   • S1: ₹{piv['s1']} | S2: ₹{piv['s2']} | S3: ₹{piv['s3']}",
        "",
        "📉 <b>Moving Averages (EMA):</b>",
        f"   • Daily 50 EMA: {ema['dema50_str']}",
        f"   • Daily 200 EMA: {ema['dema200_str']}",
        f"   • Weekly 50 EMA: {ema['wema50_str']}",
    ]
    
    if data.get("projections"):
        msg.append("")
        msg.append("🔮 <b>Statistical Price Projections:</b>")
        for k, v in data["projections"].items():
            msg.append(f"   • {k}: <b>{v}</b>")
            
    msg.append("")
    msg.append("🏢 <b>Fundamentals (Screener.in):</b>")
    msg.append(f"   • Market Cap: {fund['market_cap']} | P/E: {fund['pe']}")
    msg.append(f"   • YoY Sales Growth: {fund['sales_growth']}")
    msg.append(f"   • Shareholding: Promoter: {fund['promoter_hold']} | FII: {fund['fii_hold']} | DII: {fund['dii_hold']}")
    
    if data.get("news"):
        msg.append("")
        msg.append("📰 <b>Recent News:</b>")
        for n in data["news"][:3]:
            clean_n = html.escape(n)
            msg.append(f"   {clean_n}")
            
    msg.append("━━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(msg)

def handle_nifty50_scan(chat_id):
    """Performs bulk scan and sends summary directly to Telegram."""
    send_telegram_message(chat_id, "⏳ <i>Scanning NIFTY 50 universe for Breakout & Oversold setups... Please wait ~15 seconds.</i>")
    
    breakouts = []
    oversold = []
    
    for sym in NIFTY_50_SYMBOLS:
        try:
            analysis, err = analyze_stock(sym, include_extras=False)
            if not analysis:
                continue
            bb_st = analysis["bb_status"]
            ltp = analysis["ltp"]
            chg = analysis["day_change"]
            
            if "Breakout" in bb_st:
                breakouts.append(f"🔥 <b>{sym}</b>: ₹{ltp} ({chg})")
            elif "Oversold" in bb_st:
                oversold.append(f"❄️ <b>{sym}</b>: ₹{ltp} ({chg})")
        except Exception:
            continue
            
    msg = [
        "🚀 <b>NIFTY 50 UNIVERSE SCAN RESULTS</b>",
        "━━━━━━━━━━━━━━━━━━━━━",
        f"🔥 <b>Upper Bollinger Breakouts ({len(breakouts)}):</b>",
        "\n".join(breakouts) if breakouts else "   <i>None currently</i>",
        "",
        f"❄️ <b>Oversold / Support Bounce ({len(oversold)}):</b>",
        "\n".join(oversold) if oversold else "   <i>None currently</i>",
        "━━━━━━━━━━━━━━━━━━━━━",
        "💡 <i>Tip: Send any stock symbol (e.g. RELIANCE, TCS) for a deep dive!</i>"
    ]
    send_telegram_message(chat_id, "\n".join(msg))

def run_bot():
    """Main polling loop for the Telegram bot."""
    print("=" * 60)
    print("🤖 Telegram Algo-Scanner Bot is now LIVE!")
    print(f"📡 Bot: @mystockscanner7bot")
    print("=" * 60)
    print("Listening for incoming messages on Telegram...")
    
    last_update_id = 0
    
    while True:
        try:
            url = f"{BASE_URL}/getUpdates?offset={last_update_id + 1}&timeout=30"
            resp = requests.get(url, timeout=35)
            
            if resp.status_code != 200:
                time.sleep(2)
                continue
                
            data = resp.json()
            if not data.get("ok"):
                time.sleep(2)
                continue
                
            for update in data.get("result", []):
                last_update_id = update["update_id"]
                message = update.get("message", {})
                chat_id = message.get("chat", {}).get("id")
                text = message.get("text", "").strip()
                
                if not chat_id or not text:
                    continue
                    
                print(f"📩 Received from {chat_id}: '{text}'")
                
                # Command routing
                cmd = text.upper()
                if cmd in ["/START", "/HELP"]:
                    welcome = (
                        "👋 <b>Welcome to Algo Trading Suite Bot!</b>\n\n"
                        "I provide real-time Indian stock market scans, Fibonacci Pivots, Bollinger Bands, and financial ratios.\n\n"
                        "<b>Available Commands:</b>\n"
                        "• Send any stock symbol: <code>RELIANCE</code>, <code>TCS</code>, <code>SBIN</code>, <code>INFY</code>\n"
                        "• <code>/scan</code> or <code>/nifty50</code> : Scan entire NIFTY 50 universe\n"
                        "• <code>/help</code> : Show this help menu"
                    )
                    send_telegram_message(chat_id, welcome)
                elif cmd in ["/SCAN", "/NIFTY50", "SCAN", "NIFTY50"]:
                    handle_nifty50_scan(chat_id)
                else:
                    # Stock symbol lookup
                    stock_symbol = text.replace("/stock", "").replace("/STOCK", "").strip().upper()
                    send_telegram_message(chat_id, f"🔍 <i>Fetching deep analysis for {stock_symbol}...</i>")
                    analysis, err = analyze_stock(stock_symbol, include_extras=True)
                    if analysis:
                        card = format_telegram_stock_card(analysis)
                        send_telegram_message(chat_id, card)
                    else:
                        send_telegram_message(chat_id, f"❌ <b>Error:</b> {err}\n<i>Please verify the NSE symbol (e.g. RELIANCE, TCS, INFY).</i>")
                        
        except requests.exceptions.RequestException as req_err:
            time.sleep(3)
        except Exception as e:
            print(f"Bot error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    run_bot()
