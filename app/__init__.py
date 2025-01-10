from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from app.routes import main  # Import the Blueprint
import os

def create_app():
    # Load environment variables from .env
    load_dotenv()
    
    app = Flask(__name__)
    CORS(app, origins=["http://localhost:3000"])  # Enable CORS globally

    # Use the environment variables
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')

    # Register Blueprints
    app.register_blueprint(main)

    return app
