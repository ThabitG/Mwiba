import os, asyncio, random, pytz, threading, json
from datetime import datetime
from metaapi_cloud_sdk import MetaApi
import aiohttp
from http.server import BaseHTTPRequestHandler, HTTPServer

# ================== ENV (HARDCODED FIX BY AI) ==================
META_API_TOKEN = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiIyOWU2NGU0YjYzNWE2MTkyODNjY2U5Mjc1M2ZhYWQ5OCIsImFjY2Vzc1J1bGVzIjpbeyJpZCI6InRyYWRpbmctYWNjb3VudC1tYW5hZ2VtZW50LWFwaSIsIm1ldGhvZHMiOlsidHJhZGluZy1hY2NvdW50LW1hbmFnZW1lbnQtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiXSwicmVzb3VyY2VzIjpbImFjY291bnQ6JFVTRVJfSUQkOmZhNTQ4ZGI3LTA4YjctNGY4YS1hY2E5LWIwYjUyODBhZjY5NCJdfSx7ImlkIjoibWV0YWFwaS1yZXN0LWFwaSIsIm1ldGhvZHMiOlsibWV0YWFwaS1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiYWNjb3VudDokVVNFUl9JRCQ6ZmE1NDhkYjctMDhiNy00ZjhhLWFjYTktYjBiNTI4MGFmNjk0Il19LHsiaWQiOiJtZXRhYXBpLXJwYy1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOndzOnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyJhY2NvdW50OiRVU0VSX0lEJDpmYTU0OGRiNy0wOGI3LTRmOGEtYWNhOS1iMGI1MjgwYWY2OTQiXX0seyJpZCI6Im1ldGFhcGktcmVhbC10aW1lLXN0cmVhbWluZy1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOndzOnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyJhY2NvdW50OiRVU0VSX0lEJDpmYTU0OGRiNy0wOGI3LTRmOGEtYWNhOS1iMGI1MjgwYWY2OTQiXX0seyJpZCI6Im1ldGFzdGF0cy1hcGkiLCJtZXRob2RzIjpbIm1ldGFzdGF0cy1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciJdLCJyZXNvdXJjZXMiOlsiYWNjb3VudDokVVNFUl9JRCQ6ZmE1NDhkYjctMDhiNy00ZjhhLWFjYTktYjBiNTI4MGFmNjk0Il19LHsiaWQiOiJyaXNrLW1hbmFnZW1lbnQtYXBpIiwibWV0aG9kcyI6WyJyaXNrLW1hbmFnZW1lbnQtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiXSwicmVzb3VyY2VzIjpbImFjY291bnQ6JFVTRVJfSUQkOmZhNTQ4ZGI3LTA4YjctNGY4YS1hY2E5LWIwYjUyODBhZjY5NCJdfV0sImlnbm9yZVJhdGVMaW1pdHMiOmZhbHNlLCJ0b2tlbklkIjoiMjAyMTAyMTMiLCJpbXBlcnNvbmF0ZWQiOmZhbHNlLCJyZWFsVXNlcklkIjoiMjllNjRlNGI2MzVhNjE5MjgzY2NlOTI3NTNmYWFkOTgiLCJpYXQiOjE3Njg2MDkwODMsImV4cCI6MTc3NjM4NTA4M30.m_sSEhsv6PIL7mn-XwNQ-ldnXlG2WYT4ng4mBtLm7l0gtf7u-ZbW9-Q0OyY_Z_mP9fiJMDpD5MKHdewJeYugygl8SAms8eybdbn6GVv6ZTz-JqwX1HDI-vXoMgHR3S_wn0bsjxRrHKL-uTfaZKnjDBHxTotNBfVgrGxLjW9EtRes4oShKcngRhWri_p-dAjXkD9m6mq-ARcO_XyU0ct1-Xm5mL_KFtAWGLkWtpz6df7o1tG-vgV6K38rGIJ5piCqYC-TWxKc3yXCHKnokoueBmeCuMAQSGkKsRDTMwxYnGeU5TdIK7_eNOzAip8mUz3u1eJJUcCYLljV67gMWWYAG5wKmBogHpHVfvrXtCpIaAoNBdpUNoQZEBfgMhYvrPsbu_mbYsMeL-r1w5ob39rDteczSSXe1nFyImYG_in779WVSG8psXxg7GcsMJISW7Dtt5M2-ZolExeWvGsCFwX2wux036EFt3fXPWgFp4aW_dcUifgCVbQeRizJ7FkPdaOZ2k62biYRDCTnIz_S5LLrlUaHfTVYd2XlD1d3seFc6_lZSvfRpQljMhGIC11aYB1DCRxQs6E38F1AY2Maawx8mCLhXukgQLFussIcTJcma3C3YOo588qjLY6_DEYOQPlRn1pWOON00n9-avqbwQpc-XcGEeQi8IfXW40ekHTrhYc"
ACCOUNT_ID = "fa548db7-08b7-4f8a-aca9-b0b5280af694"
TELEGRAM_TOKEN = "8166262150:AAFeM49GfLaSvnIOzrm5JWXQdtzhJUnUexw"
CHAT_ID = 2101969412

# ================== BOT STATE ==================
BOT_ACTIVE = True
LAST_UPDATE_ID = 0
STATS = {"wins":0, "losses":0}

# ================== TRADING CONFIG ==================
SYMBOLS = ["XAUUSD", "NAS100", "US30", "SPX500", "GER40"]
TIMEFRAME = "5m"
EMA_PERIOD = 50
RSI_PERIOD = 14
LOT = 0.01
MAX_POSITIONS = 3

LOCK1_PROFIT, LOCK1_SL = 1.5, 0.80
LOCK2_PROFIT, LOCK2_SL = 2.0, 1.40
FINAL_TP = 3.0
HARD_SL = -1.0

# ================== TELEGRAM ==================
async def tg_send(msg):
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    async with aiohttp.ClientSession() as s:
        try:
            async with s.post(url, json=payload, timeout=10) as r:
                return await r.json()
        except Exception as e:
            print(f"Telegram Send Error: {e}")

async def telegram_listener(conn):
    global BOT_ACTIVE, LAST_UPDATE_ID
    if not TELEGRAM_TOKEN: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    
    while True:
        try:
            async with aiohttp.ClientSession() as s:
                params = {"offset": LAST_UPDATE_ID + 1, "timeout": 30}
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
        except Exception as e:
            print(f"TG Listener Error: {e}")
        await asyncio.sleep(2)

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
    prices = [c["close"] for c in candles]
    k = 2/(period+1)
    e = prices[0]
    for p in prices[1:]:
        e = p*k+(1-k)*e
    return e

# ================== SCALPER CORE ==================
async def scalper(acc, conn):
    # Tuma meseji ya kuanza kazi Telegram
    await tg_send("⚔️ <b>MWIBA BOT V12 ONLINE</b>\nBot imeunganishwa na inaanza kuchambua soko.")
    
    while True:
        try:
            now = datetime.now()
            print(f"DEBUG: Scalper heartbeat {now} | Active: {BOT_ACTIVE}")
            
            if not BOT_ACTIVE:
                await asyncio.sleep(30); continue

            positions = await conn.get_positions()
            if len(positions) < MAX_POSITIONS:
                for sym in SYMBOLS:
                    if any(p["symbol"]==sym for p in positions): continue
                    
                    # FIXED: account object doesn't have get_candles, RPC connection does. 
                    # And use get_historical_candles
                    candles = await conn.get_historical_candles(sym, TIMEFRAME, 100)
                    if not candles: continue
                    
                    closes = [c["close"] for c in candles]
                    price = closes[-1]
                    e_val = ema(candles, EMA_PERIOD)
                    r_val = rsi(closes, RSI_PERIOD)

                    if price > e_val and r_val < 30:
                        await conn.create_market_buy_order(sym, LOT, 0, 0)
                        await tg_send(f"🚀 <b>BUY {sym}</b>\nPrice: {price}\nRSI: {r_val:.1f}")
                    elif price < e_val and r_val > 70:
                        await conn.create_market_sell_order(sym, LOT, 0, 0)
                        await tg_send(f"📉 <b>SELL {sym}</b>\nPrice: {price}\nRSI: {r_val:.1f}")
        except Exception as e:
            print(f"Scalper Main Loop Error: {e}")
        await asyncio.sleep(15)

# ================== HEALTH SERVER ==================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"MWIBA BOT IS ALIVE")

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

# ================== START BOT ==================
async def start_bot():
    while True:
        try:
            print("DEBUG: Connecting to MetaApi...")
            api = MetaApi(META_API_TOKEN)
            acc = await api.metatrader_account_api.get_account(ACCOUNT_ID)
            
            if acc.state != 'DEPLOYED':
                print("DEBUG: Account not deployed. Waiting...")
                await asyncio.sleep(10); continue

            conn = acc.get_rpc_connection()
            await conn.connect()
            await conn.wait_synchronized()
            print("DEBUG: Connection Synchronized!")

            await asyncio.gather(
                telegram_listener(conn),
                scalper(acc, conn)
            )
        except Exception as e:
            print(f"CRITICAL ERROR: {e}. Reconnecting in 10s...")
            await asyncio.sleep(10)

if __name__=="__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        pass
