
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_functions import https_fn
import os
import json
from git_quotex_api_v2.improved_signal_generator_all_assets import get_all_signals

# Initialize Firebase Admin SDK
cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred)
db = firestore.client()

# Placeholder for API credentials from environment variables/secrets
# In a real environment, these would be set in Firebase Secret Manager
# and accessed via os.environ.get('QUOTEX_EMAIL')
EMAIL = os.environ.get('QUOTEX_EMAIL', 'your_email@example.com')
PASSWORD = os.environ.get('QUOTEX_PASSWORD', 'your_password')

@https_fn.on_request()
def generate_signals(req: https_fn.Request) -> https_fn.Response:
    """
    An HTTP-triggered Cloud Function that generates trading signals
    and stores them in Firestore.
    """
    try:
        # Generate signals using your existing logic
        signals = get_all_signals(email=EMAIL, password=PASSWORD)

        # Store signals in Firestore
        signals_collection = db.collection('signals')
        
        # Clear existing signals for a clean slate on each run
        for doc in signals_collection.stream():
            doc.reference.delete()

        # Add new signals
        for signal in signals:
            if signal:
                asset = signal.get('asset', 'UNKNOWN_ASSET')
                signals_collection.document(asset).set(signal)
        
        print(f"Successfully generated and stored {len(signals)} signals.")
        return https_fn.Response(json.dumps({'status': 'success', 'signals_generated': len(signals)}), mimetype="application/json")

    except Exception as e:
        print(f"Error generating signals: {e}")
        return https_fn.Response(json.dumps({'status': 'error', 'message': str(e)}), status=500, mimetype="application/json")
