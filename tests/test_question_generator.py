import unittest
from src.core.data_structures import PhaseContext, Answer
from src.llm.llm_service import LLMService
from src.phase_manager.question_generator import generate_dynamic_question

class TestQuestionGenerator(unittest.TestCase):

    def setUp(self):
        self.llm = LLMService() # Use mock LLM

    def test_generate_question_initial(self):
        pc = PhaseContext(current_phase="initial_inquiry")
        question = generate_dynamic_question(pc, self.llm)
        self.assertIsNotNone(question.id)
        self.assertIn("Mock LLM-generated dynamic question", question.text) # Mock response
        self.assertEqual(question.metadata["phase"], "initial_inquiry")

    def test_generate_question_with_history(self):
        history = [Answer("q1", "Previous answer.")]
        pc = PhaseContext(current_phase="details", history=history, additional_context={"goal": "get more info"})
        question = generate_dynamic_question(pc, self.llm)
        self.assertIn("Mock LLM-generated dynamic question", question.text)
        # In a real LLM test, we'd check if the prompt contained history/context.
        # Here, we rely on the mock LLM's fixed output for "question" prompts.

if __name__ == '__main__':
    unittest.main()
