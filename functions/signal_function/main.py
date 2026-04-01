# -*- coding: utf-8 -*-
# --- Path setup for local API-Quotex library ---
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))
api_quotex_path = os.path.join(root_dir, 'API-Quotex-main')
if api_quotex_path not in sys.path:
    sys.path.append(api_quotex_path)
# --- End of Path Setup ---

# --- Main Application Imports ---
import asyncio
from flask import Flask, jsonify
from flask_cors import CORS
from firebase_admin import credentials, firestore, initialize_app
from api_quotex.client import AsyncQuotexClient
from api_quotex.utils import get_ssid
from api_quotex.constants import OrderDirection, ASSET_LIST

# --- Initializations ---
app = Flask(__name__)
CORS(app)

try:
    cred = credentials.ApplicationDefault()
    initialize_app(cred)
    db = firestore.client()
    print("Firebase App initialized successfully.")
except Exception as e:
    print(f"Firebase initialization failed: {e}")
    db = None

# --- Global State ---
quotex_client = None
ssid = None

# --- Core Trading Logic ---
async def get_or_create_quotex_client():
    global quotex_client, ssid
    if quotex_client and quotex_client.is_connected:
        return quotex_client

    email = os.getenv("QUOTEX_EMAIL")
    password = os.getenv("QUOTEX_PASSWORD")
    if not email or not password:
        print("Error: QUOTEX_EMAIL and QUOTEX_PASSWORD env vars not set.")
        return None

    try:
        print("Attempting to get SSID via Playwright...")
        ssid_info = get_ssid(email=email, password=password)
        ssid = ssid_info.get("demo")
        if not ssid:
            print("Failed to retrieve SSID.")
            return None
        print("SSID retrieved successfully.")

        client = AsyncQuotexClient(ssid=ssid, is_demo=True)
        if await client.connect():
            print("Quotex client connected successfully.")
            quotex_client = client
            return client
        else:
            print("Failed to connect Quotex client.")
            return None
    except Exception as e:
        print(f"An error occurred during client initialization: {e}")
        return None

async def analyze_asset(asset_name):
    client = await get_or_create_quotex_client()
    if not client:
        return None

    try:
        await client.subscribe_candles(asset=asset_name, timeframe=60)
        async for candle in client.iter_candles(asset_name, 60):
            print(f"New candle for {asset_name}: O:{candle.open} C:{candle.close}")
            await client.unsubscribe_candles(asset=asset_name, timeframe=60)
            
            signal_type = "BUY" if candle.close > candle.open else "SELL"
            return {"asset": asset_name, "signal": signal_type, "confidence": 0.75}
            
    except Exception as e:
        print(f"Error analyzing asset {asset_name}: {e}")
        return None

# --- API Endpoints ---
@app.route("/generate-signal", methods=["GET"])
def generate_signal_endpoint():
    assets_to_check = ["EURUSD_otc", "AUDCAD_otc", "BTCUSD_otc"]
    
    async def run_analysis():
        tasks = [analyze_asset(asset) for asset in assets_to_check]
        results = await asyncio.gather(*tasks)
        
        signals = [s for s in results if s] # Filter out None results
        
        if db and signals:
            for signal in signals:
                try:
                    db.collection('signals').add(signal)
                    print(f"Signal for {signal['asset']} stored in Firestore.")
                except Exception as e:
                    print(f"Error storing signal in Firestore: {e}")
        return signals

    # Run the async analysis in a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    generated_signals = loop.run_until_complete(run_analysis())
    loop.close()

    if generated_signals:
        return jsonify({"status": "success", "signals": generated_signals})
    else:
        return jsonify({"status": "failed", "message": "Could not generate signals."}), 500

@app.route("/")
def index():
    # This is the handler for the root path, which Vercel needs.
    return "Welcome to the Quotex Signal Generation API."

# The __name__ == '__main__' block is for local execution, not for Vercel.
# if __name__ == "__main__":
    app.run(debug=True, port=8080)
