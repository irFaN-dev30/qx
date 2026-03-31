from flask import Flask, jsonify
from quotexapi.stable_api import Quotex
import asyncio

app = Flask(__name__)

# --- এই অংশটি আপনার আসল কোড থেকে নেওয়া ---
def get_top_signals():
    signals = Quotex.get_signal_all()
    if signals:
        top_signals = sorted(signals, key=lambda x: x.get('rating', 0), reverse=True)[:5]
        return top_signals
    return []
# ----------------------------------------

@app.route('/api/index', methods=['GET'])
def get_signals_api():
    # এখানে আমরা get_top_signals ফাংশনটি কল করছি
    signals_data = get_top_signals()
    # এবং ফলাফলটিকে JSON হিসেবে ফেরত পাঠাচ্ছি
    return jsonify(signals_data)

# এই অংশটি Vercel-এ লোকাল টেস্টের জন্য, ডেপ্লয়মেন্টের জন্য জরুরি নয়
if __name__ == '__main__':
    app.run(debug=True)
