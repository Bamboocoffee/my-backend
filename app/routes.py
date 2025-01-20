from flask import Blueprint, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI
import os
from app.services.google_sheets_service import google_sheets_service
from app.services.authenticate import authentication

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
def google_sheets_service_call():
    try:
        data = request.get_json()
        result = google_sheets_service(weight=data["message"])
        return {"response": result}
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@main.route('/authenticate/private-token/', methods=['GET', 'POST'])
def authenticate():
    token = request.headers.get("Authorization")
    if not token:
        response_text = """
            Hello! I'm currently only able to speak with Stephen. \n I'm still in build mode. \n However, if you'd like to learn more about Stephen, I'd suggest checking him out on LinkedIn (https://www.linkedin.com/in/stephen-keenan/) or book a time at to chat (https://calendar.google.com/calendar/u/0/appointments/schedules/AcZssZ02Ay5xQ5KRJgIT1TKOZy1wsRHvxLBejqYlRLGzlPUg5-Sbk7dcdZSVLZG77Jh8y6U3ySV4NYOE).
        """
        return jsonify({"response": response_text}), 200  # Return 401 Unauthorized with HTML content
    try:
        return authentication()
    except Exception as e:
        return jsonify({"error": str(e)}), 400