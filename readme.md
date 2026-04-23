# Crypto-Forex Signal Generator

AI-powered trading signal analysis for crypto and forex markets using:

- Rule-based technical analysis
- A trained machine learning classifier
- A Flask API backend
- A React + Vite frontend with TradingView charts

## What This Project Does

The application fetches market candle data, calculates technical indicators, generates rule-based signals, and combines them with an ML prediction to produce a final trading signal.

Supported asset types:

- Crypto (via Binance)
- Forex (via Twelve Data)

Supported timeframes:

- `15m`, `30m`, `1h`, `4h`, `1d`, `1w`

## Key Features

- Live market data fetching for crypto and forex
- Technical indicators:
  - RSI
  - EMA (20, 50)
  - MACD (line, signal, histogram)
- Rule-based signal engine
- ML-based signal prediction with confidence scores
- Combined final decision logic (rule + ML)
- Multi-symbol analysis from frontend (comma-separated input)
- TradingView embedded chart
- REST API for frontend or external integrations

## Project Structure

```text
Crypto-Forex-Signal-Generator/
	backend/
		api.py            # Flask API server
		app.py            # CLI runner (interactive or command args)
		data_fetcher.py   # Binance + Twelve Data integration
		indicators.py     # RSI / EMA / MACD calculations
		ml_model.py       # Feature engineering, training, inference
		strategy.py       # Rule logic + ML/rule signal combination
		utils.py          # Indicator validation helpers
	frontend/
		index.html
		package.json
		vite.config.js
		src/
			App.jsx         # Main UI and API integration
			TradingViewChart.jsx
			main.jsx
			styles.css
	models/             # Saved ML model (models/model.pkl)
	requirement.txt     # Python dependencies
	readme.md
```

## Tech Stack

- Backend: Python, Flask
- Frontend: React, Vite
- Data & Analysis: pandas, numpy
- ML: scikit-learn, joblib
- Data Providers:
  - Binance (crypto)
  - Twelve Data (forex)

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm
- Internet access (required for live market data)

## Setup and Run

### 1) Clone and open project

```bash
git clone <your-repo-url>
cd Crypto-Forex-Signal-Generator
```

### 2) Backend setup (Python)

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows (Git Bash):

```bash
source .venv/Scripts/activate
```

Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

Install Python dependencies:

```bash
pip install -r requirement.txt
```

### 3) Configure environment variables (optional but recommended)

Create a `.env` file in the project root:

```env
TWELVE_DATA_API_KEY=your_twelve_data_api_key
```

Notes:

- Forex requests require a valid `TWELVE_DATA_API_KEY`.
- Crypto requests use the Binance public endpoint through `python-binance`.

### 4) Start backend API

From project root:

```bash
python backend/api.py
```

The API runs on:

- `http://127.0.0.1:5000`

### 5) Start frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on:

- `http://127.0.0.1:5173`

Vite proxy is configured so frontend `/api/*` requests are forwarded to `http://127.0.0.1:5000`.

## API Endpoints

Base URL: `http://127.0.0.1:5000`

- `GET /api/health`
- `GET /api/asset-types`
- `GET /api/timeframes`
- `GET /api/symbols?asset_type=crypto&search=BTC`
- `POST /api/signal`

### `POST /api/signal` request body

```json
{
  "asset_type": "crypto",
  "symbol": "BTCUSDT",
  "timeframe": "1h"
}
```

### Example success response (shape)

```json
{
  "success": true,
  "asset_type": "crypto",
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "signal": {
    "rule_signal": "BUY",
    "rule_confidence": 54.2,
    "ml_signal": "BUY",
    "ml_confidence": 62.8,
    "final_signal": "BUY",
    "combined_confidence": 73.5,
    "price": 65321.12,
    "rsi": 58.4,
    "ema_20": 64911.02,
    "ema_50": 64240.55,
    "macd": 112.3301,
    "macd_signal": 98.7721,
    "reason": "...",
    "combined_reason": "..."
  },
  "latest_data": {
    "timestamp": "2026-04-22 11:00:00",
    "open": 65100.0,
    "high": 65400.0,
    "low": 64980.0,
    "close": 65321.12,
    "volume": 1042.55
  }
}
```

## CLI Mode (without frontend)

You can run analysis directly in terminal:

```bash
python backend/app.py
```

Or pass symbols as command-line args:

```bash
python backend/app.py BTCUSDT ETHUSDT EUR/USD
```

## ML Training Pipeline

Train and save the model:

```bash
python backend/ml_model.py
```

This trains a calibrated Random Forest model and saves it to:

- `models/model.pkl`

If the model file is missing at runtime, the strategy automatically falls back to rule-based behavior.

## How Signal Combination Works

The final signal is built from two systems:

- Rule-based signal from indicators and thresholds
- ML signal from the trained classifier

Combination logic in `backend/strategy.py`:

- If both agree, confidence is boosted
- If they disagree, weighted conflict resolution is applied
- Special handling reduces excessive HOLD bias

## Common Issues

### 1) Forex requests fail

Check that:

- `.env` exists in project root
- `TWELVE_DATA_API_KEY` is valid
- Symbol format is correct (example: `EUR/USD`)

### 2) "Not enough candles returned"

Try:

- Another symbol
- A larger timeframe
- Retrying later if provider rate limits are active

### 3) Frontend cannot call API

Check that:

- Backend is running on port `5000`
- Frontend is running with Vite dev server on `5173`
- `frontend/vite.config.js` proxy is unchanged

### 4) ML model not found

Run:

```bash
python backend/ml_model.py
```

## Notes and Disclaimer

- This project is for educational and research use.
- Signals are not financial advice.
- Always do your own risk management and independent validation before trading.
