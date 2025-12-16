import google.generativeai as genai
from app.core.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

def get_embedding(text: str, task_type: str = "retrieval_document"):
    result = genai.embed_content(model="models/embedding-001", content=text, task_type=task_type)
    return result["embedding"]

def generate_response(prompt: str):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text

async def generate_response_stream(prompt: str):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt, stream=True)
    for chunk in response:
        if chunk.text:
            yield chunk.text
