from flask import Flask, request, jsonify, redirect, url_for
from functools import wraps
import os

# Load the secret token from an environment variable
SECRET_TOKEN = os.getenv("SECRET_TOKEN")

def authentication(f):
    """
    Decorator to enforce authentication for Flask routes.

    This decorator checks for an `Authorization` token in the request headers.
    If the token is missing or invalid, it returns a 401 Unauthorized response.
    Otherwise, it allows the wrapped function to execute.

    Args:
        f (function): The Flask route function to be wrapped.

    Returns:
        function: A decorated function that enforces authentication.
    
    Raises:
        401 Unauthorized: If the token is missing or invalid.
        500 Internal Server Error: If an unexpected error occurs during execution.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            token = request.headers.get("Authorization") # Gets the token if present in the header
            if not token:
                return redirect(url_for("main.home")) # redirect to the main home page.
            # =========== OLD RESPONSE ===========
                # response_text = """Hello! I'm currently only able to speak with Stephen. 
                # I'm still in build mode. 
                # However, if you'd like to learn more about Stephen, I'd suggest checking him out on LinkedIn (https://www.linkedin.com/in/stephen-keenan/) or book a time to chat (https://calendar.google.com/calendar/u/0/appointments/schedules/AcZssZ02Ay5xQ5KRJgIT1TKOZy1wsRHvxLBejqYlRLGzlPUg5-Sbk7dcdZSVLZG77Jh8y6U3ySV4NYOE)."""
                # return jsonify({"response": response_text}), 200  # Return 401 Unauthorized with HTML content
            # elif token != SECRET_TOKEN:
                # return jsonify({"response": "Unauthorized"}), 401
            # =========== OLD RESPONSE ===========
            else:
                 # Token is valid, proceed to the original function
                return f(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": str(e)}), 500  # Internal Server Error
        
    return decorated_function
