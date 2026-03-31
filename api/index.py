# Final, Refactored & Simplified Quotex Signal Generator for Vercel

import os
import asyncio
import numpy as np
from datetime import datetime
from flask import Flask, render_template_string

# --- Attempt to import Quotex client ---
try:
    from quotexapi.stable_api import Quotex
except Exception:
    Quotex = None

# ===========================================================================
# --- App Configuration ---
# ===========================================================================
TIMEFRAME_SECONDS = 60
CANDLE_COUNT = 100
REFRESH_INTERVAL_SECONDS = 45 # How often the webpage suggests reloading

# --- List of ASSETS to scan. Keep this list short to avoid timeouts on Vercel's free tier. ---
ASSETS_TO_SCAN = [
    "EURUSD_otc", "GBPUSD_otc", "USDJPY_otc", "AUDUSD_otc", "EURJPY_otc",
    "GBPJPY_otc", "USDCAD_otc", "AUDCAD_otc", "EURGBP_otc", "BTCUSD_otc"
]

# ===========================================================================
# --- Flask App ---
# ===========================================================================
app = Flask(__name__)

# ===========================================================================
# --- HTML Template ---
# ===========================================================================
HTML_TEMPLATE = '''
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
        .status-bar { padding: 15px; margin-bottom: 20px; border-radius: 5px; text-align: center; font-size: 1.1em; }
        .status-Success { background-color: #0a9396; color: white; }
        .status-Error { background-color: #9b2226; color: white; }
        .signal-CALL { color: #4caf50; font-weight: bold; }
        .signal-PUT { color: #f44336; font-weight: bold; }
        footer { text-align: center; margin-top: 20px; font-size: 0.9em; color: #777; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Quotex Signal Generator</h1>
        {% if status and status.message %}
        <div class="status-bar status-{{ 'Success' if success else 'Error' }}">
            <strong>Status:</strong> {{ status.message }}
        </div>
        {% endif %}
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
                        <td class="signal-{{ s.direction }}">{{ s.direction }}</td>
                        <td>{{ s.strength }}%</td>
                        <td>{{ "%.2f"|format(s.rsi) }}</td>
                        <td>{{ s.macd }}</td>
                        <td>{{ s.trend }}</td>
                        <td>{{ s.price }}</td>
                    </tr>
                    {% endfor %}
                {% else %}
                    <tr>
                        <td colspan="8" style="text-align:center;">No strong signals found, or an error occurred. The page will refresh automatically.</td>
                    </tr>
                {% endif %}
            </tbody>
        </table>
    </div>
    <footer>
        Page will automatically refresh in {{ REFRESH_INTERVAL_SECONDS }} seconds.
    </footer>
</body>
</html>
'''


# ===========================================================================
# TECHNICAL ANALYSIS
# ===========================================================================
class TechnicalAnalysis:
    @staticmethod
    def calculate_rsi(prices, period=14):
        if len(prices) < period + 1: return 50.0
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        if avg_loss == 0: return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    @staticmethod
    def calculate_macd_signal(prices, fast=12, slow=26):
        if len(prices) < slow: return "NEUTRAL"
        ema_fast = np.mean(prices[-fast:])
        ema_slow = np.mean(prices[-slow:])
        macd_line = ema_fast - ema_slow
        return "BULLISH" if macd_line > 0 else "BEARISH"

    @staticmethod
    def calculate_bollinger_bands(prices, period=20, std_dev=2):
        if len(prices) < period: return None, None
        window = prices[-period:]
        sma = np.mean(window)
        sd = np.std(window)
        return sma + std_dev * sd, sma - std_dev * sd

    @staticmethod
    def detect_trend(prices, lookback=10):
        if len(prices) < lookback: return "SIDEWAYS"
        y = np.array(prices[-lookback:])
        x = np.arange(len(y))
        slope = np.polyfit(x, y, 1)[0]
        if slope > 1e-4: return "UPTREND"
        if slope < -1e-4: return "DOWNTREND"
        return "SIDEWAYS"

# ===========================================================================
# --- Core Signal Generation Logic ---
# ===========================================================================
async def get_live_signals():
    if Quotex is None:
        return [], {"message": "Quotex API client not installed properly."}, False

    email = os.getenv("QUOTEX_EMAIL")
    password = os.getenv("QUOTEX_PASSWORD")

    if not email or not password:
        return [], {"message": "QUOTEX_EMAIL or QUOTEX_PASSWORD environment variables are not set."}, False

    client = Quotex(email=email, password=password)
    try:
        check, reason = await client.connect()
        if not check:
            msg = f"Connection failed: {reason}. If it mentions a PIN, please log in via browser first and redeploy."
            return [], {"message": msg}, False

        async def analyze_asset(asset):
            try:
                candles = await client.get_candles(asset, TIMEFRAME_SECONDS, CANDLE_COUNT, int(datetime.now().timestamp()))
                if not candles or len(candles) < 20: return None
                
                close_prices = [float(c['close']) for c in candles]
                current_price = close_prices[-1]
                
                rsi = TechnicalAnalysis.calculate_rsi(close_prices)
                macd_signal = TechnicalAnalysis.calculate_macd_signal(close_prices)
                upper_bb, lower_bb = TechnicalAnalysis.calculate_bollinger_bands(close_prices)
                trend = TechnicalAnalysis.detect_trend(close_prices)

                direction = None
                strength = 0
                if rsi < 30 and (lower_bb is not None and current_price <= lower_bb): direction = "CALL"; strength = 60
                elif rsi > 70 and (upper_bb is not None and current_price >= upper_bb): direction = "PUT"; strength = 60
                
                if direction == "CALL" and macd_signal == "BULLISH": strength += 20
                if direction == "PUT" and macd_signal == "BEARISH": strength += 20
                if direction == "CALL" and trend == "UPTREND": strength += 20
                if direction == "PUT" and trend == "DOWNTREND": strength += 20
                
                if strength >= 60:
                    return {
                        'asset': asset, 'direction': direction, 'strength': min(strength, 100),
                        'rsi': rsi, 'macd': macd_signal, 'trend': trend, 'price': current_price,
                        'timestamp': datetime.now().strftime("%H:%M:%S")
                    }
                return None
            except Exception:
                return None

        tasks = [analyze_asset(asset) for asset in ASSETS_TO_SCAN]
        results = await asyncio.gather(*tasks)
        
        signals = [res for res in results if res is not None]
        signals.sort(key=lambda x: x['strength'], reverse=True)
        
        status_msg = f"Scan complete at {datetime.now().strftime('%H:%M:%S')}. Found {len(signals)} strong signal(s) from {len(ASSETS_TO_SCAN)} assets."
        return signals, {"message": status_msg}, True

    except Exception as e:
        return [], {"message": f"An unexpected error occurred during execution: {e}"}, False
    finally:
        if client.check_connect():
            await client.close()

# ===========================================================================
# --- Flask Route ---
# ===========================================================================
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    # This is the main entry point for Vercel
    signals, status, success = asyncio.run(get_live_signals())
    return render_template_string(HTML_TEMPLATE, 
                                  signals=signals, 
                                  status=status, 
                                  success=success,
                                  REFRESH_INTERVAL_SECONDS=REFRESH_INTERVAL_SECONDS)


# This part is not used by Vercel, but is good for local testing
if __name__ == '__main__':
    app.run(debug=True)
