"""
Tests for the Storyboard Writer agent.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from models.state import Scene, Storyboard


class TestStoryboardWriter:
    def test_storyboard_writer_retrieves_rag_and_generates(self, video_intent, image_analysis):
        """Storyboard writer must fetch style guides from RAG and invoke LLM for a structured Storyboard."""
        mock_storyboard = Storyboard(
            title="A Great Celebration",
            total_duration_seconds=10.0,
            narrative_arc="start to finish",
            scenes=[
                Scene(
                    order=0,
                    image_path=image_analysis.image_path,
                    duration_seconds=10.0,
                    caption="Opening moments",
                    transition_in="fade",
                    animation="zoom_in",
                    scene_note="Start with couple",
                )
            ],
            opening_text="Welcome",
            closing_text="Goodbye",
        )

        with patch("agents.storyboard_writer.retrieve") as mock_retrieve, \
             patch("agents.storyboard_writer.get_storyboard_model") as mock_get_model:

            # Mock RAG retrieval
            mock_retrieve.return_value = ["Mocked cinematic style guide content."]

            # Mock LLM call
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_storyboard
            mock_get_model.return_value = (mock_client, "test-model")

            from agents.storyboard_writer import storyboard_writer_agent

            state = {
                "video_intent": video_intent,
                "image_analyses": [image_analysis],
                "selected_images": [image_analysis.image_path],
            }

            result = storyboard_writer_agent(state)

        # Verify RAG call
        mock_retrieve.assert_called_once()
        assert "cinematic" in mock_retrieve.call_args[0][0]

        # Verify output
        assert "storyboard" in result
        assert isinstance(result["storyboard"], Storyboard)
        assert result["storyboard"].title == "A Great Celebration"
        assert len(result["storyboard"].scenes) == 1
        assert result["storyboard"].scenes[0].caption == "Opening moments"
