# AnkiConnect_AI_Generator/gemini_client.py
import json
import google.generativeai as genai
from google.generativeai.types import GenerationConfig, HarmCategory, HarmBlockThreshold
# from .consts import ANKICONNECT_URL, ANKICONNECT_API_VERSION

# from .consts import GEMINI_RESPONSE_SCHEMA, DEFAULT_GEMINI_MODEL, BASE_LLM_PROMPT
from .consts import GEMINI_RESPONSE_SCHEMA, DEFAULT_GEMINI_MODEL, BASE_LLM_PROMPT # Changed for direct run
class GeminiFlashcardGenerator:
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name
        genai.configure(api_key=self.api_key)

        # Common configuration for the model
        self.generation_config = GenerationConfig(
            response_mime_type="application/json",
            response_schema=GEMINI_RESPONSE_SCHEMA # Use the schema here
        )
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        self.model = genai.GenerativeModel(
            self.model_name,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings
        )

    def generate_cards_from_text(self, prompt: str) -> list:
        try:
            response = self.model.generate_content(prompt)

            # Debug: print raw response text
            # print("Raw Gemini Response Text:", response.text)

            # The SDK should parse JSON automatically if response_mime_type and schema are set
            # Accessing response.text directly might give the string,
            # while response.parts[0].text might already be parsed IF the schema worked as expected.
            # Let's try to be robust.
            
            raw_text_output = None
            if response.parts:
                raw_text_output = response.parts[0].text
            elif hasattr(response, 'text'): # Fallback if parts is empty
                raw_text_output = response.text

            if not raw_text_output:
                raise ValueError("Gemini API returned an empty response.")

            try:
                # If raw_text_output is already a dict/list (due to schema auto-parsing)
                if isinstance(raw_text_output, (list,dict)):
                    cards_data = raw_text_output
                else: # Otherwise, assume it's a JSON string and parse it
                    cards_data = json.loads(raw_text_output)

                if not isinstance(cards_data, list):
                    raise ValueError(f"Response is not a list of cards. Type: {type(cards_data)}. Content: {cards_data}")
                
                # Further validation against schema could be done here if needed
                # For example, check if each item has 'cardType', 'front', 'back'

                return cards_data
            
            except json.JSONDecodeError as e:
                raise ValueError(f"Error: Gemini API returned malformed JSON. Details: {e}\nResponse: {raw_text_output}")
            except ValueError as e: # Catch our own ValueError from above
                raise ValueError(f"Error processing Gemini response: {str(e)}\nResponse: {raw_text_output}")


        except Exception as e:
            error_message = f"Gemini API Error: {str(e)}"
            # More specific error parsing if needed (e.g., for API key issues)
            if "API_KEY_INVALID" in str(e) or "PERMISSION_DENIED" in str(e) or "AUTHENTICATION_FAILED" in str(e):
                error_message = "Error: Invalid or unauthorized Gemini API Key. Please check your key and permissions."
            elif "Quota" in str(e) or "quota" in str(e):
                error_message = "Error: Gemini API quota exceeded."
            # It's better to raise a custom exception or a more specific one
            raise Exception(error_message) # Or a custom GeminiAPIError

