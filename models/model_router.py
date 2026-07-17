import os
from typing import Any, Tuple
import instructor
from models.openai_provider import (
    get_openai_client,
    get_instructor_openai_client,
    get_instructor_anthropic_client,
    get_anthropic_client,
)
from models.groq_provider import (
    get_groq_client,
    get_instructor_groq_client,
)


def _is_groq() -> bool:
    """Helper to detect if Groq is the primary OpenAI-compatible provider."""
    base_url = os.environ.get("OPENAI_BASE_URL", "")
    return "groq.com" in base_url or os.environ.get("OPENAI_API_KEY", "").startswith("gsk_")


def get_intent_model() -> Tuple[instructor.Instructor, str]:
    """Get instructor client and model name for intent parsing."""
    if _is_groq():
        model = os.getenv("INTENT_PARSER_MODEL", "llama-4-scout-17b-16e-instruct")
        return get_instructor_groq_client(), model
    else:
        model = os.getenv("INTENT_PARSER_MODEL", "gpt-4o-mini")
        return get_instructor_openai_client(), model


def get_vision_model() -> Tuple[instructor.Instructor, str]:
    """Get instructor client and model name for image analysis."""
    if _is_groq():
        model = os.getenv("IMAGE_ANALYSER_MODEL", "llama-4-scout-17b-16e-instruct")
        return get_instructor_groq_client(), model
    else:
        model = os.getenv("IMAGE_ANALYSER_MODEL", "gpt-4o")
        return get_instructor_openai_client(), model


def get_storyboard_model() -> Tuple[instructor.Instructor, str]:
    """Get instructor client and model name for storyboard writing."""
    if _is_groq():
        model = os.getenv("STORYBOARD_MODEL", "llama-4-scout-17b-16e-instruct")
        return get_instructor_groq_client(), model
    else:
        model = os.getenv("STORYBOARD_MODEL", "gpt-4o-mini")
        return get_instructor_openai_client(), model


def get_script_model() -> Tuple[Any, str]:
    """Get client and model name for script generation. Can return Anthropic or OpenAI/Groq client."""
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    if anthropic_key and not anthropic_key.startswith("sk-ant-placeholder"):
        model = os.getenv("SCRIPT_GENERATOR_MODEL", "claude-sonnet-4-5")
        return get_anthropic_client(), model

    if _is_groq():
        model = os.getenv("SCRIPT_GENERATOR_MODEL", "llama-4-scout-17b-16e-instruct")
        return get_groq_client(), model
    else:
        model = os.getenv("SCRIPT_GENERATOR_MODEL", "gpt-4o")
        return get_openai_client(), model


def get_fixer_model() -> Tuple[Any, str]:
    """Get client and model name for compiler fixer."""
    if _is_groq():
        model = os.getenv("COMPILER_FIXER_MODEL", "llama-4-scout-17b-16e-instruct")
        return get_groq_client(), model
    else:
        model = os.getenv("COMPILER_FIXER_MODEL", "gpt-4o-mini")
        return get_openai_client(), model
