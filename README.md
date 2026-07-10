# Crypto & Forex Signal Generator

AI-powered **crypto and forex signal generator** that combines **technical indicators** with **machine learning** to produce actionable buy/sell/hold insights.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Why This Project?](#why-this-project)
- [Tech Stack](#tech-stack)
- [System Architecture](#system-architecture)
- [Machine Learning Pipeline](#machine-learning-pipeline)
- [Data Preprocessing](#data-preprocessing)
- [Technical Indicators Used](#technical-indicators-used)
- [API and Frontend Integration](#api-and-frontend-integration)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [How to Run](#how-to-run)
- [Usage](#usage)
- [Example API Requests](#example-api-requests)
- [Interview / Viva Questions (with Answers)](#interview--viva-questions-with-answers)
- [Model Choices and Reasoning](#model-choices-and-reasoning)
- [Troubleshooting](#troubleshooting)
- [Future Improvements](#future-improvements)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This project predicts market movement and generates trading signals for crypto and forex pairs.
It uses:

- Historical OHLCV price data
- Technical indicators (trend, momentum, volatility)
- A supervised machine learning model
- A Flask backend exposing REST API endpoints
- A web frontend that sends HTTP requests and renders predictions

The end result is a practical end-to-end ML web application.

---

## Key Features

- ✅ Signal generation: **BUY / SELL / HOLD**
- ✅ Technical-indicator-based feature engineering
- ✅ ML-powered market direction prediction
- ✅ Flask REST API for inference
- ✅ Frontend connected via JSON over HTTP
- ✅ Modular structure for easy extension
- ✅ Ready for local development and deployment

---

## Why This Project?

Financial markets are noisy and difficult to interpret manually in real time. This project demonstrates how data science and machine learning can support decision-making by:

- Standardizing market analysis
- Reducing emotional bias
- Creating reproducible, testable signals
- Bridging backend ML with frontend product experience

> ⚠️ Educational purpose only. Not financial advice.

---

## Tech Stack

Based on repository language composition:

- **Python (56.3%)** – data processing, ML, backend API
- **JavaScript (31.1%)** – frontend logic and API calls
- **CSS (11.8%)** – styling/UI
- **HTML (0.8%)** – structure/templates

Core libraries/frameworks typically used in this stack:

- Flask
- Pandas
- NumPy
- scikit-learn
- (Optional) XGBoost
- yfinance / exchange APIs (depending on your data source)

---

## System Architecture

```text
Market Data Source (CSV/API)
          |
          v
  Data Preprocessing (Pandas)
          |
          v
 Feature Engineering (Indicators)
          |
          v
   ML Model Training/Evaluation
          |
          v
   Trained Model Serialization
          |
          v
 Flask Backend (REST API /predict)
          |
          v
Frontend (HTML/CSS/JS) -> JSON HTTP requests -> Signal Output
```

---

## Machine Learning Pipeline

1. Collect historical market data.
2. Clean and preprocess data.
3. Compute technical indicators.
4. Define target label (e.g., next-candle direction).
5. Split train/test sets.
6. Train classifier.
7. Evaluate with metrics (accuracy, precision, recall, F1).
8. Save model.
9. Serve prediction through Flask API.

---

## Data Preprocessing

A strong preprocessing stage is essential for market prediction quality.

### 1) Missing Values

- Detect using `isna()` / `isnull()`
- Handle by:
  - Forward fill / backward fill for time series continuity
  - Dropping rows only when unavoidable

### 2) Duplicate Removal

- Remove duplicate candles/rows to prevent bias:
  - `drop_duplicates()`

### 3) Datetime Handling

- Parse timestamps correctly
- Sort chronologically
- Set index to datetime when needed

### 4) Outlier Considerations

- Inspect extreme spikes
- Decide whether to keep, cap, or remove based on market context

### 5) Feature Scaling (if applicable)

- **Required** for distance/gradient-based models (e.g., Logistic Regression, SVM, Neural Nets)
- Often **not required** for tree models (Random Forest, XGBoost)
- Use `StandardScaler` or `MinMaxScaler` when needed

### 6) Feature Selection

- Keep high-signal features from indicators and price action
- Remove redundant/highly collinear features when useful
- Optionally use:
  - Correlation filtering
  - Feature importance
  - Recursive feature elimination

### 7) Train-Test Split Strategy

- Prefer time-aware split (avoid leakage)
- Do not shuffle blindly for sequential financial data

### 8) Class Imbalance Handling (if present)

- Check target distribution
- Apply class weights or resampling if labels are skewed

---

## Technical Indicators Used

Common indicators for this project style:

- **SMA / EMA** – trend direction
- **RSI** – momentum and overbought/oversold zones
- **MACD** – trend + momentum crossover behavior
- **Bollinger Bands** – volatility and mean-reversion zones
- **ATR** – volatility/risk sizing insight
- **Stochastic Oscillator** – momentum reversal signals

These indicators become model input features.

---

## API and Frontend Integration

The frontend communicates with Flask via **REST API**:

1. User enters pair/timeframe/input.
2. JavaScript sends HTTP request (`fetch`/Axios) to backend endpoint.
3. Payload is serialized as **JSON**.
4. Flask receives request, validates payload, runs model inference.
5. Flask returns prediction as **JSON**.
6. Frontend renders BUY/SELL/HOLD and confidence/metadata.

### Example Flow

- Frontend → `POST /predict`
- Headers: `Content-Type: application/json`
- Body: feature values or pair+timeframe
- Response: signal + probability/confidence

---

## Project Structure

```text
Crypto-Forex-Signal-Generator/
│
├── app.py / main.py               # Flask application entry point
├── requirements.txt               # Python dependencies
├── model/
│   ├── train_model.py             # Training script
│   ├── model.pkl                  # Saved model artifact
│   └── preprocess.py              # Feature engineering/preprocessing
├── data/
│   ├── raw/                       # Raw market data
│   └── processed/                 # Cleaned datasets
├── static/
│   ├── css/
│   └── js/
├── templates/
│   └── index.html                 # Frontend template
└── README.md
```

---

## Installation

### Prerequisites

- Python 3.9+
- pip
- (Optional) virtualenv
- Git

### Steps

```bash
# 1) Clone repository
git clone https://github.com/chamodyaaa/Crypto-Forex-Signal-Generator.git
cd Crypto-Forex-Signal-Generator

# 2) Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# 3) Install dependencies
pip install -r requirements.txt
```

---

## How to Run

### Option A: Run Flask App

```bash
python app.py
```

or

```bash
flask run
```

Then open:

- `http://127.0.0.1:5000/`

### Option B: Train Model First (if required)

```bash
python model/train_model.py
```

Then run the Flask server.

---

## Usage

1. Start backend server.
2. Open web UI in browser.
3. Select trading pair / market settings.
4. Submit request.
5. View generated signal and supporting metrics.

---

## Example API Requests

### Request

```http
POST /predict HTTP/1.1
Host: 127.0.0.1:5000
Content-Type: application/json
```

```json
{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "features": {
    "rsi": 62.1,
    "macd": 1.24,
    "ema_20": 67200.5,
    "ema_50": 66510.8,
    "atr": 420.6
  }
}
```

### Response

```json
{
  "signal": "BUY",
  "confidence": 0.81,
  "model": "RandomForestClassifier",
  "timestamp": "2026-07-10T12:00:00Z"
}
```

---

## Interview / Viva Questions (with Answers)

### 1) Why did you choose Python?

Python has a simple and readable syntax, which speeds up development. It also has a rich ecosystem for data analysis and machine learning (Pandas, NumPy, scikit-learn), and integrates easily with backend frameworks like Flask for serving models through APIs.

### 2) Why Flask instead of Django?

Flask is lightweight and minimal, which is ideal for ML API projects where we only need essential web features (routing, JSON responses, inference endpoints). Django is excellent for full-scale web apps but can be heavier than necessary for a focused prediction service.

### 3) Why Pandas?

Pandas is efficient and developer-friendly for tabular and time-series data. It simplifies cleaning, transformation, joining, rolling calculations, and indicator preparation—all crucial for financial ML pipelines.

### 4) How did your ML model work?

The model is trained on historical market data and technical-indicator-derived features. During inference, incoming feature values are transformed using the same preprocessing logic and passed into the trained model, which predicts the most likely market direction (BUY/SELL/HOLD or up/down class).

### 5) What algorithm did you use?

You can tailor this based on your implementation:

- If using **Random Forest**:
  - Ensemble of decision trees
  - Captures nonlinear relationships
  - Robust to noise and overfitting (vs single tree)
  - Works well with mixed indicator features

- If using **Logistic Regression**:
  - Fast, interpretable baseline classifier
  - Works well when relationships are close to linear in transformed feature space
  - Efficient for quick iteration and explainability

- If using **XGBoost**:
  - High predictive power via gradient boosting
  - Handles complex nonlinear interactions
  - Strong regularization controls
  - Often achieves top performance on structured/tabular datasets

> Update the README model name to exactly match your actual trained classifier for maximum credibility.

### 6) How was the frontend connected?

The frontend used JavaScript to send HTTP requests to Flask REST endpoints (e.g., `/predict`). Data was exchanged as JSON. Backend responses were parsed and dynamically rendered in the UI.

### 7) How did you preprocess the data?

- Removed duplicates to avoid repeated bias
- Handled missing values (fill/drop strategy based on context)
- Generated technical indicators as features
- Applied feature scaling when model type required it
- Selected relevant features using correlation/importance checks
- Performed train-test split with time-order awareness

---

## Model Choices and Reasoning

### Why Random Forest? (Common Choice)

- Good baseline for tabular indicator data
- Handles nonlinear boundaries
- Less sensitive to outliers
- Provides feature importance
- Minimal scaling requirements

### Why Logistic Regression? (If Simplicity Matters)

- Very fast training/inference
- Interpretable coefficients
- Great as an explainable baseline

### Why XGBoost? (If Accuracy Focused)

- Excellent performance in many tabular ML tasks
- Captures subtle feature interactions
- Advanced regularization and tuning flexibility

---

## Troubleshooting

- **ModuleNotFoundError**: ensure virtual environment is active and dependencies installed.
- **Model file not found**: run training script first and verify model path.
- **CORS issues** (separate frontend/backend): configure Flask CORS.
- **Incorrect predictions**: verify preprocessing consistency between training and inference.
- **API returns 400/500**: validate JSON payload schema and server logs.

---

## Future Improvements

- Backtesting engine and performance dashboard
- Live data streaming via WebSocket
- Risk management module (SL/TP sizing)
- Explainable AI (SHAP/LIME)
- Multi-model ensemble voting
- Dockerized deployment and CI/CD

---

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Open a pull request

---

## License

Add your preferred license (MIT/Apache-2.0/etc.) in a `LICENSE` file.

---

## Disclaimer

This project is for educational and research purposes only. It does not constitute financial advice, investment recommendation, or guaranteed trading performance.
