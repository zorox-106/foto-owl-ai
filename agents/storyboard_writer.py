"""
Agent 2 — Storyboard Writer

Takes the selected images and their analyses, queries the RAG store for the
appropriate style guide, and produces a structured Storyboard (list of Scenes).

Model choice: gpt-4o-mini
Rationale: Storyboard generation is primarily a creative reasoning task with
well-defined structured output. It does NOT require vision (images have already
been described by the Analyser). gpt-4o-mini handles complex structured JSON
generation reliably and is significantly cheaper. The RAG context (style guide)
grounds the output in concrete rules, compensating for any reduced capability.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

from models import oai
from models.state import ImageAnalysis, PipelineState, Scene, Storyboard, VideoIntent
from rag import retrieve

_SYSTEM = """You are a senior video editor writing a storyboard for an event highlight reel.
Given a list of selected images with their descriptions, plus a style guide retrieved from memory,
produce a complete Storyboard JSON that maps each image to a Scene.

Rules:
- Scenes must be ordered narratively (not just chronologically).
- Total duration must equal the sum of all scene durations.
- Scene durations must reflect the pacing: slow→4–6s each, medium→2–4s, fast→1–2s.
- transition_in must be EXACTLY one of: "fade", "cut", "slide", "zoom", "dissolve".
- animation must be EXACTLY one of: "ken_burns", "zoom_in", "zoom_out", "static", "slide_in".
- Include an opening_text and closing_text appropriate to the event type.
- Caption every 2nd or 3rd scene max; never caption every scene.
"""


def _build_image_context(analyses: List[ImageAnalysis], selected_paths: List[str]) -> str:
    selected_set = set(selected_paths)
    lines = []
    for a in analyses:
        if a.image_path not in selected_set:
            continue
        lines.append(
            f"- {Path(a.image_path).name}: {a.description} "
            f"(mood={a.mood}, composition={a.composition}, "
            f"quality={a.quality_score:.2f})"
        )
    return "\n".join(lines)


def storyboard_writer_agent(state: PipelineState) -> dict:
    """Write a complete Storyboard using image analyses and style guide RAG context."""
    intent: VideoIntent = state["video_intent"]
    analyses: List[ImageAnalysis] = state["image_analyses"]
    selected: List[str] = state["selected_images"]

    # RAG: retrieve the relevant style guide
    style_query = f"{intent.visual_style} video style guide {' '.join(intent.style_keywords)}"
    style_guides = retrieve(style_query, "style_guides", n_results=1)
    style_context = style_guides[0] if style_guides else "Use professional video editing standards."

    image_context = _build_image_context(analyses, selected)

    model = os.getenv("STORYBOARD_MODEL", "gpt-4o-mini")

    storyboard: Storyboard = oai().chat.completions.create(
        model=model,
        response_model=Storyboard,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {
                "role": "user",
                "content": (
                    f"=== VIDEO INTENT ===\n"
                    f"Style: {intent.visual_style}\n"
                    f"Pacing: {intent.pacing}\n"
                    f"Color treatment: {intent.color_treatment}\n"
                    f"Target duration: {intent.target_duration_seconds}s\n"
                    f"Caption tone: {intent.caption_tone}\n"
                    f"Music energy: {intent.music_energy}\n"
                    f"Keywords: {', '.join(intent.style_keywords)}\n\n"
                    f"=== STYLE GUIDE (from memory) ===\n{style_context}\n\n"
                    f"=== SELECTED IMAGES ({len(selected)}) ===\n{image_context}\n\n"
                    f"Write the complete storyboard now."
                ),
            },
        ],
        max_tokens=2048,
    )

    return {"storyboard": storyboard}
