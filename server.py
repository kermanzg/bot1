from flask import Flask, request, jsonify
from binance.client import Client
import os

app = Flask(__name__)

# ========================
# VARIABLES DE ENTORNO
# ========================
API_KEY = os.environ.get("BINANCE_API_KEY")
API_SECRET = os.environ.get("BINANCE_API_SECRET")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")

# ========================
# CLIENTE BINANCE (SEGURO)
# ========================
client = None

try:
    if API_KEY and API_SECRET:
        client = Client(API_KEY, API_SECRET)
        print("✅ Binance conectado")
    else:
        print("⚠️ Binance NO configurado")
except Exception as e:
    print("❌ Error conectando Binance:", e)

# ========================
# ROUTE TEST
# ========================
@app.route("/", methods=["GET"])
def home():
    return {"status": "running"}

# ========================
# WEBHOOK
# ========================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    # Validación básica
    if not data:
        return {"error": "no data"}, 400

    # Seguridad
    if data.get("secret") != WEBHOOK_SECRET:
        return {"error": "unauthorized"}, 403

    # Cliente disponible
    if client is None:
        return {"error": "binance not configured"}, 500

    # Parámetros
    symbol = data.get("symbol", "BTCEUR")
    side = data.get("side")
    quantity = float(data.get("quantity", 0.001))

    # Validación
    if side not in ["BUY", "SELL"]:
        return {"error": "invalid side"}, 400

    try:
        # ========================
        # ORDENES
        # ========================
        if side == "BUY":
            order = client.order_market_buy(
                symbol=symbol,
                quantity=quantity
            )
        else:
            order = client.order_market_sell(
                symbol=symbol,
                quantity=quantity
            )

        return {
            "status": "success",
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "order": order
        }

    except Exception as e:
        return {"error": str(e)}, 500


# ========================
# START SERVER (LOCAL)
# ========================
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
