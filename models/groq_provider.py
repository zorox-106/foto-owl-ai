import os
from functools import lru_cache
import instructor
from openai import OpenAI


@lru_cache(maxsize=1)
def get_groq_client() -> OpenAI:
    """Raw Groq client via OpenAI compatibility."""
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"], base_url=base_url)


@lru_cache(maxsize=1)
def get_instructor_groq_client() -> instructor.Instructor:
    """Instructor-wrapped Groq client via OpenAI compatibility."""
    return instructor.from_openai(get_groq_client())
