"""
Dimension extraction module for organizing quiz question generation.

This module provides functionality to extract high-level "dimensions" (topics)
and "sub-dimensions" from content to structure large-scale question generation.
"""

from typing import List, Dict, Any, Optional
import json
import logging

import openai

logger = logging.getLogger(__name__)


class DimensionExtractor:
    """
    Extracts dimensions and sub-dimensions from content.
    
    A dimension is a main topic, and sub-dimensions are specific areas within
    that topic. This helps organize question generation across related topics.
    
    Attributes:
        client: OpenAI client for LLM-based extraction
        model: Model to use for extraction
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
    ):
        """
        Initialize the dimension extractor.
        
        Args:
            api_key: OpenAI API key (optional, uses environment variable if not provided)
            model: Model name for extraction
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
    
    def extract_dimensions(
        self,
        content: str,
        n_dimensions: int = 5,
    ) -> List[str]:
        """
        Extract high-level dimensions (main topics) from content.
        
        Use this when n_questions > 20 to organize question generation.
        
        Args:
            content: Content to extract dimensions from
            n_dimensions: Target number of dimensions to extract
        
        Returns:
            List of dimension names (strings)
        """
        if len(content) < 100:
            logger.warning("Content is too short for meaningful dimension extraction")
            return ["General"]
        
        prompt = f"""Analyze the following content and extract {n_dimensions} high-level main topics or dimensions.

CONTENT:
{content[:2000]}

Return ONLY a JSON array of strings with the dimension names.
Example: ["History", "Science", "Technology", "Culture", "Economics"]

Return JSON array only, no other text:"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                max_tokens=500,
                temperature=0.3,
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON array
            try:
                dimensions = json.loads(result_text)
                if isinstance(dimensions, list) and all(
                    isinstance(d, str) for d in dimensions
                ):
                    logger.info(f"Extracted {len(dimensions)} dimensions")
                    return dimensions[:n_dimensions]
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse dimensions JSON: {result_text}")
            
            # Fallback
            return ["General"]
            
        except Exception as e:
            logger.error(f"Error extracting dimensions: {e}")
            return ["General"]
    
    def extract_subdimensions(
        self,
        content: str,
        dimension: str,
        n_subdimensions: int = 10,
    ) -> List[str]:
        """
        Extract sub-dimensions from a specific dimension.
        
        Use this when n_questions > 100 to further organize within each dimension.
        
        Args:
            content: Content to extract from
            dimension: The parent dimension name
            n_subdimensions: Target number of sub-dimensions
        
        Returns:
            List of sub-dimension names (strings)
        """
        prompt = f"""Given the following content, extract {n_subdimensions} specific sub-topics or aspects within the dimension "{dimension}".

CONTENT:
{content[:2000]}

DIMENSION: {dimension}

Return ONLY a JSON array of strings with specific areas/aspects within this dimension.
Example for "Science" dimension: ["Physics", "Chemistry", "Biology", "Astronomy", "Ecology", ...]

Return JSON array only, no other text:"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                max_tokens=500,
                temperature=0.3,
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON array
            try:
                subdimensions = json.loads(result_text)
                if isinstance(subdimensions, list) and all(
                    isinstance(s, str) for s in subdimensions
                ):
                    logger.info(
                        f"Extracted {len(subdimensions)} sub-dimensions for '{dimension}'"
                    )
                    return subdimensions[:n_subdimensions]
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse subdimensions JSON: {result_text}")
            
            # Fallback
            return [f"{dimension} - Aspect {i}" for i in range(n_subdimensions)]
            
        except Exception as e:
            logger.error(f"Error extracting subdimensions: {e}")
            return [f"{dimension} - Aspect {i}" for i in range(n_subdimensions)]
    
    def get_dimension_structure(
        self,
        content: str,
        n_questions: int,
    ) -> Dict[str, Any]:
        """
        Generate a hierarchical structure for question generation.
        
        Determines how to organize questions based on total count:
        - n_questions <= 20: Single batch
        - 20 < n_questions <= 100: Multiple dimensions
        - n_questions > 100: Dimensions with sub-dimensions
        
        Args:
            content: Content to analyze
            n_questions: Total number of questions needed
        
        Returns:
            Dictionary with structure information:
            {
                "structure_type": "flat" | "dimensional" | "hierarchical",
                "dimensions": [...],
                "subdimensions": {...},
                "questions_per_dimension": int,
                "questions_per_subdimension": int
            }
        """
        if n_questions <= 20:
            return {
                "structure_type": "flat",
                "dimensions": ["General"],
                "subdimensions": {},
                "questions_per_dimension": n_questions,
                "questions_per_subdimension": None,
            }
        
        if n_questions <= 100:
            n_dims = max(2, min(10, n_questions // 10))
            dimensions = self.extract_dimensions(content, n_dimensions=n_dims)
            
            logger.info(
                f"Using dimensional structure with {len(dimensions)} dimensions"
            )
            
            return {
                "structure_type": "dimensional",
                "dimensions": dimensions,
                "subdimensions": {},
                "questions_per_dimension": n_questions // len(dimensions),
                "questions_per_subdimension": None,
            }
        
        # Hierarchical structure for large n_questions
        n_dims = max(5, min(20, n_questions // 50))
        dimensions = self.extract_dimensions(content, n_dimensions=n_dims)
        
        n_subdims = max(5, min(15, n_questions // (n_dims * 10)))
        subdimensions = {}
        
        for dim in dimensions:
            subdimensions[dim] = self.extract_subdimensions(
                content,
                dimension=dim,
                n_subdimensions=n_subdims,
            )
        
        logger.info(
            f"Using hierarchical structure with {len(dimensions)} dimensions "
            f"and {n_subdims} sub-dimensions each"
        )
        
        return {
            "structure_type": "hierarchical",
            "dimensions": dimensions,
            "subdimensions": subdimensions,
            "questions_per_dimension": n_questions // len(dimensions),
            "questions_per_subdimension": (
                n_questions // (len(dimensions) * n_subdims)
            ),
        }


def extract_dimensions(
    content: str,
    n_dimensions: int = 5,
    api_key: Optional[str] = None,
) -> List[str]:
    """
    Convenience function to extract dimensions from content.
    
    Args:
        content: Content to analyze
        n_dimensions: Number of dimensions to extract
        api_key: OpenAI API key (optional)
    
    Returns:
        List of dimension names
    """
    extractor = DimensionExtractor(api_key=api_key)
    return extractor.extract_dimensions(content, n_dimensions=n_dimensions)


def extract_subdimensions(
    content: str,
    dimension: str,
    n_subdimensions: int = 10,
    api_key: Optional[str] = None,
) -> List[str]:
    """
    Convenience function to extract sub-dimensions for a dimension.
    
    Args:
        content: Content to analyze
        dimension: Parent dimension name
        n_subdimensions: Number of sub-dimensions to extract
        api_key: OpenAI API key (optional)
    
    Returns:
        List of sub-dimension names
    """
    extractor = DimensionExtractor(api_key=api_key)
    return extractor.extract_subdimensions(
        content,
        dimension=dimension,
        n_subdimensions=n_subdimensions,
    )
