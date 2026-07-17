"""
Tests for the Script Generator agent.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


class TestScriptGenerator:
    def test_script_generator_uses_anthropic_when_key_exists(self, base_state):
        """Script Generator should use Anthropic API when ANTHROPIC_API_KEY is present and not a placeholder."""
        fake_code = "export const EventReel = () => null;"

        with patch("agents.script_generator.retrieve") as mock_retrieve, \
             patch("agents.script_generator._generate_with_anthropic") as mock_anthropic, \
             patch("agents.script_generator._generate_with_openai") as mock_openai, \
             patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-valid-key"}):

            mock_retrieve.return_value = ["mock API snippet"]
            mock_anthropic.return_value = fake_code

            from agents.script_generator import script_generator_agent

            result = script_generator_agent(base_state)

        assert result["remotion_script"] == fake_code
        mock_anthropic.assert_called_once()
        mock_openai.assert_not_called()

    def test_script_generator_falls_back_to_openai_if_no_key(self, base_state):
        """Script Generator should fall back to OpenAI when ANTHROPIC_API_KEY is empty or a placeholder."""
        fake_code = "export const EventReelFallback = () => null;"

        # Make sure no Anthropic key is set in environment (or matches placeholder/empty)
        with patch("agents.script_generator.retrieve") as mock_retrieve, \
             patch("agents.script_generator._generate_with_anthropic") as mock_anthropic, \
             patch("agents.script_generator._generate_with_openai") as mock_openai, \
             patch.dict("os.environ", {"ANTHROPIC_API_KEY": ""}):

            mock_retrieve.return_value = ["mock API snippet"]
            mock_openai.return_value = fake_code

            from agents.script_generator import script_generator_agent

            result = script_generator_agent(base_state)

        assert result["remotion_script"] == fake_code
        mock_openai.assert_called_once()
        mock_anthropic.assert_not_called()
