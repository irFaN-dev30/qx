
import sys
import os
import json

# --- Master Fix: User-Provided Path Correction for Vercel ---
# This block sets the correct library path to find the api_quotex module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
api_path = os.path.join(parent_dir, 'git-quotex-api-v2', 'API-Quotex-main')
sys.path.append(parent_dir)
sys.path.append(api_path)
# --- End Master Fix ---

# Now, import the necessary modules
from flask import Flask, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
from git_quotex_api_v2.improved_signal_generator_all_assets import get_all_signals

app = Flask(__name__)
CORS(app)

# --- Firebase & Credentials Handling ---
# 1. Firebase Initialization with key format correction
try:
    # Securely get and format the Firebase private key
    firebase_key_str = os.getenv('FIREBASE_PRIVATE_KEY')
    if not firebase_key_str:
        raise ValueError("FIREBASE_PRIVATE_KEY environment variable is not set.")
    
    # Replace escaped newlines for JSON parsing, as suggested by the user
    firebase_key_dict = json.loads(firebase_key_str.replace('\\n', '\n'))
    
    cred = credentials.Certificate(firebase_key_dict)
    
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
        
    db = firestore.client()
except Exception as e:
    print(f"CRITICAL: Firebase initialization failed: {e}")
    db = None

# 2. Get Quotex credentials from environment variables
QUOTEX_EMAIL = os.getenv('QUOTEX_EMAIL')
QUOTEX_PASSWORD = os.getenv('QUOTEX_PASSWORD')
# --- End Credentials Handling ---


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET'])
def handler(path):
    if db is None:
        return jsonify({"status": "error", "message": "Server critical error: Firebase is not initialized."}), 500

    if not QUOTEX_EMAIL or not QUOTEX_PASSWORD:
        return jsonify({"status": "error", "message": "Server configuration error: Quotex credentials are not set."}), 500

    try:
        # The improved_signal_generator_all_assets script dynamically fetches assets
        # So, no manual asset list is needed here.
        signals = get_all_signals(email=QUOTEX_EMAIL, password=QUOTEX_PASSWORD)
        
        if not signals:
            # Return success even if no signals are generated, prevents front-end error
            return jsonify({"status": "success", "message": "Scan complete. No strong signals found at this time."}), 200

        # Store signals in Firestore using a batch write
        batch = db.batch()
        for signal in signals:
            if signal and 'asset' in signal:
                asset = signal.get('asset')
                doc_ref = db.collection('signals').document(asset)
                batch.set(doc_ref, signal)
        batch.commit()

        return jsonify({"status": "success", "signals_generated": len(signals)}), 200

    except Exception as e:
        # Catch any other error during signal generation and log it
        error_message = f"An error occurred in the signal generation process: {str(e)}"
        print(error_message)
        return jsonify({"status": "error", "message": error_message}), 500
