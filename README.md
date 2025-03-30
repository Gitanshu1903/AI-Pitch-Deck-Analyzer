# AI-Pitch-Deck-Analyzer

This project provides an AI-powered tool to automatically analyze startup pitch decks (PDF format). It extracts text using Google Gemini Vision OCR, identifies key business sections, scores them based on predefined criteria using Gemini's text models, calculates an overall score, and generates qualitative feedback (strengths, weaknesses, suggestions). The analysis focuses on six core sections: Problem, Solution, Market Size, Business Model, Financial Projections, and Team.

The application is built with Python, Flask, and the Google Generative AI SDK.

https://github.com/user-attachments/assets/a0c7fe82-ee0c-4dd9-bb3a-ab30bca137e2


## Features

*   **PDF Upload:** Simple web interface to upload pitch deck PDF files.
*   **Robust Text Extraction:** Utilizes Google Gemini Vision API for OCR, handling both text-based and image-based PDFs.
*   **Rate Limit Handling:** Implements delays and backoff strategies for smoother interaction with the Gemini API, especially for the vision model.
*   **Key Section Identification:** Automatically identifies pages related to Problem, Solution, Market Size, Business Model, Financial Projections, and Team.
*   **LLM-Powered Scoring:** Each identified section is scored (0-100) by a Gemini text model based on detailed, configurable criteria.
*   **Overall Weighted Score:** Calculates a final score normalized across the weighted importance of the key sections.
*   **Qualitative Feedback:** Generates actionable strengths, weaknesses, and suggestions based on the section analysis.
*   **Web Interface:** Presents the analysis results clearly in a web browser.
*   **Modular Codebase:** Organized using OOP (PitchAnalyzer class) and Flask Blueprints for better maintainability.

## Setup and Installation

**Prerequisites:**

1.  **Python:** Version 3.9 or higher recommended.
2.  **Poppler:** Required by `pdf2image` for PDF processing. Installation varies by OS:
    *   **macOS:** `brew install poppler`
    *   **Linux (Debian/Ubuntu):** `sudo apt update && sudo apt install poppler-utils`
    *   **Linux (Fedora):** `sudo dnf install poppler-utils`
    *   **Windows:** Download binaries (e.g., from [this StackOverflow thread's links](https://stackoverflow.com/questions/18381713/how-to-install-poppler-on-windows)) and add the `bin` directory to your system's PATH. Alternatively, set the `POPPLER_PATH_WINDOWS` variable in `config.py` if needed.
3.  **Google Cloud Project & API Key:**
    *   You need a Google Cloud project with the "Generative Language API" (also known as Gemini API) enabled.
    *   Create an API Key from the Google Cloud Console or Google AI Studio. See [Google AI Setup Guide](https://ai.google.dev/gemini-api/docs/setup).

**Installation Steps:**

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/Gitanshu1903/AI-Pitch-Deck-Analyzer.git
    cd AI-Pitch-Deck-Analyzer
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # Activate it:
    # Windows: venv\Scripts\activate
    # macOS/Linux: source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up Environment Variables:**
    *   Copy the example `.env.example` file to `.env`:
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file and add your actual `GOOGLE_API_KEY`.
    *   Set a strong, random `FLASK_SECRET_KEY`. You can generate one using:
        ```python
        import secrets
        secrets.token_hex(16)
        ```

5.  **Ensure `uploads` Directory Exists:**
    The `run.py` script attempts to create it, but you can create it manually:
    ```bash
    mkdir uploads
    ```

## Configuration (`config.py`)

The `config.py` file contains key parameters:

*   **LLM Models:** Specify which Gemini models to use for Vision/OCR and Text analysis.
*   **Target Sections & Weights:** Define which pitch deck sections to focus on and their importance for the overall score.
*   **Scoring Criteria:** Detailed prompts used to guide the LLM scoring for each section.
*   **API Parameters:** Timeouts, retry attempts, delays, temperature.
*   **Rate Limiting:** `INTER_PAGE_DELAY` is crucial – increase this value (e.g., 15, 30, 60 seconds) if you encounter frequent "429 Quota Exceeded" errors during OCR, especially on free tiers.
*   **Safety Settings:** Configure content safety thresholds for Gemini.

## Running the Application

1.  **Activate your virtual environment** (if you created one).
2.  **Run the Flask development server:**
    ```bash
    python run.py
    ```
    *(For production, use a proper WSGI server like Gunicorn or Waitress)*
3.  Open your web browser and navigate to `http://localhost:5000` (or the address provided).
4.  Upload a pitch deck PDF file and click "Analyze Pitch".
5.  Wait for the analysis (can take several minutes depending on PDF length, complexity, and API delays).
6.  View the results page.

## Usage Notes

*   **Processing Time:** OCR on image-based PDFs using the Vision API, combined with inter-page delays, can make the analysis slow. Be patient, especially with longer decks.
*   **API Costs & Quotas:** Be mindful of Google Gemini API usage costs and quotas associated with your Google Cloud project, particularly for the Vision model. Adjust `INTER_PAGE_DELAY` in `config.py` to stay within limits.
*   **Accuracy:** LLM analysis provides valuable insights but isn't infallible. OCR errors can occur, and LLM interpretations have inherent subjectivity. Use results as a guide, not a definitive judgment.
*   **Poppler Path (Windows):** If `pdf2image` can't find Poppler on Windows, you might need to explicitly set the `POPPLER_PATH_WINDOWS` variable in `config.py` to the location of your Poppler `bin` directory.

