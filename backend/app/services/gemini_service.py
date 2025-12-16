import google.generativeai as genai
from app.core.config import GEMINI_API_KEY
from functools import lru_cache
from typing import List

genai.configure(api_key=GEMINI_API_KEY)


@lru_cache
def get_embedding_model():
    return "models/embedding-001"


@lru_cache
def get_chat_model():
    return genai.GenerativeModel("gemini-1.5-flash")


def get_embedding(text: str, task_type: str = "retrieval_document") -> List[float]:
    if not text.strip():
        return []

    try:
        result = genai.embed_content(
            model=get_embedding_model(),
            content=text,
            task_type=task_type,
        )
        return result["embedding"]
    except Exception as e:
        raise RuntimeError(f"Embedding failed: {e}")


def generate_response(prompt: str) -> str:
    try:
        model = get_chat_model()
        response = model.generate_content(prompt)
        return response.text or ""
    except Exception as e:
        raise RuntimeError(f"Generation failed: {e}")


async def generate_response_stream(prompt: str):
    try:
        model = get_chat_model()
        response = model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"\n[Error generating response: {e}]"
