"""
Deduplication module for quiz questions using FAISS and semantic embeddings.

This module provides functionality to remove duplicate or semantically similar
questions from a list of generated questions using OpenAI embeddings and FAISS.
"""

from typing import List, Dict, Any, Optional
import json
import logging

try:
    import faiss
    import numpy as np
except ImportError:
    raise ImportError(
        "FAISS and numpy are required for deduplication. "
        "Install with: pip install faiss-cpu numpy"
    )

import openai

logger = logging.getLogger(__name__)

# Configuration
EMBED_DIM = 1536
SIMILARITY_THRESHOLD = 0.90
EMBED_MODEL = "text-embedding-3-small"


class QuestionDeduplicator:
    """
    Deduplicates questions using semantic embeddings and FAISS similarity search.
    
    Attributes:
        embed_dim: Dimension of embeddings (1536 for text-embedding-3-small)
        similarity_threshold: Cosine similarity threshold for considering duplicates (0-1)
        embed_model: OpenAI embedding model to use
        client: OpenAI client for generating embeddings
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        embed_dim: int = EMBED_DIM,
        similarity_threshold: float = SIMILARITY_THRESHOLD,
        embed_model: str = EMBED_MODEL,
    ):
        """
        Initialize the deduplicator.
        
        Args:
            api_key: OpenAI API key (optional, uses environment variable if not provided)
            embed_dim: Dimension of embeddings
            similarity_threshold: Threshold for considering questions as duplicates
            embed_model: OpenAI embedding model name
        """
        self.embed_dim = embed_dim
        self.similarity_threshold = similarity_threshold
        self.embed_model = embed_model
        self.client = openai.OpenAI(api_key=api_key)
        
    def deduplicate(
        self,
        questions: List[Dict[str, Any]],
        target_count: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate or semantically similar questions.
        
        Args:
            questions: List of question dictionaries with 'question' field
            target_count: Target number of unique questions to return
                         If None, removes all duplicates
        
        Returns:
            List of deduplicated question dictionaries
        
        Raises:
            ValueError: If questions list is empty or invalid
        """
        if not questions:
            logger.warning("No questions provided for deduplication")
            return []
        
        if len(questions) == 1:
            return questions
        
        # Extract question texts
        question_texts = [q.get("question", "") for q in questions]
        
        if not any(question_texts):
            logger.warning("No valid question texts found")
            return []
        
        try:
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(question_texts)} questions")
            embeddings = self._generate_embeddings(question_texts)
            
            # Build FAISS index
            logger.info("Building FAISS index")
            index, normalized_embeddings = self._build_faiss_index(embeddings)
            
            # Find unique questions
            logger.info(f"Deduplicating with threshold {self.similarity_threshold}")
            unique_indices = self._find_unique_questions(
                index,
                normalized_embeddings,
                len(questions),
            )
            
            # Extract unique questions
            unique_questions = [questions[i] for i in unique_indices]
            
            # If target_count specified and we have more, keep best ones
            if target_count and len(unique_questions) > target_count:
                logger.info(
                    f"Limiting to top {target_count} questions "
                    f"(have {len(unique_questions)})"
                )
                unique_questions = unique_questions[:target_count]
            
            logger.info(
                f"Deduplication complete: {len(questions)} → {len(unique_questions)}"
            )
            return unique_questions
            
        except Exception as e:
            logger.error(f"Error during deduplication: {e}")
            raise
    
    def _generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts using OpenAI API.
        
        Args:
            texts: List of text strings to embed
        
        Returns:
            NumPy array of embeddings (shape: [n_texts, embed_dim])
        """
        embeddings = []
        batch_size = 100  # OpenAI batch limit
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = self.client.embeddings.create(
                model=self.embed_model,
                input=batch,
            )
            
            for item in response.data:
                embeddings.append(item.embedding)
        
        return np.array(embeddings, dtype=np.float32)
    
    def _build_faiss_index(
        self,
        embeddings: np.ndarray,
    ) -> tuple[faiss.Index, np.ndarray]:
        """
        Build a FAISS index for similarity search.
        
        Args:
            embeddings: NumPy array of embeddings
        
        Returns:
            Tuple of (FAISS index, normalized embeddings)
        """
        # Normalize embeddings for cosine similarity
        from sklearn.preprocessing import normalize
        normalized = normalize(embeddings, norm="l2").astype(np.float32)
        
        # Create index
        index = faiss.IndexFlatIP(self.embed_dim)  # Inner product on normalized = cosine
        index.add(normalized)
        
        return index, normalized
    
    def _find_unique_questions(
        self,
        index: faiss.Index,
        embeddings: np.ndarray,
        total_questions: int,
    ) -> List[int]:
        """
        Find indices of unique questions by removing near-duplicates.
        
        Args:
            index: FAISS index
            embeddings: Normalized embeddings array
            total_questions: Total number of questions
        
        Returns:
            List of indices of unique questions
        """
        unique_indices = []
        seen = set()
        
        # Query each embedding against index
        for i in range(total_questions):
            if i in seen:
                continue
            
            # Find similar questions
            distances, indices = index.search(
                embeddings[i : i + 1],
                min(10, total_questions),  # Search top k
            )
            
            # Mark as duplicates if similarity > threshold
            for distance, idx in zip(distances[0], indices[0]):
                if distance > self.similarity_threshold and idx != i:
                    seen.add(idx)
            
            unique_indices.append(i)
        
        return unique_indices


def deduplicate_questions(
    questions: List[Dict[str, Any]],
    api_key: Optional[str] = None,
    target_count: Optional[int] = None,
    similarity_threshold: float = SIMILARITY_THRESHOLD,
) -> List[Dict[str, Any]]:
    """
    Convenience function to deduplicate questions.
    
    Args:
        questions: List of question dictionaries
        api_key: OpenAI API key (optional)
        target_count: Target number of unique questions
        similarity_threshold: Cosine similarity threshold for duplicates
    
    Returns:
        Deduplicated list of questions
    """
    deduplicator = QuestionDeduplicator(
        api_key=api_key,
        similarity_threshold=similarity_threshold,
    )
    return deduplicator.deduplicate(questions, target_count=target_count)
