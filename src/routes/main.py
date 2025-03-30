# routes/main.py
import os
import logging
from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename

# Import configuration and the analyzer class
# Use absolute imports from the project root now
import config
from analyzer.core import PitchAnalyzer

# Create a Blueprint
main_bp = Blueprint('main', __name__, template_folder='../templates') # Point to correct template folder

# Create a single instance of the analyzer when the blueprint is loaded
analyzer_instance = PitchAnalyzer()

def allowed_file(filename):
    """Checks if the uploaded file has a PDF extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

@main_bp.route('/', methods=['GET'])
def index():
    """Renders the upload form."""
    return render_template('index.html')

@main_bp.route('/analyze', methods=['POST'])
def handle_analysis():
    """Handles PDF upload, analysis, and renders results."""
    if 'pdf_file' not in request.files:
        flash('No file part in the request.', 'error')
        return redirect(url_for('main.index')) # Use blueprint name 'main'

    file = request.files['pdf_file']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('main.index'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Use current_app.config for Flask config values
        temp_pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        try:
            file.save(temp_pdf_path)
            logging.info(f"File saved temporarily to {temp_pdf_path}")

            # Run the analysis using the analyzer instance
            analysis_results = analyzer_instance.analyze(temp_pdf_path)

            # Pass necessary context to the results template
            return render_template('results.html',
                                   results=analysis_results,
                                   error=analysis_results.get('error'),
                                   target_sections=config.TARGET_SECTIONS, # Get from config
                                   section_weights=config.SECTION_WEIGHTS) # Get from config

        except Exception as e:
            logging.error(f"Error during file processing or analysis: {e}", exc_info=True)
            flash(f"An unexpected error occurred: {e}", 'error')
            return redirect(url_for('main.index'))
        finally:
            # Clean up the uploaded file
            if os.path.exists(temp_pdf_path):
                try:
                    os.remove(temp_pdf_path)
                    logging.info(f"Temporary file {temp_pdf_path} removed.")
                except Exception as e_remove:
                    logging.error(f"Error removing temporary file {temp_pdf_path}: {e_remove}")
    else:
        flash('Invalid file type. Please upload a PDF.', 'error')
        return redirect(url_for('main.index'))