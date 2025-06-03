import unittest
from src.core.data_structures import PhaseContext, Answer
from src.llm.llm_service import LLMService
from src.document_generator.document_builder import build_document
from src.document_generator.outlines import EXAMPLE_OUTLINE_TEMPLATES # To ensure outline exists

class TestDocumentBuilder(unittest.TestCase):

    def setUp(self):
        self.llm = LLMService()
        self.sample_phase_context = PhaseContext(
            current_phase="build_phase",
            history=[Answer("q_proj", "MyProjectName"), Answer("q_detail", "Detail about project.")],
            additional_context={"project_name": "MyTestProject"} # Used for filename
        )

    def test_build_document_project_proposal(self):
        # Ensure the outline we're testing with exists
        self.assertIn("project_proposal", EXAMPLE_OUTLINE_TEMPLATES.keys())

        result = build_document("project_proposal", self.sample_phase_context, self.llm)
        self.assertIsNotNone(result)
        filename, content = result

        self.assertEqual(filename, "MyTestProject_project_proposal.md")
        self.assertIn("# Project Proposal", content) # Check H1 title
        # Based on mock LLM, each section will have "Mock LLM-generated section content"
        # Count occurrences to ensure sections were processed
        # Number of sections in project_proposal outline is 6
        # The mock LLM returns specific responses for intro and generic for others.
        # For this test, let's count "Mock LLM-generated section content" which appears in generic and intro.
        # The intro response is: "Mock LLM-generated section content: This is the introduction to the document..."
        # The generic response is: "Mock LLM-generated section content for a generic section."
        # So, all 6 sections should contain "Mock LLM-generated section content"
        self.assertEqual(content.count("Mock LLM-generated section content"), 6)
        self.assertIn("## 1. Introduction", content) # Check a section title
        self.assertIn("## 6. Conclusion", content) # Check another section title

    def test_build_document_non_existent_outline(self):
        result = build_document("non_existent_test_outline", self.sample_phase_context, self.llm)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
