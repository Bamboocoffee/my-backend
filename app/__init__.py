from flask import Flask, redirect, url_for 
from flask_cors import CORS
from dotenv import load_dotenv
from app.routes import main  # Import the Blueprint
import os


def create_app():
    # Load environment variables from .env
    load_dotenv()
    
    app = Flask(__name__)
    # CORS(app, origins=["http://localhost:3000"])  # Enable CORS globally
    CORS(app)  # Enable CORS globally

    # Use the environment variables
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
    app.config['DEBUG'] = True
    app.config['JSON_AS_ASCII'] = False  # Ensure proper decoding of JSON

    # Register Blueprints
    app.register_blueprint(main)

    @main.errorhandler(404)
    def page_not_found(e):
        return redirect(url_for("main/home"))

    return app
