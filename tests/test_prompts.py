from quizgpt.prompts import get_prompt


def test_get_prompt_contains_json_template():
    prompt = get_prompt("Learning about Python.", 3, 4, "mcq")
    assert "Create a quiz" in prompt
    assert "QUESTION" not in prompt
    assert "options" in prompt
