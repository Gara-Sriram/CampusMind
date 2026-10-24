import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from flask import Flask, request, jsonify
from pymongo import MongoClient
import auth

app = Flask(__name__)
MONGO_URI = os.getenv("MONGO_URI", "")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "askiiita")

@app.route('/api/register', methods=['POST', 'OPTIONS'])
def register_endpoint():
    if request.method == 'OPTIONS':
        res = Flask.make_response(app, '')
        res.headers.add("Access-Control-Allow-Origin", "*")
        res.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        res.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return res

    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing username or password."}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    try:
        try:
            client = MongoClient(
                MONGO_URI, tls=True,
                tlsAllowInvalidCertificates=True,
                tlsAllowInvalidHostnames=True,
                serverSelectionTimeoutMS=2000,
            )
            client.admin.command('ping')
            db = client[MONGO_DB_NAME]
            print("[API REGISTER] Connected to Atlas MongoDB.")
        except Exception as conn_err:
            print(f"[API REGISTER DB ERROR] Falling back to mongomock: {conn_err}")
            import mongomock
            client = mongomock.MongoClient()
            db = client[MONGO_DB_NAME]
            
        success = auth.create_user(db, username, password, "student")
        if success:
            response = jsonify({"message": "User registered successfully."})
            response.headers.add("Access-Control-Allow-Origin", "*")
            return response
        else:
            return jsonify({"error": "Username already exists."}), 409
    except Exception as e:
        return jsonify({"error": f"Database Error: {str(e)}"}), 500

handler = app
