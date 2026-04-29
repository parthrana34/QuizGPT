"""
Quiz response parsing and normalization module.

Handles parsing LLM responses, extracting JSON, repairing malformed JSON,
and normalizing quiz structures.
"""

import json
import difflib
from typing import List, Dict, Any
import logging
import random

logger = logging.getLogger(__name__)


class QuizParser:
    """
    Parses and normalizes quiz responses from LLM.
    """
    
    @staticmethod
    def parse_response(content: str) -> Dict[str, Any]:
        """
        Parse LLM response into a quiz structure.
        
        Args:
            content: Raw LLM response text
        
        Returns:
            Dictionary with 'quiz' key containing list of questions
        """
        json_text = QuizParser.extract_json(content)
        if not json_text:
            logger.warning("No JSON found in response")
            return {"quiz": []}
        
        response = QuizParser.load_json(json_text)
        return QuizParser.normalize_quiz(response)
    
    @staticmethod
    def extract_json(content: str) -> str:
        """
        Extract first valid JSON object from text.
        
        Args:
            content: Text potentially containing JSON
        
        Returns:
            JSON string or empty string if not found
        """
        start = content.find("{")
        end = content.rfind("}")
        
        if start < 0 or end < 0:
            logger.warning("No JSON braces found in content")
            return ""
        
        return content[start : end + 1]
    
    @staticmethod
    def load_json(json_text: str) -> Dict[str, Any]:
        """
        Load JSON with fallback repair mechanism.
        
        Args:
            json_text: JSON string to parse
        
        Returns:
            Parsed JSON dictionary
        """
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error: {e}, attempting repair")
            return QuizParser.repair_json(json_text)
    
    @staticmethod
    def repair_json(json_text: str) -> Dict[str, Any]:
        """
        Attempt to repair malformed JSON common patterns.
        
        Fixes:
        - Missing commas after "question" and "answer" fields
        - Extra characters that might break parsing
        
        Args:
            json_text: Potentially malformed JSON
        
        Returns:
            Repaired JSON dictionary
        """
        lines = json_text.splitlines()
        normalized_lines = []
        
        for line in lines:
            stripped = line.rstrip()
            
            # Add comma after question/answer if missing
            if (
                ("\"question\"" in stripped or "\"answer\"" in stripped)
                and stripped.endswith(",") is False
                and not stripped.endswith("{")
                and not stripped.endswith("}")
                and not stripped.endswith("[")
                and not stripped.endswith("]")
            ):
                stripped += ","
            
            normalized_lines.append(stripped)
        
        repaired = "\n".join(normalized_lines)
        
        try:
            return json.loads(repaired)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to repair JSON: {e}")
            return {"quiz": []}
    
    @staticmethod
    def normalize_quiz(response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize quiz structure and add computed fields.
        
        Ensures:
        - 'quiz' key exists and is a list
        - Each question has an answer_number field
        - Options are randomly shuffled for unpredictability
        - All required fields are present
        
        Args:
            response: Parsed quiz response
        
        Returns:
            Normalized quiz dictionary
        """
        if "quiz" not in response or not isinstance(response["quiz"], list):
            logger.warning("Response missing 'quiz' key or quiz is not a list")
            return {"quiz": []}
        
        normalized_quiz = []
        
        for i, item in enumerate(response["quiz"]):
            if not isinstance(item, dict):
                logger.warning(f"Quiz item {i} is not a dictionary, skipping")
                continue
            
            # Ensure required fields
            if "question" not in item or "options" not in item or "answer" not in item:
                logger.warning(f"Quiz item {i} missing required fields, skipping")
                continue
            
            # Shuffle options for randomness
            if isinstance(item["options"], list) and len(item["options"]) > 1:
                random.shuffle(item["options"])
            
            # Add answer_number
            if isinstance(item["options"], list) and len(item["options"]) > 0:
                item["answer_number"] = QuizParser.find_answer_index(
                    item["answer"],
                    item["options"],
                )
            else:
                logger.warning(f"Quiz item {i} has invalid options, skipping")
                continue
            
            normalized_quiz.append(item)
        
        return {"quiz": normalized_quiz}
    
    @staticmethod
    def find_answer_index(answer: str, options: List[str]) -> int:
        """
        Find the index of the correct answer in options list.
        
        Uses exact match first, then fuzzy matching via sequence similarity.
        
        Args:
            answer: The correct answer text
            options: List of available options
        
        Returns:
            Index of the best matching option (0-based)
        """
        if not options:
            logger.warning("Options list is empty")
            return 0
        
        normalized_answer = answer.strip().lower()
        
        # Exact match
        for index, option in enumerate(options):
            if normalized_answer == option.strip().lower():
                return index
        
        # Fuzzy match
        best_index = 0
        best_ratio = -1.0
        
        for index, option in enumerate(options):
            ratio = difflib.SequenceMatcher(
                None,
                normalized_answer,
                option.strip().lower(),
            ).ratio()
            
            if ratio > best_ratio:
                best_ratio = ratio
                best_index = index
        
        return best_index


def parse_quiz_response(content: str) -> Dict[str, Any]:
    """
    Convenience function to parse a quiz response.
    
    Args:
        content: Raw LLM response text
    
    Returns:
        Normalized quiz dictionary
    """
    return QuizParser.parse_response(content)
