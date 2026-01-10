import google.generativeai as genai
from src.config import Config
from src.utils import setup_logger
import json
import os
import time

logger = setup_logger(__name__)

class PrescriptionExtractor:
    def __init__(self):
        if not Config.GOOGLE_API_KEY:
            logger.warning("Google API Key not found")
        else:
            genai.configure(api_key=Config.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel(Config.GEMINI_MODEL_NAME)

    def extract_data(self, file_input):
        prompt = """
        You are an expert medical assistant. Analyze this prescription and extract the following information in JSON format.
        Focus strictly on the medicine details and instructions.
        
        {
            "date": "Date of prescription",
            "medicines": [
                {
                    "name": "Exact name of the tablet/medicine",
                    "quantity": "How much to take (e.g., 1 tablet, 5ml)",
                    "timing": {
                        "morning": "Yes/No",
                        "afternoon": "Yes/No",
                        "night": "Yes/No",
                        "instruction": "Before meal / After meal / Empty stomach / etc."
                    },
                    "frequency": "Raw frequency string (e.g., 1-0-1)",
                    "duration": "For how many days the medicine should be taken"
                }
            ],
            "notes": "Any special instructions"
        }
        If a field is missing, use "-". Return ONLY the JSON.
        """

        try:
            content = []
            content.append(prompt)
            
            if isinstance(file_input, str):
                if file_input.endswith(".pdf"):
                    sample_file = genai.upload_file(path=file_input, display_name="Prescription")
                    while sample_file.state.name == "PROCESSING":
                        time.sleep(2)
                        sample_file = genai.get_file(sample_file.name)
                    content.append(sample_file)
                else:
                    import PIL.Image
                    img = PIL.Image.open(file_input)
                    content.append(img)
            elif hasattr(file_input, 'read'):
                # Handle file-like objects (e.g. from st.file_uploader or open())
                import PIL.Image
                import io
                
                # Check if it's an image or PDF based on name or content
                # For simplicity here, we assume if it's passed to this branch it might be an image stream
                # or we check the name attribute if available
                filename = getattr(file_input, 'name', '').lower()
                
                if filename.endswith('.pdf'):
                    # For PDF streams, we might need to save to temp file because genai.upload_file expects a path
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                        tmp.write(file_input.read())
                        tmp_path = tmp.name
                    
                    sample_file = genai.upload_file(path=tmp_path, display_name="Prescription")
                    while sample_file.state.name == "PROCESSING":
                        time.sleep(2)
                        sample_file = genai.get_file(sample_file.name)
                    content.append(sample_file)
                    # Cleanup could happen here or rely on OS, but best effort:
                    try:
                        os.remove(tmp_path)
                    except:
                        pass
                else:
                    # Assume image stream
                    image_data = file_input.read()
                    image = PIL.Image.open(io.BytesIO(image_data))
                    content.append(image)
                    
            else:
                # Assume PIL Image or list of images
                if isinstance(file_input, list):
                    content.extend(file_input)
                else:
                    content.append(file_input)

            response = self.model.generate_content(content)
            
            # Parse JSON from response
            text = response.text
            return self._extract_json_from_text(text)

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return None

    def _extract_json_from_text(self, text):
        """
        Robustly extracts JSON object from a string using regex.
        Finds the first '{' and the last '}' to capture the JSON block.
        """
        import re
        try:
            # First, try standard json.loads in case it's clean
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Regex to find the JSON block
        # This pattern matches from the first '{' to the last '}' (greedy)
        # It handles newlines with DOTALL
        pattern = r"\{.*\}"
        match = re.search(pattern, text, re.DOTALL)
        
        if match:
            json_str = match.group(0)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.warning(f"Regex found potential JSON but failed to parse: {e}")
                
        # If still failing, try the old markdown splitting method as fallback
        try:
            if "```json" in text:
                clean_text = text.split("```json")[1].split("```")[0]
                return json.loads(clean_text.strip())
            elif "```" in text:
                clean_text = text.split("```")[1].split("```")[0]
                return json.loads(clean_text.strip())
        except:
            pass
            
        return None
