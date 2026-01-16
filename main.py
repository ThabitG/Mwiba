import os, asyncio, random, pytz
from datetime import datetime
from metaapi_cloud_sdk import MetaApi
import aiohttp
from http.server import BaseHTTPRequestHandler, HTTPServer

# ================== ENV (RENDER) ==================
META_API_TOKEN = os.getenv("META_API_TOKEN")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))

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
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    async with aiohttp.ClientSession() as s:
        try:
            await s.post(url, json=payload, timeout=5)
        except: pass

async def telegram_listener(conn):
    global BOT_ACTIVE, LAST_UPDATE_ID
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    async with aiohttp.ClientSession() as s:
        while True:
            try:
                params = {"offset": LAST_UPDATE_ID + 1, "timeout":10}
                r = await s.get(url, params=params)
                data = await r.json()
                for u in data.get("result", []):
                    LAST_UPDATE_ID = u["update_id"]
                    text = u.get("message", {}).get("text","").lower()

                    if text in ["/open", "/startbot"]:
                        BOT_ACTIVE = True
                        await tg_send("🟢 <b>MWIBA BOT OPEN</b>")
                    elif text in ["/close", "/stopbot"]:
                        BOT_ACTIVE = False
                        await tg_send("🔴 <b>MWIBA BOT CLOSED</b>")
                    elif text == "/status":
                        info = await conn.get_account_information()
                        pos = await conn.get_positions()
                        await tg_send(
                            f"📊 <b>STATUS</b>\nBalance: ${info['balance']:.2f}\nEquity: ${info['equity']:.2f}\nOpen Trades: {len(pos)}\nActive: {'YES' if BOT_ACTIVE else 'NO'}"
                        )
                    elif text == "/positions":
                        pos = await conn.get_positions()
                        if not pos: await tg_send("📂 No open positions")
                        else:
                            msg = "📂 <b>OPEN POSITIONS</b>\n"
                            for p in pos:
                                msg += f"{p['symbol']} | ${p['unrealizedProfit']:.2f}\n"
                            await tg_send(msg)
                    elif text == "/balance":
                        info = await conn.get_account_information()
                        await tg_send(f"💰 Balance: ${info['balance']:.2f}\nEquity: ${info['equity']:.2f}")
            except: pass
            await asyncio.sleep(5)

# ================== INDICATORS ==================
def rsi(closes, period=14):
    if len(closes) < period+1: return 50
    gains = losses = 0
    for i in range(-period, 0):
        diff = closes[i]-closes[i-1]
        gains += max(diff,0)
        losses += abs(min(diff,0))
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
    # London 08:00-11:30 GMT, NY 13:30-17:00 GMT
    now = datetime.utcnow()
    h = now.hour + now.minute/60
    london = 8 <= h <= 11.5
    ny = 13.5 <= h <= 17
    return london or ny

def news_block():
    # Simulate news filter
    return random.choice([False]*8+[True]*2)  # 20% chance block

# ================== SCALPER ==================
async def manage_position(conn, pos):
    global STATS, AI_HOURS
    pid = pos["id"]
    entry = float(pos["openPrice"])
    vol = float(pos["volume"])
    ptype = pos["type"]
    while True:
        positions = await conn.get_positions()
        pos = next((p for p in positions if p["id"]==pid), None)
        if not pos: return
        profit = float(pos["unrealizedProfit"])
        hour = datetime.utcnow().hour

        # Trailing stop
        if profit >= FINAL_TP:
            await conn.close_position(pid)
            STATS["wins"] +=1
            AI_HOURS[hour] = AI_HOURS.get(hour,0)+1
            await tg_send(f"🎯 <b>TARGET HIT</b> {pos['symbol']} ${profit:.2f}")
            return
        elif profit >= LOCK2_PROFIT:
            await conn.modify_position(pid, entry + LOCK2_SL if ptype=="POSITION_TYPE_BUY" else entry - LOCK2_SL,0)
        elif profit >= LOCK1_PROFIT:
            await conn.modify_position(pid, entry + LOCK1_SL if ptype=="POSITION_TYPE_BUY" else entry - LOCK1_SL,0)
        elif profit <= HARD_SL:
            await conn.close_position(pid)
            STATS["losses"] +=1
            AI_HOURS[hour] = AI_HOURS.get(hour,0)-1
            await tg_send(f"❌ <b>STOP LOSS HIT</b> {pos['symbol']} ${profit:.2f}")
            return
        await asyncio.sleep(2)

async def scalper(acc, conn):
    await tg_send("⚔️ <b>MWIBA BOT V12 ONLINE</b>")

    while True:
        if not BOT_ACTIVE:
            await asyncio.sleep(5)
            continue
        if not in_session() or news_block():
            await asyncio.sleep(5)
            continue

        positions = await conn.get_positions()
        if len(positions)>=MAX_POSITIONS:
            await asyncio.sleep(5)
            continue

        random.shuffle(SYMBOLS)
        for sym in SYMBOLS:
            if any(p["symbol"]==sym for p in positions):
                continue
            candles = await acc.get_candles(sym,TIMEFRAME,100)
            if not candles: continue
            closes = [c["close"] for c in candles]
            price = closes[-1]
            e = ema(candles,EMA_PERIOD)
            r = rsi(closes,RSI_PERIOD)

            # BUY
            if price>e and r<30:
                order = await conn.create_market_buy_order(sym,LOT,0,0)
                await tg_send(f"🚀 BUY {sym} | RSI {r:.1f}")
                asyncio.create_task(manage_position(conn, order))
                await asyncio.sleep(random.uniform(2,4))
            # SELL
            elif price<e and r>70:
                order = await conn.create_market_sell_order(sym,LOT,0,0)
                await tg_send(f"📉 SELL {sym} | RSI {r:.1f}")
                asyncio.create_task(manage_position(conn, order))
                await asyncio.sleep(random.uniform(2,4))

        await asyncio.sleep(10)

# ================== MAIN ==================
async def main():
    api = MetaApi(META_API_TOKEN)
    acc = await api.metatrader_account_api.get_account(ACCOUNT_ID)
    conn = acc.get_rpc_connection()
    await conn.connect()
    await conn.wait_synchronized()

    # Health server
    threading.Thread(target=lambda: HTTPServer(("0.0.0.0",int(os.environ.get("PORT",8080))),BaseHTTPRequestHandler).serve_forever(),daemon=True).start()

    await asyncio.gather(
        telegram_listener(conn),
        scalper(acc,conn)
    )

if __name__=="__main__":
    asyncio.run(main())
