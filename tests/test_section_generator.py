import unittest
from src.core.data_structures import DocumentSection, DocumentOutline, PhaseContext, Answer
from src.llm.llm_service import LLMService
from src.document_generator.section_generator import generate_document_section, _format_prompt_template, _prepare_context_for_prompt

class TestSectionGenerator(unittest.TestCase):

    def setUp(self):
        self.llm = LLMService()
        self.sample_outline = DocumentOutline(
            title="Test Doc",
            file_name_template="test.md",
            document_generation_context_prompt="Overall context for test doc.",
            sections=[]
        )
        self.sample_phase_context = PhaseContext(
            current_phase="doc_gen",
            history=[Answer("q1", "User wants a simple doc.")],
            additional_context={"project_name": "TestProject"}
        )

    def test_format_prompt_template(self):
        template = "Hello {name}, welcome to {place}."
        data = {"name": "World", "place": "Earth"}
        formatted = _format_prompt_template(template, data)
        self.assertEqual(formatted, "Hello World, welcome to Earth.")

        data_missing = {"name": "World"}
        formatted_missing = _format_prompt_template(template, data_missing)
        self.assertEqual(formatted_missing, "Hello World, welcome to {place_NOT_FOUND}.")

    def test_prepare_context_for_prompt(self):
        context_data = _prepare_context_for_prompt(self.sample_outline, self.sample_phase_context)
        self.assertEqual(context_data["document_title"], "Test Doc")
        self.assertIn("User wants a simple doc.", context_data["user_answers_summary"])
        self.assertEqual(context_data["project_name"], "TestProject") # From additional_context

    def test_generate_document_section(self):
        section_template = DocumentSection(
            id="intro",
            title="Introduction",
            generation_prompt_template="Write an intro about {project_name} based on: {user_answers_summary}"
        )
        generated_section = generate_document_section(
            section_template, self.sample_outline, self.sample_phase_context, self.llm
        )
        self.assertEqual(generated_section.id, "intro")
        self.assertIn("Mock LLM-generated section content", generated_section.content)
        # The mock LLM output for sections is generic, but we check it's called.
        # A more advanced test would check the prompt sent to the LLM.

if __name__ == '__main__':
    unittest.main()
