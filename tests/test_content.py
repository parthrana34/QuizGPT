from quizgpt.content import get_content_text


def test_get_content_text_returns_plain_text():
    text = "This is a test sentence."
    assert get_content_text(text) == text


def test_get_content_text_strips_whitespace():
    text = "   Hello QuizGPT   "
    assert get_content_text(text) == "Hello QuizGPT"
