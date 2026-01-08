# 📘 AI Trading Hub - API Documentation v2.0

**Backend Version:** 2.0.0 (Production Ready)  
**Base URL:** `http://localhost:8000`  
**Authentication:** Bearer Token (JWT)

---

## 🌟 Introduction

The AI Trading Hub API provides AI-based financial market analysis services, including:

- **Deep Learning (LSTM/PPO):** Price direction prediction.
- **Bandarmology (IDX):** Detection of accumulation/distribution by large players.
- **Whale Detector (Forex):** Tracking large money movements (Smart Money Concepts).
- **Pattern Recognition:** Detection of candlestick patterns (Engulfing, Doji, etc.).
- **Automated Pipeline:** Continuous Training, Validation, and Deployment of models.

---

## 🔐 1. Authentication & Users

### Register

`POST /auth/register`
Registers a new user.

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "Trader Pro"
}
```

### Login

`POST /auth/token`
Obtains an Access Token (JWT).

**Form Data:**

- `username` (email)
- `password`

**Response:**

```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

### User Profile

`GET /user/me`
Retrieves personal data, role (Free/Premium), and request quota.

### Request Upgrade

`POST /user/request-upgrade`
Requests an upgrade to a higher membership level.

**Request Body:**

```json
{
  "target_role": "premium" // or "enterprise"
}
```

## 📡 2. Real-Time Market Data

### Dashboard Stream

`GET /dashboard/all`
Retrieves the latest snapshot of signals for all monitored assets. Data is sourced from the in-memory signal bus.

**Output:** List of signals (Symbol, Action, Price, Confidence, AI Analysis).

### WebSocket Stream

`WS /ws/market/{symbol}`
Real-time connection for live prices and signals per second.

**URL Example:** ws://localhost:8000/ws/market/BBCA.JK

**Data:** JSON object containing OHLC, AI probabilities, and anomaly detection.

## 🧠 3. AI Pipeline (Auto-ML)

New feature for independently training and optimizing models.

### Run Optimization

`POST /pipeline/optimize/{symbol}`
Runs a complete cycle: Train Candidate -> Backtest Validation -> Deploy to Live.

**Parameters:**

- `target_win_rate` (Optional, default 60.0): Minimum win rate required for model deployment.

**Response:** Report of training steps and validation statistics.

## 📈 4. Backtesting

Test strategies before live trading.

### Run Backtest

`POST /backtest/run`
Simulates trading using historical data.

**Request Body:**

```json
{
  "symbol": "GOTO.JK",
  "period": "1y", // 1mo, 6mo, 1y, 2y
  "strategy": "ai_ppo", // ai_ppo, macd, rsi
  "initial_balance": 100000000
}
```

**Response:** ROI, Win Rate, Max Drawdown, Equity Curve.

## 🚨 5. Alerts & Screener

### Create Alert

`POST /alerts/create`
Sets an alarm for price or technical conditions.

**Request Body:**

```json
{
  "symbol": "XAUUSD",
  "condition": "ABOVE",
  "price": 2400.0,
  "note": "Gold Breakout"
}
```

### Market Screener

`POST /screener/scan`
Filters stocks/forex based on AI criteria.

**Request Body:**

```json
{
  "market": "IDX", // IDX, FOREX, CRYPTO
  "min_score": 70, // Minimum Bandarmology/AI score
  "trend": "UPTREND"
}
```

## 📝 6. Trading Journal

### Log Trade

`POST /journal/add`
Records manual or automatic trading positions.

**Request Body:**

```json
{
  "symbol": "BTC-USD",
  "action": "BUY",
  "entry_price": 45000,
  "lot_size": 0.1,
  "reason": "AI Signal + News"
}
```

### Performance Stats

`GET /journal/stats`
Views personal trading performance statistics (Win Rate, Profit Factor).

## 🛠 7. Admin Operations

(Accessible only by Role: ADMIN)

### View Upgrade Queue

`GET /admin/upgrade-queue`
Views the list of users requesting account upgrades.

### Execute Upgrade

`POST /admin/execute-upgrade`
Approves or rejects upgrade requests.

**Request Body:**

```json
{
  "request_id": "65e...",
  "action": "APPROVE", // or "REJECT"
  "note": "Payment received"
}
```

## ℹ️ Asset Configuration Notes

The system now uses Auto-Detection for asset configuration:

- Suffix .JK → Automatically considered Indonesian Stocks (1 Lot = 100 Shares).
- Suffix =X → Automatically considered Forex.
- JPY Pairs → Pip Scale 100.
- Other Pairs → Pip Scale 10000.
- Suffix -USD → Automatically considered Crypto.
- Others → Considered US Stocks (1 Lot = 1 Share).

You no longer need to manually register each symbol in config_assets.py.

```

```
