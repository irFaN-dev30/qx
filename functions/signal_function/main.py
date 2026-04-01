
from flask import Flask, jsonify
app = Flask(__name__)

# A simple test endpoint to check if the Vercel routing is working.
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET'])
def handler(path):
    return jsonify({"status": "Success", "message": "Backend is alive!"})
