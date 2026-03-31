# Flask-based Quotex Signal Generator Web App
# This version serves an HTML page with live signals.

import os
import time
import asyncio
import numpy as np
from datetime import datetime
import threading
from flask import Flask, render_template_string

# Attempt to import Quotex client
try:
    from quotexapi.stable_api import Quotex
except Exception:
    Quotex = None

# -----------------------
# --- App Configuration ---
# -----------------------
TIMEFRAME_SECONDS = 60
CONCURRENCY_LIMIT = 10
MAX_SIGNALS_IN_TABLE = 150
CANDLE_COUNT = 100
SCAN_INTERVAL_SECONDS = 30
REFRESH_INTERVAL_SECONDS = 30 # How often the webpage reloads

# -----------------------------------
# --- Flask App and Globals ---
# -----------------------------------
app = Flask(__name__)
latest_signals = []
app_status = {"status": "Initializing", "message": "Flask app is starting up..."}

# ============================================================================
# --- HTML TEMPLATE ---
# ============================================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quotex Live Signals</title>
    <meta http-equiv="refresh" content="{{ REFRESH_INTERVAL_SECONDS }}">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #121212; color: #e0e0e0; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: auto; background-color: #1e1e1e; padding: 20px; border-radius: 8px; box-shadow: 0 0 15px rgba(0,0,0,0.5); }
        h1, h2 { color: #bb86fc; text-align: center; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; border: 1px solid #333; text-align: left; }
        thead { background-color: #333; }
        th { color: #bb86fc; }
        tbody tr:nth-child(even) { background-color: #242424; }
        .status-bar { padding: 10px; margin-bottom: 20px; border-radius: 5px; text-align: center; }
        .status-Initializing { background-color: #005f73; color: white; }
        .status-Connected, .status-Running { background-color: #0a9396; color: white; }
        .status-Error { background-color: #9b2226; color: white; }
        .signal-call { color: #4caf50; font-weight: bold; }
        .signal-put { color: #f44336; font-weight: bold; }
        footer { text-align: center; margin-top: 20px; font-size: 0.8em; color: #777; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Quotex Signal Generator</h1>
        <div class="status-bar status-{{ status.status }}">
            <strong>Status:</strong> {{ status.status }} &mdash; {{ status.message }}
        </div>
        <h2>Live Signals</h2>
        <table>
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Asset</th>
                    <th>Direction</th>
                    <th>Strength</th>
                    <th>RSI</th>
                    <th>MACD</th>
                    <th>Trend</th>
                    <th>Price</th>
                </tr>
            </thead>
            <tbody>
                {% if signals %}
                    {% for s in signals %}
                    <tr>
                        <td>{{ s.timestamp }}</td>
                        <td>{{ s.asset.upper().replace('_', '-') }}</td>
                        <td class="{{ 'signal-call' if s.direction == 'CALL' else 'signal-put' }}">{{ s.direction }}</td>
                        <td>{{ s.strength }}%</td>
                        <td>{{ "%.2f"|format(s.rsi) }}</td>
                        <td>{{ s.macd }}</td>
                        <td>{{ s.trend }}</td>
                        <td>{{ s.price }}</td>
                    </tr>
                    {% endfor %}
                {% else %}
                    <tr>
                        <td colspan="8" style="text-align:center;">No strong signals found in the last scan, or the system is warming up...</td>
                    </tr>
                {% endif %}
            </tbody>
        </table>
    </div>
    <footer>
        Page will automatically refresh every {{ REFRESH_INTERVAL_SECONDS }} seconds.
    </footer>
</body>
</html>
"""

# ============================================================================
# TECHNICAL ANALYSIS (unchanged)
# ============================================================================
class TechnicalAnalysis:
    @staticmethod
    def calculate_rsi(prices, period=14):
        prices = np.asarray(prices, dtype=float)
        if prices.size < period + 1: return 50.0
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0: return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    @staticmethod
    def calculate_ema(prices, period=20):
        prices = list(prices)
        if len(prices) < period: return float(np.mean(prices)) if prices else 0.0
        sma = float(np.mean(prices[:period]))
        multiplier = 2.0 / (period + 1.0)
        ema = sma
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        return float(ema)

    @staticmethod
    def calculate_macd(prices, fast=12, slow=26, signal_period=9):
        if len(prices) < slow: return 0.0, 0.0, 0.0, "NEUTRAL"
        ema_fast = TechnicalAnalysis.calculate_ema(prices, fast)
        ema_slow = TechnicalAnalysis.calculate_ema(prices, slow)
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalAnalysis.calculate_ema([macd_line], signal_period) # Simplified
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram, "BULLISH" if histogram > 0 else "BEARISH"

    @staticmethod
    def calculate_bollinger_bands(prices, period=20, std_dev=2):
        prices = np.asarray(prices)
        if prices.size < period: return None, None, None
        window = prices[-period:]
        sma = float(np.mean(window))
        sd = float(np.std(window, ddof=0))
        return sma + std_dev * sd, sma, sma - std_dev * sd

    @staticmethod
    def detect_trend(prices, lookback=10, slope_threshold=1e-4):
        if len(prices) < lookback: return "SIDEWAYS"
        y = np.array(prices[-lookback:], dtype=float)
        x = np.arange(len(y))
        slope = np.polyfit(x, y, 1)[0]
        if slope > slope_threshold: return "UPTREND"
        if slope < -slope_threshold: return "DOWNTREND"
        return "SIDEWAYS"

# ============================================================================
# SIGNAL GENERATOR (unchanged)
# ============================================================================
class RealSignalGenerator:
    def __init__(self, client):
        self.client = client
        self.ta = TechnicalAnalysis()

    async def analyze_asset(self, asset, timeframe=TIMEFRAME_SECONDS, candle_count=CANDLE_COUNT):
        try:
            candles = await self.client.get_candles(asset, timeframe, candle_count, int(time.time()))
            if not candles or not isinstance(candles, list): return None
            
            close_prices = [float(c['close']) for c in candles if 'close' in c]
            if len(close_prices) < 20: return None

            rsi = self.ta.calculate_rsi(close_prices)
            _, _, _, macd_signal = self.ta.calculate_macd(close_prices)
            upper_bb, _, lower_bb = self.ta.calculate_bollinger_bands(close_prices)
            ema_20 = self.ta.calculate_ema(close_prices)
            trend = self.ta.detect_trend(close_prices)
            current_price = close_prices[-1]

            signal_strength = 0
            direction = None
            if rsi < 30:
                signal_strength += 25
                direction = "CALL"
            elif rsi > 70:
                signal_strength += 25
                direction = "PUT"
            
            if macd_signal == "BULLISH" and direction != "PUT":
                signal_strength += 20; direction = "CALL"
            elif macd_signal == "BEARISH" and direction != "CALL":
                signal_strength += 20; direction = "PUT"

            if upper_bb is not None and current_price <= lower_bb and direction != "PUT":
                signal_strength += 20; direction = "CALL"
            elif upper_bb is not None and current_price >= upper_bb and direction != "CALL":
                signal_strength += 20; direction = "PUT"

            if current_price > ema_20 and direction != "PUT":
                signal_strength += 15; direction = "CALL"
            elif current_price < ema_20 and direction != "CALL":
                signal_strength += 15; direction = "PUT"
            
            if trend == "UPTREND" and direction == "CALL": signal_strength += 20
            elif trend == "DOWNTREND" and direction == "PUT": signal_strength += 20

            if signal_strength >= 50 and direction:
                return {
                    'asset': asset, 'direction': direction, 'strength': min(int(signal_strength), 100),
                    'rsi': rsi, 'macd': macd_signal, 'trend': trend, 'price': current_price,
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                }
            return None
        except Exception:
            return None

# ============================================================================
# --- Helper Functions ---
# ============================================================================
def load_credentials_from_env():
    email = os.getenv("QUOTEX_EMAIL")
    password = os.getenv("QUOTEX_PASSWORD")
    return email, password

async def connect_with_retry(email, password, max_retries=3):
    global app_status
    if Quotex is None:
        app_status = {"status": "Error", "message": "Quotex API client not installed."}
        return None, False

    for attempt in range(1, max_retries + 1):
        try:
            app_status = {"status": "Initializing", "message": f"Connection attempt {attempt}/{max_retries}..."}
            client = Quotex(email=email, password=password)
            check, reason = await client.connect()
            if check:
                return client, True
            
            reason_text = str(reason or "")
            app_status = {"status": "Error", "message": f"Connection failed: {reason_text}. Retrying..."}
            if "pin" in reason_text.lower():
                app_status["message"] = "Login failed. A 2FA PIN is required. Please verify your session in a browser first, then redeploy."
                return None, False # Stop retrying if PIN is needed
            await asyncio.sleep(5)
        except Exception as e:
            app_status = {"status": "Error", "message": f"Exception on connect attempt {attempt}: {e}"}
            await asyncio.sleep(5)
    return None, False

async def get_all_assets(client):
    try:
        instruments = await client.get_instruments()
        if isinstance(instruments, dict) and 'crypto' in instruments:
             # Assuming the structure is {'crypto': [...], 'forex': [...]}
            all_assets = []
            for category in instruments.values():
                all_assets.extend([item['name'] for item in category if isinstance(item, dict) and 'name' in item])
            return list(set(all_assets))
        elif isinstance(instruments, list): # Fallback for flat list
            return list(set([item['name'] for item in instruments if isinstance(item, dict) and 'name' in item]))
    except Exception as e:
        app_status['message'] = f"Could not fetch assets: {e}"
    return ["EURUSD_otc", "GBPUSD_otc", "USDJPY_otc", "AUDUSD_otc"] # Fallback

# ============================================================================
# --- Background Scanning Thread ---
# ============================================================================
def run_background_tasks():
    global latest_signals, app_status

    email, password = load_credentials_from_env()
    if not email or not password:
        app_status = {"status": "Error", "message": "QUOTEX_EMAIL and QUOTEX_PASSWORD environment variables not set."}
        return

    # Create and set a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    client, success = loop.run_until_complete(connect_with_retry(email, password))

    if not success or not client:
        # app_status is already set by connect_with_retry
        return
    
    app_status = {"status": "Connected", "message": "Successfully connected to Quotex. Starting initial scan..."}
    
    try:
        if hasattr(client, "change_balance"):
             loop.run_until_complete(client.change_balance("PRACTICE"))
    except: pass
    
    signal_generator = RealSignalGenerator(client)

    while True:
        try:
            assets = loop.run_until_complete(get_all_assets(client))
            app_status = {"status": "Running", "message": f"Scanning {len(assets)} assets..."}

            sem = asyncio.Semaphore(CONCURRENCY_LIMIT)
            async def analyze_with_sem(asset):
                async with sem:
                    return await signal_generator.analyze_asset(asset)

            tasks = [analyze_with_sem(asset) for asset in assets]
            results = loop.run_until_complete(asyncio.gather(*tasks))

            signals = [res for res in results if res is not None]
            signals.sort(key=lambda x: x['strength'], reverse=True)
            
            latest_signals = signals[:MAX_SIGNALS_IN_TABLE]
            
            app_status['message'] = f"Scan complete at {datetime.now().strftime('%H:%M:%S')}. Found {len(signals)} signals. Next scan in {SCAN_INTERVAL_SECONDS}s."
            time.sleep(SCAN_INTERVAL_SECONDS)

        except Exception as e:
            app_status = {"status": "Error", "message": f"A critical error occurred in the scan loop: {e}. Reconnecting in 60s."}
            time.sleep(60)
            # Try to reconnect
            client, success = loop.run_until_complete(connect_with_retry(email, password))
            if not success:
                app_status['message'] = "Reconnect failed. Halting."
                break
    
    loop.close()

# ============================================================================
# --- Flask Routes ---
# ============================================================================
@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, signals=latest_signals, status=app_status, REFRESH_INTERVAL_SECONDS=REFRESH_INTERVAL_SECONDS)

# ============================================================================
# --- App Initialization ---
# ============================================================================
# Start the background thread when the app starts
scanner_thread = threading.Thread(target=run_background_tasks)
scanner_thread.daemon = True
scanner_thread.start()

# This block is for local execution, not for Vercel
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
