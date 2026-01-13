# 📘 AI Trading Hub - API Documentation v2.1

**Backend Version:** 2.1.0 (Production Ready)
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
  "password": "securepassword"
}
```

### Login

`POST /auth/login`
Obtains user authentication.

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**

```json
{
  "status": "success",
  "user": {
    "email": "user@example.com",
    "role": "free",
    "api_key": "generated_api_key"
  }
}
```

### Connect Telegram

`POST /user/connect-telegram`
Connects user's Telegram account for notifications.

**Request Body:**

```json
{
  "telegram_chat_id": "123456789"
}
```

### Watchlist Management

`POST /user/watchlist/add`
Adds a symbol to user's watchlist.

**Parameters:**

- `symbol`: Symbol to add (e.g., "BBCA.JK")

`DELETE /user/watchlist/remove`
Removes a symbol from user's watchlist.

**Parameters:**

- `symbol`: Symbol to remove (e.g., "BBCA.JK")

`GET /user/watchlist`
Retrieves user's watchlist.

### Balance Settings

`POST /user/settings/balance`
Updates user's trading balance settings.

**Request Body:**

```json
{
  "stock_idr": 50000000,
  "forex_usd": 500
}
```

### Personal Signal Check

`GET /user/signal/check/{symbol}`
Gets AI signal with personalized money management based on user's balance.

### Telegram Settings

`POST /user/settings/telegram`
Updates user's Telegram ID for notifications.

**Request Body:**

```json
{
  "chat_id": "123456789"
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

### Chart Data

`GET /market/chart/{symbol}`
Gets advanced chart data with indicators.

**Parameters:**

- `symbol`: Trading symbol (e.g., "BBCA.JK")
- `timeframe`: Chart timeframe (1d, 1h, 15m, default: 1h)

**Response:** OHLCV data with SMA, RSI, and Bandar accumulation indicators.

### Market Depth

`GET /market/depth/{symbol}`
Gets market depth (order book) data.

**Note:** Currently returns mock data. Connect to real broker API for live order book.

## 🔍 3. Search Functionality

### Search Assets

`GET /search/`
Searches for assets by symbol or name.

**Parameters:**

- `q`: Search query (minimum 2 characters)

**Response:** List of matching assets with their current signal status.

### Search Users (Admin)

`GET /user/admin/search-user`
Searches for users by email (Admin only).

**Parameters:**

- `q`: Search query

## 🧠 4. AI Pipeline (Auto-ML)

### Run Optimization

`POST /pipeline/optimize`
Runs a complete AI optimization cycle: Train -> Validate -> Deploy.

**Parameters:**

- `symbol`: Symbol to optimize (e.g., "BBCA.JK")

**Requires:** Admin role
**Response:** Optimization process started in background.

### Optimization Status

`GET /pipeline/status`
Gets current optimization status.

**Parameters:**

- `symbol`: Symbol to check status for

## 📈 5. Backtesting

### Run Backtest

`GET /backtest/run`
Simulates trading using historical data.

**Parameters:**

- `symbol`: Trading symbol (e.g., "BBCA.JK")
- `period`: Time period (1mo, 3mo, 6mo, 1y, 2y, default: 2y)
- `balance`: Initial balance (default: 100000000)

**Response:** Backtest results including ROI, Win Rate, Max Drawdown, Equity Curve.

## 🚨 6. Alerts & Screener

### Create Alert

`POST /alerts/create`
Sets an alarm for price or technical conditions.

**Request Body:**

```json
{
  "symbol": "XAUUSD",
  "type": "PRICE", // or "FORMULA"
  "condition": "ABOVE", // or technical formula like "RSI < 30"
  "target_price": 2400.0,
  "note": "Gold Breakout"
}
```

### List Alerts

`GET /alerts/list`
Retrieves user's active alerts.

## 📊 7. Market Screener

### Run Screener

`GET /screener/run`
Filters assets based on technical indicators.

**Parameters:**

- `min_score`: Minimum score (default: 0)
- `rsi_max`: Maximum RSI (default: 100)
- `rsi_min`: Minimum RSI (default: 0)
- `signal_only`: Only show assets with signals (default: false)
- `bandar_accum`: Only show assets with accumulation (default: false)

## 📝 8. Trading Journal

### Trade History

`GET /journal/history`
Retrieves trading history with completed trades (WIN/LOSS).

**Parameters:**

- `limit`: Maximum number of trades to return (default: 50)

### Performance Stats

`GET /journal/stats`
Views personal trading performance statistics.

**Response:** Win Rate, Profit Factor, Risk:Reward Ratio, Net PnL, Max Drawdown, Equity Curve.

## 🛠 9. Admin Operations

### Request Upgrade

`POST /user/request-upgrade`
Requests an upgrade to a higher membership level.

**Request Body:**

```json
{
  "target_role": "premium" // or "enterprise"
}
```

### View Upgrade Queue

`GET /admin/upgrade-queue`
Views the list of users requesting account upgrades.

**Requires:** Admin role

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

**Requires:** Admin role

## 👑 10. Owner Operations

### File Tree

`GET /owner/files/tree`
Gets the project file structure (Owner only).

**Requires:** Owner role

### Read File

`POST /owner/files/read`
Reads file content (Owner only).

**Request Body:**

```json
{
  "path": "src/core/agent.py"
}
```

**Requires:** Owner role

### Save File

`POST /owner/files/save`
Saves file content with syntax validation (Owner only).

**Request Body:**

```json
{
  "path": "src/core/agent.py",
  "content": "file content here"
}
```

**Requires:** Owner role

### Validate & Fix Code

`POST /owner/files/validate-fix`
Validates and automatically fixes Python code syntax (Owner only).

**Request Body:**

```json
{
  "path": "src/core/agent.py",
  "content": "file content here"
}
```

**Requires:** Owner role

### View Logs

`GET /owner/logs/stream`
Streams application logs (Owner only).

**Requires:** Owner role

### Manual Retraining

`POST /owner/action/retrain`
Triggers manual AI retraining (Owner only).

**Requires:** Owner role

### Restart Bot Logic

`POST /owner/action/restart-bot`
Restarts internal bot logic without stopping API server (Owner only).

**Requires:** Owner role

### View Database

`GET /owner/db/view/{collection_name}`
Views database content (Owner only).

**Parameters:**

- `collection_name`: Database collection name
- `limit`: Maximum records to return (default: 20)

**Requires:** Owner role

## ℹ️ Asset Configuration Notes

The system now uses Auto-Detection for asset configuration:

- Suffix .JK → Automatically considered Indonesian Stocks (1 Lot = 100 Shares).
- Suffix =X → Automatically considered Forex.
- JPY Pairs → Pip Scale 100.
- Other Pairs → Pip Scale 10000.
- Suffix -USD → Automatically considered Crypto.
- Others → Considered US Stocks (1 Lot = 1 Share).

You no longer need to manually register each symbol in config_assets.py.

## 🎯 Health & Monitoring

### Health Check

`GET /health`
Returns server health status including CPU and RAM usage.
