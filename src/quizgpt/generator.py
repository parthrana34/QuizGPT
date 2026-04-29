"""
Quiz generation module with scalable batched generation and deduplication.

Supports generating 10 to 10,000 questions with intelligent batching,
threading, and semantic deduplication.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional
import json

import openai

from .content import get_content_text
from .prompts import get_prompt
from .parser import QuizParser
from .dimension import DimensionExtractor
from .deduplicator import QuestionDeduplicator
from .utils import (
    validate_n_questions,
    calculate_batches,
    distribute_questions_across_dimensions,
    distribute_questions_hierarchical,
    flatten_questions,
    MAX_QUESTIONS_PER_REQUEST,
    OVER_GENERATION_FACTOR,
)

logger = logging.getLogger(__name__)

DEFAULT_DIFFICULTY = "medium"
OPTION_COUNT = {"easy": 3, "medium": 4, "hard": 5}
DEFAULT_MODEL = "gpt-4o-mini"
MAX_CHUNK_SIZE = 4000


def chunk_text(text: str, max_chars: int = MAX_CHUNK_SIZE) -> List[str]:
    """
    Split text into chunks of maximum size.
    
    Args:
        text: Text to chunk
        max_chars: Maximum characters per chunk
    
    Returns:
        List of text chunks
    """
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    
    return [text[i : i + max_chars] for i in range(0, len(text), max_chars)]


class QuizGPT:
    """
    Advanced quiz generation with batching, threading, and deduplication.
    
    Supports:
    - Large-scale generation (10-10,000 questions)
    - Intelligent batching (10 questions per request)
    - Multi-threaded execution
    - Dimension-based organization
    - Semantic deduplication via FAISS
    
    Attributes:
        api_key: OpenAI API key
        model: Model name for generation
        max_tokens: Max tokens per response
        n_questions: Target number of questions
        max_workers: Max threads for concurrent requests
        client: OpenAI client
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = 1200,
        n_questions: int = 10,
        max_workers: int = 4,
    ):
        """
        Initialize QuizGPT generator.
        
        Args:
            api_key: OpenAI API key (optional)
            model: Model for generation
            max_tokens: Max tokens per response
            n_questions: Target number of questions (10-10,000)
            max_workers: Max concurrent threads
        
        Raises:
            ValueError: If n_questions out of valid range
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.n_questions = validate_n_questions(n_questions)
        self.max_workers = max(1, min(max_workers, 10))
        self.client = openai.OpenAI(api_key=self.api_key)
        
        logger.info(
            f"QuizGPT initialized: model={model}, "
            f"n_questions={self.n_questions}, "
            f"max_workers={self.max_workers}"
        )
    
    def generate_quiz(
        self,
        input_text: str,
        difficulty: str = DEFAULT_DIFFICULTY,
        question_type: str = "mcq",
        enable_deduplication: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a quiz from input content.
        
        Main orchestration method that:
        1. Extracts content
        2. Plans question distribution (flat/dimensional/hierarchical)
        3. Generates batches of questions using threading
        4. Deduplicates via FAISS
        5. Returns exactly n_questions
        
        Args:
            input_text: Content URL or raw text
            difficulty: "easy", "medium", or "hard"
            question_type: "mcq" (multiple choice)
            enable_deduplication: Use FAISS deduplication
        
        Returns:
            Dictionary with 'quiz' (questions) and 'short' (summary)
        """
        try:
            logger.info(f"Starting quiz generation: n_questions={self.n_questions}")
            
            # Extract content
            content = get_content_text(input_text)
            if not content:
                logger.warning("No content extracted")
                return {"quiz": [], "short": ""}
            
            option_count = OPTION_COUNT.get(difficulty.lower(), OPTION_COUNT[DEFAULT_DIFFICULTY])
            
            # Plan distribution of questions
            logger.info("Planning question distribution strategy")
            distribution_plan = self._plan_distribution(content)
            
            # Generate questions
            logger.info(f"Generating questions using {distribution_plan['strategy']} strategy")
            all_questions = self._generate_with_strategy(
                content=content,
                distribution_plan=distribution_plan,
                option_count=option_count,
                question_type=question_type,
            )
            
            # Deduplicate
            if enable_deduplication and len(all_questions) > 0:
                logger.info(f"Deduplicating {len(all_questions)} questions")
                all_questions = self._deduplicate_questions(all_questions)
            
            # Retry if not enough after deduplication
            while len(all_questions) < self.n_questions:
                shortage = self.n_questions - len(all_questions)
                logger.info(f"Shortage detected: {shortage} questions, retrying")
                
                retry_plan = {
                    "strategy": "flat",
                    "n_batches": max(1, shortage // MAX_QUESTIONS_PER_REQUEST + 1),
                }
                retry_questions = self._generate_with_strategy(
                    content=content,
                    distribution_plan=retry_plan,
                    option_count=option_count,
                    question_type=question_type,
                )
                
                if enable_deduplication and retry_questions:
                    retry_questions = self._deduplicate_questions(retry_questions)
                
                all_questions.extend(retry_questions)
                
                if len(all_questions) >= self.n_questions:
                    break
            
            # Ensure exactly n_questions
            final_quiz = all_questions[:self.n_questions]
            
            # Generate summary
            logger.info("Generating content summary")
            summary = self._summarize_content(content)
            
            logger.info(f"Quiz generation complete: {len(final_quiz)} questions")
            return {"quiz": final_quiz, "short": summary}
            
        except Exception as e:
            logger.error(f"Error during quiz generation: {e}", exc_info=True)
            return {"quiz": [], "short": ""}
    
    def _plan_distribution(self, content: str) -> Dict[str, Any]:
        """
        Plan how to distribute question generation.
        
        - n_questions <= 20: Single batch
        - 20 < n_questions <= 100: Multiple dimension-based batches
        - n_questions > 100: Hierarchical dimension/subdimension batches
        
        Args:
            content: Source content
        
        Returns:
            Distribution plan dictionary
        """
        target_with_overgen = int(self.n_questions * OVER_GENERATION_FACTOR)
        n_batches, target = calculate_batches(self.n_questions)
        
        if self.n_questions <= 20:
            logger.info("Using flat distribution strategy")
            return {
                "strategy": "flat",
                "n_batches": n_batches,
            }
        
        if self.n_questions <= 100:
            logger.info("Using dimensional distribution strategy")
            try:
                extractor = DimensionExtractor(api_key=self.api_key)
                structure = extractor.get_dimension_structure(
                    content,
                    self.n_questions,
                )
                
                if structure["structure_type"] == "dimensional":
                    return {
                        "strategy": "dimensional",
                        "dimensions": structure["dimensions"],
                        "questions_per_dimension": structure["questions_per_dimension"],
                        "n_batches": (
                            structure["questions_per_dimension"]
                            // MAX_QUESTIONS_PER_REQUEST + 1
                        ),
                    }
            except Exception as e:
                logger.warning(f"Dimension extraction failed: {e}, falling back to flat")
            
            return {"strategy": "flat", "n_batches": n_batches}
        
        # Hierarchical for large n_questions
        logger.info("Using hierarchical distribution strategy")
        try:
            extractor = DimensionExtractor(api_key=self.api_key)
            structure = extractor.get_dimension_structure(
                content,
                self.n_questions,
            )
            
            if structure["structure_type"] == "hierarchical":
                return {
                    "strategy": "hierarchical",
                    "dimensions": structure["dimensions"],
                    "subdimensions": structure["subdimensions"],
                    "questions_per_subdimension": structure["questions_per_subdimension"],
                    "n_batches": max(1, structure["questions_per_subdimension"] // MAX_QUESTIONS_PER_REQUEST),
                }
        except Exception as e:
            logger.warning(f"Hierarchical extraction failed: {e}, falling back to dimensional")
        
        return {"strategy": "flat", "n_batches": n_batches}
    
    def _generate_with_strategy(
        self,
        content: str,
        distribution_plan: Dict[str, Any],
        option_count: int,
        question_type: str,
    ) -> List[Dict[str, Any]]:
        """
        Generate questions according to distribution strategy.
        
        Args:
            content: Source content (may be chunked)
            distribution_plan: Plan from _plan_distribution()
            option_count: Number of options per question
            question_type: Type of questions ("mcq")
        
        Returns:
            List of generated questions
        """
        strategy = distribution_plan.get("strategy", "flat")
        
        if strategy == "flat":
            return self._generate_flat(
                content,
                distribution_plan.get("n_batches", 1),
                option_count,
                question_type,
            )
        
        elif strategy == "dimensional":
            return self._generate_dimensional(
                content,
                distribution_plan.get("dimensions", [content]),
                distribution_plan.get("questions_per_dimension", 10),
                option_count,
                question_type,
            )
        
        elif strategy == "hierarchical":
            return self._generate_hierarchical(
                content,
                distribution_plan.get("dimensions", []),
                distribution_plan.get("subdimensions", {}),
                distribution_plan.get("questions_per_subdimension", 10),
                option_count,
                question_type,
            )
        
        return []
    
    def _generate_flat(
        self,
        content: str,
        n_batches: int,
        option_count: int,
        question_type: str,
    ) -> List[Dict[str, Any]]:
        """
        Generate questions in flat batches.
        
        Args:
            content: Source content
            n_batches: Number of batches to generate
            option_count: Options per question
            question_type: Question type
        
        Returns:
            List of questions
        """
        tasks = [
            {
                "content": content,
                "n_questions": MAX_QUESTIONS_PER_REQUEST,
                "option_count": option_count,
                "question_type": question_type,
                "batch_id": i,
            }
            for i in range(n_batches)
        ]
        
        return self._execute_generation_tasks(tasks)
    
    def _generate_dimensional(
        self,
        content: str,
        dimensions: List[str],
        questions_per_dimension: int,
        option_count: int,
        question_type: str,
    ) -> List[Dict[str, Any]]:
        """
        Generate questions organized by dimensions.
        
        Args:
            content: Source content
            dimensions: List of dimension names
            questions_per_dimension: Target per dimension
            option_count: Options per question
            question_type: Question type
        
        Returns:
            List of questions
        """
        n_batches_per_dim = max(
            1,
            (questions_per_dimension + MAX_QUESTIONS_PER_REQUEST - 1) // MAX_QUESTIONS_PER_REQUEST
        )
        
        tasks = [
            {
                "content": content,
                "n_questions": min(MAX_QUESTIONS_PER_REQUEST, questions_per_dimension),
                "option_count": option_count,
                "question_type": question_type,
                "dimension": dim,
                "batch_id": f"{dim}_batch{b}",
            }
            for dim in dimensions
            for b in range(n_batches_per_dim)
        ]
        
        return self._execute_generation_tasks(tasks)
    
    def _generate_hierarchical(
        self,
        content: str,
        dimensions: List[str],
        subdimensions: Dict[str, List[str]],
        questions_per_subdimension: int,
        option_count: int,
        question_type: str,
    ) -> List[Dict[str, Any]]:
        """
        Generate questions organized hierarchically.
        
        Args:
            content: Source content
            dimensions: List of dimensions
            subdimensions: Mapping of dimension -> list of subdimensions
            questions_per_subdimension: Target per subdimension
            option_count: Options per question
            question_type: Question type
        
        Returns:
            List of questions
        """
        n_batches = max(
            1,
            (questions_per_subdimension + MAX_QUESTIONS_PER_REQUEST - 1) // MAX_QUESTIONS_PER_REQUEST
        )
        
        tasks = [
            {
                "content": content,
                "n_questions": min(MAX_QUESTIONS_PER_REQUEST, questions_per_subdimension),
                "option_count": option_count,
                "question_type": question_type,
                "dimension": dim,
                "subdimension": subdim,
                "batch_id": f"{dim}_{subdim}_batch{b}",
            }
            for dim in dimensions
            for subdim in subdimensions.get(dim, [])
            for b in range(n_batches)
        ]
        
        return self._execute_generation_tasks(tasks)
    
    def _execute_generation_tasks(
        self,
        tasks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Execute generation tasks concurrently using ThreadPoolExecutor.
        
        Args:
            tasks: List of generation task dictionaries
        
        Returns:
            Flattened list of generated questions
        """
        all_questions = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {
                executor.submit(self._execute_task, task): task
                for task in tasks
            }
            
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    questions = result.get("quiz", [])
                    all_questions.extend(questions)
                    logger.debug(f"Task {task['batch_id']} completed: {len(questions)} questions")
                except Exception as e:
                    logger.error(f"Task {task['batch_id']} failed: {e}")
        
        logger.info(f"All generation tasks complete: {len(all_questions)} questions")
        return all_questions
    
    def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single generation task.
        
        Args:
            task: Task configuration dictionary
        
        Returns:
            Result with 'quiz' key
        """
        content = task["content"]
        n_questions = task["n_questions"]
        option_count = task["option_count"]
        question_type = task["question_type"]
        dimension = task.get("dimension")
        subdimension = task.get("subdimension")
        
        # Build context-aware prompt
        if subdimension:
            prompt_context = (
                f"Dimension: {dimension}\n"
                f"Sub-dimension: {subdimension}\n"
            )
        elif dimension:
            prompt_context = f"Dimension: {dimension}\n"
        else:
            prompt_context = ""
        
        prompt = get_prompt(
            content,
            n_questions,
            option_count,
            question_type,
            context=prompt_context,
        )
        
        response_text = self._send_prompt(prompt)
        result = QuizParser.parse_response(response_text)
        
        # Add dimension metadata to each question
        if result.get("quiz"):
            for question in result["quiz"]:
                if dimension:
                    question["dimension"] = dimension
                if subdimension:
                    question["subdimension"] = subdimension
        
        return result
    
    def _deduplicate_questions(
        self,
        questions: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Deduplicate questions using FAISS embeddings.
        
        Args:
            questions: List of questions to deduplicate
        
        Returns:
            Deduplicated list
        """
        if len(questions) <= 1:
            return questions
        
        try:
            deduplicator = QuestionDeduplicator(api_key=self.api_key)
            return deduplicator.deduplicate(questions, target_count=self.n_questions)
        except Exception as e:
            logger.error(f"Deduplication failed: {e}, keeping all questions")
            return questions
    
    def _send_prompt(self, prompt: str) -> str:
        """
        Send prompt to LLM and get response.
        
        Args:
            prompt: Prompt text
        
        Returns:
            Response text
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You generate high-quality quizzes from content. Always return valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content
    
    def _summarize_content(self, content: str) -> str:
        """
        Generate a summary of the content.
        
        Args:
            content: Content to summarize
        
        Returns:
            Summary text
        """
        prompt = (
            "Summarize the following content concisely in three lines. "
            "Keep the key points clear, eliminate redundancy, and use simple language.\n\n"
            f"CONTENT:\n{content[:2000]}"
        )
        return self._send_prompt(prompt).strip()


def generate_quiz(
    input_text: str,
    api_key: Optional[str] = None,
    difficulty: str = DEFAULT_DIFFICULTY,
    question_type: str = "mcq",
    n_questions: int = 10,
) -> Dict[str, Any]:
    """
    Convenience function to generate a quiz.
    
    Args:
        input_text: Content URL or text
        api_key: OpenAI API key (optional)
        difficulty: Quiz difficulty
        question_type: Question type
        n_questions: Target number of questions (10-10,000)
    
    Returns:
        Dictionary with 'quiz' and 'short' keys
    """
    generator = QuizGPT(api_key=api_key, n_questions=n_questions)
    return generator.generate_quiz(
        input_text,
        difficulty=difficulty,
        question_type=question_type,
    )
