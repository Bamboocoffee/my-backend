from flask import Flask, request, jsonify
import os

# Load the secret token from an environment variable
SECRET_TOKEN = os.getenv("SECRET_TOKEN")

def authentication():
    token = request.headers.get("Authorization")
    if token != SECRET_TOKEN:
        return jsonify({"error": "Unauthorized"}), 401

    # Process the request (e.g., update the spreadsheet)
    data = request.json
    weight = data.get("weight")
    if not weight:
        return jsonify({"error": "Weight value is missing"}), 400

    # (Add your spreadsheet updating logic here)
    return jsonify({"message": "Spreadsheet updated successfully"}), 200