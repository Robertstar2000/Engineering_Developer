import uuid
from src.core.data_structures import PhaseContext, Question, Answer
from src.llm.llm_service import LLMService

def generate_dynamic_question(phase_context: PhaseContext, llm_service: LLMService) -> Question:
    """
    Generates a dynamic question using the LLM based on the current phase and context.

    :param phase_context: The current context of the phase, including history.
    :param llm_service: The LLM service client.
    :return: A Question object.
    """

    # Construct the prompt for the LLM
    prompt = f"You are an assistant helping gather information for a document. "
    prompt += f"The current phase is '{phase_context.current_phase}'. "

    if phase_context.history:
        prompt += "So far, the user has provided the following answers: "
        for i, ans in enumerate(phase_context.history):
            prompt += f"Q{i+1}: (ID: {ans.question_id}) A{i+1}: '{ans.text}'. "
    else:
        prompt += "This is the first question in this interaction. "

    if phase_context.additional_context:
        prompt += f"Additional context for this phase: {phase_context.additional_context}. "

    prompt += "Based on this, what is the next single, specific question you should ask the user to gather relevant information? "
    prompt += "The question should be clear and concise. Do not provide any preamble, just the question text."

    # Call the LLM service
    generated_question_text = llm_service.generate_text(prompt=prompt, context=phase_context.to_dict()) # Make context serializable if needed by LLM

    # Create a Question object
    # For simplicity, using a UUID for question ID.
    question_id = str(uuid.uuid4())

    # Basic parsing: LLM response is directly used as question text.
    # More sophisticated parsing might be needed if LLM adds conversational fluff.
    # The prompt tries to mitigate this.

    return Question(id=question_id, text=generated_question_text.strip(), metadata={"phase": phase_context.current_phase})

# Example Usage (optional, for testing this module directly)
if __name__ == '__main__':
    # Mock LLM Service for testing
    mock_llm = LLMService(api_key="test_key_qg")

    # Example PhaseContext
    history_answers = [
        Answer(question_id="prev_q1", text="To build a new project management tool."),
        Answer(question_id="prev_q2", text="My target audience is small businesses.")
    ]
    current_context = PhaseContext(
        current_phase="Feature Definition",
        history=history_answers,
        additional_context={"document_type": "Software Requirements Specification"}
    )

    print(f"Testing with PhaseContext: {current_context.to_dict()}")
    new_question = generate_dynamic_question(phase_context=current_context, llm_service=mock_llm)

    print(f"Generated Question ID: {new_question.id}")
    print(f"Generated Question Text: {new_question.text}")
    print(f"Question Metadata: {new_question.metadata}")

    # Test with empty history
    empty_history_context = PhaseContext(
        current_phase="Initial Inquiry",
        additional_context={"goal": "Understand user needs"}
    )
    print(f"\nTesting with empty history PhaseContext: {empty_history_context.to_dict()}")
    first_question = generate_dynamic_question(phase_context=empty_history_context, llm_service=mock_llm)

    print(f"Generated First Question ID: {first_question.id}")
    print(f"Generated First Question Text: {first_question.text}")
    print(f"Question Metadata: {first_question.metadata}")
