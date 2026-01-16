import os, asyncio, random, pytz, datetime
from dotenv import load_dotenv
from metaapi_cloud_sdk import MetaApi
import telebot

# ================= LOAD ENV =================
load_dotenv()
META_API_TOKEN = os.getenv("META_API_TOKEN")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ================= GLOBAL STATE =================
BOT_ACTIVE = False
AI_WIN_HOURS = {}
STATS = {"wins": 0, "losses": 0}
SYMBOLS = ["EURUSD", "GBPUSD"]
LOT = 0.01

# ================= TELEGRAM COMMANDS =================
@bot.message_handler(commands=["startbot"])
def start_bot(msg):
    global BOT_ACTIVE
    BOT_ACTIVE = True
    bot.send_message(CHAT_ID, "🤖 BOT STARTED")

@bot.message_handler(commands=["stopbot"])
def stop_bot(msg):
    global BOT_ACTIVE
    BOT_ACTIVE = False
    bot.send_message(CHAT_ID, "⛔ BOT STOPPED")

@bot.message_handler(commands=["status"])
def status(msg):
    bot.send_message(CHAT_ID, f"📊 Bot Active: {BOT_ACTIVE}")

@bot.message_handler(commands=["stats"])
def stats(msg):
    text = f"🏆 Wins: {STATS['wins']}\n❌ Losses: {STATS['losses']}\n🧠 Learned Hours: {AI_WIN_HOURS}"
    bot.send_message(CHAT_ID, text)

# ================= TIME FILTER =================
def session_allowed():
    tz = pytz.timezone("Europe/London")
    hour = datetime.datetime.now(tz).hour
    return (8 <= hour <= 11) or (13 <= hour <= 16)

# ================= AI FILTER =================
def ai_hour_allowed():
    tz = pytz.timezone("Europe/London")
    hour = datetime.datetime.now(tz).hour
    if not AI_WIN_HOURS:
        return True
    return AI_WIN_HOURS.get(hour, 0) >= 0

# ================= NEWS FILTER (SAFE MOCK) =================
def news_block():
    return random.choice([False, False, False, True])  # simulate rare block

# ================= PROFIT MANAGEMENT =================
async def manage_position(conn, position):
    soft_sl = -0.8
    while True:
        pos = (await conn.get_positions()).get(position['id'])
        if not pos:
            return

        profit = pos['profit']

        if profit >= 3.0:
            await conn.close_position(position['id'])
            STATS["wins"] += 1
            hour = datetime.datetime.utcnow().hour
            AI_WIN_HOURS[hour] = AI_WIN_HOURS.get(hour, 0) + 1
            bot.send_message(CHAT_ID, "🎯 TARGET ACHIEVED +$3 ✅")
            return

        if profit >= 2.0:
            soft_sl = 1.40
            bot.send_message(CHAT_ID, "🔒 SL moved → $1.40")

        elif profit >= 1.5:
            soft_sl = 0.80
            bot.send_message(CHAT_ID, "🔒 SL moved → $0.80")

        if profit <= soft_sl:
            await conn.close_position(position['id'])
            STATS["losses"] += 1
            bot.send_message(CHAT_ID, f"❌ STOP HIT @ {profit}$")
            return

        await asyncio.sleep(2)

# ================= TRADE LOGIC =================
async def trade_loop():
    api = MetaApi(META_API_TOKEN)
    account = await api.metatrader_account_api.get_account(ACCOUNT_ID)
    await account.deploy()
    await account.wait_connected()
    conn = account.get_rpc_connection()
    await conn.connect()

    bot.send_message(CHAT_ID, "✅ Trading Engine Connected")

    while True:
        if not BOT_ACTIVE:
            await asyncio.sleep(2)
            continue

        if not session_allowed() or not ai_hour_allowed() or news_block():
            await asyncio.sleep(5)
            continue

        positions = await conn.get_positions()
        if positions:
            await asyncio.sleep(3)
            continue

        symbol = random.choice(SYMBOLS)
        order = await conn.create_market_buy_order(symbol, LOT)

        bot.send_message(CHAT_ID, f"📈 Trade Opened: {symbol}")
        asyncio.create_task(manage_position(conn, order))

        await asyncio.sleep(random.uniform(10, 20))

# ================= RUN =================
def run():
    loop = asyncio.get_event_loop()
    loop.create_task(trade_loop())
    bot.infinity_polling()

if __name__ == "__main__":
    run()
