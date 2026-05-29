import os
from typing import List
from google import genai
from dotenv import load_dotenv

load_dotenv()


def get_embedding(text: str, model: str = "text-embedding-004") -> List[float]:
    """
    Generate embedding for a given text using Google Gemini API.
    """
    if not text or not text.strip():
        return []
    
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY is not set in the environment or .env file.")
    
    client = genai.Client(api_key=key)
    
    try:
        if model.startswith("models/"):
            model = model[len("models/"):]
            
        response = client.models.embed_content(
            model=model,
            contents=text
        )
        
        if hasattr(response, "embeddings") and response.embeddings:
            return response.embeddings[0].values
        
        return []
    except Exception as e:
        raise RuntimeError(f"Failed to generate embedding: {e}")
