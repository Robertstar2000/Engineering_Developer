import json
import os  # For environment variable access in test block
from typing import Dict, List, Any, Optional

# Assuming your config.py and gemini_client.py are in the same directory (root)
from config import get_phase_config, PhaseSchema # PhaseSchema for type hinting
from gemini_client import generate_document_section

def build_document_for_phase(
    phase_id: int,
    current_phase_data: Dict[str, Any],
    all_project_data: Dict[str, Dict[str, Any]] # Keys are string phase IDs e.g. "1", "2"
) -> str:
    """
    Builds a complete Markdown document for a given phase by iterating through its
    defined outline and generating content for each section using an AI model.

    Args:
        phase_id: The integer ID of the current phase.
        current_phase_data: Data specific to the current phase.
        all_project_data: Data from all phases, where keys are string phase IDs.
                          This provides historical context.
    Returns:
        A string containing the full Markdown document or an error message string.
    """
    phase_config: Optional[PhaseSchema] = get_phase_config(phase_id)

    if not phase_config:
        return f"# Error: Document Generation Failed\n\nPhase {phase_id} configuration not found."
    if not phase_config.document or not phase_config.document.outline:
        return f"# Error: Document Generation Failed\n\nDocument outline not configured for Phase {phase_id}: {phase_config.title}."

    full_document_parts: List[str] = []

    doc_main_title = phase_config.document.name.replace('.md', '').replace('_', ' ').title()
    full_document_parts.append(f"# {phase_config.title}: {doc_main_title}\n")

    current_phase_data_json_str = json.dumps(current_phase_data, indent=2) if current_phase_data else "{}"

    historical_data_for_prompt: Dict[str, Dict[str, Any]] = {
        pid_str: pdata
        for pid_str, pdata in all_project_data.items()
        if pid_str.isdigit() and int(pid_str) < phase_id
    }
    all_project_data_json_str = json.dumps(historical_data_for_prompt, indent=2) if historical_data_for_prompt else "{}"

    for section_title_from_outline in phase_config.document.outline:
        full_document_parts.append(f"\n{section_title_from_outline}\n")

        clean_prompt_section_title = section_title_from_outline.lstrip('#').lstrip()

        generated_section_content = generate_document_section(
            section_title=clean_prompt_section_title,
            current_phase_data_json_str=current_phase_data_json_str,
            all_project_data_json_str=all_project_data_json_str
        )

        full_document_parts.append(generated_section_content)
        full_document_parts.append("\n")

    return "".join(full_document_parts)

if __name__ == '__main__':
    print("Testing Document Generator...")

    from config import PHASES_CONFIG, get_phase_config

    if not PHASES_CONFIG:
        print("CRITICAL: Phase configurations not loaded. Check 'phases.yaml' and 'config.py'.")
    elif not os.environ.get("GEMINI_API_KEY"):
        print("CRITICAL: GEMINI_API_KEY environment variable not set. Cannot test document generation.")
    else:
        mock_phase_1_id = 1
        mock_current_phase_1_data = {
            "project_name": "AI-Powered Recipe Assistant",
            "objective": "To develop a smart kitchen assistant that suggests recipes based on available ingredients and user dietary preferences.",
            "stakeholders": ["Home cooks", "Professional chefs", "Nutritionists", "Grocery delivery services"],
            "constraints": ["Budget: $75,000", "Timeline: 4 months for MVP", "Tech: Python backend, Mobile-first (React Native)"]
        }
        mock_all_project_data_for_p1: Dict[str, Dict[str, Any]] = {}

        print(f"\n--- Generating Document for Phase {mock_phase_1_id} ---")
        phase_1_config_test = get_phase_config(mock_phase_1_id)
        if phase_1_config_test and phase_1_config_test.document and phase_1_config_test.document.outline:
            phase_1_document = build_document_for_phase(
                mock_phase_1_id,
                mock_current_phase_1_data,
                mock_all_project_data_for_p1
            )
            print("\n--- Generated Document (Phase 1) ---")
            print(phase_1_document)
            print("--- End of Phase 1 Document ---")
        else:
            print(f"Phase {mock_phase_1_id} or its document outline is not configured correctly in 'phases.yaml'. Skipping test.")

        mock_phase_2_id = 2
        mock_current_phase_2_data = {
            "functional_reqs": "User registration & login; Ingredient inventory input (manual & OCR); Recipe search & filtering; Meal planning.",
            "nonfunctional_reqs": "High availability (99.95%); Secure user data (GDPR compliant); Fast response times (<1.5s for searches).",
            "data_reqs": "Recipe database (ingredients, instructions, nutritional info); User profiles; Ingredient data.",
            "acceptance_criteria": "Users can successfully find and save 5 recipes within 10 minutes of first use."
        }
        mock_all_project_data_for_p2: Dict[str, Dict[str, Any]] = {
            "1": mock_current_phase_1_data
        }

        print(f"\n--- Generating Document for Phase {mock_phase_2_id} ---")
        phase_2_config_test = get_phase_config(mock_phase_2_id)
        if phase_2_config_test and phase_2_config_test.document and phase_2_config_test.document.outline:
            phase_2_document = build_document_for_phase(
                mock_phase_2_id,
                mock_current_phase_2_data,
                mock_all_project_data_for_p2
            )
            print("\n--- Generated Document (Phase 2) ---")
            print(phase_2_document)
            print("--- End of Phase 2 Document ---")
        else:
            print(f"Phase {mock_phase_2_id} or its document outline is not configured correctly in 'phases.yaml'. Skipping test.")
