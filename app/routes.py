from flask import Blueprint, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI
import os
from app.services.google_sheets_service import google_sheets_service
from app.services.authenticate_service import authentication
from app.services.test_service import test_agent_function

# Define the Blueprint
main = Blueprint('main', __name__)
CORS(main, origins=["http://localhost:3000"])  # Allow requests from localhost:3000

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@main.route('/')
def home():
    return render_template('black_hole.html')

@main.route('/completion/', methods=['GET', 'POST'])
def completion_call():
    def parse_email_with_gpt(input_text="weight 46, sleep quality 88"):
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts structured data from text emails."},
                {"role": "user", "content": f"Extract weight, sleep duration, sleep quality, and sleep HRV from this email:\n{input_text}"}
            ]
        )
        return response.choices[0].message.content

    try:
        data = request.get_json()
        return {"response": parse_email_with_gpt(data["message"])}
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@main.route('/health/google_sheets_service/', methods=['GET', 'POST'])
@authentication
def google_sheets_service_call():
    try:
        data = request.get_json()
        result = google_sheets_service(weight=data["message"])
        return jsonify({"status": "success", "response": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    

@main.route('/test/', methods=['GET', 'POST'])
def test_call():
    try:
        result = test_agent_function()
        return jsonify({"status": "success", "response": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400