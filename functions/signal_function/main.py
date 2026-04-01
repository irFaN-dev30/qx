
import sys
import os
import json

# --- User-Provided Path Correction for Vercel Serverless Environment ---
# This adds the correct path to find the sibling api_quotex module.
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
api_path = os.path.join(parent_dir, 'git-quotex-api-v2', 'API-Quotex-main')
sys.path.append(parent_dir) # Add root 'functions' directory
sys.path.append(api_path) # Add specific API directory
# --- End Path Correction ---

from flask import Flask, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
from git_quotex_api_v2.improved_signal_generator_all_assets import get_all_signals

app = Flask(__name__)
CORS(app)

# --- Firebase Initialization ---
try:
    firebase_key_str = os.getenv('FIREBASE_PRIVATE_KEY')
    if not firebase_key_str:
        raise ValueError("FIREBASE_PRIVATE_KEY environment variable not set.")

    # Handle escaped newline characters from Vercel env vars and parse JSON
    firebase_key_dict = json.loads(firebase_key_str.replace('\\n', '\n'))
    
    cred = credentials.Certificate(firebase_key_dict)
    
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
        
    db = firestore.client()
except Exception as e:
    print(f"CRITICAL: Firebase initialization failed: {e}")
    db = None
# --- End Firebase Initialization ---


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET'])
def handler(path):
    if db is None:
        return jsonify({"status": "error", "message": "Firebase is not initialized."}), 500

    try:
        email = os.getenv('QUOTEX_EMAIL')
        password = os.getenv('QUOTEX_PASSWORD')

        if not email or not password:
            return jsonify({"status": "error", "message": "Quotex credentials are not set."}), 500
        
        signals = get_all_signals(email=email, password=password)
        
        if not signals:
            return jsonify({"status": "success", "message": "No new signals generated."}), 200

        batch = db.batch()
        for signal in signals:
            if signal and 'asset' in signal:
                asset = signal.get('asset')
                doc_ref = db.collection('signals').document(asset)
                batch.set(doc_ref, signal)
        batch.commit()

        return jsonify({"status": "success", "signals_generated": len(signals)}), 200

    except Exception as e:
        print(f"Error in signal generation handler: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
