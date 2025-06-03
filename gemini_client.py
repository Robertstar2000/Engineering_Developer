import os
import json
import google.generativeai as genai
import backoff
import google.api_core.exceptions as gexc # For more specific Gemini exceptions

# --- Configuration ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY environment variable not set. Gemini client will not function.")
    # Depending on strictness, you might raise an error here or allow the app to run with Gemini features disabled.
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e: # Catch potential errors during configure()
        print(f"Error configuring Gemini API: {e}")
        GEMINI_API_KEY = None # Disable client if configuration fails

# Model selection - consider making this configurable if needed
# Using "gemini-1.5-flash-latest" as it's generally faster and more cost-effective for many tasks.
# For tasks requiring maximum capability, "gemini-1.5-pro-latest" could be used.
MODEL_NAME = "gemini-1.5-flash-latest"
_MODEL = genai.GenerativeModel(MODEL_NAME) if GEMINI_API_KEY else None

# Default Generation Configuration
DEFAULT_GENERATION_CONFIG = {
    "temperature": 0.7, # Controls randomness. Lower for more predictable, higher for more creative.
    "top_p": 0.95,      # Nucleus sampling parameter
    "top_k": 40,        # Top-k sampling parameter
    # "max_output_tokens": 2048, # Uncomment and adjust if you need to control output length explicitly
    # "response_mime_type": "text/plain", # Explicitly setting for text responses
}

# Default Safety Settings - adjust as per application requirements
DEFAULT_SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# --- Retry Logic ---
# Defining specific exceptions to retry on.
# gexc.RetryError and gexc.DeadlineExceeded are good candidates.
# gexc.ResourceExhaustedError (like quota issues) might also be retried, but with caution.
# gexc.InternalServerError, gexc.ServiceUnavailable are also good candidates.
RETRYABLE_GEMINI_EXCEPTIONS = (
    gexc.RetryError,
    gexc.DeadlineExceeded,
    gexc.InternalServerError,
    gexc.ServiceUnavailable,
    gexc.UnknownError # A general catch-all for unexpected server-side issues
    # Consider adding gexc.ResourceExhaustedError if you want to retry on quota issues,
    # but be mindful this might just delay hitting a hard limit.
)

@backoff.on_exception(backoff.expo,
                      RETRYABLE_GEMINI_EXCEPTIONS,
                      max_tries=5, # Maximum number of retries
                      max_time=120, # Maximum total time to spend retrying in seconds
                      jitter=backoff.full_jitter) # Adds randomness to backoff
def _call_gemini_api(prompt: str, generation_config: dict = None, safety_settings: list = None) -> str:
    if not _MODEL:
        return "Error: Gemini model not initialized. Check API key and configuration."

    try:
        current_gen_config = generation_config or DEFAULT_GENERATION_CONFIG
        current_safety_settings = safety_settings or DEFAULT_SAFETY_SETTINGS

        response = _MODEL.generate_content(
            prompt,
            generation_config=current_gen_config,
            safety_settings=current_safety_settings
        )

        # Check for empty candidates or parts, which can happen if content is blocked or empty
        if not response.candidates or not response.candidates[0].content.parts:
            block_reason = "Unknown (response was empty or no content parts)"
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                block_reason = response.prompt_feedback.block_reason.name # Use .name for enum
            # print(f"Warning: Gemini response blocked or empty. Reason: {block_reason}") # For server logs
            return f"Content generation blocked or result was empty. Reason: {block_reason}. Please revise your input or try again."

        return response.text # .text provides a convenient way to get the combined text

    except ValueError as ve: # Handles cases like invalid API key format during generation, or blocked prompts
        # This can also be triggered if the prompt itself is blocked by safety settings before even sending.
        # print(f"ValueError during Gemini API call: {ve}") # For server logs
        # Attempt to get more specific feedback if available
        block_reason_detail = "Input may be inappropriate or violate safety policies."
        if hasattr(ve, 'args') and len(ve.args) > 0 and "response" in ve.args[0]:
             # This is a bit of a heuristic, actual error structure can vary
            block_reason_detail = f"Input may be blocked by safety settings. ({ve})"

        return f"Content generation failed due to an input error or safety blocking. Detail: {block_reason_detail}"
    except gexc.GoogleAPIError as api_error: # Catch other Google API specific errors
        # print(f"A Google API error occurred: {api_error}") # For server logs
        # You might want to re-raise specific types of API errors if they shouldn't be masked
        return f"A Google API error occurred: {type(api_error).__name__} - {str(api_error)[:100]}..." # Return a user-friendly message
    except Exception as e: # Catch-all for other unexpected errors during the API call
        # print(f"An unexpected error occurred in _call_gemini_api: {e}") # For server logs
        return f"An unexpected error occurred while communicating with the AI model: {type(e).__name__}"


def generate_solution_summary(phase_data_json_str: str) -> str:
    if not _MODEL: return "Error: AI model not available."
    prompt = f"""
You are an expert engineering assistant.
Given the following JSON data for a development phase:
{phase_data_json_str}

Summarise a high-quality solution or key insights based on this data in approximately 150-300 words.
Focus on actionable advice or a concise overview.
The summary should be well-structured and easy to read.
Avoid conversational fluff. Be direct and professional.
"""
    return _call_gemini_api(prompt)

def generate_document_section(section_title: str, current_phase_data_json_str: str, all_project_data_json_str: str) -> str:
    if not _MODEL: return "Error: AI model not available."
    prompt = f"""
You are an expert engineering documentation writer.
You are writing a specific section for a larger technical document.
The current section title to generate content for is: "{section_title}"

The data for the current development phase is:
{current_phase_data_json_str}

For broader context, historical data from all previous phases of this project is:
{all_project_data_json_str}

Generate the content ONLY for the section titled "{section_title}".
Ensure the content is highly relevant to this section title and leverages the provided current and historical data.
The output should be well-structured Markdown.
Do NOT repeat the section title (e.g., "## {section_title}") in your response; only provide the body content for that section.
If the data provided is insufficient for a meaningful response for this specific section, state that clearly (e.g., "Insufficient data provided to generate content for this section.").
Be professional and adhere to a technical writing style.
"""
    return _call_gemini_api(prompt)

def seed_next_phase_data(current_phase_data_json_str: str, next_phase_field_keys: list) -> dict:
    if not _MODEL: return {"error": "AI model not available."}

    # Convert list to a JSON string representation for the prompt
    next_phase_field_keys_json_array = json.dumps(next_phase_field_keys)

    prompt = f"""
You are an AI assistant helping to transition data from one engineering phase to the next.
Given the data from the current phase:
{current_phase_data_json_str}

Your task is to prepare a concise JSON structure for the *next* phase.
The next phase requires *only* the following field keys: {next_phase_field_keys_json_array}.

Infer reasonable placeholder values or brief summaries from the current phase data to populate these fields.
Keep values concise and directly relevant to the key.
If some information is not directly inferable from the current phase data for a specific key, use a plausible placeholder like "To be determined based on [relevant current phase field]" or "Requires further definition in Phase X".
Return ONLY a raw JSON object without any surrounding text, comments, or markdown code fences (e.g., ```json ... ```).

Example of the EXACT desired output format if next_phase_field_keys were ["summary", "key_risks"]:
{{
  "summary": "Derived summary from current phase.",
  "key_risks": "Identified potential risks based on current data."
}}
"""
    raw_json_str = _call_gemini_api(prompt)

    try:
        # Basic cleaning of common non-JSON artifacts
        cleaned_json_str = raw_json_str.strip()
        if cleaned_json_str.startswith("```json"):
            cleaned_json_str = cleaned_json_str[len("```json"):].strip()
        elif cleaned_json_str.startswith("```"):
            cleaned_json_str = cleaned_json_str[len("```"):].strip()

        if cleaned_json_str.endswith("```"):
            cleaned_json_str = cleaned_json_str[:-len("```")].strip()

        # Ensure it's actually a JSON object string
        if not (cleaned_json_str.startswith("{") and cleaned_json_str.endswith("}")):
             # print(f"Warning: Gemini response for seeding does not look like a JSON object: {cleaned_json_str}") # For server logs
             # Attempt to find JSON within the string if it's embedded
             json_start = cleaned_json_str.find('{')
             json_end = cleaned_json_str.rfind('}')
             if json_start != -1 and json_end != -1 and json_start < json_end:
                 cleaned_json_str = cleaned_json_str[json_start:json_end+1]
             else: # Give up if no clear JSON object found
                raise json.JSONDecodeError("Response is not a valid JSON object string.", cleaned_json_str, 0)

        decoded_json = json.loads(cleaned_json_str)

        # Ensure all requested keys are present, fill with error/placeholder if not
        # This is important because the LLM might not always return all requested keys.
        final_seeded_data = {}
        for key in next_phase_field_keys:
            final_seeded_data[key] = decoded_json.get(key, f"Data for '{key}' not generated by AI.")

        return final_seeded_data

    except json.JSONDecodeError as e:
        # print(f"Error decoding JSON from Gemini for seeding: {e}") # For server logs
        # print(f"Raw response was: {raw_json_str}") # For server logs
        # Return a dict with error messages for each key, or a general error
        error_payload = {key: f"Error generating data for '{key}': AI response was not valid JSON." for key in next_phase_field_keys}
        error_payload["_raw_ai_response_error"] = raw_json_str # Include raw response for debugging
        return error_payload
    except Exception as e: # Catch any other unexpected error during parsing
        # print(f"Unexpected error processing seeded JSON: {e}") # For server logs
        error_payload = {key: f"Unexpected error processing data for '{key}'." for key in next_phase_field_keys}
        error_payload["_unexpected_error"] = str(e)
        return error_payload

if __name__ == '__main__':
    # This block is for testing the client directly.
    # Ensure GEMINI_API_KEY is set in your environment before running.
    if not GEMINI_API_KEY:
        print("Cannot run tests: GEMINI_API_KEY environment variable is not set.")
    else:
        print("Gemini Client Initialized with API Key. Testing functions...")

        # Test Data
        test_phase_1_data = {
            "project_name": "Ecoleta Recycling App",
            "objective": "Develop a mobile application to connect waste generators with collectors, promoting efficient recycling and waste management in urban areas.",
            "stakeholders": ["Households", "Waste Collection Companies", "Recycling Centers", "Municipal Authorities"],
            "constraints": ["Budget: $50,000 USD", "Timeline: 3 months for MVP", "Platform: Android & iOS", "Tech Stack: Python (Flask) backend, React Native frontend"]
        }
        test_phase_1_data_json = json.dumps(test_phase_1_data, indent=2)

        test_all_project_data_json = json.dumps({}, indent=2) # No previous phases for this test

        print("
--- Testing Solution Summary Generation ---")
        summary = generate_solution_summary(test_phase_1_data_json)
        print("Generated Summary:
", summary)

        print("
--- Testing Document Section Generation ---")
        section_title_test = "## 1.1. Project Name" # Example from phase 1 outline
        section_content = generate_document_section(section_title_test, test_phase_1_data_json, test_all_project_data_json)
        print(f"Generated Content for Section '{section_title_test}':
", section_content)

        section_title_test_2 = "## 2.1. Primary Objectives"
        section_content_2 = generate_document_section(section_title_test_2, test_phase_1_data_json, test_all_project_data_json)
        print(f"Generated Content for Section '{section_title_test_2}':
", section_content_2)

        print("
--- Testing Seed Next Phase Data ---")
        # Simulate fields for Phase 2: Requirements Engineering
        next_phase_2_fields = [
            "functional_reqs_summary",
            "nonfunctional_reqs_initial_thoughts",
            "data_reqs_overview",
            "acceptance_criteria_ideas"
        ]
        seeded_data = seed_next_phase_data(test_phase_1_data_json, next_phase_2_fields)
        print("Seeded Data for Next Phase (raw dict):
", seeded_data)
        print("Seeded Data for Next Phase (JSON formatted):
", json.dumps(seeded_data, indent=2))

        # Test with a more complex seeding scenario (e.g., data from phase 3, seeding for phase 4)
        test_phase_3_data = {
            "system_context": "The system is a cloud-native application with a web front-end, API gateway, and several microservices.",
            "chosen_architecture": "Microservices architecture using Kubernetes for orchestration.",
            "high_level_components": ["Frontend WebApp", "API Gateway", "User Service", "Order Service", "Payment Service"],
            "tech_stack_summary": "React, Python (Flask/FastAPI), PostgreSQL, Kafka, Docker, Kubernetes on GCP."
        }
        test_phase_3_data_json = json.dumps(test_phase_3_data)
        next_phase_4_fields = ["component_specs_todo", "api_definitions_outline", "data_model_focus_areas"]

        print("
--- Testing Seed Next Phase Data (Phase 3 to 4) ---")
        seeded_data_p3_p4 = seed_next_phase_data(test_phase_3_data_json, next_phase_4_fields)
        print("Seeded Data for Phase 4 (JSON formatted):
", json.dumps(seeded_data_p3_p4, indent=2))
