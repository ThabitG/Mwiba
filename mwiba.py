import asyncio, os, threading, requests, time, math, random, aiohttp
from datetime import datetime, timezone
from metaapi_cloud_sdk import MetaApi
from http.server import BaseHTTPRequestHandler, HTTPServer

# ================== ENV VARIABLES ==================
TOKEN = os.getenv('META_API_TOKEN')
ACCOUNT_ID = os.getenv('ACCOUNT_ID')
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

# Remote Control State
BOT_ACTIVE = True 
_last_update_id = 0

# ================== CONFIGURATION ==================
# Majina kamili kama yalivyo kwa Broker wako
SYMBOLS = ["XAUUSD", "NAS100", "US30", "SPX500", "GER40"]
TIMEFRAME = '5m'
INSTITUTIONAL_PERIOD = 50
RSI_PERIOD = 14
ATR_PERIOD = 14

BASE_LOT = 0.01
MAX_SPREAD = 35 

# Sniper Profit-Locking Targets
JUMP_1_PROFIT = 1.20
JUMP_1_LOCK = 0.80
JUMP_2_PROFIT = 2.00
JUMP_2_LOCK = 1.30
HARD_TP = 3.00
HARD_SL_USD = 1.00

# ================== TELEGRAM MWIBA CONTROL ==================
async def check_remote_commands():
    """Commands: 'Mwiba Open' to Start | 'Mwiba Close' to Stop"""
    global BOT_ACTIVE, _last_update_id
    url = f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates"
    
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                params = {"offset": _last_update_id + 1, "timeout": 10}
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
                    if "result" in data:
                        for update in data["result"]:
                            _last_update_id = update["update_id"]
                            msg_text = update.get("message", {}).get("text", "").lower()
                            
                            if "mwiba close" in msg_text:
                                BOT_ACTIVE = False
                                await tg_report("🔴 <b>MWIBA BOT: CLOSED</b>\nStatus: Sleeping. No new entries will be taken.")
                            elif "mwiba open" in msg_text:
                                BOT_ACTIVE = True
                                await tg_report("🟢 <b>MWIBA BOT: OPEN</b>\nStatus: Hunting for institutional entries...")
            except: pass
            await asyncio.sleep(5)

async def tg_report(msg):
    """Non-blocking Telegram Notifications"""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, timeout=5) as resp: return await resp.json()
        except: pass

# ================== INSTITUTIONAL INDICATORS ==================
def rsi_logic(closes, period=14):
    if len(closes) < period + 1: return 50
    gains, losses = [], []
    for i in range(len(closes) - period, len(closes)):
        diff = closes[i] - closes[i-1]
        if diff >= 0: gains.append(diff)
        else: losses.append(abs(diff))
    ag, al = sum(gains)/period, sum(losses)/period
    if al == 0: return 100
    return 100 - (100 / (1 + (ag/al)))

def institutional_ema(candles, period):
    """Institutional calculation using Typical Price: (H+L+C)/3"""
    prices = [(c['high'] + c['low'] + c['close']) / 3 for c in candles]
    k = 2 / (period + 1)
    ema_val = prices[0]
    for p in prices[1:]: ema_val = p * k + ema_val * (1 - k)
    return ema_val

# ================== MWIBA SCALPING ENGINE ==================
async def scalper():
    global BOT_ACTIVE
    api = MetaApi(TOKEN)
    
    try:
        acc = await api.metatrader_account_api.get_account(ACCOUNT_ID)
        conn = acc.get_rpc_connection()
        await conn.connect()
        await conn.wait_synchronized()
        
        await tg_report("⚔️ <b>MWIBA V7.5 SNIPER DEPLOYED</b>\nWatching: <code>Gold & Top Indices</code>\nCommands: <code>Mwiba Open</code> / <code>Mwiba Close</code>")

        while True:
            if not BOT_ACTIVE:
                await asyncio.sleep(10); continue

            positions = await conn.get_positions()
            
            # --- 1. Position Management & ATR Trailing ---
            for p in positions:
                p_id, sym, vol = p['id'], p['symbol'], float(p['volume'])
                profit, entry = float(p['unrealizedProfit']), float(p['openPrice'])
                curr_sl = float(p.get('stopLoss') or 0)

                # Hard TP & SL Checks
                if profit >= HARD_TP:
                    await conn.close_position(p_id)
                    await tg_report(f"✅ <b>PROFIT: ${profit:.2f}</b>\nSymbol: {sym}")
                    continue
                if profit <= -HARD_SL_USD:
                    await conn.close_position(p_id)
                    await tg_report(f"❌ <b>LOSS: ${profit:.2f}</b>\nSymbol: {sym}")
                    continue

                # Sniper Step-Trailing Logic
                new_sl = None
                if profit >= JUMP_2_PROFIT:
                    dist = (JUMP_2_LOCK / (vol * 100)) if "XAU" in sym else 0.15
                    new_sl = entry + dist if p['type'] == 'POSITION_TYPE_BUY' else entry - dist
                elif profit >= JUMP_1_PROFIT:
                    dist = (JUMP_1_LOCK / (vol * 100)) if "XAU" in sym else 0.09
                    new_sl = entry + dist if p['type'] == 'POSITION_TYPE_BUY' else entry - dist

                if new_sl:
                    # Only move SL forward, never backward
                    if (p['type'] == 'POSITION_TYPE_BUY' and new_sl > curr_sl) or \
                       (p['type'] == 'POSITION_TYPE_SELL' and (curr_sl == 0 or new_sl < curr_sl)):
                        await conn.modify_position(p_id, round(new_sl, 2), 0)

            # --- 2. Sniper Entry Confirmation (Trend + Overextended) ---
            if len(positions) < 3: # Max 3 concurrent trades
                for sym in SYMBOLS:
                    # Skip if we already have a trade in this symbol
                    if any(pos['symbol'] == sym for pos in positions): continue
                    
                    candles = await conn.get_candles(sym, TIMEFRAME, 100)
                    if not candles: continue
                    
                    closes = [c['close'] for c in candles]
                    ema_val = institutional_ema(candles, INSTITUTIONAL_PERIOD)
                    rsi_val = rsi_logic(closes, RSI_PERIOD)
                    price = closes[-1]
                    
                    # Entry Confirmation: Trend + RSI Discount/Premium
                    # BUY: Trend is UP (Price > EMA) AND RSI < 30 (Dips)
                    if price > ema_val and rsi_val < 30:
                        await conn.create_market_buy_order(sym, BASE_LOT, round(price - 0.70, 2), 0)
                        await tg_report(f"🚀 <b>MWIBA BUY</b>\nSymbol: {sym}\nRSI: {rsi_val:.1f}")
                        await asyncio.sleep(5)

                    # SELL: Trend is DOWN (Price < EMA) AND RSI > 70 (Rips)
                    elif price < ema_val and rsi_val > 70:
                        await conn.create_market_sell_order(sym, BASE_LOT, round(price + 0.70, 2), 0)
                        await tg_report(f"📉 <b>MWIBA SELL</b>\nSymbol: {sym}\nRSI: {rsi_val:.1f}")
                        await asyncio.sleep(5)

            await asyncio.sleep(15)
    except Exception as e:
        print(f"Main Error: {e}")
        await asyncio.sleep(10)

# ================== RUN ==================
if __name__ == "__main__":
    # Health check for cloud uptime
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', 8080), BaseHTTPRequestHandler).serve_forever(), daemon=True).start()
    
    loop = asyncio.get_event_loop()
    loop.create_task(check_remote_commands()) # Telegram Listener
    loop.run_until_complete(scalper()) # Main Bot Engine
