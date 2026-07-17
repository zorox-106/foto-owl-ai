"""
Shared fixtures and mock factories for the test suite.
"""
from __future__ import annotations

import os
import pytest
from unittest.mock import MagicMock

# Set dummy env vars so imports don't fail
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-key-for-tests")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-dummy-key-for-tests")

from models.state import (
    CompileError,
    ImageAnalysis,
    PipelineState,
    Scene,
    Storyboard,
    VideoIntent,
)


# ── Canonical fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def video_intent() -> VideoIntent:
    return VideoIntent(
        pacing="slow",
        visual_style="cinematic",
        caption_tone="emotional",
        transition_preference="fade",
        color_treatment="warm golden tones",
        music_energy="low",
        target_duration_seconds=30.0,
        style_keywords=["cinematic", "wedding", "romantic"],
    )


@pytest.fixture
def image_analysis(tmp_path) -> ImageAnalysis:
    img = tmp_path / "test_image.jpg"
    img.write_bytes(b"FAKE_JPEG_DATA")
    return ImageAnalysis(
        image_path=str(img),
        subject="Wedding couple walking",
        mood="romantic",
        composition="portrait",
        quality_score=0.9,
        relevance_score=0.85,
        description="Couple in traditional wedding attire walking through garden.",
        dominant_colors=["white", "green", "gold"],
    )


@pytest.fixture
def scene(tmp_path) -> Scene:
    img = tmp_path / "scene_image.jpg"
    img.write_bytes(b"FAKE_JPEG_DATA")
    return Scene(
        order=0,
        image_path=str(img),
        duration_seconds=4.0,
        caption="A new beginning",
        transition_in="fade",
        animation="ken_burns",
        scene_note="Open on the couple, slow zoom",
    )


@pytest.fixture
def storyboard(scene) -> Storyboard:
    return Storyboard(
        title="Wedding Highlights",
        total_duration_seconds=30.0,
        narrative_arc="opening → build → climax → close",
        scenes=[scene],
        opening_text="Two hearts, one journey",
        closing_text="Forever begins today",
    )


@pytest.fixture
def base_state(tmp_path, video_intent, image_analysis, storyboard) -> PipelineState:
    """A fully populated base state for testing agents in isolation."""
    img_path = str(tmp_path / "test_image.jpg")
    return {
        "image_paths": [img_path],
        "raw_prompt": "Cinematic wedding reel, warm and emotional",
        "video_intent": video_intent,
        "image_analyses": [image_analysis],
        "selected_images": [img_path],
        "storyboard": storyboard,
        "remotion_script": "export const EventReel = () => null;",
        "compile_success": False,
        "compile_errors": [],
        "retry_count": 0,
        "max_retries": 3,
        "video_output_path": None,
        "failure_report": None,
        "pipeline_status": "running",
    }
