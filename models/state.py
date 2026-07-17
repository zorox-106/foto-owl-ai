"""
All shared Pydantic models and the LangGraph TypedDict pipeline state.
Every agent reads from and writes to PipelineState — single source of truth.
"""
from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


# ── Enums as Literals (Pydantic v2 compatible) ────────────────────────────────

Pacing = Literal["slow", "medium", "fast"]
VisualStyle = Literal["cinematic", "upbeat", "corporate", "documentary", "sports_highlights"]
CaptionTone = Literal["emotional", "bold", "minimal", "professional", "energetic"]
TransitionType = Literal["fade", "cut", "slide", "zoom", "dissolve"]
AnimationType = Literal["ken_burns", "zoom_in", "zoom_out", "static", "slide_in"]


# ── Intent ────────────────────────────────────────────────────────────────────

class VideoIntent(BaseModel):
    """Structured representation of the user's creative brief.
    Parsed once from raw_prompt; every downstream agent reads this — never re-interprets the raw prompt.
    """
    pacing: Pacing
    visual_style: VisualStyle
    caption_tone: CaptionTone
    transition_preference: TransitionType
    color_treatment: str = Field(description="e.g. 'warm golden tones', 'cool and crisp', 'natural'")
    music_energy: Literal["low", "medium", "high"]
    target_duration_seconds: float = Field(ge=10.0, le=120.0)
    style_keywords: List[str] = Field(description="Top 3–5 keywords summarising the requested style")


# ── Image Analysis ────────────────────────────────────────────────────────────

class ImageAnalysis(BaseModel):
    """Vision model's structured output for one image."""
    image_path: str
    subject: str = Field(description="Main subject(s) in the image")
    mood: str = Field(description="Emotional tone of the image")
    composition: Literal["portrait", "wide_shot", "action", "group", "detail", "landscape"]
    quality_score: float = Field(ge=0.0, le=1.0, description="Technical quality: sharpness, exposure, framing")
    relevance_score: float = Field(ge=0.0, le=1.0, description="How well this image fits the VideoIntent")
    description: str = Field(description="One-sentence description for storyboard use")
    dominant_colors: List[str] = Field(description="2–3 dominant color descriptors")


# ── Storyboard ────────────────────────────────────────────────────────────────

class Scene(BaseModel):
    """One scene in the storyboard, directly maps to one Remotion <Sequence>."""
    order: int = Field(ge=0)
    image_path: str
    duration_seconds: float = Field(ge=0.5, le=15.0)
    caption: Optional[str] = Field(None, description="On-screen text. None for no caption.")
    transition_in: TransitionType
    animation: AnimationType
    scene_note: str = Field(description="Brief director's note for this scene")


class Storyboard(BaseModel):
    """Complete narrative storyboard driving the Remotion composition."""
    title: str
    total_duration_seconds: float
    narrative_arc: str = Field(description="e.g. 'opening → build → climax → close'")
    scenes: List[Scene]
    opening_text: Optional[str] = Field(None, description="Intro title card text")
    closing_text: Optional[str] = Field(None, description="Outro / closing card text")


# ── Compiler Feedback ─────────────────────────────────────────────────────────

class CompileError(BaseModel):
    """Structured compiler error, enriched with a RAG-retrieved API snippet."""
    error_type: Literal["TypeScript", "Remotion", "Runtime", "Syntax"]
    message: str
    line_number: Optional[int] = None
    relevant_api_snippet: str = Field(
        description="RAG-retrieved Remotion API usage example most relevant to this error"
    )


class FailureReport(BaseModel):
    """Structured exit state emitted when compilation fails after max retries."""
    total_retries: int
    final_errors: List[CompileError]
    last_script_preview: str = Field(description="First 500 chars of the last generated script")
    recommendation: str = Field(description="Human-readable summary of what went wrong")


# ── LangGraph Shared State ────────────────────────────────────────────────────

class PipelineState(TypedDict):
    # Inputs — set at invocation, never mutated
    image_paths: List[str]
    raw_prompt: str

    # Parsed intent — set by intent_parser, read by all subsequent agents
    video_intent: VideoIntent

    # Agent outputs (written once each, except remotion_script which is overwritten on retry)
    image_analyses: List[ImageAnalysis]
    selected_images: List[str]
    storyboard: Storyboard
    remotion_script: str

    # Compiler feedback loop fields
    compile_success: bool
    compile_errors: List[CompileError]
    retry_count: int
    max_retries: int

    # Terminal state — exactly one will be set on completion
    video_output_path: Optional[str]
    failure_report: Optional[FailureReport]
    pipeline_status: Literal["running", "success", "failed"]
