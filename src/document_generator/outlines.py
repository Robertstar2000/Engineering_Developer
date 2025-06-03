from typing import Dict, Optional, List
from src.core.data_structures import DocumentOutline, DocumentSection

# In a real application, these templates might be loaded from JSON/YAML files.
EXAMPLE_OUTLINE_TEMPLATES: Dict[str, Dict] = {
    "project_proposal": {
        "title": "Project Proposal",
        "file_name_template": "{project_name}_project_proposal.md",
        "document_generation_context_prompt": "This document is a project proposal. Ensure a professional and persuasive tone.",
        "sections": [
            {
                "id": "introduction",
                "title": "1. Introduction",
                "generation_prompt_template": "Generate an introduction for a project proposal titled '{document_title}'. Key information to include: {user_answers_summary}. The project aims to solve: {problem_statement}. This proposal outlines: {solution_overview}."
            },
            {
                "id": "problem_statement",
                "title": "2. Problem Statement",
                "generation_prompt_template": "Describe the problem this project addresses. Use the following user inputs: {user_problem_description}. Elaborate on the impact of this problem: {user_impact_details}."
            },
            {
                "id": "proposed_solution",
                "title": "3. Proposed Solution",
                "generation_prompt_template": "Detail the proposed solution. Based on user input: {user_solution_ideas}. Explain how it works: {user_solution_mechanism}. Highlight key features: {user_key_features}."
            },
            {
                "id": "timeline",
                "title": "4. Timeline",
                "generation_prompt_template": "Outline a project timeline. User's expected duration: {user_timeline_input}. Key milestones: {user_milestones}."
            },
            {
                "id": "budget",
                "title": "5. Budget",
                "generation_prompt_template": "Provide a budget overview. User's budget constraints: {user_budget_info}. Cost breakdown: {user_cost_items}."
            },
            {
                "id": "conclusion",
                "title": "6. Conclusion",
                "generation_prompt_template": "Write a concluding statement for the project proposal. Reiterate the value proposition: {user_value_prop}. Call to action: {user_next_steps}."
            }
        ]
    },
    "meeting_minutes": {
        "title": "Meeting Minutes",
        "file_name_template": "meeting_minutes_{date}_{topic}.md",
        "document_generation_context_prompt": "This document records meeting minutes. Focus on clarity, conciseness, and accurate representation of discussions and decisions.",
        "sections": [
            {
                "id": "header",
                "title": "Meeting Details",
                "generation_prompt_template": "Generate the meeting header. Meeting Title/Topic: {meeting_topic}. Date: {meeting_date}. Attendees: {attendees_list}. Apologies: {apologies_list}."
            },
            {
                "id": "agenda_items_discussion",
                "title": "Agenda Items & Discussion",
                "generation_prompt_template": "Summarize the discussion for each agenda item. Agenda: {agenda_items}. For item '{current_item_title}', discussion points were: {discussion_summary_for_item}. Decisions made: {decisions_for_item}."
            },
            {
                "id": "action_items",
                "title": "Action Items",
                "generation_prompt_template": "List all action items. For each action: Description: {action_description}, Assigned to: {assignee}, Deadline: {deadline}."
            },
            {
                "id": "next_meeting",
                "title": "Next Meeting",
                "generation_prompt_template": "Details for the next meeting (if any). Date: {next_meeting_date}. Time: {next_meeting_time}. Location/Platform: {next_meeting_location}."
            }
        ]
    }
    # Add more templates as needed
}

def get_document_outline(outline_name: str) -> Optional[DocumentOutline]:
    """
    Retrieves a document outline template by its name and converts it
    into a DocumentOutline data structure.

    :param outline_name: The name of the outline template to retrieve.
    :return: A DocumentOutline object if the template is found, otherwise None.
    """
    template_data = EXAMPLE_OUTLINE_TEMPLATES.get(outline_name)
    if not template_data:
        return None

    sections = []
    for sec_data in template_data.get("sections", []):
        sections.append(
            DocumentSection(
                id=sec_data["id"],
                title=sec_data["title"],
                # Content will be generated later
                generation_prompt_template=sec_data.get("generation_prompt_template", "")
            )
        )

    return DocumentOutline(
        title=template_data["title"],
        file_name_template=template_data.get("file_name_template", "document.md"),
        sections=sections,
        document_generation_context_prompt=template_data.get("document_generation_context_prompt", "")
    )

# Example Usage (optional, for testing this module directly)
if __name__ == '__main__':
    print("Available outline templates:", list(EXAMPLE_OUTLINE_TEMPLATES.keys()))

    # Test fetching a project proposal outline
    proposal_outline = get_document_outline("project_proposal")
    if proposal_outline:
        print(f"\n--- {proposal_outline.title} Outline ---")
        print(f"File Name Template: {proposal_outline.file_name_template}")
        print(f"Document Context Prompt: {proposal_outline.document_generation_context_prompt}")
        for section in proposal_outline.sections:
            print(f"  Section ID: {section.id}, Title: {section.title}")
            print(f"    Prompt Template: {section.generation_prompt_template[:100]}...") # Print first 100 chars
    else:
        print("\nProject proposal outline not found.")

    # Test fetching meeting minutes outline
    minutes_outline = get_document_outline("meeting_minutes")
    if minutes_outline:
        print(f"\n--- {minutes_outline.title} Outline ---")
        for section in minutes_outline.sections:
            print(f"  Section ID: {section.id}, Title: {section.title}")
    else:
        print("\nMeeting minutes outline not found.")

    # Test fetching a non-existent outline
    non_existent_outline = get_document_outline("non_existent_template")
    if not non_existent_outline:
        print("\nSuccessfully handled non-existent template as expected.")
    else:
        print("\nError: Non-existent template was somehow found.")
