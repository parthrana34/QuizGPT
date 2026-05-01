# Changelog

All notable changes to this project will be documented in this file.

## [3.4.3] - 2026-04-30

### Changed
- Updated README and dimension handling with recent improvements

## [3.4.2] - 2026-04-28

### Changed
- Updated package description to emphasize unique quiz generation and 10,000 question capability

## [3.4.1] - 2026-04-27

### Added
- **Option Shuffling**: Multiple choice options are now randomly shuffled for unpredictability
- **Dimension Metadata**: Questions include optional `dimension` and `subdimension` fields for topic organization

### Fixed
- Improved question structure documentation

## [3.4.0] - 2026-04-26

### Added
- **Scalable Question Generation**: Support for generating 10 to 10,000 questions in a single request
- **Intelligent Batching**: Automatic splitting of large requests into LLM-friendly batches (10 questions per request)
- **FAISS-Based Deduplication**: Semantic duplicate removal using OpenAI embeddings and FAISS index
  - Cosine similarity-based matching
  - Configurable similarity threshold
  - Preserves question diversity
- **Dimension Extraction**: Automatic topic/subject extraction from content
  - Flat structure for small requests (≤20 questions)
  - Dimensional structure for medium requests (20-100 questions)
  - Hierarchical structure for large requests (>100 questions)
- **Thread-Safe Concurrency**: ThreadPoolExecutor-based parallel processing
  - Configurable number of workers (1-10)
  - No shared mutable state issues
  - Proper exception handling for failed tasks
- **Over-Generation Strategy**: Generate 20% extra questions to account for duplicate removal
- **Automatic Retry Logic**: Intelligently retries if deduplication reduces count below target
- **Enhanced Parsing**: New `QuizParser` module with improved JSON extraction and repair
- **Option Shuffling**: Random shuffling of multiple choice options for unpredictability
- **Dimension Metadata**: Questions include `dimension` and `subdimension` fields when available
- **Modular Architecture**:
  - `deduplicator.py`: FAISS-based semantic deduplication
  - `dimension.py`: Topic extraction and hierarchical organization
  - `parser.py`: Robust response parsing and JSON repair
  - `utils.py`: Batching helpers and distribution functions

### Changed
- **Generator Orchestration**: `generate_quiz()` now handles multi-step pipeline with deduplication
- **Prompt Format**: Enhanced prompts with optional dimension/sub-dimension context
- **Dependency Management**: Added faiss-cpu, scikit-learn, numpy as core dependencies
- **Thread Management**: Replaced multiprocessing.ThreadPool with ThreadPoolExecutor
- **API Parameter**: Changed `thread_workers` to `max_workers` for clarity

### Fixed
- Parser now handles malformed JSON more robustly
- Improved answer index matching with fuzzy matching fallback
- Better error handling for network and API failures

### Dependencies Added
- `faiss-cpu>=1.7.0` - Semantic similarity search
- `scikit-learn>=1.0.0` - Vector normalization
- `numpy>=1.21.0` - Numerical operations

### Breaking Changes
- **Class Method Relocation**: `_find_answer_index` moved from `QuizGPT` to `QuizParser`
- **Parameter Rename**: `thread_workers` → `max_workers`
- **Default n_questions**: Changed from 5 to 10

### Migration Guide
```python
# Old way (v3.3.x)
generator = QuizGPT(thread_workers=2)
result_dict = generator._find_answer_index(...)

# New way (v3.4.0)
generator = QuizGPT(max_workers=2, n_questions=10)
from quizgpt import QuizParser
idx = QuizParser.find_answer_index(...)
```

---

## [3.3.1] - 2026-04-26

### Added
- PyPI badge in README
- Package name clarification in documentation

### Changed
- Updated README with installation and usage examples

---

## [3.3.0] - 2026-04-24

### Added
- OpenAI API v1.0+ support

### Changed
- **Breaking**: Migrated from deprecated `openai.ChatCompletion.create()` to `client.chat.completions.create()`
- **Breaking**: Response access changed from dict notation `response["choices"][0]["message"]["content"]` to attribute notation `response.choices[0].message.content`

### Deprecated
- Support for OpenAI API versions < 1.0.0

---

## [3.2.2] - 2026-04-20

### Initial Public Release
- Basic quiz generation from text, URLs, and YouTube transcripts
- Multiple difficulty levels (easy, medium, hard)
- CLI interface
- Python API interface
- Content summarization

### Features
- Extract content from web pages using beautifulsoup4
- Extract YouTube transcripts using youtube-transcript-api
- Generate multiple choice questions with validation
- Parse and normalize quiz responses
- Support for easy/medium/hard question difficulty levels
- Concise content summarization

---

## Versioning

This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes or significant new features
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

## Future Roadmap

### Planned for v3.5.0
- [ ] Additional question types (True/False, Short Answer, Matching)
- [ ] Caching for repeated content
- [ ] Streaming responses for large generations
- [ ] Custom prompt templates

### Planned for v4.0.0
- [ ] Support for other LLM providers (Claude, Gemini)
- [ ] Fine-tuning support for custom question styles
- [ ] Web interface/dashboard
- [ ] Database integration for question storage

---

For detailed implementation changes, see the [GitHub commit history](https://github.com/your-org/quizgpt/commits).
