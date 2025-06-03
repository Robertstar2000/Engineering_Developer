from dataclasses import dataclass, field, asdict # Add asdict
from typing import Any, List, Dict

# ... (Question, Answer dataclasses remain the same) ...

@dataclass
class Question:
    id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)

@dataclass
class Answer:
    question_id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)

@dataclass
class PhaseContext:
    current_phase: str
    history: List[Answer] = field(default_factory=list)
    additional_context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        # Ensure history items are also dicts if they are custom objects
        return {
            "current_phase": self.current_phase,
            "history": [h.to_dict() for h in self.history],
            "additional_context": self.additional_context,
        }

# ... (DocumentSection, DocumentOutline, and answer store functions remain the same) ...
@dataclass
class DocumentSection:
    id: str
    title: str
    content: str = ""
    # Defines the prompt to be used for generating this section,
    # can include placeholders for context from answers.
    generation_prompt_template: str = ""

    def to_dict(self):
        return asdict(self)

@dataclass
class DocumentOutline:
    title: str
    file_name_template: str # e.g., "{project_name}_proposal.md"
    sections: List[DocumentSection] = field(default_factory=list)
    # Global prompt or context for the entire document generation, if needed
    document_generation_context_prompt: str = ""

    def to_dict(self):
        return {
            "title": self.title,
            "file_name_template": self.file_name_template,
            "sections": [s.to_dict() for s in self.sections],
            "document_generation_context_prompt": self.document_generation_context_prompt
        }
# Simple in-memory store for answers
# In a real application, this would be a database or a more robust storage solution.
_answer_store: Dict[str, List[Answer]] = {} # Stores answers per session or user_id

def store_answer(session_id: str, answer: Answer):
    if session_id not in _answer_store:
        _answer_store[session_id] = []
    _answer_store[session_id].append(answer)

def get_answers(session_id: str) -> List[Answer]:
    return _answer_store.get(session_id, [])

def clear_answers(session_id: str):
    if session_id in _answer_store:
        del _answer_store[session_id]
