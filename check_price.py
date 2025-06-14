
import json, os, time
from datetime import datetime
import requests
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

TOKEN_ID = "0xe9244d1c2ce9f06e46b7056d88f7b8b6d911e6b3"  # SUSD/USDC Pool ID on Velodrome V2
SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/velodrome-labs/velodrome-v2"
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
K_FACTOR = 0.8

def load_json(fn):
    if os.path.exists(fn):
        with open(fn, "r") as f:
            return json.load(f)
    return []

def save_json(fn, data):
    with open(fn, "w") as f:
        json.dump(data, f)

def fetch_price():
    client = Client(transport=RequestsHTTPTransport(url=SUBGRAPH_URL), fetch_schema_from_transport=True)
    q = gql("""
    {
      pair(id: \"%s\") {
        token0Price
      }
    }
    """) % TOKEN_ID
    res = client.execute(q)
    return float(res["pair"]["token0Price"])

def update_history():
    hist = load_json("price_history.json")
    now = int(time.time())
    hist = [h for h in hist if now - h["ts"] <= 86400]
    price = fetch_price()
    hist.append({"ts": now, "price": price})
    save_json("price_history.json", hist)
    prices = [h["price"] for h in hist]
    mn, mx = min(prices), max(prices)
    mid = (mn + mx) / 2
    rng = (mid * (1 - K_FACTOR), mid * (1 + K_FACTOR))
    return price, (mn, mx), rng

def notify(price, hist_range, monitor_range):
    msgs = load_json("message_log.json")
    text = (
        f"⚠️ [SUSD/USDC] レンジ外アラート！\n\n"
        f"現在価格: {price:.6f}\n"
        f"監視レンジ: {monitor_range[0]:.6f} - {monitor_range[1]:.6f}\n"
        f"24hレンジ: {hist_range[0]:.6f} - {hist_range[1]:.6f}\n\n"
        f"🕓 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
    )
    res = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": text}
    )
    mid = res.json()["result"]["message_id"]
    msgs.append(mid)
    while len(msgs) > 10:
        old = msgs.pop(0)
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage", data={"chat_id": CHAT_ID, "message_id": old})
    save_json("message_log.json", msgs)

if __name__ == "__main__":
    price, hist_range, mon_range = update_history()
    low, high = mon_range
    if price < low or price > high:
        notify(price, hist_range, mon_range)
