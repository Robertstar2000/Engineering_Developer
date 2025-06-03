import unittest
from src.document_generator.outlines import get_document_outline, EXAMPLE_OUTLINE_TEMPLATES
from src.core.data_structures import DocumentOutline, DocumentSection

class TestDocumentOutlines(unittest.TestCase):

    def test_get_existing_outline(self):
        outline = get_document_outline("project_proposal")
        self.assertIsNotNone(outline)
        self.assertIsInstance(outline, DocumentOutline)
        self.assertEqual(outline.title, "Project Proposal")
        self.assertTrue(len(outline.sections) > 0)
        self.assertIsInstance(outline.sections[0], DocumentSection)
        self.assertTrue(outline.sections[0].generation_prompt_template) # Check prompt exists

    def test_get_non_existent_outline(self):
        outline = get_document_outline("non_existent_dummy_outline")
        self.assertIsNone(outline)

    def test_all_example_outlines_loadable(self):
        for name in EXAMPLE_OUTLINE_TEMPLATES.keys():
            outline = get_document_outline(name)
            self.assertIsNotNone(outline, f"Failed to load example outline: {name}")
            self.assertEqual(outline.title, EXAMPLE_OUTLINE_TEMPLATES[name]["title"])

if __name__ == '__main__':
    unittest.main()
