# 🚀 Trading Signal Terminal – High-Performance Quotex Signal Generator

<div align="center">

<h2>⚡ Real-Time Market Analysis with Advanced Technical Indicators</h2>

<p><b>Production-ready web application powered by Next.js + Vercel serverless Python API</b></p>

<p>
  <a href="https://nextjs.org/"><img alt="Next.js 14" src="https://img.shields.io/badge/Next.js-14.2.5-black?logo=next.js" /></a>
  <a href="https://vercel.com/"><img alt="Vercel" src="https://img.shields.io/badge/Deployed%20on-Vercel-000000?logo=vercel" /></a>
  <a href="https://flask.palletsprojects.com/"><img alt="Flask" src="https://img.shields.io/badge/API-Flask-blue?logo=flask" /></a>
  <a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/pypi/pyversions/pandas?label=python&logo=python" /></a>
  <a href="https://github.com/irFaN-dev30/qx/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/badge/License-MIT-green.svg" /></a>
</p>

**[📊 Live Demo](#deployment) • [🔧 Setup Guide](#installation) • [📖 Documentation](#documentation)**

</div>

---

## ✨ Key Features

### 🎯 Advanced Signal Generation
- **3-Layer Security Filter** for BUY/SELL signals:
  - RSI < 30 (oversold) + Price below Lower Bollinger Band + EMA5 > EMA20 = **BUY**
  - RSI > 70 (overbought) + Price above Upper Bollinger Band + EMA5 < EMA20 = **SELL**
- **Confidence Scoring**: 0–100% based on indicator alignment
- **Multi-Asset Scanning**: Monitor 4+ forex pairs simultaneously

### 📈 Real-Time Dashboard
- **Live Signal Display**: Large, bold card showing active BUY/SELL with color coding
- **Comprehensive Metrics**: RSI, EMA5/20, Bollinger Bands (upper/middle/lower)
- **Signal History Table**: All detected signals with timestamps
- **Auto-Refresh**: 5-second polling for near-instant updates
- **Audio Alerts**: Notification sound for high-confidence signals (>90%)

### 🏗️ Architecture
- **Frontend**: Next.js 14 (App Router) with Tailwind CSS
- **Backend**: Vercel Python serverless function (Flask)
- **Data Source**: Quotex API via `api_quotex` async client
- **Session Management**: Automated SSID retrieval & persistence
- **Error Handling**: Comprehensive logging & fallback responses

### 🔐 Security & Reliability
- Environment variables for credentials (no hardcoded secrets)
- Async non-blocking operations
- Connection pooling & auto-reconnect
- Structured error responses

---

## 📋 Table of Contents
1. [Quick Start](#-quick-start)
2. [Installation](#installation)
3. [Local Development](#local-development)
4. [Deployment to Vercel](#deployment-to-vercel)
5. [Configuration](#configuration)
6. [API Reference](#api-reference)
7. [Troubleshooting](#troubleshooting)
8. [Project Structure](#project-structure)
9. [Contributing](#contributing)
10. [License](#license)

---

## 🚀 Quick Start

### Prerequisites
- **Node.js** 16+ & **npm** / **yarn**
- **Python** 3.9+
- **Quotex Account** (demo or live)
- **Vercel Account** (for production) or local development

### 1. Clone & Install

```bash
git clone https://github.com/irFaN-dev30/qx
cd qx

# Dashboard dependencies
cd dashboard
npm install
cd ..

# Python dependencies (for local testing)
pip install -r requirements.txt
pip install -r functions/signal_function/requirements.txt
```

### 2. Set Environment Variables

Create `.env.local` in the `dashboard/` folder:

```env
# Frontend (Next.js)
NEXT_PUBLIC_API_URL=http://localhost:3000/api/signal
```

For backend testing locally, set in your shell:

```bash
export QUOTEX_EMAIL="your.email@example.com"
export QUOTEX_PASSWORD="your_password"
export SIGNAL_ASSETS="EURUSD,GBPUSD,USDJPY,AUDUSD"  # Optional
```

### 3. Run Locally

```bash
# Terminal 1: Next.js Frontend
cd dashboard
npm run dev
# Open http://localhost:3000

# Terminal 2 (optional): Test API locally
# Make sure env vars are set, then call the signal endpoint
```

### 4. Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Follow prompts to link your Git repo
```

Then **set Vercel environment variables** in your project settings:
- `QUOTEX_EMAIL`
- `QUOTEX_PASSWORD`
- `SIGNAL_ASSETS` (optional)

---

## Installation

### Full Setup from Scratch

```bash
# 1. Clone repository
git clone https://github.com/irFaN-dev30/qx qx
cd qx

# 2. Install Frontend
cd dashboard
npm install
npm run build  # Test build
cd ..

# 3. Install Python Backend (for local dev)
pip install --upgrade pip
pip install numpy flask cloudscraper playwright pillow loguru pandas

# 4. Install Playwright browser
python -m playwright install chromium

# 5. Verify API-Quotex imports
# The functions/signal_function/main.py imports from API-Quotex-main/
# Ensure the folder exists and dependencies are present
pip install playwright cloudscraper loguru
```

---

## Local Development

### Running the Frontend Only
```bash
cd dashboard
npm run dev
```
Visit `http://localhost:3000`. The dashboard will try to fetch from `/api/signal`.

### Running Backend Locally (Flask)
```bash
# Set environment variables
export QUOTEX_EMAIL="your_email@example.com"
export QUOTEX_PASSWORD="your_password"

# Run the Flask server
cd functions/signal_function
python -m flask run --port=5000
```

Or to test the signal endpoint directly:
```bash
curl http://localhost:5000/api/signal
```

### Full Local Stack
```bash
# Terminal 1: Frontend
cd dashboard && npm run dev

# Terminal 2: Backend Flask (if testing locally)
export QUOTEX_EMAIL="your_email"
export QUOTEX_PASSWORD="your_password"
cd functions/signal_function
python -m flask run --port=5000
```

Then update `dashboard/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:5000/api/signal
```

---

## Deployment to Vercel

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Ready for Vercel deployment"
git push origin main
```

### Step 2: Connect to Vercel
1. Go to [vercel.com](https://vercel.com)
2. Click **"New Project"** → Select your GitHub repo
3. Vercel auto-detects **Next.js** + **Python** builds using `vercel.json`

### Step 3: Set Environment Variables
In your Vercel project dashboard:
1. Go to **Settings** → **Environment Variables**
2. Add:
   - `QUOTEX_EMAIL` = `your_email@example.com`
   - `QUOTEX_PASSWORD` = `your_password`
   - `SIGNAL_ASSETS` = `EURUSD,GBPUSD,USDJPY,AUDUSD` (optional)

### Step 4: Deploy
```bash
# Redeploy if already connected
vercel --prod
```

Or click **Deploy** in Vercel dashboard. Your app is live at `https://your-project.vercel.app/`

---

## Configuration

### Environment Variables

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `QUOTEX_EMAIL` | string | ✅ Yes | Quotex login email |
| `QUOTEX_PASSWORD` | string | ✅ Yes | Quotex login password |
| `SIGNAL_ASSETS` | string | ❌ No | Comma-separated currency pairs (default: `EURUSD,GBPUSD,USDJPY,AUDUSD`) |

### Signal Thresholds
Located in `functions/signal_function/main.py`:

```python
# BUY Conditions (all must be true):
rsi < 30                          # RSI oversold
price < lower_bollinger_band      # Price near support
ema5 > ema20                       # Bullish crossover

# SELL Conditions (all must be true):
rsi > 70                          # RSI overbought
price > upper_bollinger_band      # Price near resistance
ema5 < ema20                       # Bearish crossover

# Confidence = (matching_conditions / 3) * 100 + RSI_edge_boost
```

**To modify thresholds**, edit the `SignalEngine.score_and_classify()` method in the main.py file.

---

## API Reference

### GET `/api/signal`

Fetches real-time trading signals from all configured assets.

#### Response (Success)

```json
{
  "active_signal": {
    "asset": "EURUSD",
    "direction": "BUY",
    "confidence": 87,
    "rsi": 28.5,
    "ema5": 1.0945,
    "ema20": 1.0920,
    "upper_bb": 1.0980,
    "middle_bb": 1.0950,
    "lower_bb": 1.0920,
    "price": 1.0925,
    "timestamp": "2026-04-01T12:34:56.789Z",
    "conditions": {
      "rsi_buy": true,
      "bollinger_buy": true,
      "ema_buy": true,
      "rsi_sell": false,
      "bollinger_sell": false,
      "ema_sell": false
    }
  },
  "all_signals": [
    { "asset": "EURUSD", "direction": "BUY", "confidence": 87, ... },
    { "asset": "GBPUSD", "direction": "SELL", "confidence": 72, ... }
  ],
  "status": "ok",
  "timestamp": "2026-04-01T12:34:56.789Z"
}
```

#### Response (No Signals)

```json
{
  "signal": "SCANNING",
  "status": "no_signals",
  "all_signals": [],
  "timestamp": "2026-04-01T12:34:56.789Z"
}
```

#### Response (Error)

```json
{
  "error": "Missing QUOTEX_EMAIL or QUOTEX_PASSWORD environment variables",
  "status": "config_error",
  "timestamp": "2026-04-01T12:34:56.789Z"
}
```

Status codes:
- `200 OK` – Signals generated successfully
- `500 Internal Server Error` – Auth, connection, or processing error

---

## Troubleshooting

### ❌ `status 500` – No Signals Generated

**Cause**: Missing or invalid Quotex credentials

**Fix**:
1. Verify `QUOTEX_EMAIL` and `QUOTEX_PASSWORD` are set in Vercel → Settings → Environment Variables
2. Test credentials locally:
   ```bash
   export QUOTEX_EMAIL="your_email"
   export QUOTEX_PASSWORD="your_password"
   python functions/signal_function/main.py
   ```
3. If error persists, credentials may be invalid. Test login at [qxbroker.com](https://qxbroker.com)

---

### ❌ Dashboard shows "SCANNING..." (No Data)

**Cause**: API endpoint is not responding

**Fix**:
1. Check Vercel deployment logs: Project → Deployments → View Logs
2. Ensure `vercel.json` routes are correct:
   ```json
   {
     "routes": [
       { "src": "/api/signal", "dest": "/functions/signal_function/main.py" }
     ]
   }
   ```
3. Test the API directly:
   ```bash
   curl https://your-project.vercel.app/api/signal
   ```

---

### ❌ Playwright Browser Not Found (Local Development)

**Fix**:
```bash
python -m playwright install chromium
```

---

### ❌ Module Not Found Errors

**Fix**: Ensure `API-Quotex-main/` folder exists and dependencies are installed:
```bash
pip install playwright cloudscraper loguru pandas
```

---

## Project Structure

```
qx/
├── README.md                          # This file
├── vercel.json                        # Vercel build & routes config
├── requirements.txt                   # Python dependencies
│
├── functions/
│   └── signal_function/
│       ├── main.py                    # Flask API server with signal logic
│       └── requirements.txt
│
├── dashboard/                         # Next.js frontend
│   ├── package.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── app/
│       ├── layout.js                  # Root layout
│       ├── page.js                    # Dashboard UI
│       └── globals.css                # Tailwind + custom styles
│
└── API-Quotex-main/                   # Quotex async client library
    ├── api_quotex/
    │   ├── client.py
    │   ├── login.py
    │   ├── models.py
    │   ├── constants.py
    │   └── ...
    └── requirements.txt
```

---

## Technical Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 14, React 18, Tailwind CSS | Dynamic UI, real-time updates |
| **Backend** | Flask, Python 3.9+ | Signal generation, API endpoint |
| **WebSocket** | `api_quotex.AsyncQuotexClient` | Real-time market data |
| **Hosting** | Vercel (Edge Functions) | Serverless deployment |
| **Data** | Quotex Broker API | Live OHLC candles, quotes |

---

## Advanced Usage

### Custom Asset Scanning

Edit `functions/signal_function/main.py`:

```python
# Change line ~170
assets = os.getenv('SIGNAL_ASSETS', 'EURUSD,GBPUSD,USDJPY,AUDUSD').split(',')
# Example: add more pairs
assets = os.getenv('SIGNAL_ASSETS', 'EURUSD,GBPUSD,USDJPY,AUDUSD,BTCUSD,GCDUSD').split(',')
```

Or set `SIGNAL_ASSETS` environment variable in Vercel.

### Modifying Signal Thresholds

Edit `functions/signal_function/main.py` in the `SignalEngine.score_and_classify()` method:

```python
# Adjust RSI thresholds (default: <30 for BUY, >70 for SELL)
conditions = {
    'rsi_buy': rsi < 25,      # More aggressive
    'rsi_sell': rsi > 75,
    # ... rest of conditions
}
```

### Adding Custom Indicators

Extend `TechnicalAnalysis` class:

```python
class TechnicalAnalysis:
    @staticmethod
    def calculate_macd(prices, fast=12, slow=26, signal=9):
        # Your MACD logic here
        pass

    @staticmethod
    def calculate_stochastic(prices, period=14):
        # Your Stochastic logic here
        pass
```

---

## Performance Optimization

- **Vercel Python Max Size**: 50MB (set in `vercel.json`)
- **Concurrent Asset Analysis**: Async gathering with `asyncio`
- **Caching**: SSID reused across calls (stored in API-Quotex config)
- **Polling Interval**: Dashboard refreshes every 5 seconds (configurable in `dashboard/app/page.js`)

---

## Contributing

Contributions welcome! Please:

1. **Fork** the repository
2. **Create a branch** for your feature:
   ```bash
   git checkout -b feature/my-awesome-feature
   ```
3. **Commit** changes:
   ```bash
   git commit -m "Add: my awesome feature"
   ```
4. **Push** to your fork:
   ```bash
   git push origin feature/my-awesome-feature
   ```
5. **Open a Pull Request** with detailed description

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- **Quotex**: Real-time market data via `api_quotex` async client
- **Next.js**: Modern React framework for the dashboard
- **Vercel**: Serverless deployment platform
- **Playwright**: Automated login & session management

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/irFaN-dev30/qx/issues)
- **Email**: irfan.dev30@gmail.com
- **Telegram**: [@irFaN_dev30](https://t.me/irFaN_dev30)

---

**Last Updated**: April 1, 2026  
**Version**: 1.0.0  
**Status**: ✅ Production Ready
