from typing import Dict, Any

class LLMService:
    """
    A mock LLM service client.
    In a real application, this class would handle actual API calls
    to an LLM provider (e.g., OpenAI, Anthropic, Google Gemini).
    """

    def __init__(self, api_key: str = None, model_name: str = "mock-model"):
        """
        Initializes the LLM service.
        :param api_key: API key for the LLM service (unused in mock).
        :param model_name: Name of the LLM model to use (unused in mock).
        """
        self.api_key = api_key
        self.model_name = model_name
        print(f"MockLLMService initialized for model: {self.model_name}")

    def generate_text(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """
        Generates text based on a given prompt and context.
        This mock implementation returns a fixed string indicating it's a mock response.

        :param prompt: The prompt to send to the LLM.
        :param context: Additional context to provide to the LLM (e.g., conversation history).
        :return: The LLM's generated text.
        """
        print(f"MockLLMService received prompt: {prompt}")
        if context:
            print(f"MockLLMService received context: {context}")

        # Simulate LLM processing delay (optional)
        # import time
        # time.sleep(0.1)

        mock_response = f"This is a mock LLM response to the prompt: '{prompt[:50]}...'"

        if "question" in prompt.lower():
            mock_response = "Mock LLM-generated dynamic question: What is your primary goal for this project?"
        elif "section" in prompt.lower() and "introduction" in prompt.lower():
            mock_response = "Mock LLM-generated section content: This is the introduction to the document, based on the user's inputs and project phase."
        elif "section" in prompt.lower():
            mock_response = "Mock LLM-generated section content for a generic section."

        return mock_response

# Example usage (optional, can be removed or kept for direct testing of the module)
if __name__ == '__main__':
    mock_llm = LLMService(api_key="test_key")

    sample_prompt_q = "Generate a question for the user about their budget."
    question_response = mock_llm.generate_text(prompt=sample_prompt_q, context={"phase": "budgeting"})
    print(f"Response to question prompt: {question_response}")

    sample_prompt_s = "Generate content for the 'Executive Summary' section."
    section_response = mock_llm.generate_text(prompt=sample_prompt_s, context={"previous_answers": ["Answer 1", "Answer 2"]})
    print(f"Response to section prompt: {section_response}")
