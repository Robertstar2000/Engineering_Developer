from src.llm.llm_service import LLMService
from src.phase_manager.phase_handler import PhaseHandler
from src.document_generator.document_builder import build_document
from src.core.data_structures import clear_answers # To reset session for demo

def run_interactive_session():
    """
    Runs a simple interactive command-line session to demonstrate the system.
    """
    session_id = "cli_demo_session"
    # Clear previous answers for a clean demo run
    clear_answers(session_id)
    print(f"Welcome! Starting new session: {session_id}")

    # Initialize services
    llm_service = LLMService(api_key="mock_cli_key")

    # Start with the initial phase defined in PhaseHandler
    # (default is "initial_inquiry")
    phase_handler = PhaseHandler(llm_service=llm_service, session_id=session_id)

    print("\n--- Starting Interaction ---")
    while phase_handler.current_phase_id:
        current_phase_def = phase_handler._get_current_phase_definition() # Protected access for demo
        if not current_phase_def: # Should not happen if current_phase_id is set
            print("Error: Could not get phase definition. Exiting.")
            break

        print(f"\nPhase: {current_phase_def.get('name', phase_handler.current_phase_id)}")
        print(f"Goal: {current_phase_def.get('goal', 'N/A')}")

        question = phase_handler.get_next_question()
        if not question:
            print("No more questions in this phase or an issue occurred.")
            # Attempt to advance phase if no question, or decide to end/ask to advance
            user_choice_advance = input("No more questions. Advance to next phase? (yes/no): ").strip().lower()
            if user_choice_advance == 'yes':
                if not phase_handler.advance_to_next_phase():
                    print("Could not advance or no more phases. Ending interaction.")
                    break
                continue # Loop to get question from new phase
            else:
                print("Staying in current phase or ending.")
                break # Or implement logic to retry/ask different question

        print(f"\nQuestion: {question.text}")
        user_response = input("Your answer: ")

        phase_handler.submit_answer(question.id, user_response)
        print("Answer recorded.")

        # Simple logic to decide when to advance phase (e.g., after a certain number of Qs or specific answers)
        # For demo, let's ask user if they want to try advancing after each answer.
        if phase_handler.current_phase_id: # Check if phase didn't end due to advance_to_next_phase
            advance_prompt = input("Try to advance to next phase? (yes/no/quit): ").strip().lower()
            if advance_prompt == 'yes':
                if not phase_handler.advance_to_next_phase():
                    print("Could not advance or no more phases. Interaction might end here.")
                    # If advance_to_next_phase sets current_phase_id to None, loop will terminate
            elif advance_prompt == 'quit':
                print("Quitting interaction.")
                break

    print("\n--- Interaction Ended ---")

    # Document Generation
    # Ask user if they want to generate a document
    generate_doc_choice = input("\nDo you want to generate a document now? (yes/no): ").strip().lower()
    if generate_doc_choice == 'yes':
        # For demo, always try to generate "project_proposal".
        # In a real app, user might choose or it would be context-dependent.
        outline_name = "project_proposal"
        print(f"Attempting to generate document: '{outline_name}'...")

        # Get the full context from the phase_handler
        final_context = phase_handler.get_full_context()
        if not final_context.history:
            print("No answers were recorded. Document generation might be minimal.")

        document_result = build_document(
            outline_name=outline_name,
            phase_context=final_context, # Use the complete context
            llm_service=llm_service
        )

        if document_result:
            filename, content = document_result
            print(f"\n--- Document Generated: {filename} ---")
            print(content)
            print("--- End of Document ---")
            # Optionally, save the document
            # with open(filename, "w", encoding="utf-8") as f:
            #     f.write(content)
            # print(f"Document saved as {filename}")
        else:
            print("Failed to generate the document.")
    else:
        print("Skipping document generation.")

    print("\nSession finished. Thank you!")

if __name__ == '__main__':
    run_interactive_session()
