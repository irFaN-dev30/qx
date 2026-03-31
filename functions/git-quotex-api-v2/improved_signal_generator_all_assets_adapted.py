import logging
import asyncio
from datetime import datetime, time, timedelta
import pandas as pd
import pandas_ta as ta
import firebase_admin
from firebase_admin import credentials, firestore

from api_quotex.client import QuotexClient

# --- Firebase Initialization ---
cred = credentials.Certificate("sessions/config.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO)

# --- Global Variables ---
client = None
candle_data_cache = {}
MAX_CACHE_SIZE = 200

def get_custom_indicators(candle_data):
    df = pd.DataFrame(candle_data)
    if df.empty:
        return None

    # Calculate indicators
    df.ta.rsi(length=14, append=True)
    df.ta.bbands(length=20, append=True)
    df.ta.ema(length=50, append=True, col_names=('EMA_50',))
    df.ta.ema(length=200, append=True, col_names=('EMA_200',))

    return df.iloc[-1]

async def trade(client, asset, amount, action, duration):
    """Function to place a trade."""
    if await client.trade(asset, amount, action, duration):
        logging.info(f"Successfully placed {action} trade for {asset}")

async def get_signal(asset_data):
    """Analyzes candle data to generate a trading signal."""
    last_candle = asset_data.iloc[-1]
    
    # Example Strategy: RSI + Bollinger Bands + EMA
    signal = "NEUTRAL"
    if last_candle['close'] > last_candle['BBL_20_2.0'] and last_candle['close'] < last_candle['BBU_20_2.0']:
        if last_candle['RSI_14'] < 30 and last_candle['close'] > last_candle['EMA_50']:
            signal = "BUY"
        elif last_candle['RSI_14'] > 70 and last_candle['close'] < last_candle['EMA_50']:
            signal = "SELL"
            
    return signal

async def update_firestore(asset, indicators, signal):
    """Updates Firestore with the latest asset data."""
    try:
        doc_ref = db.collection('signals').document(asset)
        asset_info = await client.get_asset_info(asset_name=asset)
        
        update_data = {
            "asset": asset,
            "price": indicators['close'],
            "rsi": indicators['RSI_14'],
            "bollinger_upper": indicators['BBU_20_2.0'],
            "bollinger_lower": indicators['BBL_20_2.0'],
            "ema50": indicators['EMA_50'],
            "ema200": indicators['EMA_200'],
            "signal": signal,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "underlying": asset_info.get("underlying", "")
        }
        await doc_ref.set(update_data, merge=True)
        logging.info(f"Successfully updated Firestore for {asset}")
    except Exception as e:
        logging.error(f"Error updating Firestore for {asset}: {e}")

async def on_candle(asset, new_candle_data):
    """Callback function for when new candle data is received."""
    global candle_data_cache

    if asset not in candle_data_cache:
        candle_data_cache[asset] = []

    candle_data_cache[asset].append(new_candle_data)

    if len(candle_data_cache[asset]) > MAX_CACHE_SIZE:
        candle_data_cache[asset].pop(0)

    indicators = get_custom_indicators(candle_data_cache[asset])
    if indicators is not None:
        signal = await get_signal(pd.DataFrame(candle_data_cache[asset]))
        await update_firestore(asset, indicators, signal)

async def main():
    global client
    client = await QuotexClient.create("irfanp.dev@gmail.com", "Ilovemycountry", "wss://ws.quotex.com/socket.io/?EIO=4&transport=websocket")
    if not client:
        logging.error("Login failed")
        return

    assets_info = await client.get_assets(asset_type="crypto")
    if not assets_info:
        logging.error("Could not retrieve asset list.")
        return
        
    open_assets = [asset for asset, info in assets_info.items() if info.get("isOpen")]
    logging.info(f"Trading on open assets: {open_assets}")
    
    # Subscribe to candle data for all open assets
    for asset in open_assets:
        await client.subscribe_live_deal(asset, "live-deal-binary-option-v2", size=60, on_deal_callback=on_candle)

    # Keep the script running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logging.info("Shutting down...")
    finally:
        if client:
            await client.close()
            logging.info("Connection closed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(f"An error occurred: {e}")
