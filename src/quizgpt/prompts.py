def get_prompt(
    text: str,
    n_questions: int,
    n_options: int,
    question_type: str = "mcq",
    context: str = "",
) -> str:
    """
    Generate a prompt for quiz generation.
    
    Args:
        text: Content to create quiz from
        n_questions: Number of questions to generate
        n_options: Number of options per question
        question_type: Type of question ("mcq" for multiple choice)
        context: Optional context (dimension/subdimension info)
    
    Returns:
        Formatted prompt string
    """
    if len(text.strip()) < 50:
        text_type = "shortText"
    else:
        text_type = "longText"

    prompt_templates = {
        "mcq": {
            "shortText": (
                "{context}"
                "Create a quiz with {questions} questions, {options} options, and include the answer with a one-line description. "
                "Provide the output in JSON format so it can be parsed automatically. Each quiz item should include:\n"
                '"question": "Question text",\n'
                '"options": ["option1", "option2", ...],\n'
                '"answer": "Exact answer text matching one option",\n'
                '"description": "Short explanation for the answer"\n\n'
                "CONTENT:\n{content}"
            ),
            "longText": (
                "{context}"
                "Create a quiz with {questions} questions, {options} options, and include the answer with a one-line description. "
                "Provide the output in JSON format so it can be parsed automatically. Each quiz item should include:\n"
                '"question": "Question text",\n'
                '"options": ["option1", "option2", ...],\n'
                '"answer": "Exact answer text matching one option",\n'
                '"description": "Short explanation for the answer"\n\n'
                "CONTENT:\n{content}"
            ),
        }
    }

    template = prompt_templates.get(question_type, prompt_templates["mcq"])[text_type]
    return template.format(context=context, questions=n_questions, options=n_options, content=text)
