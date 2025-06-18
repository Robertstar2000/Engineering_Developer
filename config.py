import yaml
import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional # Added Optional

@dataclass
class FieldSchema:
    label: str
    type: str
    placeholder: str = ""

@dataclass
class DocumentSchema:
    name: str
    outline: List[str]

@dataclass
class PhaseSchema:
    id: int
    title: str
    doc_shortname: str
    fields: Dict[str, FieldSchema]
    document: Optional[DocumentSchema] # Made DocumentSchema optional

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PhaseSchema':
        fields_data = data.get('fields', {})
        fields_dict = {k: FieldSchema(**v) for k, v in fields_data.items()}

        document_data = data.get('document')
        document_obj = None
        if document_data:
            # Ensure outline is a list of strings, even if it's missing or malformed in YAML
            outline_data = document_data.get('outline', [])
            if not isinstance(outline_data, list) or not all(isinstance(item, str) for item in outline_data):
                print(f"Warning: Outline for phase {data.get('id')} document '{document_data.get('name')}' is malformed. Using empty outline.")
                outline_data = []
            document_obj = DocumentSchema(name=document_data.get('name', 'DefaultDocName.md'), outline=outline_data)

        return cls(
            id=data['id'], # id is mandatory
            title=data.get('title', f"Phase {data['id']}"),
            doc_shortname=data.get('doc_shortname', f"Phase{data['id']}"),
            fields=fields_dict,
            document=document_obj
        )

PHASES_CONFIG: Dict[int, PhaseSchema] = {}

def load_phases_config(path: str = 'phases.yaml') -> None:
    global PHASES_CONFIG
    try:
        with open(path, 'r', encoding='utf-8') as f: # Added encoding
            config_data = yaml.safe_load(f)

        if not config_data or 'phases' not in config_data:
            print(f"Warning: 'phases' key not found in '{path}' or file is empty.")
            PHASES_CONFIG = {}
            return

        loaded_phases = {}
        for phase_id_str, phase_data in config_data['phases'].items():
            try:
                phase_id = int(phase_id_str)
                phase_data['id'] = phase_id # Ensure 'id' from key is part of data for from_dict
                loaded_phases[phase_id] = PhaseSchema.from_dict(phase_data)
            except (ValueError, TypeError, KeyError) as e:
                print(f"Warning: Skipping phase due to parsing error in phase '{phase_id_str}': {e}")
                # print(f"Problematic data for phase '{phase_id_str}': {phase_data}") # Potentially verbose

        # Sort phases by ID for consistent order if needed elsewhere
        PHASES_CONFIG = dict(sorted(loaded_phases.items()))

    except FileNotFoundError:
        print(f"Error: Configuration file '{path}' not found.")
        PHASES_CONFIG = {}
    except yaml.YAMLError as e:
        print(f"Error: Could not parse YAML file '{path}': {e}")
        PHASES_CONFIG = {}
    except Exception as e:
        print(f"An unexpected error occurred while loading '{path}': {e}")
        PHASES_CONFIG = {}

def get_phase_config(phase_id: int) -> Optional[PhaseSchema]: # Return type changed to Optional
    return PHASES_CONFIG.get(phase_id)

def get_all_phases() -> List[PhaseSchema]:
    return list(PHASES_CONFIG.values())

# Load configuration when this module is imported
load_phases_config()

if __name__ == '__main__':
    # This block is for testing the config loading directly
    if not PHASES_CONFIG:
        print("No phases were loaded. Check 'phases.yaml' path and content.")
    else:
        print(f"Successfully loaded {len(PHASES_CONFIG)} phase configurations.")
        for phase_id, phase_detail in PHASES_CONFIG.items():
            print(f"Phase {phase_id}: {phase_detail.title}")
            if phase_detail.document:
                print(f"  Document: {phase_detail.document.name}")
                # print(f"  Outline sections: {len(phase_detail.document.outline)}")
            else:
                print("  Document: Not configured for this phase.")

        # Test retrieval
        # test_phase_1 = get_phase_config(1)
        # if test_phase_1:
        #     print(f"Test retrieval for Phase 1: {test_phase_1.title}")
        #     if test_phase_1.fields:
        #         print(f"  Field 'project_name' label: {test_phase_1.fields['project_name'].label}")

# Database Configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_SQLITE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'app.db')

# Default to SQLite for local development if DATABASE_URL is not set.
# For production, DATABASE_URL should be set to a PostgreSQL connection string.
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', DEFAULT_SQLITE_URI)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Check for DATABASE_URL and inform if using default SQLite
if not os.environ.get('DATABASE_URL'):
    print(f"INFO: DATABASE_URL environment variable not set. Using default SQLite URI: {SQLALCHEMY_DATABASE_URI}")
    # Ensure the instance folder exists for SQLite
    os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)
elif 'sqlite' in SQLALCHEMY_DATABASE_URI:
    print(f"INFO: Using SQLite database: {SQLALCHEMY_DATABASE_URI}")
    # Ensure the instance folder exists for SQLite if it's specified in the path and is relative
    if SQLALCHEMY_DATABASE_URI.startswith('sqlite:///./'):
        instance_path = os.path.join(BASE_DIR, os.path.dirname(SQLALCHEMY_DATABASE_URI.replace('sqlite:///./','')))
        os.makedirs(instance_path, exist_ok=True)
    elif SQLALCHEMY_DATABASE_URI.startswith('sqlite:///instance'):
         os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)
else:
    print(f"INFO: Using configured DATABASE_URL: {SQLALCHEMY_DATABASE_URI}")

# Check for Gemini API Key
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("CRITICAL: GEMINI_API_KEY environment variable not set.")
    print("This key is essential for interacting with the Gemini API.")
    print("Please set this variable to your Google Generative AI API key.")
    # Depending on the application's design, you might:
    # - Raise an exception: raise EnvironmentError("GEMINI_API_KEY not set.")
    # - Exit the application: sys.exit("Exiting: GEMINI_API_KEY not set.")
    # - Use a mock/dummy key if some parts of the app can run without it (not recommended for core features).
    # For now, just printing a critical warning.
