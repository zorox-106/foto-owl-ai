"""
Agent 0 — Intent Parser

Converts the raw user prompt into a strongly-typed VideoIntent struct.
This is the cheapest and fastest LLM call in the pipeline.

Model choice: gpt-4o-mini
Rationale: Intent parsing is a straightforward classification + extraction task.
The output schema is well-defined (Pydantic). gpt-4o-mini handles this perfectly
at ~5–10× lower cost than gpt-4o, with negligible quality difference.
"""
from __future__ import annotations

import os
from models import oai
from models.state import PipelineState, VideoIntent


_SYSTEM = """You are a creative director assistant specialising in event video production.
Given a user's free-form prompt, extract their creative intent into a structured JSON schema.

Guidelines:
- pacing: 'slow' for cinematic/emotional, 'medium' for corporate/documentary, 'fast' for sports/party
- visual_style: choose the SINGLE closest match from allowed values
- target_duration_seconds: if not specified, infer from style (cinematic→45, upbeat→30, corporate→40)
- Be opinionated but reasonable — fill in unspecified fields using best creative judgment
"""


def intent_parser_agent(state: PipelineState) -> dict:
    """Parse the raw prompt into a VideoIntent and return it as a state patch."""
    model = os.getenv("INTENT_PARSER_MODEL", "gpt-4o-mini")

    intent: VideoIntent = oai().chat.completions.create(
        model=model,
        response_model=VideoIntent,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": state["raw_prompt"]},
        ],
        max_tokens=512,
    )

    return {"video_intent": intent}
