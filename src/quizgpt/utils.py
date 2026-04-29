"""
Utility functions for quiz generation including batching helpers.
"""

from typing import List, Tuple, Any, Dict
import logging

logger = logging.getLogger(__name__)

# Constants
MAX_QUESTIONS_PER_REQUEST = 10
OVER_GENERATION_FACTOR = 1.2  # Generate 20% extra to account for duplicates


def validate_n_questions(n_questions: int) -> int:
    """
    Validate and constrain n_questions parameter.
    
    Args:
        n_questions: Requested number of questions
    
    Returns:
        Validated n_questions value
    
    Raises:
        ValueError: If n_questions is out of valid range
    """
    if not isinstance(n_questions, int):
        raise ValueError(f"n_questions must be an integer, got {type(n_questions)}")
    
    if n_questions < 1:
        raise ValueError(f"n_questions must be >= 1, got {n_questions}")
    
    if n_questions > 10000:
        raise ValueError(f"n_questions must be <= 10000, got {n_questions}")
    
    return n_questions


def calculate_batches(
    n_questions: int,
    batch_size: int = MAX_QUESTIONS_PER_REQUEST,
) -> Tuple[int, int]:
    """
    Calculate number of batches and over-generated target.
    
    Args:
        n_questions: Target number of questions
        batch_size: Questions per batch (default 10)
    
    Returns:
        Tuple of (n_batches, target_with_overgen)
    """
    target_with_overgen = int(n_questions * OVER_GENERATION_FACTOR)
    n_batches = (target_with_overgen + batch_size - 1) // batch_size  # Ceiling division
    
    return n_batches, target_with_overgen


def distribute_questions_across_dimensions(
    n_questions: int,
    dimensions: List[str],
    batch_size: int = MAX_QUESTIONS_PER_REQUEST,
) -> Dict[str, int]:
    """
    Distribute question targets across dimensions.
    
    Args:
        n_questions: Total target questions
        dimensions: List of dimension names
        batch_size: Questions per batch
    
    Returns:
        Dictionary mapping dimension -> target question count
    """
    if not dimensions:
        return {}
    
    target_with_overgen = int(n_questions * OVER_GENERATION_FACTOR)
    per_dimension = max(batch_size, target_with_overgen // len(dimensions))
    
    distribution = {}
    remaining = target_with_overgen
    
    for i, dim in enumerate(dimensions):
        if i == len(dimensions) - 1:
            # Last dimension gets the remainder
            distribution[dim] = remaining
        else:
            distribution[dim] = per_dimension
            remaining -= per_dimension
    
    logger.info(
        f"Distributed {target_with_overgen} questions across {len(dimensions)} dimensions"
    )
    return distribution


def distribute_questions_hierarchical(
    n_questions: int,
    dimensions: List[str],
    subdimensions: Dict[str, List[str]],
    batch_size: int = MAX_QUESTIONS_PER_REQUEST,
) -> Dict[str, Dict[str, int]]:
    """
    Distribute questions hierarchically across dimensions and sub-dimensions.
    
    Args:
        n_questions: Total target questions
        dimensions: List of dimension names
        subdimensions: Dict mapping dimension -> list of subdimension names
        batch_size: Questions per batch
    
    Returns:
        Nested dictionary: dimension -> subdimension -> question count
    """
    if not dimensions:
        return {}
    
    target_with_overgen = int(n_questions * OVER_GENERATION_FACTOR)
    
    total_subdims = sum(
        len(subdimensions.get(dim, [])) for dim in dimensions
    )
    
    per_subdim = max(batch_size, target_with_overgen // total_subdims)
    
    distribution = {}
    remaining = target_with_overgen
    
    for dim in dimensions:
        distribution[dim] = {}
        subdims = subdimensions.get(dim, [])
        
        for i, subdim in enumerate(subdims):
            if i == len(subdims) - 1 and dim == dimensions[-1]:
                # Last of last gets remainder
                distribution[dim][subdim] = remaining
            else:
                distribution[dim][subdim] = per_subdim
                remaining -= per_subdim
    
    logger.info(
        f"Distributed {target_with_overgen} questions hierarchically "
        f"({len(dimensions)} dimensions, {total_subdims} sub-dimensions)"
    )
    return distribution


def chunk_items(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.
    
    Args:
        items: List to chunk
        chunk_size: Size of each chunk
    
    Returns:
        List of chunks
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


def flatten_questions(
    batches: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Flatten nested question batches into a single list.
    
    Args:
        batches: List of batch responses (each with 'quiz' key)
    
    Returns:
        Flattened list of questions
    """
    questions = []
    for batch in batches:
        if isinstance(batch, dict) and "quiz" in batch:
            questions.extend(batch.get("quiz", []))
    
    return questions
