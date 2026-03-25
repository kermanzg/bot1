from flask import Flask, request
from binance.client import Client
import os, time, json

app = Flask(__name__)

API_KEY = os.environ.get("BINANCE_API_KEY")
API_SECRET = os.environ.get("BINANCE_API_SECRET")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")

client = Client(API_KEY, API_SECRET)

STATE_FILE = "state.json"

TAKE_PROFIT = 1.02
STOP_LOSS = 0.98
TRAILING = 0.005

# ========================
# STATE
# ========================
def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"in_position": False, "entry_price": 0, "peak_price": 0}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

state = load_state()

# ========================
# UTILS
# ========================
def get_price(symbol):
    return float(client.get_symbol_ticker(symbol=symbol)["price"])

def get_balance(asset):
    return float(client.get_asset_balance(asset=asset)["free"])

# ========================
# BACKGROUND CHECK
# ========================
def check_exit(symbol):
    global state

    if not state["in_position"]:
        return

    price = get_price(symbol)

    # actualizar máximo
    if price > state["peak_price"]:
        state["peak_price"] = price

    # trailing stop
    trailing_stop = state["peak_price"] * (1 - TRAILING)

    # condiciones salida
    if (
        price >= state["entry_price"] * TAKE_PROFIT or
        price <= state["entry_price"] * STOP_LOSS or
        price <= trailing_stop
    ):
        btc = get_balance("BTC")

        if btc > 0.00001:
            quantity = float(f"{btc:.5f}")

            client.create_order(
                symbol=symbol,
                side="SELL",
                type="MARKET",
                quantity=quantity
            )

            print(f"🔴 SELL automático a {price}")

            state = {"in_position": False, "entry_price": 0, "peak_price": 0}
            save_state(state)

# ========================
# ROUTES
# ========================
@app.route("/", methods=["GET"])
def home():
    return {"status": "running"}

@app.route("/webhook", methods=["POST"])
def webhook():
    global state

    data = request.get_json()

    if data.get("secret") != WEBHOOK_SECRET:
        return {"error": "unauthorized"}, 403

    symbol = data.get("symbol", "BTCEUR")

    if state["in_position"]:
        return {"status": "already in trade"}

    eur = get_balance("EUR")

    if eur < 5:
        return {"error": "not enough EUR"}

    amount = max(eur * 0.10, 6)

    order = client.create_order(
        symbol=symbol,
        side="BUY",
        type="MARKET",
        quoteOrderQty=round(amount, 2)
    )

    price = get_price(symbol)

    state = {
        "in_position": True,
        "entry_price": price,
        "peak_price": price
    }

    save_state(state)

    print(f"🟢 BUY a {price}")

    return {"status": "bought", "price": price}

# ========================
# LOOP
# ========================
import threading

def loop():
    while True:
        try:
            check_exit("BTCEUR")
        except Exception as e:
            print("Error loop:", e)
        time.sleep(5)

threading.Thread(target=loop, daemon=True).start()

# ========================
# START
# ========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
