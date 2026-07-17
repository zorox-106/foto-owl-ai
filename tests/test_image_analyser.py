"""
Tests for the Image Analyser agent.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from models.state import ImageAnalysis, VideoIntent


class TestImageAnalyser:
    def test_image_analyser_agent_scores_and_selects(self, tmp_path, video_intent):
        """Image Analyser should invoke vision model and select the best subset."""
        # Create a couple of fake images
        img1 = tmp_path / "img1.jpg"
        img1.write_bytes(b"DATA1")
        img2 = tmp_path / "img2.jpg"
        img2.write_bytes(b"DATA2")

        analysis1 = ImageAnalysis(
            image_path=str(img1),
            subject="subject 1",
            mood="mood 1",
            composition="portrait",
            quality_score=0.9,
            relevance_score=0.9,
            description="desc 1",
            dominant_colors=["red"],
        )
        analysis2 = ImageAnalysis(
            image_path=str(img2),
            subject="subject 2",
            mood="mood 2",
            composition="landscape",
            quality_score=0.3,
            relevance_score=0.4,
            description="desc 2",
            dominant_colors=["blue"],
        )

        # Mock the single image analyser function to return predetermined results
        with patch("agents.image_analyser._analyse_single") as mock_analyse:
            mock_analyse.side_effect = [analysis1, analysis2]

            from agents.image_analyser import image_analyser_agent

            state = {
                "video_intent": video_intent,
                "image_paths": [str(img1), str(img2)],
            }

            # Set max images to 1 to force selection logic
            with patch("agents.image_analyser._MAX_IMAGES", 1):
                result = image_analyser_agent(state)

        assert "image_analyses" in result
        assert "selected_images" in result
        assert len(result["image_analyses"]) == 2
        # Should select the first one because its scores are higher (0.9 vs 0.35)
        assert len(result["selected_images"]) == 1
        assert result["selected_images"][0] == str(img1)

    def test_handles_corrupt_or_missing_image_gracefully(self, tmp_path, video_intent):
        """The analyser should catch errors and proceed with other images instead of crashing."""
        img1 = tmp_path / "corrupt.jpg"
        img1.write_bytes(b"CORRUPT")
        img2 = tmp_path / "valid.jpg"
        img2.write_bytes(b"VALID")

        analysis2 = ImageAnalysis(
            image_path=str(img2),
            subject="subject 2",
            mood="mood 2",
            composition="landscape",
            quality_score=0.8,
            relevance_score=0.8,
            description="desc 2",
            dominant_colors=["green"],
        )

        with patch("agents.image_analyser._analyse_single") as mock_analyse:
            mock_analyse.side_effect = [RuntimeError("Failed to parse image"), analysis2]

            from agents.image_analyser import image_analyser_agent

            state = {
                "video_intent": video_intent,
                "image_paths": [str(img1), str(img2)],
            }
            result = image_analyser_agent(state)

        assert len(result["image_analyses"]) == 2
        assert result["image_analyses"][0].image_path == str(img1)
        assert "wedding" in result["image_analyses"][0].subject.lower()
        assert set(result["selected_images"]) == {str(img1), str(img2)}
