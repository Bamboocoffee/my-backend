from flask import Blueprint, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI
import os
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

# @main.route('/completion/', methods=['GET', 'POST'])
# def completion_call():
#     def parse_email_with_gpt(input_text="weight 46, sleep quality 88"):
#         response = client.chat.completions.create(
#             model="gpt-4",
#             messages=[
#                 {"role": "system", "content": "You are a helpful assistant that extracts structured data from text emails."},
#                 {"role": "user", "content": f"Extract weight, sleep duration, sleep quality, and sleep HRV from this email:\n{input_text}"}
#             ]
#         )
#         return response.choices[0].message.content

#     try:
#         data = request.get_json()
#         return {"response": parse_email_with_gpt(data["message"])}
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

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
        result = OuraServiceAPI()
        result.get_daily_readiness("2025-02-05", "2025-02-06")
        print(result.get_daily_sleep("2025-02-05", "2025-02-06"))
        return jsonify({"status": "success", "response": [], "thread_id": ""}), 200
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 400