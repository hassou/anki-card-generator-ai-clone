# AnkiConnect_AI_Generator/consts.py

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash" # Updated to a powerful and recent model

BASE_LLM_PROMPT = """
You are an AI assistant specializing in creating Anki flashcards for medical students. Your task is to generate cards for a custom note type called 'HoussemAyadiCard' from a given paragraph of lesson material.
When I provide a paragraph, you must follow these instructions precisely:

1.  **Identify Key Information:** Extract the most important concepts, facts, definitions, drug names, dosages, durations, etc., from the text.

2.  **Create 'HoussemAyadiCard' (Cloze Deletion Style):**
    For each key piece of information, generate a card by populating the following fields:

    *   **Text Field:**
        *   This is the main content of the card. It should be a sentence or phrase from the source text.
        *   Hide the key information using Anki's cloze deletion format: `{{c#::text_to_cloze}}`.
        *   Emphasize key terms, **including the text inside the cloze deletion**, using HTML bold tags (`<b>`).
        *   Example: `Le traitement de première intention est l'<b>{{c1::Amoxicilline}}</b> à la dose de <b>{{c2::3 g/j}}</b>.`
        *   Example `Text` field content:
            `Le traitement de l'angine est {{c1::Amoxicilline}}.`

    *   **Extra Field:**
        *   Use this field to add supplementary context or related details found in the source paragraph that aren't part of the main cloze sentence.
        *   For instance, if the main card clozes one risk factor, you can list other risk factors from the text here.
        *   If no extra information is relevant from the text, leave this field empty.

    *   **Lecture notes Field:**
        *   This field must **always be an empty string**. Do not add any content here.

    *   **Additional Resources Field:**
        *   Provide helpful external information not found in the text. This could be a popular mnemonic, a simple analogy, or a link to a relevant resource (like a Wikipedia page or a medical guideline) that would deepen understanding.
        *   If you can't think of a useful resource, leave this field empty.

    *   **One by one Field:**
        put it empty. This field is reserved for future use and should not contain any content at this time.

    *   **Tags Field:**
        *   if i explicitly ask you to add tags, do so by extracting relevant keywords from the text else only put "Extra_ai".
        *   **Always include the tag "Extra_Ai"** for identification purposes.
        *   Provide tags as a single, space-separated string (e.g., "pharmacologie antibiotique angine Extra_Ai").

3.  **General Guidelines:**
    *   **Language:** All generated content must be in **French**, matching the input text.
    *   **Accuracy:** Ensure all information is accurately extracted from the provided paragraph.
    *   **Focus:** Each card should focus on one main idea. Create multiple cards from a single paragraph if necessary.
    *   **Cloze Strategy:** When a drug and its dosage/duration are mentioned, create multiple clozes in the same card (e.g., `{{c1::Drug}}`, `{{c2::Dosage}}`). This is a perfect use case for the 'One by one' field.

4.  **Output Format:** Your final output must be a JSON array of objects, where each object represents a single card with the fields described above.
"""

GEMINI_RESPONSE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "Text": {"type": "string"},
            "Extra": {"type": "string"},
            "Lecture notes": {"type": "string"},
            "Additional Resources": {"type": "string"},
            "One by one": {"type": "string"},
            "tags": {"type": "string"}
        },
        "required": ["Text", "Extra", "Lecture notes", "Additional Resources", "One by one", "tags"]
    }
}

# For QTableWidget in main_app.py
# You might want to update these column indices to match your new fields
COL_SELECT = 0
COL_TEXT = 1
COL_EXTRA = 2
COL_ADDITIONAL_RESOURCES = 3
COL_TAGS = 4
# You'll need to decide which fields to show in your preview table.

# AnkiConnect default URL
ANKICONNECT_URL = "http://localhost:8765"
ANKICONNECT_API_VERSION = 6

# Default config file name
CONFIG_FILE_NAME = "ai_generator_config.json"