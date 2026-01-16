import os, asyncio, random, pytz, threading
from datetime import datetime
from metaapi_cloud_sdk import MetaApi
import aiohttp
from http.server import BaseHTTPRequestHandler, HTTPServer

# ================== ENV (RENDER FIX) ==================
META_API_TOKEN = os.getenv("META_API_TOKEN")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")
# HAPA: Nimesahihisha majina ili yafanane na Render Variables zako
TELEGRAM_TOKEN = os.getenv("TG_TOKEN") 
CHAT_ID_RAW = os.getenv("TG_CHAT_ID")

# Error handling kwa ajili ya CHAT_ID
if CHAT_ID_RAW:
    CHAT_ID = int(CHAT_ID_RAW)
else:
    CHAT_ID = 0 # Itatoa error baadae badala ya kuua bot kikatili

# ================== BOT STATE ==================
BOT_ACTIVE = True
LAST_UPDATE_ID = 0
AI_HOURS = {}  # Hourly wins/losses for adaptive AI
STATS = {"wins":0, "losses":0}

# ================== TRADING CONFIG ==================
SYMBOLS = ["XAUUSD", "NAS100", "US30", "SPX500", "GER40"]
TIMEFRAME = "5m"
EMA_PERIOD = 50
RSI_PERIOD = 14
LOT = 0.01
MAX_POSITIONS = 3

# Profit / Stop logic
LOCK1_PROFIT, LOCK1_SL = 1.5, 0.80
LOCK2_PROFIT, LOCK2_SL = 2.0, 1.40
FINAL_TP = 3.0
HARD_SL = -1.0

# Spread check (points)
MAX_SPREAD = 35

# ================== TELEGRAM ==================
async def tg_send(msg):
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    async with aiohttp.ClientSession() as s:
        try:
            await s.post(url, json=payload, timeout=5)
        except: pass

async def telegram_listener(conn):
    global BOT_ACTIVE, LAST_UPDATE_ID
    if not TELEGRAM_TOKEN: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    async with aiohttp.ClientSession() as s:
        while True:
            try:
                params = {"offset": LAST_UPDATE_ID + 1, "timeout":10}
                async with s.get(url, params=params) as r:
                    data = await r.json()
                    for u in data.get("result", []):
                        LAST_UPDATE_ID = u["update_id"]
                        msg = u.get("message", {})
                        text = msg.get("text","").lower()

                        if text in ["/open", "/startbot", "mwiba open"]:
                            BOT_ACTIVE = True
                            await tg_send("🟢 <b>MWIBA BOT OPEN</b>")
                        elif text in ["/close", "/stopbot", "mwiba close"]:
                            BOT_ACTIVE = False
                            await tg_send("🔴 <b>MWIBA BOT CLOSED</b>")
                        elif text in ["/status", "mwiba status"]:
                            info = await conn.get_account_information()
                            pos = await conn.get_positions()
                            await tg_send(
                                f"📊 <b>STATUS</b>\nBalance: ${info['balance']:.2f}\nEquity: ${info['equity']:.2f}\nOpen Trades: {len(pos)}\nActive: {'YES' if BOT_ACTIVE else 'NO'}"
                            )
                        elif text in ["/positions", "mwiba positions"]:
                            pos = await conn.get_positions()
                            if not pos: await tg_send("📂 No open positions")
                            else:
                                msg_out = "📂 <b>OPEN POSITIONS</b>\n"
                                for p in pos:
                                    msg_out += f"{p['symbol']} | ${p['unrealizedProfit']:.2f}\n"
                                await tg_send(msg_out)
            except: pass
            await asyncio.sleep(5)

# ================== INDICATORS ==================
def rsi(closes, period=14):
    if len(closes) < period+1: return 50
    gains = losses = 0
    for i in range(-period, 0):
        diff = closes[i]-closes[i-1]
        if diff >= 0: gains += diff
        else: losses += abs(diff)
    if losses==0: return 100
    rs = gains/losses
    return 100-(100/(1+rs))

def ema(candles, period):
    prices = [(c["high"]+c["low"]+c["close"])/3 for c in candles]
    k = 2/(period+1)
    e = prices[0]
    for p in prices[1:]:
        e = p*k+(1-k)*e
    return e

# ================== SESSION & NEWS ==================
def in_session():
    now = datetime.utcnow()
    h = now.hour + now.minute/60
    london = 8 <= h <= 11.5
    ny = 13.5 <= h <= 17
    return london or ny

# ================== SCALPER ==================
async def manage_position(conn, pos_id, sym, entry, ptype):
    global STATS, AI_HOURS
    while True:
        try:
            positions = await conn.get_positions()
            pos = next((p for p in positions if p["id"]==pos_id), None)
            if not pos: return
            
            profit = float(pos["unrealizedProfit"])
            hour = datetime.utcnow().hour

            if profit >= FINAL_TP:
                await conn.close_position(pos_id)
                STATS["wins"] +=1
                AI_HOURS[hour] = AI_HOURS.get(hour,0)+1
                await tg_send(f"🎯 <b>TARGET HIT</b> {sym} ${profit:.2f}")
                return
            elif profit >= LOCK2_PROFIT:
                sl = entry + LOCK2_SL if ptype=="POSITION_TYPE_BUY" else entry - LOCK2_SL
                await conn.modify_position(pos_id, round(sl, 2), 0)
            elif profit >= LOCK1_PROFIT:
                sl = entry + LOCK1_SL if ptype=="POSITION_TYPE_BUY" else entry - LOCK1_SL
                await conn.modify_position(pos_id, round(sl, 2), 0)
            elif profit <= HARD_SL:
                await conn.close_position(pos_id)
                STATS["losses"] +=1
                AI_HOURS[hour] = AI_HOURS.get(hour,0)-1
                await tg_send(f"❌ <b>STOP LOSS HIT</b> {sym} ${profit:.2f}")
                return
        except: pass
        await asyncio.sleep(5)

async def scalper(acc, conn):
    await tg_send("⚔️ <b>MWIBA BOT V12 ONLINE</b>")
    while True:
        if not BOT_ACTIVE or not in_session():
            await asyncio.sleep(10); continue

        try:
            positions = await conn.get_positions()
            if len(positions) < MAX_POSITIONS:
                shuffled_syms = list(SYMBOLS)
                random.shuffle(shuffled_syms)
                for sym in shuffled_syms:
                    if any(p["symbol"]==sym for p in positions): continue
                    
                    candles = await acc.get_candles(sym, TIMEFRAME, 100)
                    if not candles: continue
                    closes = [c["close"] for c in candles]
                    price = closes[-1]
                    e_val = ema(candles, EMA_PERIOD)
                    r_val = rsi(closes, RSI_PERIOD)

                    if price > e_val and r_val < 30:
                        order = await conn.create_market_buy_order(sym, LOT, 0, 0)
                        await tg_send(f"🚀 BUY {sym} | RSI {r_val:.1f}")
                        asyncio.create_task(manage_position(conn, order["id"], sym, price, "POSITION_TYPE_BUY"))
                    elif price < e_val and r_val > 70:
                        order = await conn.create_market_sell_order(sym, LOT, 0, 0)
                        await tg_send(f"📉 SELL {sym} | RSI {r_val:.1f}")
                        asyncio.create_task(manage_position(conn, order["id"], sym, price, "POSITION_TYPE_SELL"))
        except: pass
        await asyncio.sleep(15)

# ================== MAIN ==================
async def main():
    api = MetaApi(META_API_TOKEN)
    acc = await api.metatrader_account_api.get_account(ACCOUNT_ID)
    conn = acc.get_rpc_connection()
    await conn.connect()
    await conn.wait_synchronized()

    # Health server
    port = int(os.environ.get("PORT", 8080))
    threading.Thread(target=lambda: HTTPServer(("0.0.0.0", port), BaseHTTPRequestHandler).serve_forever(), daemon=True).start()

    await asyncio.gather(
        telegram_listener(conn),
        scalper(acc, conn)
    )

if __name__=="__main__":
    asyncio.run(main())
