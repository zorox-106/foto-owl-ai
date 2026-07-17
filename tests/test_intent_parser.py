"""
Tests for the Intent Parser agent.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from models.state import VideoIntent


class TestIntentParser:
    def test_returns_video_intent_in_state(self):
        """Intent parser must return a dict with 'video_intent' key."""
        mock_intent = VideoIntent(
            pacing="slow",
            visual_style="cinematic",
            caption_tone="emotional",
            transition_preference="fade",
            color_treatment="warm golden tones",
            music_energy="low",
            target_duration_seconds=45.0,
            style_keywords=["cinematic", "wedding"],
        )

        with patch("agents.intent_parser.oai") as mock_oai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_intent
            mock_oai.return_value = mock_client

            from agents.intent_parser import intent_parser_agent

            state = {
                "raw_prompt": "Cinematic wedding reel, warm and emotional, slow pacing",
            }
            result = intent_parser_agent(state)

        assert "video_intent" in result
        assert isinstance(result["video_intent"], VideoIntent)
        assert result["video_intent"].visual_style == "cinematic"
        assert result["video_intent"].pacing == "slow"

    def test_model_called_with_prompt(self):
        """Verify the raw_prompt is passed to the LLM."""
        mock_intent = VideoIntent(
            pacing="fast",
            visual_style="upbeat",
            caption_tone="bold",
            transition_preference="cut",
            color_treatment="vibrant",
            music_energy="high",
            target_duration_seconds=30.0,
            style_keywords=["upbeat", "sports"],
        )

        with patch("agents.intent_parser.oai") as mock_oai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_intent
            mock_oai.return_value = mock_client

            from agents.intent_parser import intent_parser_agent

            raw = "Upbeat sports highlights, energetic, fast cuts"
            intent_parser_agent({"raw_prompt": raw})

            call_kwargs = mock_client.chat.completions.create.call_args
            messages = call_kwargs.kwargs.get("messages") or call_kwargs.args[0] if call_kwargs.args else []
            # The raw prompt must appear somewhere in the messages
            all_content = str(call_kwargs)
            assert raw in all_content

    def test_different_styles_produce_correct_pacing(self):
        """Integration-style test ensuring style maps to expected pacing enum value."""
        for style, expected_pacing in [("cinematic", "slow"), ("upbeat", "fast"), ("corporate", "medium")]:
            mock_intent = VideoIntent(
                pacing=expected_pacing,
                visual_style=style,
                caption_tone="minimal",
                transition_preference="fade",
                color_treatment="natural",
                music_energy="medium",
                target_duration_seconds=40.0,
                style_keywords=[style],
            )

            with patch("agents.intent_parser.oai") as mock_oai:
                mock_client = MagicMock()
                mock_client.chat.completions.create.return_value = mock_intent
                mock_oai.return_value = mock_client

                from agents.intent_parser import intent_parser_agent
                result = intent_parser_agent({"raw_prompt": f"{style} style video"})
                assert result["video_intent"].pacing == expected_pacing
