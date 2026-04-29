from quizgpt.generator import QuizGPT, chunk_text
from quizgpt.parser import QuizParser


def test_chunk_text_splits_long_text():
    text = "x" * 8100
    chunks = chunk_text(text, max_chars=4000)
    assert len(chunks) == 3
    assert all(len(chunk) <= 4000 for chunk in chunks)


def test_find_answer_index_exact_match():
    answer = "Paris"
    options = ["London", "Paris", "Rome"]
    assert QuizParser.find_answer_index(answer, options) == 1


def test_find_answer_index_fuzzy_match():
    answer = "paris"
    options = ["London", "Paris", "Rome"]
    assert QuizParser.find_answer_index(answer, options) == 1


def test_normalize_quiz_shuffles_options():
    """Test that options are shuffled during normalization."""
    # Create a mock response with predictable options order
    mock_response = {
        "quiz": [
            {
                "question": "What is the capital of France?",
                "options": ["London", "Paris", "Rome", "Berlin"],  # Paris is at index 1
                "answer": "Paris",
                "description": "The capital city"
            }
        ]
    }
    
    # Normalize the quiz
    result = QuizParser.normalize_quiz(mock_response)
    
    # Check that we have a quiz with shuffled options
    assert len(result["quiz"]) == 1
    question = result["quiz"][0]
    
    # Options should still contain all original options
    assert set(question["options"]) == {"London", "Paris", "Rome", "Berlin"}
    
    # Answer should still be "Paris"
    assert question["answer"] == "Paris"
    
    # answer_number should point to the correct position of "Paris" in shuffled options
    assert question["options"][question["answer_number"]] == "Paris"


def test_normalize_quiz_preserves_metadata():
    """Test that dimension and subdimension metadata is preserved."""
    mock_response = {
        "quiz": [
            {
                "question": "What is the capital of France?",
                "options": ["London", "Paris", "Rome"],
                "answer": "Paris",
                "description": "The capital city",
                "dimension": "Geography",
                "subdimension": "European Capitals"
            }
        ]
    }
    
    result = QuizParser.normalize_quiz(mock_response)
    
    assert len(result["quiz"]) == 1
    question = result["quiz"][0]
    
    # Check that metadata is preserved
    assert question["dimension"] == "Geography"
    assert question["subdimension"] == "European Capitals"
    
    # Check that required fields are still there
    assert question["question"] == "What is the capital of France?"
    assert question["answer"] == "Paris"
    assert "answer_number" in question
