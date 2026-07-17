"""Shared LLM client instances, patched by tests via monkeypatching llm_call functions."""
import os
from functools import lru_cache

import instructor
from openai import OpenAI
from anthropic import Anthropic


@lru_cache(maxsize=1)
def oai() -> instructor.Instructor:
    """OpenAI client with instructor (structured output via function calling)."""
    return instructor.from_openai(OpenAI(api_key=os.environ["OPENAI_API_KEY"]))


@lru_cache(maxsize=1)
def ant() -> instructor.Instructor:
    """Anthropic client with instructor (structured output via tool use)."""
    return instructor.from_anthropic(Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"]))
