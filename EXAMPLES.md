# QuizGPT Examples

Practical examples demonstrating QuizGPT features and capabilities.

## Basic Examples

### Example 1: Simple Text-to-Quiz

```python
from quizgpt import QuizGPT
import json

# Initialize generator
generator = QuizGPT(api_key="sk-...")

# Your content
content = """
Python is a high-level, interpreted programming language created by Guido van Rossum.
It emphasizes code readability and simplicity. Python supports multiple programming paradigms
including procedural, object-oriented, and functional programming.
"""

# Generate quiz
result = generator.generate_quiz(
    input_text=content,
    difficulty="medium"
)

# Display results
print(f"Generated {len(result['quiz'])} questions\n")
print("Summary:", result['short'])
print("\nSample Question:")
q = result['quiz'][0]
print(f"Q: {q['question']}")
print(f"Options: {q['options']}")
print(f"Answer: {q['answer']}")
print(f"Explanation: {q['description']}")
```

### Example 2: Quiz from Web Article

```python
from quizgpt import QuizGPT

generator = QuizGPT(api_key="sk-...")

# Generate from Wikipedia
result = generator.generate_quiz(
    input_text="https://en.wikipedia.org/wiki/Artificial_intelligence",
    difficulty="hard",
    n_questions=25
)

print(f"Generated {len(result['quiz'])} questions from Wikipedia")
```

### Example 3: YouTube Transcript Quiz

```python
from quizgpt import QuizGPT

generator = QuizGPT(api_key="sk-...")

# Generate from YouTube video
result = generator.generate_quiz(
    input_text="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    difficulty="easy",
    n_questions=20
)

print(f"Generated {len(result['quiz'])} questions from video transcript")
```

---

## Intermediate Examples

### Example 4: Difficulty Progression

Create quizzes at different difficulty levels from the same content:

```python
from quizgpt import QuizGPT
import json

content = open('chapter_content.txt').read()

results = {}
for difficulty in ['easy', 'medium', 'hard']:
    print(f"Generating {difficulty} quiz...")
    
    generator = QuizGPT(api_key="sk-...", n_questions=30)
    result = generator.generate_quiz(
        input_text=content,
        difficulty=difficulty
    )
    
    results[difficulty] = result['quiz']
    
    # Save to file
    with open(f'quiz_{difficulty}.json', 'w') as f:
        json.dump(result['quiz'], f, indent=2)
    
    print(f"✓ Generated {len(result['quiz'])} {difficulty} questions")

print("\nAll difficulty levels completed!")
```

### Example 5: Large Scale Generation

Generate 500 questions from a textbook chapter:

```python
from quizgpt import QuizGPT
import json
import time

# Large content (e.g., entire chapter)
content = open('biology_chapter.txt').read()

print("Generating 500 questions... this may take a few minutes")
start = time.time()

generator = QuizGPT(
    api_key="sk-...",
    n_questions=500,
    max_workers=4  # Use 4 concurrent threads
)

result = generator.generate_quiz(
    input_text=content,
    difficulty="medium",
    enable_deduplication=True
)

elapsed = time.time() - start

print(f"\n✓ Generated {len(result['quiz'])} unique questions")
print(f"⏱️  Time: {elapsed:.1f} seconds ({elapsed/len(result['quiz']):.2f}s per question)")
print(f"\nSummary: {result['short']}")

# Save results
with open('biology_questions_500.json', 'w') as f:
    json.dump(result['quiz'], f, indent=2)

# Generate statistics
print(f"\nStatistics:")
print(f"- Total questions: {len(result['quiz'])}")
print(f"- Questions with answer_number: {sum(1 for q in result['quiz'] if 'answer_number' in q)}")
print(f"- Average options per question: {sum(len(q['options']) for q in result['quiz']) / len(result['quiz']):.1f}")
```

### Example 6: Question Deduplication

Manually deduplicate questions:

```python
from quizgpt import QuestionDeduplicator
import json

# Load questions from file
with open('raw_questions.json', 'r') as f:
    questions = json.load(f)

print(f"Starting with {len(questions)} questions")

# Deduplicate
deduplicator = QuestionDeduplicator(
    api_key="sk-...",
    similarity_threshold=0.85  # Stricter threshold
)

unique_questions = deduplicator.deduplicate(
    questions=questions,
    target_count=100
)

print(f"After deduplication: {len(unique_questions)} unique questions")

# Save deduplicated questions
with open('unique_questions.json', 'w') as f:
    json.dump(unique_questions, f, indent=2)
```

### Example 7: Topic-Based Organization

Extract topics and generate targeted questions:

```python
from quizgpt import DimensionExtractor, QuizGPT
import json

content = open('science_textbook.txt').read()

# Extract main topics
extractor = DimensionExtractor(api_key="sk-...")
topics = extractor.extract_dimensions(content, n_dimensions=5)

print(f"Main topics in content: {topics}")

# Generate questions per topic
all_questions = []

for topic in topics:
    print(f"\nGenerating questions for: {topic}")
    
    generator = QuizGPT(api_key="sk-...", n_questions=20)
    result = generator.generate_quiz(
        input_text=content,
        difficulty="medium"
    )
    
    # Tag questions with topic
    for q in result['quiz']:
        q['topic'] = topic
    
    all_questions.extend(result['quiz'])

# Save organized questions
with open('questions_by_topic.json', 'w') as f:
    json.dump(all_questions, f, indent=2)

print(f"\n✓ Generated {len(all_questions)} total questions across {len(topics)} topics")
```

---

## Advanced Examples

### Example 8: Assessment Bank Creation

Create a comprehensive question bank for assessments:

```python
from quizgpt import QuizGPT
import json
from datetime import datetime

# Source materials
chapters = {
    'chapter_1.txt': 'Introduction to Biology',
    'chapter_2.txt': 'Cell Structure and Function',
    'chapter_3.txt': 'Genetics and Heredity',
}

assessment_bank = {
    'metadata': {
        'subject': 'Biology 101',
        'created': datetime.now().isoformat(),
        'total_questions': 0,
        'sources': list(chapters.values())
    },
    'questions': []
}

for filepath, chapter_name in chapters.items():
    print(f"Processing: {chapter_name}")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Generate 100 questions per chapter
    generator = QuizGPT(
        api_key="sk-...",
        n_questions=100,
        max_workers=4
    )
    
    result = generator.generate_quiz(
        input_text=content,
        difficulty="medium",
        enable_deduplication=True
    )
    
    # Add metadata
    for q in result['quiz']:
        q['chapter'] = chapter_name
        q['difficulty'] = 'medium'
    
    assessment_bank['questions'].extend(result['quiz'])
    assessment_bank['metadata']['total_questions'] = len(assessment_bank['questions'])

# Save assessment bank
with open('assessment_bank.json', 'w') as f:
    json.dump(assessment_bank, f, indent=2)

print(f"\n✓ Created assessment bank with {assessment_bank['metadata']['total_questions']} questions")
```

### Example 9: Multi-Language Support (Using APIs)

Generate quizzes, then translate them:

```python
from quizgpt import QuizGPT
import json
import openai

def translate_text(text, target_language, api_key):
    """Translate text to target language using OpenAI"""
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Translate to {target_language}:\n{text}"
        }],
        max_tokens=500
    )
    return response.choices[0].message.content

# Generate English quiz
api_key = "sk-..."
generator = QuizGPT(api_key=api_key, n_questions=50)
english_quiz = generator.generate_quiz(
    input_text="Your content...",
    difficulty="medium"
)

# Translate to Spanish
print("Translating to Spanish...")
spanish_quiz = []
for q in english_quiz['quiz']:
    translated_q = q.copy()
    translated_q['question'] = translate_text(q['question'], 'Spanish', api_key)
    translated_q['options'] = [
        translate_text(opt, 'Spanish', api_key) 
        for opt in q['options']
    ]
    translated_q['language'] = 'es'
    spanish_quiz.append(translated_q)

# Save
with open('quiz_spanish.json', 'w') as f:
    json.dump(spanish_quiz, f, indent=2, ensure_ascii=False)

print("✓ Spanish translation completed")
```

### Example 10: Real-Time Quiz Performance Monitoring

Track quiz generation performance:

```python
from quizgpt import QuizGPT
import time
import json
from statistics import mean, stdev

performance_metrics = {
    'runs': [],
    'summary': {}
}

# Run multiple generations to track performance
for i in range(3):
    print(f"Run {i+1}/3...")
    
    metrics = {
        'run_number': i + 1,
        'n_questions': 100,
        'timestamps': {}
    }
    
    start_total = time.time()
    
    generator = QuizGPT(api_key="sk-...", n_questions=100, max_workers=4)
    
    start_gen = time.time()
    result = generator.generate_quiz(
        input_text="Long content...",
        difficulty="medium",
        enable_deduplication=True
    )
    metrics['timestamps']['generation'] = time.time() - start_gen
    metrics['questions_generated'] = len(result['quiz'])
    metrics['total_time'] = time.time() - start_total
    
    performance_metrics['runs'].append(metrics)

# Calculate summary statistics
times = [r['total_time'] for r in performance_metrics['runs']]
performance_metrics['summary'] = {
    'avg_time': mean(times),
    'min_time': min(times),
    'max_time': max(times),
    'stdev': stdev(times) if len(times) > 1 else 0
}

print("\nPerformance Summary:")
print(f"Average time: {performance_metrics['summary']['avg_time']:.2f}s")
print(f"Range: {performance_metrics['summary']['min_time']:.2f}s - {performance_metrics['summary']['max_time']:.2f}s")

with open('performance_metrics.json', 'w') as f:
    json.dump(performance_metrics, f, indent=2)
```

---

## Tips & Tricks

### 1. Optimize for Speed
```python
# Use fewer questions initially for testing
generator = QuizGPT(n_questions=10)  # Fast

# Increase workers for larger requests
generator = QuizGPT(n_questions=500, max_workers=8)

# Disable deduplication if quality isn't critical
result = generator.generate_quiz(..., enable_deduplication=False)
```

### 2. Handle Errors Gracefully
```python
try:
    result = generator.generate_quiz(input_text=content)
except ValueError as e:
    print(f"Invalid input: {e}")
    # Fall back to smaller request
    result = generator.generate_quiz(input_text=content[:1000])
```

### 3. Cache Generated Quizzes
```python
import json
import hashlib

def get_or_create_quiz(content, difficulty, cache_dir='cache'):
    # Generate cache key
    key = hashlib.md5(f"{content}{difficulty}".encode()).hexdigest()
    cache_file = f"{cache_dir}/{key}.json"
    
    # Check cache
    try:
        with open(cache_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        pass
    
    # Generate and cache
    generator = QuizGPT(api_key="sk-...")
    result = generator.generate_quiz(content, difficulty=difficulty)
    
    with open(cache_file, 'w') as f:
        json.dump(result, f)
    
    return result
```

### 4. Batch Process Multiple Contents
```python
from pathlib import Path

contents_dir = Path('course_materials')
all_quizzes = []

for chapter_file in contents_dir.glob('*.txt'):
    with open(chapter_file, 'r') as f:
        content = f.read()
    
    generator = QuizGPT(api_key="sk-...", n_questions=50)
    result = generator.generate_quiz(content)
    
    all_quizzes.append({
        'chapter': chapter_file.stem,
        'quiz': result['quiz']
    })

with open('all_quizzes.json', 'w') as f:
    json.dump(all_quizzes, f, indent=2)
```

---

## Common Use Cases

### 📚 Educational Platform Integration
Generate quizzes programmatically for online learning platforms

### 📝 Assessment Creation
Build question banks for exams and assessments

### 🎓 Automated Testing
Create tests for software documentation and tutorials

### 🔍 Content Verification
Generate questions to validate content understanding

### 📊 Knowledge Gap Analysis
Identify learning gaps through diverse questioning

---

**For more information, see the [main README](README.md) or [API Reference](README.md#-api-reference)**
