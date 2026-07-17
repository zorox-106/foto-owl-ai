"""
Tests for the Script Generator agent.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


class TestScriptGenerator:
    def test_script_generator_generates_script(self, base_state):
        """Script Generator should call _generate_script and return remotion_script."""
        fake_code = "export const EventReel = () => null;"

        with patch("agents.script_generator.retrieve") as mock_retrieve, \
             patch("agents.script_generator._generate_script") as mock_generate:

            mock_retrieve.return_value = ["mock API snippet"]
            mock_generate.return_value = fake_code

            from agents.script_generator import script_generator_agent

            result = script_generator_agent(base_state)

        assert result["remotion_script"] == fake_code
        mock_generate.assert_called_once()

    def test_script_generator_falls_back_to_fix_when_errors_present(self, base_state):
        """Script Generator should call _fix_script when compile_errors are present, not _generate_script."""
        from models.state import CompileError

        compile_error = CompileError(
            error_type="TypeScript",
            message="error TS1005: ';' expected.",
            line_number=5,
            relevant_api_snippet="Use semicolons.",
        )
        fixed_code = "export const EventReel = () => null; // fixed"
        state_with_errors = {**base_state, "compile_errors": [compile_error]}

        with patch("agents.script_generator.retrieve") as mock_retrieve, \
             patch("agents.script_generator._generate_script") as mock_generate, \
             patch("agents.compiler_fixer._fix_script") as mock_fix:

            mock_retrieve.return_value = ["mock API snippet"]
            mock_fix.return_value = fixed_code

            from agents.script_generator import script_generator_agent

            result = script_generator_agent(state_with_errors)

        assert result["remotion_script"] == fixed_code
        mock_generate.assert_not_called()
        mock_fix.assert_called_once()

    def test_script_generator_returns_correct_keys(self, base_state):
        """script_generator_agent must return the expected state keys."""
        fake_code = "export const EventReel = () => null;"

        with patch("agents.script_generator.retrieve"), \
             patch("agents.script_generator._generate_script") as mock_generate:

            mock_generate.return_value = fake_code

            from agents.script_generator import script_generator_agent

            result = script_generator_agent(base_state)

        assert "remotion_script" in result
        assert "compile_success" in result
        assert "compile_errors" in result
        assert result["compile_errors"] == []
        assert result["compile_success"] is False
