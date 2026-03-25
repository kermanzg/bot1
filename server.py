from flask import Flask, request
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
# CLIENTE BINANCE
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
# TEST
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

    symbol = data.get("symbol", "BTCEUR")
    side = data.get("side")

    if side not in ["BUY", "SELL"]:
        return {"error": "invalid side"}, 400

    try:
        # ========================
        # BUY → usa % del balance €
        # ========================
        if side == "BUY":
            balance = client.get_asset_balance(asset="EUR")
            eur_balance = float(balance["free"])

            if eur_balance < 5:
                return {"error": "not enough EUR"}, 400

            # 🔥 FIX IMPORTANTE → mínimo 6€
            amount = max(eur_balance * 0.10, 6)

            order = client.create_order(
                symbol=symbol,
                side="BUY",
                type="MARKET",
                quoteOrderQty=round(amount, 2)
            )

        # ========================
        # SELL → vende todo el BTC
        # ========================
        else:
            balance = client.get_asset_balance(asset="BTC")
            btc_balance = float(balance["free"])

            if btc_balance <= 0:
                return {"error": "no BTC to sell"}, 400

            order = client.create_order(
                symbol=symbol,
                side="SELL",
                type="MARKET",
                quantity=round(btc_balance, 6)
            )

        return {
            "status": "success",
            "symbol": symbol,
            "side": side,
            "order": order
        }

    except Exception as e:
        return {"error": str(e)}, 500


# ========================
# START SERVER
# ========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
