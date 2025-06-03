import unittest
from src.llm.llm_service import LLMService

class TestLLMService(unittest.TestCase):

    def setUp(self):
        self.llm = LLMService(api_key="test_key", model_name="test-mock-model")

    def test_generate_text_basic_prompt(self):
        prompt = "This is a test prompt."
        response = self.llm.generate_text(prompt)
        self.assertIn("mock LLM response", response)
        self.assertIn(prompt[:50], response)

    def test_generate_text_question_prompt(self):
        prompt = "Generate a question about project scope."
        response = self.llm.generate_text(prompt)
        self.assertIn("Mock LLM-generated dynamic question", response)

    def test_generate_text_section_prompt(self):
        prompt = "Generate content for the introduction section."
        response = self.llm.generate_text(prompt)
        self.assertIn("Mock LLM-generated section content", response)
        self.assertIn("introduction", response.lower())

    def test_generate_text_with_context(self):
        prompt = "Another prompt"
        context = {"user_id": 123, "topic": "general"}
        # The mock doesn't really use context to change response, but we check it's passed
        response = self.llm.generate_text(prompt, context=context)
        self.assertIn("mock LLM response", response)
        # In a real test, you might check if the LLM's output reflects the context.
        # For a mock, we're mainly ensuring the call doesn't break.

if __name__ == '__main__':
    unittest.main()
