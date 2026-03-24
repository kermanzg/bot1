from flask import Flask, request, jsonify
import ccxt, os, logging
from datetime import datetime

app = Flask(__name__)

API_KEY        = os.environ.get("BINANCE_API_KEY")
API_SECRET     = os.environ.get("BINANCE_API_SECRET")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "mi_clave_secreta")

exchange = ccxt.binance({
    "apiKey": API_KEY,
    "secret": API_SECRET,
    "options": {"defaultType": "spot"},
    "enableRateLimit": True,
})

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Sin datos JSON"}), 400
    if data.get("secret") != WEBHOOK_SECRET:
        return jsonify({"error": "No autorizado"}), 403
    symbol   = data.get("symbol", "BTC/USDT")
    side     = data.get("side", "").upper()
    quantity = float(data.get("quantity", 0.001))
    if side not in ("BUY", "SELL"):
        return jsonify({"error": "side debe ser BUY o SELL"}), 400
    log.info(f"Señal → {side} {quantity} {symbol}")
    try:
        if side == "BUY":
            order = exchange.create_market_buy_order(symbol, quantity)
        else:
            order = exchange.create_market_sell_order(symbol, quantity)
        return jsonify({"status": "ok", "orderId": order["id"]}), 200
    except Exception as e:
        log.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "online", "server": "Supertrend Bot"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
```
