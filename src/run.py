# run.py
import os
import sys
import logging
from flask import Flask

script_dir = os.path.dirname(os.path.abspath(__file__))
# Assuming run.py is in the root of your project structure that contains 'analyzer', 'routes', 'config.py'
project_root = script_dir # Adjust if run.py is nested deeper, e.g., project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# Import configuration and the main routes blueprint
import config
from routes.main import main_bp



# Configure logging (can also be done via app config)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_app():
    """Creates and configures the Flask application."""
    app = Flask(__name__)

    # Load configuration from config.py
    app.config['SECRET_KEY'] = config.FLASK_SECRET_KEY
    app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        try:
            os.makedirs(app.config['UPLOAD_FOLDER'])
            logging.info(f"Created upload folder: {app.config['UPLOAD_FOLDER']}")
        except OSError as e:
            logging.error(f"Could not create upload folder {app.config['UPLOAD_FOLDER']}: {e}")
            # Depending on severity, might want to exit or handle differently

    # Register the blueprint containing the routes
    app.register_blueprint(main_bp)

    logging.info("Flask app created and configured.")
    return app

# --- Main Execution Guard ---
if __name__ == '__main__':
    app = create_app()
    # Run the Flask app
    # Use debug=False and a proper WSGI server (Gunicorn, Waitress) for production!
    logging.info("Starting Flask development server.")
    app.run(debug=True, host='0.0.0.0', port=5000)