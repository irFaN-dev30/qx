
import sys
import os
import json
from flask import Flask, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore

# --- Path Correction for Vercel Serverless Environment ---
# This adds the parent directory (functions) to the system path
# so that it can find the 'git_quotex_api_v2' module.
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
# --- End Path Correction ---

from git_quotex_api_v2.improved_signal_generator_all_assets import get_all_signals

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# --- Firebase Initialization ---
try:
    firebase_key_str = os.getenv('FIREBASE_PRIVATE_KEY')
    if not firebase_key_str:
        raise ValueError("FIREBASE_PRIVATE_KEY environment variable not set.")

    # Handle escaped newline characters from Vercel environment variables
    firebase_key_dict = json.loads(firebase_key_str.replace('\\n', '\n'))
    
    cred = credentials.Certificate(firebase_key_dict)
    
    # Initialize app if not already initialized
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
        
    db = firestore.client()
except Exception as e:
    # Log the error but don't crash the app on startup
    print(f"CRITICAL: Firebase initialization failed: {e}")
    db = None
# --- End Firebase Initialization ---


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET'])
def handler(path):
    """
    Main function to generate and serve trading signals.
    This is triggered by requests to /api/signal.
    """
    if db is None:
        return jsonify({"status": "error", "message": "Firebase is not initialized."}), 500

    try:
        email = os.getenv('QUOTEX_EMAIL')
        password = os.getenv('QUOTEX_PASSWORD')

        if not email or not password:
            return jsonify({"status": "error", "message": "Quotex credentials are not set in environment variables."}), 500
        
        # 1. Generate signals using your script
        signals = get_all_signals(email=email, password=password)
        
        # 2. Store signals in Firestore
        signals_collection = db.collection('signals')
        
        # Batch write for efficiency
        batch = db.batch()
        for signal in signals:
            if signal and 'asset' in signal:
                asset = signal.get('asset')
                doc_ref = signals_collection.document(asset)
                batch.set(doc_ref, signal)
        batch.commit()

        print(f"Successfully generated and stored {len(signals)} signals.")
        return jsonify({"status": "success", "signals_generated": len(signals)}), 200

    except Exception as e:
        print(f"Error in signal generation handler: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# This is the entry point for Vercel
# The file is executed and the 'app' object is used by the WSGI server
