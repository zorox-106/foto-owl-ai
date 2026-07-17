"""
Tests for the Compiler & Fixer agent.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from models.state import FailureReport


class TestCompilerFixer:
    def test_compiler_success(self, base_state):
        """If tsc returns no errors, compiler agent should mark success and proceed."""
        with patch("agents.compiler_fixer._run_tsc") as mock_tsc:
            mock_tsc.return_value = []

            from agents.compiler_fixer import compiler_fixer_agent
            result = compiler_fixer_agent(base_state)

        assert result["compile_success"] is True
        assert len(result["compile_errors"]) == 0

    def test_compiler_failure_triggers_fix(self, base_state):
        """If tsc has errors, compiler agent maps them to CompileError list and passes them back in the state."""
        from models.state import CompileError
        compile_error = CompileError(
            error_type="TypeScript",
            message="EventReel.tsx:12:34 - error TS2307: Cannot find module 'remotion'.",
            line_number=12,
            relevant_api_snippet="Mock API documentation"
        )

        with patch("agents.compiler_fixer._run_tsc") as mock_tsc:
            mock_tsc.return_value = [compile_error]

            from agents.compiler_fixer import compiler_fixer_agent

            state = base_state.copy()
            state["retry_count"] = 0
            state["max_retries"] = 3

            result = compiler_fixer_agent(state)

        assert result["compile_success"] is False
        assert len(result["compile_errors"]) == 1
        assert result["compile_errors"][0].error_type == "TypeScript"
        assert result["compile_errors"][0].line_number == 12
        assert "remotion_script" not in result  # Not modified by the compiler fixer itself anymore
        assert result["retry_count"] == 1

    def test_max_retries_emits_failure_report(self, base_state):
        """When retry count hits max_retries, it must emit a FailureReport and terminate."""
        from models.state import CompileError
        compile_error = CompileError(
            error_type="TypeScript",
            message="EventReel.tsx:5:10 - error TS2554: Expected 2 arguments, but got 1.",
            line_number=5,
            relevant_api_snippet="Mock API doc"
        )

        with patch("agents.compiler_fixer._run_tsc") as mock_tsc:
            mock_tsc.return_value = [compile_error]

            from agents.compiler_fixer import compiler_fixer_agent

            state = base_state.copy()
            state["retry_count"] = 2  # retry_count + 1 = 3 (matches max_retries)
            state["max_retries"] = 3

            result = compiler_fixer_agent(state)

        assert result["compile_success"] is False
        assert "failure_report" in result
        assert isinstance(result["failure_report"], FailureReport)
        assert result["failure_report"].total_retries == 3
        assert result["pipeline_status"] == "failed"
