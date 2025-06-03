from typing import Dict, Any
from src.core.data_structures import DocumentSection, DocumentOutline, PhaseContext, Answer
from src.llm.llm_service import LLMService
import re # For simple placeholder replacement

def _format_prompt_template(template: str, context_data: Dict[str, Any]) -> str:
    """
    Formats a prompt template string by replacing placeholders {key}
    with values from the context_data dictionary.
    Missing keys will be replaced with a placeholder string.
    """
    def replace_match(match):
        key = match.group(1)
        return str(context_data.get(key, f"{{{key}_NOT_FOUND}}"))

    # Regex to find {key} placeholders
    return re.sub(r'{([a-zA-Z0-9_]+)}', replace_match, template)

def _prepare_context_for_prompt(outline: DocumentOutline, phase_context: PhaseContext) -> Dict[str, Any]:
    """
    Prepares a flat dictionary of context data for populating prompt templates.
    This can be expanded to include more sophisticated context extraction.
    """
    context_data = {
        "document_title": outline.title,
        # Add other global outline properties if needed
    }

    # Summarize answers or provide them in a structured way
    # For simplicity, let's join all answers into a single string for now.
    # A more advanced version might categorize or select relevant answers.
    answer_summary = "\n".join([f"- Q: (ID {ans.question_id}) A: {ans.text}" for ans in phase_context.history])
    context_data["user_answers_summary"] = answer_summary if answer_summary else "No answers provided yet."

    # Allow direct access to phase context attributes if needed by specific prompts
    context_data.update(phase_context.additional_context) # Add specific phase context
    context_data["current_phase_name"] = phase_context.current_phase

    # You might want to extract specific answers based on question IDs or metadata
    # For example:
    # for ans in phase_context.history:
    #     if "user_problem_description" in ans.metadata.get("tags", []):
    #         context_data["user_problem_description"] = ans.text

    # This is a placeholder for making individual answers available by a known key
    # This requires knowing what data each prompt template variable (e.g., {user_problem_description}) expects
    # and how to find that in the answers. For now, we'll rely on the summary
    # and specific additional_context from the phase.
    # Example:
    # context_data["problem_statement"] = "User wants to solve X, Y, Z" (extracted from answers)
    # context_data["solution_overview"] = "Proposed solution is A, B, C" (extracted from answers)


    # Flatten history for easier access in simple templates if desired
    # for i, ans in enumerate(phase_context.history):
    #    context_data[f"answer_q_{ans.question_id}"] = ans.text
    #    context_data[f"answer_text_{i+1}"] = ans.text


    # Placeholder values for common template variables, if not found in context
    # These should ideally be derived from actual user input / phase_context
    common_template_keys = [
        "project_name", "problem_statement", "solution_overview", "user_problem_description",
        "user_impact_details", "user_solution_ideas", "user_solution_mechanism", "user_key_features",
        "user_timeline_input", "user_milestones", "user_budget_info", "user_cost_items",
        "user_value_prop", "user_next_steps", "meeting_topic", "meeting_date", "attendees_list",
        "apologies_list", "agenda_items", "current_item_title", "discussion_summary_for_item",
        "decisions_for_item", "action_description", "assignee", "deadline", "next_meeting_date",
        "next_meeting_time", "next_meeting_location"
    ]
    for key in common_template_keys:
        if key not in context_data: # Make sure not to overwrite if already populated from phase_context.additional_context
            context_data[key] = f"Data for '{key}' (not found in context)"


    return context_data


def generate_document_section(
    section_template: DocumentSection,
    outline: DocumentOutline,
    phase_context: PhaseContext,
    llm_service: LLMService
) -> DocumentSection:
    """
    Generates content for a specific document section using the LLM.

    :param section_template: The DocumentSection object defining the section to generate (contains the prompt template).
    :param outline: The overall DocumentOutline for context.
    :param phase_context: The current PhaseContext containing user answers and other info.
    :param llm_service: The LLM service client.
    :return: The DocumentSection object updated with the generated content.
    """

    # Prepare data for filling placeholders in the prompt template
    prompt_fill_data = _prepare_context_for_prompt(outline, phase_context)

    # Format the specific section's prompt template
    specific_section_prompt = _format_prompt_template(
        section_template.generation_prompt_template,
        prompt_fill_data
    )

    # Construct the full prompt for the LLM
    # Includes overall document context and specific section instructions
    full_llm_prompt = (
        f"Context for the entire document ('{outline.title}'): {outline.document_generation_context_prompt}\n\n"
        f"Now, generate content for the section: '{section_template.title}'.\n"
        f"Instructions for this section: {specific_section_prompt}"
    )

    # Call the LLM service
    generated_content = llm_service.generate_text(
        prompt=full_llm_prompt,
        context=phase_context.to_dict() # Pass full phase context if LLM can use it
    )

    # Update the section object with the generated content
    section_template.content = generated_content.strip()

    return section_template

# Example Usage (optional, for testing this module directly)
if __name__ == '__main__':
    from src.llm.llm_service import LLMService
    from src.document_generator.outlines import get_document_outline

    # Mock LLM Service and PhaseContext for testing
    mock_llm = LLMService(api_key="test_key_sg")

    sample_history = [
        Answer(question_id="q1", text="The project is about creating a new type of coffee machine."),
        Answer(question_id="q2", text="The target users are home baristas."),
        Answer(question_id="q3", text="Key features include temperature control and automated grinding.", metadata={"tags": ["user_key_features"]}),
        Answer(question_id="q4", text="The problem is existing machines are too complex.", metadata={"tags": ["user_problem_description"]})
    ]
    test_phase_context = PhaseContext(
        current_phase="document_drafting",
        history=sample_history,
        additional_context={"project_name": "SuperCoffee 3000", "solution_overview": "A smart, user-friendly coffee machine."}
    )

    # Get a document outline
    proposal_outline = get_document_outline("project_proposal")

    if proposal_outline and proposal_outline.sections:
        print(f"--- Generating sections for: {proposal_outline.title} ---")

        # Test generating the first section (Introduction)
        intro_section_template = next((s for s in proposal_outline.sections if s.id == "introduction"), None)
        if intro_section_template:
            print(f"\nGenerating section: '{intro_section_template.title}'...")
            # Create a copy to avoid modifying the original template in this test
            section_to_generate = DocumentSection(id=intro_section_template.id, title=intro_section_template.title, generation_prompt_template=intro_section_template.generation_prompt_template)

            generated_intro_section = generate_document_section(
                section_template=section_to_generate,
                outline=proposal_outline,
                phase_context=test_phase_context,
                llm_service=mock_llm
            )
            print(f"  ID: {generated_intro_section.id}")
            print(f"  Title: {generated_intro_section.title}")
            print(f"  Generated Content: {generated_intro_section.content}")
        else:
            print("\n'Introduction' section template not found in proposal outline.")

        # Test generating another section (Proposed Solution)
        solution_section_template = next((s for s in proposal_outline.sections if s.id == "proposed_solution"), None)
        if solution_section_template:
            print(f"\nGenerating section: '{solution_section_template.title}'...")
            section_to_generate_solution = DocumentSection(id=solution_section_template.id, title=solution_section_template.title, generation_prompt_template=solution_section_template.generation_prompt_template)

            generated_solution_section = generate_document_section(
                section_template=section_to_generate_solution,
                outline=proposal_outline,
                phase_context=test_phase_context,
                llm_service=mock_llm
            )
            print(f"  ID: {generated_solution_section.id}")
            print(f"  Title: {generated_solution_section.title}")
            print(f"  Generated Content: {generated_solution_section.content}")
        else:
            print("\n'Proposed Solution' section template not found in proposal outline.")
    else:
        print("Project proposal outline not found or has no sections.")
