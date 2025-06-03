# Example phase definitions. In a real app, this might come from a config file.
PHASE_DEFINITIONS = {
    "initial_inquiry": {
        "name": "Initial Inquiry",
        "goal": "Understand the user's primary objective and basic needs.",
        "next_phase": "requirements_gathering"
    },
    "requirements_gathering": {
        "name": "Requirements Gathering",
        "goal": "Collect detailed requirements for the project or document.",
        "next_phase": "solution_brainstorming" # Example next phase
    },
    "solution_brainstorming": {
        "name": "Solution Brainstorming",
        "goal": "Explore potential solutions or approaches based on gathered requirements.",
        "next_phase": "document_drafting"
    },
    "document_drafting": {
        "name": "Document Drafting",
        "goal": "Start drafting the document based on all collected information.",
        "next_phase": None # End of this example flow
    }
    # Add more phases as needed
}
