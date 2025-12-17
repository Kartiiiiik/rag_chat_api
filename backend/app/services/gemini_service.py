import google.generativeai as genai
import time
from google.api_core import exceptions
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from app.core.config import GEMINI_API_KEY
from functools import lru_cache
from typing import List
import logging
import asyncio

logger = logging.getLogger(__name__)

genai.configure(api_key=GEMINI_API_KEY)

# Global rate limiter state
_last_request_time = 0
_min_request_interval = 1.0  # Minimum seconds between requests


def _rate_limit():
    """Simple rate limiter to prevent overwhelming the API"""
    global _last_request_time
    current_time = time.time()
    time_since_last = current_time - _last_request_time
    
    if time_since_last < _min_request_interval:
        sleep_time = _min_request_interval - time_since_last
        logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
        time.sleep(sleep_time)
    
    _last_request_time = time.time()


@lru_cache
def get_embedding_model():
    return "models/embedding-001"


@lru_cache
def get_chat_model():
    return genai.GenerativeModel("gemini-1.5-flash")


@retry(
    retry=retry_if_exception_type(
        (exceptions.ResourceExhausted, exceptions.ServiceUnavailable)
    ),
    wait=wait_exponential(multiplier=2, min=4, max=30),
    stop=stop_after_attempt(5),
)
def get_embedding(text: str, task_type: str = "retrieval_document") -> List[float]:
    if not text or not text.strip():
        raise ValueError("Cannot embed empty text")
    
    _rate_limit()
    
    try:
        result = genai.embed_content(
            model=get_embedding_model(),
            content=text,
            task_type=task_type,
        )
        return result["embedding"]
    except exceptions.InvalidArgument as e:
        raise ValueError(f"Invalid input to Gemini: {e}")
    except exceptions.ResourceExhausted as e:
        logger.warning(f"Rate limit hit in get_embedding: {e}")
        raise
    except Exception as e:
        raise RuntimeError(f"Embedding failed: {e}")


def _embed_single_batch_no_retry(model: str, batch: List[str], task_type: str):
    """Single batch embedding WITHOUT retry - let caller handle retries"""
    _rate_limit()
    return genai.embed_content(
        model=model,
        content=batch,
        task_type=task_type,
    )


def _embed_texts_individually(texts: List[str], task_type: str) -> List[List[float]]:
    """Fallback: embed each text individually with aggressive rate limiting"""
    logger.info(f"Falling back to individual embeddings for {len(texts)} texts")
    embeddings = []
    
    for idx, text in enumerate(texts):
        if not text or not text.strip():
            logger.warning(f"Skipping empty text at index {idx}")
            # Return a zero vector or handle as needed
            # For now, we'll skip and the caller needs to handle
            continue
        
        try:
            logger.debug(f"Embedding text {idx + 1}/{len(texts)}")
            embedding = get_embedding(text, task_type)
            embeddings.append(embedding)
            
            # Extra delay between individual requests
            if idx < len(texts) - 1:
                time.sleep(2.0)
                
        except Exception as e:
            logger.error(f"Failed to embed text {idx}: {e}")
            raise RuntimeError(f"Individual embedding failed at index {idx}: {e}")
    
    return embeddings


def get_batch_embeddings(
    texts: List[str], 
    task_type: str = "retrieval_document",
    batch_size: int = 10,  # Very conservative
    delay_between_batches: float = 3.0,  # Longer delay
    max_retries: int = 3
) -> List[List[float]]:
    """
    Get embeddings for multiple texts with aggressive rate limiting.
    Falls back to individual embedding if batch fails.
    """
    if not texts:
        return []
    
    # Filter out empty texts
    valid_texts = [(idx, text) for idx, text in enumerate(texts) if text and text.strip()]
    
    if not valid_texts:
        logger.warning("No valid texts to embed")
        return []
    
    # Extract just the texts for processing
    texts_to_embed = [text for _, text in valid_texts]
    
    logger.info(f"Embedding {len(texts_to_embed)} texts in batches of {batch_size}")
    
    # Try batch processing with retries
    for attempt in range(max_retries):
        try:
            all_embeddings = []
            total_batches = (len(texts_to_embed) + batch_size - 1) // batch_size
            
            logger.info(f"Attempt {attempt + 1}/{max_retries}: Processing {total_batches} batches")
            
            for batch_idx in range(0, len(texts_to_embed), batch_size):
                batch = texts_to_embed[batch_idx : batch_idx + batch_size]
                current_batch_num = (batch_idx // batch_size) + 1
                
                logger.info(f"Processing batch {current_batch_num}/{total_batches}")
                
                # Delay between batches
                if batch_idx > 0:
                    time.sleep(delay_between_batches)
                
                try:
                    result = _embed_single_batch_no_retry(
                        get_embedding_model(), 
                        batch, 
                        task_type
                    )
                    
                    batch_embeddings = result.get("embedding") or result.get("embeddings")
                    
                    if not batch_embeddings:
                        raise ValueError(f"No embeddings in response for batch {current_batch_num}")
                    
                    if len(batch_embeddings) != len(batch):
                        raise ValueError(
                            f"Expected {len(batch)} embeddings, got {len(batch_embeddings)}"
                        )
                    
                    all_embeddings.extend(batch_embeddings)
                    logger.info(f"✓ Batch {current_batch_num}/{total_batches} complete")
                    
                except exceptions.ResourceExhausted as e:
                    logger.warning(f"Rate limit hit on batch {current_batch_num}: {e}")
                    
                    # Wait longer and retry this specific batch
                    wait_time = (attempt + 1) * 10
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    
                    # Retry this batch once
                    try:
                        result = _embed_single_batch_no_retry(
                            get_embedding_model(), 
                            batch, 
                            task_type
                        )
                        batch_embeddings = result.get("embedding") or result.get("embeddings")
                        all_embeddings.extend(batch_embeddings)
                        logger.info(f"✓ Batch {current_batch_num} succeeded on retry")
                    except exceptions.ResourceExhausted:
                        logger.error(f"Batch {current_batch_num} failed again, will retry with smaller batches")
                        raise  # Let outer retry handle it
            
            logger.info(f"✓ Successfully embedded all {len(all_embeddings)} texts")
            return all_embeddings
            
        except exceptions.ResourceExhausted as e:
            logger.warning(f"Attempt {attempt + 1} failed with rate limit: {e}")
            
            if attempt < max_retries - 1:
                # Reduce batch size and increase delay
                batch_size = max(1, batch_size // 2)
                delay_between_batches = min(10.0, delay_between_batches * 1.5)
                wait_time = (attempt + 1) * 15
                
                logger.info(f"Retrying with batch_size={batch_size}, delay={delay_between_batches}s after {wait_time}s wait")
                time.sleep(wait_time)
            else:
                # Final attempt: fall back to individual embeddings
                logger.warning("All batch attempts exhausted, falling back to individual embeddings")
                time.sleep(30)  # Long wait before individual processing
                return _embed_texts_individually(texts_to_embed, task_type)
        
        except Exception as e:
            logger.error(f"Unexpected error in batch processing: {e}")
            if attempt == max_retries - 1:
                # Last resort: try individual
                logger.info("Falling back to individual embeddings due to error")
                time.sleep(10)
                return _embed_texts_individually(texts_to_embed, task_type)
            time.sleep(5)
    
    # Should not reach here, but just in case
    raise RuntimeError("Failed to get embeddings after all attempts")


@retry(
    retry=retry_if_exception_type(
        (exceptions.ResourceExhausted, exceptions.ServiceUnavailable)
    ),
    wait=wait_exponential(multiplier=2, min=4, max=30),
    stop=stop_after_attempt(5),
)
def generate_response(prompt: str) -> str:
    _rate_limit()
    
    try:
        model = get_chat_model()
        response = model.generate_content(prompt)
        return response.text or ""
    except exceptions.InvalidArgument as e:
        raise ValueError(f"Invalid input to Gemini: {e}")
    except exceptions.ResourceExhausted as e:
        logger.warning(f"Rate limit hit in generate_response: {e}")
        raise
    except Exception as e:
        raise RuntimeError(f"Generation failed: {e}")


@retry(
    retry=retry_if_exception_type(
        (exceptions.ResourceExhausted, exceptions.ServiceUnavailable)
    ),
    wait=wait_exponential(multiplier=2, min=4, max=30),
    stop=stop_after_attempt(5),
)
async def generate_response_stream(prompt: str):
    _rate_limit()
    
    try:
        model = get_chat_model()
        response = model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except exceptions.InvalidArgument as e:
        yield f"\n[Error: Invalid input to Gemini: {e}]"
    except exceptions.ResourceExhausted as e:
        logger.warning(f"Rate limit hit in generate_response_stream: {e}")
        yield f"\n[Error: Rate limit exceeded. Please try again in a moment.]"
    except Exception as e:
        yield f"\n[Error generating response: {e}]"