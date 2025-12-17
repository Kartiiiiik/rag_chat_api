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
def get_chat_model():
    return genai.GenerativeModel("gemini-1.5-flash")




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