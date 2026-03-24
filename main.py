from flask import Flask, request, jsonify
from binance.client import Client
from binance.enums import *
import os

from flask import Flask

app = Flask(__name__)

API_KEY = os.environ.get("BINANCE_API_KEY")
API_SECRET = os.environ.get("BINANCE_API_SECRET")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")

client = Client(API_KEY, API_SECRET)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if data.get("secret") != WEBHOOK_SECRET:
        return {"error": "unauthorized"}, 403

    symbol = data.get("symbol", "BTCUSDT")
    side = data.get("side")
    quantity = data.get("quantity", "0.001")

    try:
        order = client.create_order(
            symbol=symbol,
            side=SIDE_BUY if side == "BUY" else SIDE_SELL,
            type=ORDER_TYPE_MARKET,
            quantity=quantity
        )
        return {"status": "ok", "order": order}

    except Exception as e:
        return {"error": str(e)}

@app.route("/")
def home():
    return {"status": "running"}
