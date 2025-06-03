import unittest
from src.core.data_structures import Question, Answer, PhaseContext, DocumentSection, DocumentOutline, store_answer, get_answers, clear_answers

class TestCoreDataStructures(unittest.TestCase):

    def test_question_creation(self):
        q = Question(id="q1", text="What is your name?")
        self.assertEqual(q.id, "q1")
        self.assertEqual(q.text, "What is your name?")
        self.assertEqual(q.metadata, {})

    def test_answer_creation(self):
        a = Answer(question_id="q1", text="My name is Jules.")
        self.assertEqual(a.question_id, "q1")
        self.assertEqual(a.text, "My name is Jules.")

    def test_phase_context_creation(self):
        history = [Answer("q1", "Ans1")]
        pc = PhaseContext(current_phase="intro", history=history, additional_context={"key": "value"})
        self.assertEqual(pc.current_phase, "intro")
        self.assertEqual(len(pc.history), 1)
        self.assertEqual(pc.additional_context["key"], "value")

    def test_document_section_creation(self):
        ds = DocumentSection(id="s1", title="Section 1", content="Content here", generation_prompt_template="Prompt")
        self.assertEqual(ds.id, "s1")
        self.assertEqual(ds.title, "Section 1")

    def test_document_outline_creation(self):
        sections = [DocumentSection(id="s1", title="S1")]
        do = DocumentOutline(title="DocTitle", file_name_template="file.md", sections=sections)
        self.assertEqual(do.title, "DocTitle")
        self.assertEqual(len(do.sections), 1)

    def test_answer_storage(self):
        session_id = "test_session_ds"
        clear_answers(session_id) # Ensure clean state

        a1 = Answer("q1", "Answer 1")
        a2 = Answer("q2", "Answer 2")

        store_answer(session_id, a1)
        store_answer(session_id, a2)

        retrieved_answers = get_answers(session_id)
        self.assertEqual(len(retrieved_answers), 2)
        self.assertEqual(retrieved_answers[0].text, "Answer 1")
        self.assertEqual(retrieved_answers[1].text, "Answer 2")

        clear_answers(session_id)
        self.assertEqual(len(get_answers(session_id)), 0)

    def test_to_dict_methods(self):
        q = Question(id="q1", text="Q")
        self.assertTrue("id" in q.to_dict())
        a = Answer(question_id="q1", text="A")
        self.assertTrue("question_id" in a.to_dict())
        pc = PhaseContext(current_phase="test", history=[a])
        self.assertTrue("current_phase" in pc.to_dict())
        self.assertEqual(len(pc.to_dict()["history"]), 1)
        ds = DocumentSection(id="ds1", title="DSTitle")
        self.assertTrue("id" in ds.to_dict())
        do = DocumentOutline(title="DOTitle", file_name_template="do.md", sections=[ds])
        self.assertTrue("title" in do.to_dict())
        self.assertEqual(len(do.to_dict()["sections"]), 1)

if __name__ == '__main__':
    unittest.main()
