# AnkiConnect_AI_Generator/anki_connect_client.py
import json
import requests # Using requests library
from .consts import ANKICONNECT_URL, ANKICONNECT_API_VERSION

class AnkiConnectClient:
    def __init__(self, url=ANKICONNECT_URL, version=ANKICONNECT_API_VERSION):
        self.url = url
        self.version = version

    def _invoke(self, action, **params):
        payload = {'action': action, 'params': params, 'version': self.version}
        request_body_json = json.dumps(payload)
        print(f"[AnkiConnectClient._invoke] Sending to {self.url}: Action='{action}', Body='{request_body_json}'") # DEBUG
        try:
            response = requests.post(self.url, data=json.dumps(payload), timeout=10) # 10s timeout
            print(f"[AnkiConnectClient._invoke] Received status: {response.status_code}, Response text (first 200): {response.text[:200]}") # DEBUG
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            response_json = response.json()
        except requests.exceptions.RequestException as e: # Catches network errors, timeout, etc.
            print(f"[AnkiConnectClient._invoke] Timeout connecting to AnkiConnect for action '{action}'") # DEBUG
            raise ConnectionError(f"Failed to connect to AnkiConnect at {self.url}. Is Anki running with AnkiConnect active? Details: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"AnkiConnect returned invalid JSON. Response: {response.text}. Error: {e}")


        if 'error' not in response_json or 'result' not in response_json:
            raise ValueError(f"AnkiConnect response is missing 'error' or 'result' field. Response: {response_json}")

        if response_json['error'] is not None:
            raise Exception(f"AnkiConnect API Error: {response_json['error']}")

        return response_json['result']

    def get_deck_names(self):
        return self._invoke('deckNames')

    def get_model_names(self):
        return self._invoke('modelNames')

    def get_model_field_names(self, model_name: str):
        return self._invoke('modelFieldNames', modelName=model_name)

    def add_note(self, deck_name: str, model_name: str, fields: dict, tags: list = None, options: dict = None):
        note = {
            "deckName": deck_name,
            "modelName": model_name,
            "fields": fields,
            "tags": tags or []
        }
        if options:
            note["options"] = options
        return self._invoke('addNote', note=note)

    def add_notes(self, notes_data: list):
        """
        Adds multiple notes. notes_data should be a list of note objects,
        each structured like the 'note' parameter in add_note.
        """
        return self._invoke('addNotes', notes=notes_data)

    def request_permission(self):
        """
        Requests permission. Useful for initial setup or if CORS issues arise.
        AnkiConnect usually handles localhost automatically.
        """
        try:
            return self._invoke('requestPermission')
        except Exception as e:
            # This specific call might behave differently on error depending on AnkiConnect version
            # and whether it's a CORS issue or a connection issue.
            print(f"Error during requestPermission: {e}")
            if "ConnectionError" in str(e): # re-raise if it's a fundamental connection problem
                raise
            return {"permission": "denied", "error": str(e)} # Or some other default error structure

# Example Usage (for testing this file independently)
if __name__ == '__main__':
    client = AnkiConnectClient()
    try:
        # First, test connection & permissions
        permission_status = client.request_permission()
        print(f"Permission status: {permission_status}")
        
        if permission_status.get("permission") != "granted":
            print("Permission to AnkiConnect not granted. Please check Anki and AnkiConnect settings.")
        else:
            print("AnkiConnect permission granted.")
            decks = client.get_deck_names()
            print(f"Available decks: {decks}")

            models = client.get_model_names()
            print(f"Available models: {models}")

            if "Basic" in models:
                basic_fields = client.get_model_field_names("Basic")
                print(f"Basic model fields: {basic_fields}")

            # Example: Add a basic note (BE CAREFUL - THIS WILL ADD A CARD TO YOUR ANKI)
            # fields_to_add = {"Front": "Test Front from AnkiConnect", "Back": "Test Back"}
            # new_note_id = client.add_note(deck_name="Default", model_name="Basic", fields=fields_to_add, tags=["test", "ai_generated"])
            # print(f"Added new note with ID: {new_note_id}")

    except ConnectionError as e:
        print(e)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")