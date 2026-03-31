
import os
import time
import pandas as pd
import pandas_ta as ta
from threading import Thread
from firebase_admin import credentials, firestore, initialize_app
from flask import Flask
from api_quotex.quotex_api import Quotex
# Initialize Firebase
cred = credentials.ApplicationDefault()
initialize_app(cred)
db = firestore.client()
# --- Indicator Calculation ---
def calculate_indicators(df):
    df.ta.rsi(length=14, append=True)
    df.ta.ema(length=5, append=True)
    df.ta.ema(length=10, append=True)
    df.ta.ema(length=20, append=True)
    df.ta.bbands(length=20, append=True)
    return df
# --- Signal Generation ---
def get_signal(df):
    latest = df.iloc[-1]
    # Strong Buy
    if (latest['RSI_14'] < 30 and latest['close'] < latest['BBL_20_2.0'] and 
        latest['EMA_5'] > latest['EMA_10'] > latest['EMA_20']):
        return {'asset': latest['asset'], 'signal': 'Buy', 'confidence': 0.9, 'countdown': 60}
    # Strong Sell
    elif (latest['RSI_14'] > 70 and latest['close'] > latest['BBU_20_2.0'] and
          latest['EMA_5'] < latest['EMA_10'] < latest['EMA_20']):
        return {'asset': latest['asset'], 'signal': 'Sell', 'confidence': 0.9, 'countdown': 60}
    return None
# --- Quotex WebSocket Client ---
class QuotexClient:
    def __init__(self, email, password, assets):
        self.api = Quotex(email=email, password=password)
        self.assets = assets
        self.data = {asset: pd.DataFrame() for asset in assets}
    def connect(self):
        self.api.connect()
    def subscribe_to_assets(self):
        self.api.subscribe_real_time_candles(self.assets, 1) # 1-minute candles
        for asset in self.assets:
            Thread(target=self.run, args=(asset,)).start()
    def run(self, asset):
        while True:
            candles = self.api.get_real_time_candles(asset, 1)
            if candles:
                for timestamp, candle in candles.items():
                    candle_df = pd.DataFrame([candle], index=[timestamp])
                    candle_df['asset'] = asset
                    self.data[asset] = pd.concat([self.data[asset], candle_df])
                    # Keep last 100 candles
                    self.data[asset] = self.data[asset].iloc[-100:] 
                    # Calculate indicators and check for signals
                    self.data[asset] = calculate_indicators(self.data[asset])
                    signal = get_signal(self.data[asset])
                    if signal:
                        print(f"Signal found: {signal}")
                        db.collection('signals').document('active').set(signal)
                        db.collection('all_signals').document(asset).set(signal)
            time.sleep(1)
# --- Flask App ---
app = Flask(__name__)
@app.route('/run_signal_generator')
def run_signal_generator():
    # --- Securely get credentials ---
    EMAIL = os.environ.get('QUOTEX_EMAIL')
    PASSWORD = os.environ.get('QUOTEX_PASSWORD')
    ASSETS = ['EURUSD-OTC', 'USDJPY-OTC', 'GBPUSD-OTC']
    if not EMAIL or not PASSWORD:
        return "Error: Quotex credentials not set.", 500
    client = QuotexClient(email=EMAIL, password=PASSWORD, assets=ASSETS)
    client.connect()
    client.subscribe_to_assets()
    return "Signal generator started."
if __name__ == '__main__':
    app.run()
