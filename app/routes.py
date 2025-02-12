from flask import Blueprint, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI
import os
import json
from datetime import datetime, timedelta
from app.services.archived.google_sheets_service import google_sheets_service
from app.services.authenticate_service import authentication
from app.services.agent_service import agent_service
from app.services.oura_service import OuraServiceAPI

# Define the Blueprint
main = Blueprint('main', __name__)
CORS(main, origins=["http://localhost:3000"])  # Allow requests from localhost:3000

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@main.route('/')
def home():
    return render_template('welcome.html')

@main.route('/agent/basic_service/', methods=['GET', 'POST'])
@authentication
def call_agent_service():
    data = request.get_json()
    print(data)
    try:
        result = agent_service(data["message"], data["user_thread_id"])
        print(result)
        return jsonify({"status": "success", "response": result["message"], "thread_id": result["thread_id"]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@main.route('/test/', methods=['GET', 'POST'])
@authentication
def test_call():
    try:
        result = google_sheets_service(weight=46, steps=4680, cardio=555, protein=178)
        print(result)
        return jsonify({"status": "success", "response": [], "thread_id": ""}), 200
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 400
    
@main.route('/oura/', methods=['GET', 'POST'])
@authentication
def oura_service():
    try:
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        result = OuraServiceAPI()
        summary_sleep_data = result.get_daily_sleep(today, tomorrow)
        all_sleep_data = result.get_sleep_details(yesterday, today)
        try:
            result = agent_service(content="This is my hrv: {0} , sleep score: {1} and sleep duration: {2}."
                                   .format(all_sleep_data["total_hrv"], 
                                            summary_sleep_data["sleep_score"], 
                                            all_sleep_data["total_sleep_duration"]))
            return jsonify({"status": "success", "response": [], "thread_id": ""}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400