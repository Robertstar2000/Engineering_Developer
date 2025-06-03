from typing import Optional, Tuple
from src.core.data_structures import PhaseContext, DocumentOutline
from src.llm.llm_service import LLMService
from .outlines import get_document_outline
from .section_generator import generate_document_section, _prepare_context_for_prompt # For filename formatting

def build_document(
    outline_name: str,
    phase_context: PhaseContext,
    llm_service: LLMService
) -> Optional[Tuple[str, str]]: # Returns (filename, document_content)
    """
    Builds a complete document by loading an outline, generating content for each section,
    and assembling it into a Markdown string.

    :param outline_name: The name of the document outline to use.
    :param phase_context: The current PhaseContext containing all user answers and context.
    :param llm_service: The LLM service client.
    :return: A tuple containing the suggested filename and the full document content as a string,
             or None if the outline is not found.
    """

    outline = get_document_outline(outline_name)
    if not outline:
        print(f"Error: Document outline '{outline_name}' not found.")
        return None

    document_parts = []

    # Add a document title (H1 for Markdown)
    document_parts.append(f"# {outline.title}\n")

    # Iterate through sections, generate content, and append to document_parts
    for section_template in outline.sections:
        # The section_template from the outline is just a template.
        # We pass it to generate_document_section which will fill its 'content'.
        # No need to create a new DocumentSection object here unless you want to preserve the original template.
        # For this implementation, generate_document_section modifies the content of the section object from the outline.
        # Let's ensure we are working with copies if we don't want to modify the global outline objects.
        # However, get_document_outline already returns fresh copies of DocumentSection objects.

        print(f"Generating content for section: '{section_template.title}'...")
        generated_section = generate_document_section(
            section_template=section_template, # This section_template will have its content updated
            outline=outline,
            phase_context=phase_context,
            llm_service=llm_service
        )

        # Add section title (H2 for Markdown, if title exists)
        if generated_section.title:
            document_parts.append(f"## {generated_section.title}\n")
        document_parts.append(generated_section.content)
        document_parts.append("\n") # Add a newline for spacing between sections

    full_document_content = "\n".join(document_parts)

    # Format the filename
    # Use the same _prepare_context_for_prompt to get data for filename placeholders
    filename_context_data = _prepare_context_for_prompt(outline, phase_context)

    # Simple placeholder replacement for filename (e.g., {project_name})
    # Using the internal _format_prompt_template from section_generator for consistency
    from .section_generator import _format_prompt_template as format_filename_template
    formatted_filename = format_filename_template(outline.file_name_template, filename_context_data)

    return formatted_filename, full_document_content

# Example Usage (optional, for testing this module directly)
if __name__ == '__main__':
    from src.llm.llm_service import LLMService
    from src.core.data_structures import Answer # For creating sample history

    # Mock LLM Service and PhaseContext for testing
    mock_llm = LLMService(api_key="test_key_db")

    sample_history = [
        Answer(question_id="q1", text="The project is Super Kiosk."),
        Answer(question_id="q2", text="It's for public information access in city centers."),
        Answer(question_id="q3", text="Key features are touch screen, map, and local event listings."),
        Answer(question_id="q4", text="The problem is tourists can't find info easily."),
        Answer(question_id="q5", text="Timeline is 3 months."),
        Answer(question_id="q6", text="Budget is $50,000."),
    ]
    test_phase_context = PhaseContext(
        current_phase="final_document_generation",
        history=sample_history,
        additional_context={
            "project_name": "SuperKiosk", # This will be used in filename
            "user_problem_description": "Tourists struggle to find local information.",
            "user_solution_ideas": "A network of interactive kiosks.",
            "user_key_features": "Touch screen, maps, event listings, multilingual support.",
            "user_timeline_input": "3 months",
            "user_milestones": "Design, Development, Pilot, Launch",
            "user_budget_info": "$50,000",
            "user_cost_items": "Hardware, Software, Deployment",
            "user_value_prop": "Easy access to city info for tourists.",
            "user_next_steps": "Approve proposal to proceed."
        }
    )

    outline_to_build = "project_proposal"
    print(f"--- Building document for outline: '{outline_to_build}' ---")

    result = build_document(
        outline_name=outline_to_build,
        phase_context=test_phase_context,
        llm_service=mock_llm
    )

    if result:
        filename, document_content = result
        print(f"\nSuccessfully generated document!")
        print(f"Suggested Filename: {filename}")
        print(f"--- Document Content Start ---")
        print(document_content)
        print(f"--- Document Content End ---")

        # Simulate saving the document (optional)
        # with open(filename, "w", encoding="utf-8") as f:
        #     f.write(document_content)
        # print(f"\nDocument notionally saved to '{filename}'")
    else:
        print(f"\nFailed to build document for outline: '{outline_to_build}'.")
