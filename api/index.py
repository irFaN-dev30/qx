
from flask import Flask, jsonify
import os
import asyncio
import numpy as np
from datetime import datetime
import time

# --- আপনার রিপোজিটরি থেকে আনা Quotex ক্লায়েন্ট ---
# আমরা ধরে নিচ্ছি যে `quotexapi` ফোল্ডারটি প্রজেক্টের রুটে আছে
from quotexapi.stable_api import Quotex

# --- Flask অ্যাপ ইনিশিয়ালাইজেশন ---
app = Flask(__name__)

# ============================================================================
# টেকনিক্যাল অ্যানালাইসিস ক্লাস (আপনার improved_signal_generator থেকে)
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
    def calculate_bollinger_bands(prices, period=20, std_dev=2):
        prices = np.asarray(prices)
        if prices.size < period: return None, None, None
        window = prices[-period:]
        sma = float(np.mean(window))
        sd = float(np.std(window, ddof=0))
        upper = sma + std_dev * sd
        lower = sma - std_dev * sd
        return float(upper), float(sma), float(lower)

# ============================================================================
# সিগন্যাল জেনারেটর ক্লাস (আপনার লজিক ব্যবহার করে)
# ============================================================================
class ApiSignalGenerator:
    def __init__(self, client):
        self.client = client
        self.ta = TechnicalAnalysis()

    async def analyze_asset(self, asset, timeframe=60, candle_count=100):
        try:
            # দ্রষ্টব্য: আপনার ক্লায়েন্টে get_candles প্যারামিটারগুলো ভিন্ন হতে পারে।
            # আমি 'par', 'timeframe', 'quantidade' এর পরিবর্তে 'asset', 'interval', 'count' ব্যবহার করছি।
            candles = await self.client.get_candles(asset=asset, interval=timeframe, count=candle_count, end_time=int(time.time()))
            if not candles or not isinstance(candles, list):
                return None

            candles_sorted = sorted(candles, key=lambda c: c.get("from", 0))
            close_prices = [float(c.get('close', 0)) for c in candles_sorted]
            if len(close_prices) < 20:
                return None

            # --- আপনার সিগন্যাল রুল প্রয়োগ ---
            rsi = self.ta.calculate_rsi(close_prices, period=14)
            upper_bb, middle_bb, lower_bb = self.ta.calculate_bollinger_bands(close_prices)
            ema5 = self.ta.calculate_ema(close_prices, period=5)
            ema20 = self.ta.calculate_ema(close_prices, period=20)
            current_price = close_prices[-1]

            confidence_score = 0
            direction = None
            
            # রুল ১: RSI
            is_oversold = rsi < 30
            is_overbought = rsi > 70

            # রুল ২: Bollinger Bands
            price_touches_lower = current_price <= lower_bb if lower_bb else False
            price_touches_upper = current_price >= upper_bb if upper_bb else False
            
            # রুল ৩: EMA Crossover
            ema_cross_up = ema5 > ema20
            ema_cross_down = ema5 < ema20

            # সিগন্যাল সিদ্ধান্ত
            if is_oversold and price_touches_lower and ema_cross_up:
                direction = "Buy" # CALL
                confidence_score = (100 - rsi) * 1.5 # উদাহরণস্বরূপ গণনা
            elif is_overbought and price_touches_upper and ema_cross_down:
                direction = "Sell" # PUT
                confidence_score = rsi * 1.5 # উদাহরণস্বরূপ গণনা

            if direction:
                return {
                    'asset': asset,
                    'signal': direction,
                    'confidence': min(int(confidence_score), 100),
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                }
            return None

        except Exception:
            # সার্ভারলেস পরিবেশে ত্রুটি লগ করা গুরুত্বপূর্ণ
            return None

# ============================================================================
# Flask API রুট
# ============================================================================
@app.route('/api/index', methods=['GET'])
def get_signals_api():
    # Vercel-এর সার্ভারলেস ফাংশনের জন্য একটি নতুন অ্যাসিঙ্ক্রোনাস লুপ তৈরি করুন
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # run_until_complete ব্যবহার করে অ্যাসিঙ্ক্রোনাস ফাংশন চালান
    signals = loop.run_until_complete(fetch_signals())
    loop.close()
    
    return jsonify(signals)

async def fetch_signals():
    # --- এনভায়রনমেন্ট ভেরিয়েবল থেকে ক্রেডেনশিয়াল লোড করুন ---
    email = os.environ.get('QUOTEX_EMAIL')
    password = os.environ.get('QUOTEX_PASSWORD')

    if not email or not password:
        return [{"error": "Credentials not configured in environment variables."}]

    client = Quotex(email=email, password=password)
    try:
        # --- ক্লায়েন্টের সাথে সংযোগ স্থাপন ---
        check, reason = await client.connect()
        if not check:
            await client.close()
            return [{"error": f"Connection failed: {reason}"}]

        # --- ডেমো ব্যালেন্সে পরিবর্তন (নিরাপত্তার জন্য) ---
        try:
            await client.change_balance('PRACTICE')
        except: # পুরোনো ক্লায়েন্টে এই মেথড নাও থাকতে পারে
            pass

        # --- অ্যাসেট বা ইন্সট্রুমেন্ট তালিকা আনুন ---
        # আমরা শুধুমাত্র কয়েকটি জনপ্রিয় অ্যাসেট দিয়ে শুরু করছি, কারণ সবগুলো একসাথে আনা সময়সাপেক্ষ হতে পারে
        assets_to_scan = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD_otc", "EURUSD_otc"]
        
        gen = ApiSignalGenerator(client)
        
        # --- অ্যাসেটগুলো সমান্তরালভাবে বিশ্লেষণ করুন ---
        tasks = [gen.analyze_asset(asset) for asset in assets_to_scan]
        results = await asyncio.gather(*tasks)
        
        # --- সফল সিগন্যালগুলো ফিল্টার করুন ---
        strong_signals = [res for res in results if res and res['confidence'] > 50]
        
        await client.close()
        return sorted(strong_signals, key=lambda x: x['confidence'], reverse=True)

    except Exception as e:
        await client.close()
        return [{"error": f"An unexpected error occurred: {str(e)}"}]

