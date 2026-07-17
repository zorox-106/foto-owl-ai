import os
from functools import lru_cache
import instructor
from openai import OpenAI
from anthropic import Anthropic


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    """Raw OpenAI client."""
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])


@lru_cache(maxsize=1)
def get_instructor_openai_client() -> instructor.Instructor:
    """Instructor-wrapped OpenAI client."""
    return instructor.from_openai(get_openai_client())


@lru_cache(maxsize=1)
def get_anthropic_client() -> Anthropic:
    """Raw Anthropic client."""
    return Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


@lru_cache(maxsize=1)
def get_instructor_anthropic_client() -> instructor.Instructor:
    """Instructor-wrapped Anthropic client."""
    return instructor.from_anthropic(get_anthropic_client())
