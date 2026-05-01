# QuizGPT

[![PyPI version](https://badge.fury.io/py/quizgpt.svg)](https://pypi.org/project/quizgpt/)

**QuizGPT** is a production-grade Python package for generating high-quality quizzes from raw text, web pages, or YouTube video transcripts using OpenAI models. Supports scalable generation of 10 to 10,000 questions with intelligent batching, semantic deduplication, and dimension-based organization.

## 🌟 Key Features

### Core Functionality
- **Content Extraction**: Automatically extracts text from URLs, web pages, YouTube videos, or plain text
- **Multiple Choice Quiz Generation**: Creates MCQ quizzes with configurable difficulty levels (easy/medium/hard)
- **Content Summarization**: Generates concise summaries of source content
- **Flexible Interface**: Python API and command-line interface

### Advanced Features (v3.4.0+)
- **Scalable Generation**: Generate 10 to 10,000 questions in a single request
- **Intelligent Batching**: Automatically splits large question requests into LLM-friendly batches (10 questions per request)
- **Thread-Safe Concurrency**: Uses ThreadPoolExecutor for efficient parallel processing (configurable workers)
- **Semantic Deduplication**: FAISS-based embeddings remove semantic duplicates while preserving variety
- **Dimension-Based Organization**: Automatically extracts and organizes questions by topic:
  - **Flat**: For 10-20 questions
  - **Dimensional**: For 20-100 questions (organizes by main topics)
  - **Hierarchical**: For 100-10,000 questions (organizes by topics and subtopics)
- **Automatic Retry Logic**: Intelligently retries if deduplication reduces count below target
- **Over-Generation Strategy**: Generates 20% extra questions to account for duplicate removal

## 📦 Installation

```bash
pip install quizgpt
```

### Required Dependencies
- Python 3.9+
- OpenAI API key (get one at https://platform.openai.com/api-keys)

### Optional Dependencies for Advanced Features
```bash
# FAISS is included in dependencies, but for GPU acceleration:
pip install faiss-gpu  # instead of faiss-cpu
```

## 🚀 Quick Start

### Generate a Simple Quiz (10 Questions)

```python
from quizgpt import QuizGPT

# Initialize generator
generator = QuizGPT(api_key="sk-...")

# Generate quiz from text
result = generator.generate_quiz(
    input_text="The mitochondria is the powerhouse of the cell...",
    difficulty="medium"
)

print(f"Questions: {len(result['quiz'])}")
print(f"Summary: {result['short']}")

for question in result['quiz'][:3]:
    print(f"\n❓ {question['question']}")
    print(f"   Options: {question['options']}")
    print(f"   Answer: {question['answer']} (#{question['answer_number']})")
```

### Generate from a URL

```python
result = generator.generate_quiz(
    input_text="https://en.wikipedia.org/wiki/Python_(programming_language)"
)
```

### Generate from YouTube

```python
result = generator.generate_quiz(
    input_text="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
)
```

## 🔧 Advanced Usage

### Generate Large-Scale Quizzes (100+ Questions)

```python
from quizgpt import QuizGPT

# Generate 500 questions from content
generator = QuizGPT(
    api_key="sk-...",
    n_questions=500,  # Will auto-organize into dimensions
    max_workers=4     # Use 4 concurrent threads
)

result = generator.generate_quiz(
    input_text="Long article content...",
    difficulty="hard",
    enable_deduplication=True  # Remove semantic duplicates
)

print(f"Generated {len(result['quiz'])} unique questions")
```

### Using Dimension Extractor Directly

```python
from quizgpt import DimensionExtractor

extractor = DimensionExtractor(api_key="sk-...")

# Extract main topics from content
dimensions = extractor.extract_dimensions(
    content="Your long article...",
    n_dimensions=5
)
print(f"Main topics: {dimensions}")

# Extract subtopics within a dimension
subtopics = extractor.extract_subdimensions(
    content="Your long article...",
    dimension="History",
    n_subdimensions=10
)
print(f"Subtopics in History: {subtopics}")
```

### Using Deduplicator Directly

```python
from quizgpt import QuestionDeduplicator

deduplicator = QuestionDeduplicator(
    api_key="sk-...",
    similarity_threshold=0.90  # 0-1, higher = stricter dedup
)

# Remove duplicates from questions
unique_questions = deduplicator.deduplicate(
    questions=your_questions_list,
    target_count=100  # Try to keep exactly 100 questions
)

print(f"Removed {len(your_questions_list) - len(unique_questions)} duplicates")
```

### CLI Usage

```bash
# Basic usage
quizgpt --input "Your text content" --api-key sk-...

# Advanced options
quizgpt \
  --input "https://example.com/article" \
  --api-key sk-... \
  --difficulty hard \
  --question-type mcq \
  --output results.json

# Generate 100 questions and save to file
quizgpt \
  --input "Long article..." \
  --api-key sk-... \
  --output quiz_100_questions.json
```

## 📋 API Reference

### QuizGPT Class

```python
from quizgpt import QuizGPT

generator = QuizGPT(
    api_key=None,           # OpenAI API key (defaults to env var)
    model="gpt-4o-mini",    # LLM model to use
    max_tokens=1200,        # Max tokens per response
    n_questions=10,         # Target number of questions (10-10,000)
    max_workers=4           # Number of concurrent threads
)
```

#### `.generate_quiz()`

```python
result = generator.generate_quiz(
    input_text,              # URL, YouTube URL, or text content (required)
    difficulty="medium",     # "easy", "medium", or "hard"
    question_type="mcq",     # "mcq" for multiple choice
    enable_deduplication=True # Use FAISS deduplication
)

# Returns: {"quiz": [...], "short": "summary"}
# quiz: List of question dicts with keys: question, options, answer, answer_number, description
# short: Concise summary of content
```

### QuizParser Class

```python
from quizgpt import QuizParser

# Parse LLM response into quiz structure
parsed = QuizParser.parse_response(llm_response_text)

# Extract JSON from text
json_str = QuizParser.extract_json(text)

# Find answer index in options list
idx = QuizParser.find_answer_index("Paris", ["London", "Paris", "Rome"])
# Returns: 1
```

**Note:** Options are automatically shuffled during parsing to ensure the correct answer appears in random positions across different quiz generations.

### DimensionExtractor Class

```python
from quizgpt import DimensionExtractor, extract_dimensions, extract_subdimensions

extractor = DimensionExtractor(api_key="sk-...")

# Extract main dimensions/topics from content
dimensions = extractor.extract_dimensions(content, n_dimensions=5)

# Extract sub-dimensions within a dimension
subdimensions = extractor.extract_subdimensions(
    content, 
    dimension="Science",
    n_subdimensions=10
)

# Get full hierarchical structure (auto-detects based on question count)
structure = extractor.get_dimension_structure(
    content,
    n_questions=500
)
```

### QuestionDeduplicator Class

```python
from quizgpt import QuestionDeduplicator

deduplicator = QuestionDeduplicator(
    api_key=None,
    embed_dim=1536,
    similarity_threshold=0.90,
    embed_model="text-embedding-3-small"
)

# Remove semantic duplicates
unique = deduplicator.deduplicate(
    questions,
    target_count=100
)
```

## 📊 Question Structure

Each generated question follows this format:

```python
{
    "question": "What is the capital of France?",
    "options": ["London", "Paris", "Berlin", "Madrid"],  # Randomly shuffled order
    "answer": "Paris",
    "answer_number": 1,  # 0-based index into shuffled options
    "description": "The largest city and capital of France",
    "dimension": "Geography",        # Optional: topic category (for large quizzes)
    "subdimension": "European Capitals"  # Optional: sub-topic (for hierarchical quizzes)
}
```

**Note:** Options are shuffled randomly during processing, so the correct answer (`answer`) appears at different positions (`answer_number`) in each quiz generation for unpredictability.

**Dimension fields:** When generating large quizzes (100+ questions), questions are organized by topics (`dimension`) and subtopics (`subdimension`) for better content coverage and organization.

## 🏗️ Architecture & Algorithms

### Generation Pipeline

```
Input Content
    ↓
Extract Text
    ↓
Plan Distribution (how to organize questions)
    ├─ n_questions ≤ 20: Flat (single batch)
    ├─ 20 < n_questions ≤ 100: Dimensional (by topic)
    └─ n_questions > 100: Hierarchical (by topic + subtopic)
    ↓
Generate Batches (ThreadPoolExecutor, max 10 Q per request)
    ↓
Collect Questions
    ↓
Deduplicate (FAISS + cosine similarity)
    ↓
Ensure Exact Count (retry if needed)
    ↓
Generate Summary
    ↓
Return Results
```

### Deduplication Algorithm

1. **Generate Embeddings**: Use OpenAI's `text-embedding-3-small` (1536-dim)
2. **Build FAISS Index**: Create IndexFlatIP for cosine similarity
3. **Similarity Search**: For each question, find similar questions
4. **Remove Duplicates**: Mark questions similar above threshold as duplicates
5. **Keep First Occurrence**: Preserve diversity

### Over-Generation Strategy

- **Target**: 100 questions
- **Generate**: 120 questions (20% extra)
- **After Dedup**: ~100 unique questions
- **Result**: Always deliver exactly the requested count

## ⚡ Performance

### Benchmarks (Typical Hardware)

| Questions | Time | Threads | Cost (est.) |
|-----------|------|---------|------------|
| 10        | 5-10s | 1       | $0.02      |
| 50        | 15-20s | 4       | $0.10      |
| 100       | 25-35s | 4       | $0.20      |
| 500       | 90-120s | 4       | $1.00      |
| 1000      | 180-240s | 4       | $2.00      |

### Optimization Tips

1. **Increase `max_workers`** for more parallelism (up to 10)
2. **Enable deduplication** to ensure quality (slight time cost)
3. **Use shorter content** for faster processing
4. **Batch multiple requests** instead of single large request

## 🧪 Examples

### Example 1: Educational Quiz from Article

```python
from quizgpt import QuizGPT

content = """
Machine learning is a subset of artificial intelligence. 
It enables computers to learn from data without explicit programming.
Types include supervised learning, unsupervised learning, and reinforcement learning.
"""

generator = QuizGPT(api_key="sk-...", n_questions=20)
result = generator.generate_quiz(content, difficulty="easy")

for q in result["quiz"]:
    print(f"Q: {q['question']}")
    print(f"A: {q['answer']} - {q['description']}")
    print()
```

### Example 2: Large-Scale Assessment

```python
# Generate 1000 questions for a assessment bank
generator = QuizGPT(api_key="sk-...", n_questions=1000, max_workers=8)

result = generator.generate_quiz(
    input_text="https://en.wikipedia.org/wiki/Biology",
    difficulty="hard",
    enable_deduplication=True
)

# Save to file
import json
with open("biology_questions.json", "w") as f:
    json.dump(result["quiz"], f, indent=2)

print(f"Generated {len(result['quiz'])} unique questions")
print(f"Summary: {result['short']}")
```

### Example 3: Multi-Difficulty Quiz Set

```python
from quizgpt import QuizGPT

content = open("textbook_chapter.txt").read()

for difficulty in ["easy", "medium", "hard"]:
    generator = QuizGPT(api_key="sk-...", n_questions=50)
    result = generator.generate_quiz(content, difficulty=difficulty)
    
    with open(f"quiz_{difficulty}.json", "w") as f:
        json.dump(result["quiz"], f)
```

## 🔐 Security

- **API Keys**: Never hardcode API keys. Use environment variables:
  ```bash
  export OPENAI_API_KEY="sk-..."
  python your_script.py
  ```
  Or configure in `.env`:
  ```
  OPENAI_API_KEY=sk-...
  ```

- **Rate Limiting**: OpenAI API has rate limits. Use exponential backoff for retries.

## 🆘 Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'faiss'`
**Solution**: Install with `pip install faiss-cpu` or system dependencies

### Issue: `OPENAI_API_KEY not found`
**Solution**: Set environment variable: `export OPENAI_API_KEY="sk-..."`

### Issue: Low quality questions
**Solution**: 
- Reduce `n_questions` (fewer = more focused)
- Use better source content
- Increase `similarity_threshold` in deduplicator for stricter dedup

### Issue: Too slow for large requests
**Solution**:
- Increase `max_workers` (up to 10)
- Use shorter content chunks
- Consider caching for repeated content

## 📚 Requirements

- Python 3.9 or higher
- OpenAI API key (gpt-4o-mini or gpt-4 compatible)
- FAISS (CPU or GPU)
- scikit-learn
- numpy
- beautifulsoup4
- requests
- validators
- youtube-transcript-api

## 🛠️ Development

### Setup Development Environment

```bash
git clone https://github.com/your-org/quizgpt.git
cd quizgpt
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### Run Tests

```bash
python -m pytest tests/ -v
```

### Build & Publish

```bash
python -m build
python -m twine upload dist/*
```

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests
4. Submit a pull request

## 📞 Support

- **Issues**: Report on GitHub
- **Discussions**: GitHub Discussions for Q&A

## 🎉 Changelog

### v3.4.0 (Latest)
- ✨ **Scalable Generation**: Support for 10-10,000 questions
- ✨ **Intelligent Batching**: Automatic LLM-friendly batch sizes
- ✨ **FAISS Deduplication**: Semantic duplicate removal
- ✨ **Dimension Extraction**: Topic-based organization
- ✨ **Thread-Safe Concurrency**: ThreadPoolExecutor-based parallelism
- 🔧 **Enhanced Prompt Contextualization**: Dimension-aware prompts
- 🐛 **Bug Fixes**: Parser improvements

### v3.3.1
- 📖 README improvements
- 🔧 Minor fixes

### v3.3.0
- 🔄 OpenAI API v1.0+ migration

---

**Made with ❤️ for educators and learners worldwide**

