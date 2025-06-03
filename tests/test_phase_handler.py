import unittest
from src.core.data_structures import clear_answers, get_answers
from src.llm.llm_service import LLMService
from src.phase_manager.phase_handler import PhaseHandler
from src.phase_manager.phase_definitions import PHASE_DEFINITIONS # To check phase names

class TestPhaseHandler(unittest.TestCase):
    SESSION_ID = "test_phase_handler_session"

    def setUp(self):
        self.llm = LLMService()
        clear_answers(self.SESSION_ID) # Ensure clean state for each test
        self.handler = PhaseHandler(self.llm, session_id=self.SESSION_ID, initial_phase_id="initial_inquiry")

    def tearDown(self):
        clear_answers(self.SESSION_ID)

    def test_initialization(self):
        self.assertEqual(self.handler.current_phase_id, "initial_inquiry")
        self.assertEqual(len(self.handler.history), 0)

    def test_get_next_question(self):
        question = self.handler.get_next_question()
        self.assertIsNotNone(question)
        self.assertIn("Mock LLM-generated dynamic question", question.text)

    def test_submit_answer(self):
        self.handler.submit_answer("q_test_1", "Test answer 1")
        self.assertEqual(len(self.handler.history), 1)
        self.assertEqual(self.handler.history[0].text, "Test answer 1")

        stored_answers = get_answers(self.SESSION_ID)
        self.assertEqual(len(stored_answers), 1)
        self.assertEqual(stored_answers[0].text, "Test answer 1")

    def test_advance_phase(self):
        initial_phase_name = PHASE_DEFINITIONS[self.handler.current_phase_id]["name"]
        # print(f"Initial phase for test_advance_phase: {initial_phase_name}") # Debug print

        can_advance = self.handler.advance_to_next_phase()
        self.assertTrue(can_advance)
        self.assertEqual(self.handler.current_phase_id, "requirements_gathering")

        next_phase_name = PHASE_DEFINITIONS[self.handler.current_phase_id]["name"]
        # print(f"Advanced phase to: {next_phase_name}") # Debug print

        # Advance again
        can_advance_again = self.handler.advance_to_next_phase()
        self.assertTrue(can_advance_again)
        self.assertEqual(self.handler.current_phase_id, "solution_brainstorming")

        # Advance until no more phases
        while self.handler.current_phase_id and PHASE_DEFINITIONS.get(self.handler.current_phase_id, {}).get("next_phase"):
            self.handler.advance_to_next_phase()

        # Final advance to make current_phase_id None
        self.handler.advance_to_next_phase()
        self.assertIsNone(self.handler.current_phase_id) # Should be None at the end of defined flow


    def test_get_full_context(self):
        self.handler.submit_answer("q_ctx_1", "Context answer")
        full_context = self.handler.get_full_context()
        self.assertEqual(full_context.current_phase, "initial_inquiry")
        self.assertEqual(len(full_context.history), 1)
        self.assertEqual(full_context.history[0].text, "Context answer")

if __name__ == '__main__':
    unittest.main()
