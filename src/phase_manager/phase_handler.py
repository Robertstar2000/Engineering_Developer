from typing import List, Dict, Optional
from src.core.data_structures import Question, Answer, PhaseContext, store_answer as global_store_answer, get_answers as global_get_answers
from src.llm.llm_service import LLMService
from .question_generator import generate_dynamic_question
from .phase_definitions import PHASE_DEFINITIONS # Import phase definitions

SESSION_ID_EXAMPLE = "user123_sessionABC" # Example session ID for answer storage

class PhaseHandler:
    def __init__(self, llm_service: LLMService, session_id: str, initial_phase_id: str = "initial_inquiry"):
        self.llm_service = llm_service
        self.session_id = session_id
        self.current_phase_id = initial_phase_id
        self.history: List[Answer] = global_get_answers(self.session_id) # Load history for session

        if not self.current_phase_id in PHASE_DEFINITIONS:
            raise ValueError(f"Initial phase ID '{self.current_phase_id}' not found in phase definitions.")

    def _get_current_phase_definition(self) -> Dict:
        return PHASE_DEFINITIONS.get(self.current_phase_id, {})

    def get_next_question(self) -> Optional[Question]:
        """
        Gets the next question for the current phase.
        If the current phase is completed or has no more questions, it might return None
        or trigger phase transition (simplified here).
        """
        if not self.current_phase_id:
            print("No current phase ID, cannot get next question.")
            return None # No more phases

        phase_def = self._get_current_phase_definition()
        if not phase_def:
            print(f"Warning: Phase definition for '{self.current_phase_id}' not found.")
            return None

        additional_context_for_phase = {
            "goal": phase_def.get("goal", "No specific goal defined for this phase."),
            "phase_name": phase_def.get("name", self.current_phase_id)
        }

        phase_context = PhaseContext(
            current_phase=self.current_phase_id, # Use phase ID here
            history=self.history,
            additional_context=additional_context_for_phase
        )

        return generate_dynamic_question(phase_context, self.llm_service)

    def submit_answer(self, question_id: str, answer_text: str) -> None:
        """
        Submits an answer from the user and stores it.
        """
        answer = Answer(question_id=question_id, text=answer_text)
        self.history.append(answer)
        global_store_answer(self.session_id, answer) # Persist answer

    def advance_to_next_phase(self) -> bool:
        """
        Advances the handler to the next phase as defined in PHASE_DEFINITIONS.
        Returns True if successfully advanced, False if no next phase or current phase not found.
        """
        current_phase_def = self._get_current_phase_definition()
        if not current_phase_def: # Current phase ID might have been set to None
             print(f"Cannot advance: Current phase '{self.current_phase_id}' definition not found or is None.")
             return False
        next_phase_id = current_phase_def.get("next_phase")

        if next_phase_id and next_phase_id in PHASE_DEFINITIONS:
            self.current_phase_id = next_phase_id
            print(f"Advanced to phase: {PHASE_DEFINITIONS[self.current_phase_id]['name']}")
            return True
        elif next_phase_id:
            print(f"Warning: Next phase ID '{next_phase_id}' not found in definitions. Staying in phase '{self.current_phase_id}'.")
            return False
        else:
            print(f"End of defined phase progression or no next phase for '{self.current_phase_id}'.")
            self.current_phase_id = None # Mark as no current phase
            return False

    def get_full_context(self) -> PhaseContext:
        """Returns the complete current context including all history."""
        phase_def = self._get_current_phase_definition() # This will be {} if current_phase_id is None
        current_phase_name = self.current_phase_id
        additional_context_for_phase = {
            "goal": phase_def.get("goal", "No specific goal defined for this phase."),
            "phase_name": phase_def.get("name", current_phase_name if current_phase_name else "N/A")
        }
        return PhaseContext(
            current_phase=current_phase_name if current_phase_name else "completed",
            history=self.history,
            additional_context=additional_context_for_phase
        )


# Example Usage (optional, for testing this module directly)
if __name__ == '__main__':
    mock_llm = LLMService(api_key="test_key_ph")

    # Initialize handler for a session
    session_id = "test_session_123"
    # Clear any previous answers for this test session
    from src.core.data_structures import clear_answers
    clear_answers(session_id)

    handler = PhaseHandler(llm_service=mock_llm, session_id=session_id, initial_phase_id="initial_inquiry")

    print(f"Starting with phase: {handler._get_current_phase_definition().get('name')}")

    # Get first question
    q1 = handler.get_next_question()
    if q1:
        print(f"Q1 ({q1.id}): {q1.text}")
        handler.submit_answer(q1.id, "My main goal is to automate customer support documentation.")

    # Get second question (still in initial_inquiry or based on LLM's mock logic)
    q2 = handler.get_next_question()
    if q2:
        print(f"Q2 ({q2.id}): {q2.text}")
        handler.submit_answer(q2.id, "The primary users are our internal support agents.")

    # Advance phase
    if handler.advance_to_next_phase():
        q3 = handler.get_next_question() # Question for "requirements_gathering"
        if q3:
            print(f"Q3 ({q3.id}) for phase '{handler._get_current_phase_definition().get('name')}': {q3.text}")
            handler.submit_answer(q3.id, "We need it to integrate with Zendesk.")

    # Show all collected answers for the session
    all_session_answers = global_get_answers(session_id)
    print(f"\nAll answers for session '{session_id}':")
    for ans in all_session_answers:
        print(f"  Q: {ans.question_id}, A: {ans.text}")

    full_context = handler.get_full_context()
    print(f"\nFull context at end of interaction: {full_context.to_dict()}")
