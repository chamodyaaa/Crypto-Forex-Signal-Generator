from flask import Flask, request, jsonify
from data_fetcher import DataFetchError, get_market_data
from ml_model import add_indicators
from utils import validate_indicators
from strategy import generate_signal
import traceback

app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    """Allow the React frontend to call the API during development."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

# Available trading pairs
CRYPTO_PAIRS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT", 
    "DOGEUSDT",  "SOLUSDT"
]

FOREX_PAIRS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", 
    "USD/CAD", "AUD/USD", "NZD/USD", "EUR/GBP"
]

TIMEFRAMES = ["15m", "30m", "1h", "4h", "1d", "1w"]


@app.route("/api/asset-types", methods=["GET"])
def get_asset_types():
    """Get available asset types."""
    return jsonify({
        "asset_types": ["crypto", "forex"]
    })


@app.route("/api/timeframes", methods=["GET"])
def get_timeframes():
    """Get available timeframes."""
    return jsonify({
        "timeframes": TIMEFRAMES
    })


@app.route("/api/symbols", methods=["GET"])
def get_symbols():
    """Get symbol suggestions by asset type, optionally filtered by search query."""
    asset_type = request.args.get("asset_type", "crypto").lower()
    search = request.args.get("search", "").strip().upper()
    
    if asset_type == "crypto":
        symbols = CRYPTO_PAIRS
    elif asset_type == "forex":
        symbols = FOREX_PAIRS
    else:
        return jsonify({"error": "Invalid asset type"}), 400
    
    # Filter by search query
    if search:
        symbols = [s for s in symbols if search in s]
    
    return jsonify({
        "asset_type": asset_type,
        "symbols": symbols,
        "count": len(symbols),
        "note": "These are suggested pairs. You can enter any valid symbol."
    })


@app.route("/api/signal", methods=["POST"])
def get_signal():
    """Get trading signal for a selected asset."""
    try:
        data = request.get_json(silent=True) or {}
        
        # Validate required fields
        asset_type = data.get("asset_type", "").lower()
        symbol = data.get("symbol", "").upper()
        timeframe = data.get("timeframe", "1h")
        
        if not asset_type:
            return jsonify({"error": "asset_type is required"}), 400
        if not symbol:
            return jsonify({"error": "symbol is required"}), 400
        if asset_type not in ["crypto", "forex"]:
            return jsonify({"error": "Invalid asset_type. Must be 'crypto' or 'forex'"}), 400
        if timeframe not in TIMEFRAMES:
            return jsonify({"error": f"Invalid timeframe. Must be one of: {TIMEFRAMES}"}), 400
        
        # Note: Symbol validation is removed to allow custom symbols
        # The data fetcher will handle validation and throw appropriate errors
        
        print(f"\nProcessing: {symbol} ({asset_type}) - Timeframe: {timeframe}")
        
        # Fetch market data
        df = get_market_data(
            asset_type=asset_type,
            symbol=symbol,
            timeframe=timeframe
        )
        
        if df.empty:
            return jsonify({"error": "No market data available for this symbol"}), 400

        if len(df) < 35:
            return jsonify({"error": f"Not enough candles returned ({len(df)}). Try another timeframe/symbol."}), 400
        
        # Add all required indicators for ML model
        df = add_indicators(df)
        
        # Validate indicators
        validate_indicators(df, min_rows=35)
        
        # Generate signal
        signal = generate_signal(df)
        
        return jsonify({
            "success": True,
            "asset_type": asset_type,
            "symbol": symbol,
            "timeframe": timeframe,
            "signal": signal,
            "latest_data": {
                "timestamp": str(df.iloc[-1]["timestamp"]) if "timestamp" in df.columns else "N/A",
                "open": float(df.iloc[-1]["open"]),
                "high": float(df.iloc[-1]["high"]),
                "low": float(df.iloc[-1]["low"]),
                "close": float(df.iloc[-1]["close"]),
                "volume": float(df.iloc[-1]["volume"]) if "volume" in df.columns else None
            }
        })

    except DataFetchError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 502

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "message": "Crypto-Forex Signal Generator API is running"
    })


@app.route("/", methods=["GET"])
def index():
    """API documentation."""
    return jsonify({
        "name": "Crypto-Forex Signal Generator API",
        "version": "1.0",
        "endpoints": {
            "GET /api/health": "Health check",
            "GET /api/asset-types": "Get available asset types (crypto, forex)",
            "GET /api/timeframes": "Get available timeframes",
            "GET /api/symbols?asset_type=crypto&search=BTC": "Get symbols with optional search filter",
            "POST /api/signal": "Get trading signal (requires JSON body with asset_type, symbol, timeframe)"
        },
        "example_request": {
            "method": "POST",
            "url": "/api/signal",
            "body": {
                "asset_type": "crypto",
                "symbol": "BTCUSDT",
                "timeframe": "1h"
            }
        }
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
