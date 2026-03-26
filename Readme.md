# ⚡ AI Trading Hub (SaaS Platform)

<div align="center">
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Database-MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white" alt="MongoDB" />
  <img src="https://img.shields.io/badge/AI-PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white" alt="PyTorch" />
  <img src="https://img.shields.io/badge/DevOps-Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
</div>

<br/>

**AI Trading Hub** is an advanced, full-stack algorithmic trading platform designed for **Forex, Indonesian Stocks (IDX), and US Stocks**. It combines Deep Reinforcement Learning (PPO) with specialized market analysis (Bandarmology & Smart Money Concepts) and LLM-based decision support using Groq/Llama 3.

## 🚀 Key Features

### 🧠 Artificial Intelligence Core

- **Hybrid AI Engine:** Uses PyTorch (LSTM + PPO) optimized for CPU inference (Quantized).
- **Multi-Asset Support:** Handles dynamic lot sizing for Forex (Lots) vs IDX (Shares/Lembar).
- **LLM Analyst (Groq):** Integrated Llama-3 70B to provide a "Second Opinion", estimating Profit/Loss and validating technical signals with human-like reasoning.

### 📊 Specialized Detectors

- **🇮🇩 Bandarmology (IDX):** Detects accumulation/distribution flow (Big Player) using Volume Price Analysis (VPA) for Indonesian stocks.
- **🌍 Smart Money Concepts (Forex):** Identifies institutional footprints like Liquidity Grabs, Stop Hunts, and Imbalance (FVG).

### 💻 Modern Dashboard (SaaS)

- **Role-Based Access (RBAC):** Free, Premium, Enterprise, Admin, and Owner roles.
- **Payment Gateway:** Automated subscription via **Midtrans** (QRIS, GoPay, VA).
- **Real-time News Radar:** Scrapes high-impact economic events (NFP, FOMC).
- **Command Palette:** Global search (`Ctrl+K`) for assets and system navigation.
- **Owner "God Mode":** Edit backend code, view logs, and monitor server stats directly from the UI.

---

## 🛠️ Tech Stack

### Backend

- **Framework:** FastAPI (Python 3.10+)
- **Database:** MongoDB (Async Motor Driver) & Redis (Pub/Sub & Caching)
- **AI/ML:** PyTorch, Stable-Baselines3, Scikit-learn, Pandas-TA
- **Data Source:** YFinance, CCXT (Crypto)
- **Security:** JWT Auth, Bcrypt Hashing, API Key headers, SlowAPI Rate Limiting

### Frontend (Reference)

- **Framework:** Next.js 15 (App Router)
- **UI Library:** Shadcn UI, Tailwind CSS, Lucide Icons
- **State Management:** Zustand (Persisted)
- **Data Fetching:** TanStack Query (React Query)

---

## ⚙️ Installation & Setup

### Prerequisites

- Python 3.10+
- MongoDB (Local or Atlas)
- Redis Server (Local or Cloud)

### 1. Backend Setup

```bash
# Clone repository
git clone [https://github.com/adhitiad/ai-trading-hub.git](https://github.com/adhitiad/ai-trading-hub.git)
cd ai-trading-hub

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install PyTorch CPU (Lighter version)
pip install torch torchvision torchaudio --index-url [https://download.pytorch.org/whl/cpu](https://download.pytorch.org/whl/cpu)

# Setup Environment Variables
cp .env.example .env
# (Edit .env with your MongoDB URI, Redis Config, and API Keys)

# Run Server
uvicorn main:app --reload
```

🔑 Environment Variables (.env)
Create a .env file in the root directory:

```bash
# DATABASE
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=ai_trading_hub

# REDIS
REDIS_HOST=localhost
REDIS_PORT=6379

# SECURITY
SECRET_KEY=your_super_secret_jwt_key_here

# EXTERNAL APIS
GROQ_API_KEY=gsk_xxxxxxxxxxxxxx
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuVWXyz
```

# 🤖 AI Training Pipeline

To retrain the models with the latest market data:

Manual Trigger: Run python train_all.py

Via Dashboard: Login as Owner -> Go to God Mode -> Click "Retrain AI".

The system uses yfinance to fetch historical data, calculates 50+ technical indicators, and trains a PPO Agent using the Gymnasium environment.

# 🛡️ License

Distributed under the MIT License. See LICENSE for more information.

# 🔗Built with ❤️ by Adhitiad [@adhitiad](https://github.com/adhitiad)
