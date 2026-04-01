"""Vercel serverless function for trading signal generation"""
import os
import sys
import asyncio
import json
from datetime import datetime
from pathlib import Path
import traceback

import numpy as np
from flask import Flask, jsonify

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "API-Quotex-main"))

# import error reporting
IMPORT_EXCEPTION = None

try:
    from api_quotex import AsyncQuotexClient
    from api_quotex.login import get_ssid
except Exception as e:
    AsyncQuotexClient = None
    get_ssid = None
    IMPORT_EXCEPTION = traceback.format_exc()

app = Flask(__name__)


class TechnicalAnalysis:
    @staticmethod
    def calculate_rsi(prices, period=14):
        prices = np.asarray(prices, dtype=float)
        if prices.size < period + 1:
            return 50.0
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return float(100.0 - (100.0 / (1.0 + rs)))

    @staticmethod
    def calculate_ema(prices, period=20):
        prices = list(prices)
        if not prices:
            return 0.0
        if len(prices) < period:
            return float(np.mean(prices))
        sma = float(np.mean(prices[:period]))
        mult = 2.0 / (period + 1.0)
        ema = sma
        for p in prices[period:]:
            ema = (p - ema) * mult + ema
        return float(ema)

    @staticmethod
    def calculate_bollinger_bands(prices, period=20, std_dev=2):
        prices = np.asarray(prices, dtype=float)
        if prices.size < period:
            return None, None, None
        window = prices[-period:]
        sma = float(np.mean(window))
        sd = float(np.std(window, ddof=0))
        return float(sma + std_dev * sd), float(sma), float(sma - std_dev * sd)


class SignalEngine:
    def __init__(self):
        self.ta = TechnicalAnalysis()

    def score_and_classify(self, prices, asset="UNKNOWN"):
        if not prices or len(prices) < 20:
            return None

        rsi = self.ta.calculate_rsi(prices, period=14)
        upper_bb, middle_bb, lower_bb = self.ta.calculate_bollinger_bands(prices, period=20, std_dev=2)
        ema5 = self.ta.calculate_ema(prices, period=5)
        ema20 = self.ta.calculate_ema(prices, period=20)
        price = float(prices[-1])

        conditions = {
            'rsi_buy': rsi < 30,
            'rsi_sell': rsi > 70,
            'bollinger_buy': lower_bb is not None and price < lower_bb,
            'bollinger_sell': upper_bb is not None and price > upper_bb,
            'ema_buy': ema5 > ema20,
            'ema_sell': ema5 < ema20,
        }

        buy_ok = conditions['rsi_buy'] and conditions['bollinger_buy'] and conditions['ema_buy']
        sell_ok = conditions['rsi_sell'] and conditions['bollinger_sell'] and conditions['ema_sell']

        if not buy_ok and not sell_ok:
            return None

        direction = 'BUY' if buy_ok else 'SELL'
        match_count = (
            int(conditions['rsi_buy'] if direction == 'BUY' else conditions['rsi_sell']) +
            int(conditions['bollinger_buy'] if direction == 'BUY' else conditions['bollinger_sell']) +
            int(conditions['ema_buy'] if direction == 'BUY' else conditions['ema_sell'])
        )

        confidence = int(min(100, (match_count / 3) * 100))
        if direction == 'BUY':
            confidence = int(min(100, confidence + max(0, 35 - rsi)))
        else:
            confidence = int(min(100, confidence + max(0, rsi - 65)))

        return {
            'asset': asset,
            'direction': direction,
            'confidence': confidence,
            'rsi': round(rsi, 2),
            'ema5': round(ema5, 5),
            'ema20': round(ema20, 5),
            'upper_bb': round(upper_bb, 5) if upper_bb else None,
            'middle_bb': round(middle_bb, 5) if middle_bb else None,
            'lower_bb': round(lower_bb, 5) if lower_bb else None,
            'price': round(price, 5),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'conditions': conditions,
        }


async def analyze_asset(client, asset, timeframe=60, count=100):
    """Fetch candles and analyze asset"""
    try:
        if hasattr(client, 'get_candles'):
            candles = await client.get_candles(asset, timeframe, count)
        else:
            return None

        if not candles or not isinstance(candles, (list, tuple)):
            return None

        close_prices = []
        for c in candles[-count:]:
            if hasattr(c, 'close'):
                close_prices.append(float(c.close))
            elif isinstance(c, dict):
                close_prices.append(float(c.get('close') or c.get('price') or 0))
            else:
                close_prices.append(float(c))

        if not close_prices:
            return None

        return SignalEngine().score_and_classify(close_prices, asset)

    except Exception as e:
        print(f"Error analyzing {asset}: {str(e)}")
        return None


async def generate_signals():
    """Main signal generation logic"""
    email = os.environ.get('QUOTEX_EMAIL')
    password = os.environ.get('QUOTEX_PASSWORD')

    if not email or not password:
        return {
            'error': 'Missing QUOTEX_EMAIL or QUOTEX_PASSWORD environment variables',
            'status': 'config_error',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    ssid_from_env = os.environ.get('QUOTEX_SSID', '').strip()

    if AsyncQuotexClient is None:
        return {
            'error': 'Quotex API client library (AsyncQuotexClient) is not available',
            'status': 'import_error',
            'details': IMPORT_EXCEPTION,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    ssid = None
    if ssid_from_env:
        ssid = ssid_from_env

    if not ssid:
        if get_ssid is None:
            return {
                'error': 'QUOTEX_SSID not found and get_ssid login helper is unavailable in this environment',
                'status': 'auth_error',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }

        try:
            # Get SSID via Playwright helper (note: may not work in Vercel serverless)
            ok, session_data = await get_ssid(email=email, password=password, is_demo=True)
            if not ok or not session_data:
                return {
                    'error': 'Failed to authenticate with Quotex (invalid credentials?)',
                    'status': 'auth_error',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }

            ssid = session_data.get('ssid', '')
            if not ssid:
                return {
                    'error': 'No SSID in session_data after login',
                    'status': 'auth_error',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }

        except Exception as e:
            return {
                'error': 'Error while calling get_ssid. Playwright might not be available in serverless',
                'status': 'auth_error',
                'details': str(e),
                'trace': traceback.format_exc(),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }

    if not ssid:
        return {
            'error': 'SSID could not be obtained from environment or login flow',
            'status': 'auth_error',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    # Connect client
    client = AsyncQuotexClient(ssid=ssid, is_demo=True, persistent_connection=False, auto_reconnect=False)

    try:
        connected = await client.connect()

        if not connected:
            return {
                'error': 'Could not connect to Quotex server - check SSID/credentials and network',
                'status': 'connection_error',
                'ssid': (ssid[:50] + '...') if ssid else None,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }

        assets = os.getenv('SIGNAL_ASSETS', 'EURUSD,GBPUSD,USDJPY,AUDUSD').split(',')
        results = []
        for asset in assets:
            try:
                signal = await analyze_asset(client, asset.strip(), timeframe=60, count=100)
                if signal and isinstance(signal, dict) and 'direction' in signal:
                    results.append(signal)
            except Exception as e:
                print(f"Asset {asset} error: {e}")
                continue

        if not results:
            return {
                'signal': 'SCANNING',
                'status': 'no_signals',
                'all_signals': [],
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }

        results = sorted(results, key=lambda r: r.get('confidence', 0), reverse=True)
        return {
            'active_signal': results[0],
            'all_signals': results,
            'status': 'ok',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    except Exception as e:
        return {
            'error': f'Unexpected error: {str(e)}',
            'status': 'error',
            'details': traceback.format_exc(),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    finally:
        try:
            await client.disconnect()
        except Exception:
            pass
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }

        results = sorted(results, key=lambda r: r.get('confidence', 0), reverse=True)
        return {
            'active_signal': results[0],
            'all_signals': results,
            'status': 'ok',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    except Exception as e:
        return {
            'error': f'Unexpected error: {str(e)}',
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }


@app.route('/api/signal', methods=['GET', 'POST'])
def signal_handler():
    """HTTP handler for signal endpoint"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        data = loop.run_until_complete(generate_signals())
        status = 200 if data.get('status') == 'ok' or data.get('signal') else 500
        return jsonify(data), status
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'internal_error'}), 500
    finally:
        loop.close()


@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'Trading Signal API v1.0 - Use /api/signal'})
