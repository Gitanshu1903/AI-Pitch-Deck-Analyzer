# config.py
import os
from dotenv import load_dotenv
from google.generativeai.types import HarmCategory, HarmBlockThreshold

load_dotenv()

# --- Flask Configuration ---
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'default_dev_secret_key')
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # 16 MB limit

# --- Gemini API Configuration ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- LLM Models ---
LLM_VISION_MODEL = "gemini-1.5-pro-latest"
LLM_TEXT_MODEL = "gemini-1.5-flash-latest"

# --- Analysis Configuration ---
TARGET_SECTIONS = [
    "Problem", "Solution", "Market Size", "Business Model",
    "Financial Projections", "Team"
]
SECTION_WEIGHTS = {
    "Problem": 20, "Solution": 20, "Market Size": 13, "Business Model": 13,
    "Financial Projections": 14, "Team": 20
}
# Shortened prompts for config file, can be expanded if preferred
SCORING_CRITERIA = {
    "Problem": "Evaluate 'Problem': 1. Clarity(25) 2. Magnitude/Significance/Data(35) 3. Urgency(20) 4. Target Audience(20). Score(0-100). Justification(2-3 sentences).",
    "Solution": "Evaluate 'Solution': 1. Clarity(25) 2. Problem Fit(35) 3. Value Prop/Differentiation(25) 4. Feasibility/Scalability(15). Score(0-100). Justification(2-3 sentences).",
    "Market Size": "Evaluate 'Market Size': 1. Definition(TAM/SAM/SOM)(30) 2. Data/Sources(30) 3. Realism/Focus(SOM)(30) 4. Growth(10). Score(0-100). Justification(2-3 sentences).",
    "Business Model": "Evaluate 'Business Model': 1. Revenue Stream Clarity(30) 2. Pricing Strategy(25) 3. Profitability Path/Unit Econ(30) 4. Scalability(15). Score(0-100). Justification(2-3 sentences).",
    "Financial Projections": "Evaluate 'Financials': 1. Clarity/Metrics(25) 2. Assumptions/Realism(35) 3. Time Horizon/Detail(20) 4. Link to Funding Ask(20). Score(0-100). Justification(2-3 sentences).",
    "Team": "Evaluate 'Team': 1. Founder Relevance/Experience(40) 2. Completeness/Roles(25) 3. Execution/Passion(Deduced)(20) 4. Advisors(15). Score(0-100). Justification(2-3 sentences).",
}

# --- API Call Parameters ---
LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS_OCR = 4096
LLM_MAX_TOKENS_SECTION_ID = 500
LLM_MAX_TOKENS_SCORING = 350
LLM_MAX_TOKENS_FEEDBACK = 1000
LLM_REQUEST_TIMEOUT = 180
LLM_RETRY_ATTEMPTS = 3
LLM_RETRY_DELAY = 5

# --- Rate Limit Handling ---
INTER_PAGE_DELAY = 10 # ADJUST AS NEEDED
RATE_LIMIT_BACKOFF_MULTIPLIER = 15

# --- Safety Settings ---
SAFETY_SETTINGS_TEXT = { HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE, HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE, HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE, HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE, }
SAFETY_SETTINGS_VISION = { HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH, HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH, HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH, HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH, }

# --- Optional Paths ---
# POPPLER_PATH_WINDOWS = r"C:\path\to\your\poppler-xx.xx.x\bin" # Set if needed