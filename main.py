import os, asyncio, random, threading
from datetime import datetime
from metaapi_cloud_sdk import MetaApi
import aiohttp
from http.server import BaseHTTPRequestHandler, HTTPServer

# ================== CREDENTIALS ==================
META_API_TOKEN = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiIyOWU2NGU0YjYzNWE2MTkyODNjY2U5Mjc1M2ZhYWQ5OCIsImFjY2Vzc1J1bGVzIjpbeyJpZCI6InRyYWRpbmctYWNjb3VudC1tYW5hZ2VtZW50LWFwaSIsIm1ldGhvZHMiOlsidHJhZGluZy1hY2NvdW50LW1hbmFnZW1lbnQtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiXSwicmVzb3VyY2VzIjpbImFjY291bnQ6JFVTRVJfSUQkOmZhNTQ4ZGI3LTA4YjctNGY4YS1hY2E5LWIwYjUyODBhZjY5NCJdfSx7ImlkIjoibWV0YWFwaS1yZXN0LWFwaSIsIm1ldGhvZHMiOlsibWV0YWFwaS1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiYWNjb3VudDokVVNFUl9JRCQ6ZmE1NDhkYjctMDhiNy00ZjhhLWFjYTktYjBiNTI4MGFmNjk0Il19LHsiaWQiOiJtZXRhYXBpLXJwYy1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOndzOnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyJhY2NvdW50OiRVU0VSX0lEJDpmYTU0OGRiNy0wOGI3LTRmOGEtYWNhOS1iMGI1MjgwYWY2OTQiXX0seyJpZCI6Im1ldGFhcGktcmVhbC10aW1lLXN0cmVhbWluZy1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOndzOnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyJhY2NvdW50OiRVU0VSX0lEJDpmYTU0OGRiNy0wOGI3LTRmOGEtYWNhOS1iMGI1MjgwYWY2OTQiXX0seyJpZCI6Im1ldGFzdGF0cy1hcGkiLCJtZXRob2RzIjpbIm1ldGFzdGF0cy1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciJdLCJyZXNvdXJjZXMiOlsiYWNjb3VudDokVVNFUl9JRCQ6ZmE1NDhkYjctMDhiNy00ZjhhLWFjYTktYjBiNTI4MGFmNjk0Il19LHsiaWQiOiJyaXNrLW1hbmFnZW1lbnQtYXBpIiwibWV0aG9kcyI6WyJyaXNrLW1hbmFnZW1lbnQtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiXSwicmVzb3VyY2VzIjpbImFjY291bnQ6JFVTRVJfSUQkOmZhNTQ4ZGI3LTA4YjctNGY4YS1hY2E5LWIwYjUyODBhZjY5NCJdfV0sImlnbm9yZVJhdGVMaW1pdHMiOmZhbHNlLCJ0b2tlbklkIjoiMjAyMTAyMTMiLCJpbXBlcnNvbmF0ZWQiOmZhbHNlLCJyZWFsVXNlcklkIjoiMjllNjRlNGI2MzVhNjE5MjgzY2NlOTI3NTNmYWFkOTgiLCJpYXQiOjE3Njg2NTI3OTAsImV4cCI6MTc3NjQyODc5MH0.N-h8idvah5EGfIw6hOehU6naU5Fy7EyTGjMEDounROIqqWH1OJQSa0b8YX-LlfbYzjgo1rKbBs4aRFrqGvm7Mu3LbiX72wl-uFe1CnKj9Ap6ayTIkZob58cUK0vdvvlraE-jncDaFetdqpQqbTCWgpJrQpOXYrI0vqJdQ4nzPC8uf-x1UBK-5HD5sMg76SuE27SaliqMjIhVuIe5_esmgCoGiNtcGfZ6N7LAUngUZDiT7ndyRGygFJjsO1ljf6AeTEAAD3SDiDM_OV39vnGcvCAfVDOPml0f81vZXvk5W5zgtJhrkeoXs_kQ6dKCVwspm1jNClrP968iO_kuOs8OHYXPVWqxc63wyvPq26urmdvWPPgi6rMJPGWiFhkTKQTVQcWGUAzHqCQQft-Cn3_lrOhIpDJCydQXdBp0gD4qb_4zE9ooqJDjHK8RC3kwKy7e3bJKVWdE5-CbDV1vWoEUqxHtYd2gzQTwRZcXrsKxRWbbXqEHDq3y2fCwopqDsEPEMPdqmnSOt1rL4i9FZIX119ts6fZCyN-5qsoRQHvQXKhCNvz68XZmbPNeC15jUTlUd2nqQWH-3lcLlbrY8E5HwHN2Dny4fW8nw2t2on81eOW-ohhUW6ufxYL4-UI3UGMeDVJVGlZdplJEvfzRbSv11nkjGac3RykXc-GKxvHh1f0"
ACCOUNT_ID = "fa548db7-08b7-4f8a-aca9-b0b5280af694"
TELEGRAM_TOKEN = "8166262150:AAFeM49GfLa5vnIOzrM5JWXQdtzhJUnUexw"
CHAT_ID = 2101969412

# ================== BOT CONFIG ==================
BOT_ACTIVE = True
LAST_UPDATE_ID = 0
SYMBOLS = ["XAUUSD", "NAS100", "US30", "SPX500", "GER40"]
TIMEFRAME = "5m"
EMA_PERIOD = 50
RSI_PERIOD = 14
LOT = 0.01
MAX_POSITIONS = 3
FINAL_TP = 3.0
HARD_SL = -1.0

# ================== HELPERS ==================
async def tg_send(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    async with aiohttp.ClientSession() as s:
        try:
            await s.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=5)
        except: pass

def calculate_rsi(closes, period=14):
    if len(closes) < period + 1: return 50
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [abs(d) if d < 0 else 0 for d in deltas]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0: return 100
    return 100 - (100 / (1 + (avg_gain / avg_loss)))

def calculate_ema(closes, period):
    k = 2 / (period + 1)
    ema_val = sum(closes[:period]) / period
    for price in closes[period:]:
        ema_val = (price * k) + (ema_val * (1 - k))
    return ema_val

# ================== CORE LOGIC ==================
async def manage_position(conn, pid, symbol):
    while True:
        try:
            pos = next((p for p in await conn.get_positions() if p["id"] == pid), None)
            if not pos: return
            profit = float(pos["unrealizedProfit"])
            if profit >= FINAL_TP or profit <= HARD_SL:
                await conn.close_position(pid)
                await tg_send(f"{'🎯 TP' if profit > 0 else '❌ SL'} HIT: {symbol} | ${profit:.2f}")
                return
            await asyncio.sleep(5)
        except: break

async def scalper(conn):
    print("--- ⚔️ MWIBA SCALPER ACTIVE ---")
    await tg_send("⚔️ <b>MWIBA BOT V22 ONLINE</b>")
    while True:
        if BOT_ACTIVE:
            try:
                positions = await conn.get_positions()
                if len(positions) < MAX_POSITIONS:
                    for sym in SYMBOLS:
                        if any(p["symbol"] == sym for p in positions): continue
                        
                        # Correct way to get candles in RPC
                        candles = await conn.get_candles(sym, TIMEFRAME, None, 100)
                        if not candles: continue
                        
                        closes = [float(c["close"]) for c in candles]
                        price, ema_v, rsi_v = closes[-1], calculate_ema(closes, EMA_PERIOD), calculate_rsi(closes, RSI_PERIOD)
                        
                        if price > ema_v and rsi_v < 35:
                            res = await conn.create_market_buy_order(sym, LOT, 0, 0)
                            await tg_send(f"🚀 <b>BUY {sym}</b> | RSI: {rsi_v:.1f}")
                            asyncio.create_task(manage_position(conn, res["id"], sym))
                        elif price < ema_v and rsi_v > 65:
                            res = await conn.create_market_sell_order(sym, LOT, 0, 0)
                            await tg_send(f"📉 <b>SELL {sym}</b> | RSI: {rsi_v:.1f}")
                            asyncio.create_task(manage_position(conn, res["id"], sym))
                print(f"Scanning... {datetime.now().strftime('%H:%M:%S')}")
            except Exception as e: print(f"Error: {e}")
        await asyncio.sleep(30)

async def main():
    api = MetaApi(META_API_TOKEN)
    acc = await api.metatrader_account_api.get_account(ACCOUNT_ID)
    await acc.wait_connected()
    conn = acc.get_rpc_connection()
    await conn.connect()
    await conn.wait_synchronized()
    
    # Health check server
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', 8080), BaseHTTPRequestHandler).serve_forever(), daemon=True).start()
    await scalper(conn)

if __name__ == "__main__":
    asyncio.run(main())
