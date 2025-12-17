import logging
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import torch
from functools import lru_cache

logger = logging.getLogger(__name__)

class SentenceTransformerService:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SentenceTransformerService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._model is None:
            self._load_model()

    def _load_model(self):
        try:
            logger.info("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
            # Automatically uses CUDA if available, otherwise CPU
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")
            
            self._model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise RuntimeError(f"Could not load embedding model: {e}")

    def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        """
        try:
            if not text or not text.strip():
                raise ValueError("Cannot embed empty text")
            
            # encode returns a numpy array by default, convert to list
            embedding = self._model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def get_embeddings(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using batch processing.
        Includes fallback to individual processing on error.
        """
        if not texts:
            return []
            
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            logger.warning("No valid texts provided for embedding")
            return []
            
        try:
            logger.info(f"Generating embeddings for {len(valid_texts)} texts with batch_size={batch_size}")
            
            embeddings = self._model.encode(
                valid_texts, 
                batch_size=batch_size, 
                convert_to_tensor=False, 
                show_progress_bar=False
            )
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Error extracting embeddings in batch: {e}")
            logger.info("Falling back to individual embedding generation")
            
            # Fallback: Process one by one
            results = []
            for i, text in enumerate(valid_texts):
                try:
                    results.append(self.get_embedding(text))
                except Exception as inner_e:
                    logger.error(f"Failed to embed text at index {i} during fallback: {inner_e}")
                    raise inner_e
            return results

@lru_cache()
def get_embedding_service():
    return SentenceTransformerService()
