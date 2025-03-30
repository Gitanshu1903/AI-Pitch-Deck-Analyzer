# analyzer/core.py
import os
import io
import re
import json
import time
import logging
from PIL import Image

# --- Import Google Generative AI & PDF Processing ---
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFPageCountError, PDFSyntaxError

# --- Import Configuration ---
# Use relative import since config.py is one level up
import config

class PitchAnalyzer:
    """Encapsulates the pitch deck analysis logic."""

    def __init__(self):
        """Initializes the analyzer and configures Gemini."""
        self.genai_configured = False
        self._configure_gemini()
        self.last_error = None
        # Store config values needed within the class
        self.target_sections = config.TARGET_SECTIONS
        self.section_weights = config.SECTION_WEIGHTS
        self.scoring_criteria = config.SCORING_CRITERIA

    def _configure_gemini(self):
        """Configures the Google Generative AI client."""
        if not config.GOOGLE_API_KEY:
            logging.warning("Google API key missing. Gemini features disabled.")
            self.genai_configured = False
            return
        try:
            genai.configure(api_key=config.GOOGLE_API_KEY)
            self.genai_configured = True
            logging.info("Google Generative AI client configured successfully.")
        except Exception as e:
            logging.error(f"Failed to configure Google Generative AI: {e}")
            self.genai_configured = False

    # --- Internal Methods (_call_gemini_vision_ocr, _call_gemini_text, etc.) ---
    # (Copy ALL the internal methods _call_*, _extract_text, _preprocess_text,
    #  _identify_sections, _aggregate_content, _score_sections,
    #  _calculate_score, _generate_feedback from the previous app.py
    #  implementation of the PitchAnalyzer class HERE)
    # --- START COPY of Internal Methods ---

    def _call_gemini_vision_ocr(self, image_bytes, mime_type="image/jpeg"):
        """Internal method to call Gemini Vision API for OCR."""
        if not self.genai_configured: return None
        try:
            model = genai.GenerativeModel(config.LLM_VISION_MODEL)
            generation_config = genai.GenerationConfig(temperature=0.1, max_output_tokens=config.LLM_MAX_TOKENS_OCR)
            prompt = "Extract all text visible in this image. Provide only the text content, maintaining layout if possible (e.g., using line breaks)."
            payload = [prompt, {"mime_type": mime_type, "data": image_bytes}]
            for attempt in range(config.LLM_RETRY_ATTEMPTS):
                try:
                    response = model.generate_content(contents=payload, generation_config=generation_config, safety_settings=config.SAFETY_SETTINGS_VISION, request_options={'timeout': config.LLM_REQUEST_TIMEOUT})
                    if not response.parts: return None
                    return response.text.strip()
                except google_exceptions.GoogleAPIError as e:
                    wait_time = config.LLM_RETRY_DELAY * (2 ** attempt); logging.warning(f"Gemini Vision API error (Attempt {attempt + 1}): {e}. Waiting {wait_time:.2f}s...")
                    if attempt == config.LLM_RETRY_ATTEMPTS - 1: return None
                    time.sleep(wait_time)
                except (google_exceptions.InvalidArgument, ValueError) as e: logging.error(f"Non-retryable Gemini Vision error: {e}"); return None
                except Exception as e: logging.error(f"Unexpected Vision call error: {e}"); time.sleep(config.LLM_RETRY_DELAY * (2 ** attempt));
            return None
        except Exception as model_init_error: logging.error(f"Failed to init Vision model: {model_init_error}"); return None

    def _call_gemini_text(self, prompt, max_output_tokens, temperature=config.LLM_TEMPERATURE):
        """Internal method to call Gemini Text API."""
        if not self.genai_configured: return None
        try:
            model = genai.GenerativeModel(config.LLM_TEXT_MODEL)
            generation_config = genai.GenerationConfig(temperature=temperature, max_output_tokens=max_output_tokens)
            for attempt in range(config.LLM_RETRY_ATTEMPTS):
                try:
                    response = model.generate_content(contents=prompt, generation_config=generation_config, safety_settings=config.SAFETY_SETTINGS_TEXT, request_options={'timeout': config.LLM_REQUEST_TIMEOUT})
                    if not response.parts: return None
                    return response.text.strip()
                except google_exceptions.GoogleAPIError as e:
                    wait_time = config.LLM_RETRY_DELAY * (2 ** attempt); logging.warning(f"Gemini Text API error (Attempt {attempt + 1}): {e}. Waiting {wait_time:.2f}s...")
                    if attempt == config.LLM_RETRY_ATTEMPTS - 1: return None
                    time.sleep(wait_time)
                except (google_exceptions.InvalidArgument, ValueError) as e: logging.error(f"Non-retryable Gemini Text error: {e}"); return None
                except Exception as e: logging.error(f"Unexpected Text call error: {e}"); time.sleep(config.LLM_RETRY_DELAY * (2 ** attempt));
            return None
        except Exception as model_init_error: logging.error(f"Failed to init Text model: {model_init_error}"); return None

    def _extract_text(self, pdf_path):
        """Internal method for text extraction using OCR."""
        pages_text = []; logging.info(f"Starting OCR for: {pdf_path}")
        try:
            poppler_path_to_use = None
            # if os.name == 'nt' and hasattr(config, 'POPPLER_PATH_WINDOWS') and os.path.exists(config.POPPLER_PATH_WINDOWS): # Check config
            #     poppler_path_to_use = config.POPPLER_PATH_WINDOWS
            images = convert_from_path(pdf_path, dpi=200, poppler_path=poppler_path_to_use)
            logging.info(f"Converted {len(images)} pages.")
            for i, image in enumerate(images):
                page_num = i + 1; logging.info(f"Processing page {page_num}/{len(images)}...")
                img_byte_arr = io.BytesIO(); image.save(img_byte_arr, format='JPEG', quality=90)
                extracted_text = self._call_gemini_vision_ocr(img_byte_arr.getvalue(), "image/jpeg")
                pages_text.append(extracted_text if extracted_text else "")
                if not extracted_text: logging.warning(f"Failed/empty OCR for page {page_num}.")
                if page_num < len(images): logging.info(f"Waiting {config.INTER_PAGE_DELAY}s..."); time.sleep(config.INTER_PAGE_DELAY)
            return pages_text
        except (ImportError, FileNotFoundError, PDFPageCountError, PDFSyntaxError, Exception) as e:
             logging.error(f"Error during text extraction: {e}", exc_info=True)
             self.last_error = f"Text extraction failed: {e}"
             return None

    def _preprocess_text(self, text):
        """Internal basic preprocessing."""
        if not text: return ""
        text = text.lower(); text = re.sub(r'\s+', ' ', text).strip(); return text

    def _identify_sections(self, pages_text):
        """Internal method for section identification."""
        logging.info(f"Identifying target sections: {', '.join(self.target_sections)}")
        if not pages_text or not any(pages_text): return {}
        formatted_pages = []; max_len = 400
        for i, text in enumerate(pages_text):
             processed = text[:max_len//2] + "..." + text[-max_len//2:] if len(text) > max_len else text
             formatted_pages.append(f"--- Page {i + 1} ---\n{processed}\n")
        full_text = "\n".join(formatted_pages)
        prompt = f"**Role:** Analyst. Map content to sections.\n**Instructions:** Find pages for ONLY these sections: {', '.join(self.target_sections)}. Output ONLY valid JSON mapping section names to page lists (e.g., [1, 2]). Omit others.\n**Example:** {{\"Problem\":[2,3],\"Team\":[10]}}\n---\n**Text:**\n{full_text}\n---\n**JSON Output:**"
        response = self._call_gemini_text(prompt, config.LLM_MAX_TOKENS_SECTION_ID)
        if not response: return None

        try:
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL | re.IGNORECASE) or re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match: raise json.JSONDecodeError("No JSON found", response, 0)
            json_string = json_match.group(1) if len(json_match.groups()) == 1 else json_match.group(0)
            raw_map = json.loads(json_string)
            validated = {}
            for section, pages in raw_map.items():
                if section in self.target_sections and isinstance(pages, list):
                    valid_p = sorted(list(set(p - 1 for p in pages if isinstance(p, int) and 0 < p <= len(pages_text))))
                    if valid_p: validated[section] = valid_p
            logging.info(f"Validated section map: {validated}")
            return validated
        except (json.JSONDecodeError, Exception) as e:
             logging.error(f"Failed parsing section ID JSON: {e}. Response: {response}")
             self.last_error = "Failed to understand section identification from AI."
             return None

    def _aggregate_content(self, pages_text, section_pages_map):
        """Internal content aggregation."""
        section_content = {};
        if not section_pages_map: return {}
        for section, indices in section_pages_map.items():
            content = "".join(pages_text[idx] + "\n\n" for idx in indices if 0 <= idx < len(pages_text))
            section_content[section] = self._preprocess_text(content)
        return section_content

    def _score_sections(self, section_content):
        """Internal section scoring."""
        section_scores = {};
        if not section_content: return {}
        instructions = """**Role:** Analyst. Evaluate section text based *only* on criteria. **Instructions:** Provide score (0-100) & brief justification. Format ONLY valid JSON: {"score": integer, "justification": string}."""
        for section, text in section_content.items():
            if section in self.scoring_criteria:
                logging.info(f"Scoring section: {section}")
                if not text or len(text.strip()) < 20: section_scores[section] = {"score": 0, "justification": "Content missing/brief."}; continue
                prompt = f"{instructions}\n---\n**Section:** {section}\n**Criteria:**\n{self.scoring_criteria[section]}\n---\n**Text:**\n{text[:4000]}\n---\n**JSON Output:**"
                response = self._call_gemini_text(prompt, config.LLM_MAX_TOKENS_SCORING)
                if response:
                     try:
                        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL | re.IGNORECASE) or re.search(r'\{.*\}', response, re.DOTALL)
                        if not json_match: raise json.JSONDecodeError("No JSON found", response, 0)
                        score_data = json.loads(json_match.group(1) if len(json_match.groups()) == 1 else json_match.group(0))
                        if isinstance(score_data.get('score'), int) and 0 <= score_data['score'] <= 100 and isinstance(score_data.get('justification'), str): section_scores[section] = score_data
                        else: section_scores[section] = {"score": 0, "justification": "Failed parsing score (invalid format/values)."}
                     except Exception as e: logging.warning(f"Failed scoring JSON parse for '{section}': {e}. Resp: {response}"); section_scores[section] = {"score": 0, "justification": "Failed parsing score."}
                else: section_scores[section] = {"score": 0, "justification": "LLM call failed during scoring."}
        return section_scores

    def _calculate_score(self, section_scores):
        """Internal overall score calculation."""
        points, weight_sum = 0, 0;
        if not section_scores: return 0
        for section, data in section_scores.items():
            if section in self.section_weights:
                weight = self.section_weights[section]; weight_sum += weight
                if isinstance(data.get('score'), int) and data['score'] >= 0: points += data['score'] * weight
        return round(points / weight_sum) if weight_sum > 0 else 0

    def _generate_feedback(self, section_scores):
        """Internal feedback generation."""
        if not section_scores: return {"strengths": [], "weaknesses": []}
        summary = ""; found = False
        for section in self.target_sections:
            if section in section_scores:
                data = section_scores[section]; score = data.get('score'); just = data.get('justification', 'N/A')
                if isinstance(score, int): summary += f"Section: {section}\nScore: {score}/100\nJustification: {just}\n---\n"; found = True
            else: summary += f"Section: {section}\nScore: Not Found\n---\n"
        if not found: return {"strengths": ["Analysis incomplete."], "weaknesses": []}

        prompt = f"**Role:** Analyst. Synthesize core section analysis into feedback.\n**Summary (Core Sections Only):**\n---\n{summary}---\n**Instructions:** Identify 2-3 key STRENGTHS & 2-3 critical WEAKNESSES based *primarily* on this summary. Add actionable suggestions for weaknesses. Format ONLY valid JSON: {{\"strengths\": [strings], \"weaknesses\": [strings]}}.\n**Example:** {{\"strengths\": [\"Problem clear(90)\"], \"weaknesses\": [\"Market lacks data(40). Suggest: Cite sources.\"]}}\n---\n**JSON Output:**"
        response = self._call_gemini_text(prompt, config.LLM_MAX_TOKENS_FEEDBACK)
        if not response: return {"strengths": ["Feedback LLM call failed."], "weaknesses": []}
        try:
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL | re.IGNORECASE) or re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match: raise json.JSONDecodeError("No JSON found", response, 0)
            feedback_data = json.loads(json_match.group(1) if len(json_match.groups()) == 1 else json_match.group(0))
            if isinstance(feedback_data.get('strengths'), list) and isinstance(feedback_data.get('weaknesses'), list): return feedback_data
            else: return {"strengths": ["Failed parsing feedback (invalid format)."], "weaknesses": []}
        except Exception as e: logging.error(f"Failed feedback JSON parse: {e}. Resp: {response}"); return {"strengths": ["Failed parsing feedback."], "weaknesses": []}

    # --- END COPY of Internal Methods ---

    def analyze(self, pdf_path):
        """Public method to run the full analysis pipeline."""
        self.last_error = None # Reset last error
        results = {'overall_score': 0, 'section_scores': {}, 'feedback': {}, 'error': None}
        start_time = time.time()
        logging.info(f"--- Starting Analysis via OOP for: {pdf_path} ---")

        if not self.genai_configured:
             results['error'] = "Gemini client not configured. Check API Key."
             logging.error(results['error']); return results

        # Step 1: Extract Text
        pages_text = self._extract_text(pdf_path)
        if pages_text is None: results['error'] = self.last_error or "Text extraction failed."; logging.error(results['error']); return results
        if not any(pg.strip() for pg in pages_text): results['error'] = "No text content extracted from PDF."; logging.error(results['error']); return results

        # Step 2: Identify Sections
        section_map = self._identify_sections(pages_text)
        if section_map is None: results['error'] = self.last_error or "Section identification failed."; logging.error(results['error']); return results
        if not section_map: logging.warning("Could not identify any target sections.")

        # Step 3: Aggregate Content
        section_content = self._aggregate_content(pages_text, section_map)

        # Step 4: Score Sections
        section_scores = self._score_sections(section_content)
        results['section_scores'] = section_scores

        # Step 5: Calculate Score
        results['overall_score'] = self._calculate_score(section_scores)

        # Step 6: Generate Feedback
        results['feedback'] = self._generate_feedback(section_scores)

        logging.info(f"--- Analysis via OOP Completed in {time.time() - start_time:.2f}s ---")
        return results