import os
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

# ============================================================
# KALSHI BTC 15M BOT — WEBHOOK RECEIVER
# Phase 1: Receive + validate TradingView signals
# ============================================================

BOT_NAME = "kalshi_btc_15m"

# Must match or exceed the minimum score from TradingView
MIN_SCORE = 75

# Duplicate protection
last_signal = {
    "timestamp": None,
    "direction": None
}


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "bot": "Kalshi BTC 15M Bot",
        "mode": "SIGNAL ONLY",
        "kalshi_trading": False
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "server_time": int(time.time())
    })


@app.route("/tradingview", methods=["POST"])
def tradingview_webhook():

    # --------------------------------------------------------
    # 1. Read JSON from TradingView
    # --------------------------------------------------------

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "status": "rejected",
            "reason": "Invalid or missing JSON"
        }), 400

    print("\n======================================")
    print("TRADINGVIEW WEBHOOK RECEIVED")
    print("======================================")
    print(data)

    # --------------------------------------------------------
    # 2. Extract signal information
    # --------------------------------------------------------

    bot = data.get("bot")
    symbol = data.get("symbol")
    timeframe = str(data.get("timeframe"))
    direction = str(data.get("direction", "")).upper()
    quality = data.get("quality", "UNKNOWN")

    try:
        score = int(float(data.get("score", 0)))
        price = float(data.get("price", 0))
        timestamp = int(data.get("timestamp", 0))
    except (ValueError, TypeError):

        return jsonify({
            "status": "rejected",
            "reason": "Invalid numeric data"
        }), 400

    # --------------------------------------------------------
    # 3. Validate this is our TradingView bot
    # --------------------------------------------------------

    if bot != BOT_NAME:
        return jsonify({
            "status": "rejected",
            "reason": "Unknown bot"
        }), 400

    # --------------------------------------------------------
    # 4. Only allow 15-minute signals
    # --------------------------------------------------------

    if timeframe != "15":
        return jsonify({
            "status": "skipped",
            "reason": "Not a 15-minute signal"
        }), 200

    # --------------------------------------------------------
    # 5. Only allow UP / DOWN
    # --------------------------------------------------------

    if direction not in ["UP", "DOWN"]:
        return jsonify({
            "status": "rejected",
            "reason": "Direction must be UP or DOWN"
        }), 400

    # --------------------------------------------------------
    # 6. Minimum signal score
    # --------------------------------------------------------

    if score < MIN_SCORE:
        return jsonify({
            "status": "skipped",
            "reason": "Signal score too low",
            "score": score
        }), 200

    # --------------------------------------------------------
    # 7. Duplicate protection
    # --------------------------------------------------------

    if (
        last_signal["timestamp"] == timestamp
        and last_signal["direction"] == direction
    ):
        return jsonify({
            "status": "skipped",
            "reason": "Duplicate signal"
        }), 200

    last_signal["timestamp"] = timestamp
    last_signal["direction"] = direction

    # --------------------------------------------------------
    # 8. Signal accepted
    #
    # IMPORTANT:
    # NO REAL KALSHI ORDER IS PLACED YET.
    # --------------------------------------------------------

    print("--------------------------------------")
    print("VALID SIGNAL")
    print("--------------------------------------")
    print(f"Symbol:     {symbol}")
    print(f"Direction:  {direction}")
    print(f"Score:      {score}/100")
    print(f"Quality:    {quality}")
    print(f"BTC Price:  ${price:,.2f}")
    print(f"Timestamp:  {timestamp}")
    print("--------------------------------------")
    print("ACTION: SIGNAL ACCEPTED")
    print("KALSHI ORDER: DISABLED")
    print("======================================\n")

    return jsonify({
        "status": "accepted",
        "bot": BOT_NAME,
        "symbol": symbol,
        "direction": direction,
        "score": score,
        "quality": quality,
        "btc_price": price,
        "kalshi_order": False,
        "message": "Signal accepted. Kalshi execution is currently disabled."
    }), 200


# ============================================================
# ERROR HANDLER
# ============================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "message": "Route not found"
    }), 404


# ============================================================
# LOCAL DEVELOPMENT
# Render will use Gunicorn instead.
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
