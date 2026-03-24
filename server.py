from flask import Flask, request, jsonify
from binance.client import Client
from binance.enums import *
import hmac, hashlib, os, logging
from datetime import datetime

app = Flask(__name__)

# ─────────────────────────────────────────
# CONFIGURACIÓN — pon tus claves en Railway
# como variables de entorno, nunca en código
# ─────────────────────────────────────────
API_KEY     = os.environ.get("BINANCE_API_KEY")
API_SECRET  = os.environ.get("BINANCE_API_SECRET")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "mi_clave_secreta")

client = Client(API_KEY, API_SECRET)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ─────────────────────────────────────────
# WEBHOOK — recibe alertas de TradingView
# ─────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Sin datos JSON"}), 400

    # Verificación de seguridad con clave secreta
    if data.get("secret") != WEBHOOK_SECRET:
        log.warning("⚠️  Intento de acceso con clave incorrecta")
        return jsonify({"error": "No autorizado"}), 403

    symbol   = data.get("symbol", "BTCUSDT")
    side     = data.get("side", "").upper()       # BUY o SELL
    quantity = data.get("quantity", "0.001")

    if side not in ("BUY", "SELL"):
        return jsonify({"error": "side debe ser BUY o SELL"}), 400

    log.info(f"📨 Señal recibida → {side} {quantity} {symbol}")

    try:
        order = place_order(symbol, side, quantity)
        log.info(f"✅ Orden ejecutada: {order}")
        return jsonify({"status": "ok", "order": order}), 200
    except Exception as e:
        log.error(f"❌ Error al ejecutar orden: {e}")
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────
# FUNCIÓN — ejecuta orden en Binance SPOT
# ─────────────────────────────────────────
def place_order(symbol, side, quantity):
    order = client.create_order(
        symbol    = symbol,
        side      = SIDE_BUY if side == "BUY" else SIDE_SELL,
        type      = ORDER_TYPE_MARKET,
        quantity  = quantity
    )
    return {
        "orderId"    : order["orderId"],
        "symbol"     : order["symbol"],
        "side"       : order["side"],
        "status"     : order["status"],
        "quantity"   : order["executedQty"],
        "time"       : datetime.utcnow().isoformat()
    }


# ─────────────────────────────────────────
# RUTA DE ESTADO — para verificar que vive
# ─────────────────────────────────────────
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "online", "server": "Supertrend Bot"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
