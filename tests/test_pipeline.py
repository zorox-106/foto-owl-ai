"""
Integration tests for the LangGraph StateGraph pipeline.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from graph import pipeline
from models.state import FailureReport


class TestPipelineIntegration:
    @patch("agents.intent_parser.get_intent_model")
    @patch("agents.image_analyser._analyse_single")
    @patch("agents.storyboard_writer.retrieve")
    @patch("agents.storyboard_writer.get_storyboard_model")
    @patch("agents.script_generator.retrieve")
    @patch("agents.script_generator._generate_script")
    @patch("agents.compiler_fixer._run_tsc")
    @patch("agents.renderer.subprocess.run")
    def test_successful_pipeline_execution(
        self,
        mock_render_run,
        mock_tsc,
        mock_generate_script,
        mock_script_rag,
        mock_storyboard_llm,
        mock_storyboard_rag,
        mock_analyse_image,
        mock_intent_llm,
        video_intent,
        image_analysis,
        storyboard,
        tmp_path,
    ):
        """Test a full successful path of the pipeline graph with mock models and subprocesses."""
        # 1. Setup mocks
        mock_intent_client = MagicMock()
        mock_intent_client.chat.completions.create.return_value = video_intent
        mock_intent_llm.return_value = (mock_intent_client, "test-model")
        mock_analyse_image.return_value = image_analysis
        mock_storyboard_rag.return_value = ["Style guide content"]
        mock_storyboard_client = MagicMock()
        mock_storyboard_client.chat.completions.create.return_value = storyboard
        mock_storyboard_llm.return_value = (mock_storyboard_client, "test-model")
        mock_script_rag.return_value = ["API docs"]
        mock_generate_script.return_value = "export const EventReel = () => null; // Generated script"
        mock_tsc.return_value = []  # Compile success on first try!

        # Mock render process success
        mock_render = MagicMock()
        mock_render.returncode = 0
        mock_render_run.return_value = mock_render

        # Create input photo
        img = tmp_path / "photo.jpg"
        img.write_bytes(b"PHOTO_DATA")

        # 2. Run graph
        initial_state = {
            "image_paths": [str(img)],
            "raw_prompt": "Create a romantic wedding video.",
            "retry_count": 0,
            "max_retries": 3,
        }

        # Override Remotion dir to temp dir so renderer doesn't clutter actual repository
        remotion_dir = tmp_path / "remotion"
        output_dir = tmp_path / "out"

        with patch("agents.renderer.REMOTION_DIR", remotion_dir), \
             patch("agents.renderer.OUTPUT_DIR", output_dir):

            final_state = pipeline.invoke(initial_state)

        # 3. Assert outputs
        assert final_state.get("pipeline_status") == "success"
        assert final_state.get("compile_success") is True
        assert final_state.get("video_output_path") is not None
        assert final_state.get("retry_count") == 0

        # Check that script file was written
        script_file = remotion_dir / "src" / "EventReel.tsx"
        assert script_file.exists()
        assert "Generated script" in script_file.read_text()

        # Check that image was copied to public folder
        copied_image = remotion_dir / "public" / "test_image.jpg"
        assert copied_image.exists()

    @patch("agents.intent_parser.get_intent_model")
    @patch("agents.image_analyser._analyse_single")
    @patch("agents.storyboard_writer.retrieve")
    @patch("agents.storyboard_writer.get_storyboard_model")
    @patch("agents.script_generator.retrieve")
    @patch("agents.script_generator._generate_script")
    @patch("agents.compiler_fixer._run_tsc")
    @patch("agents.compiler_fixer.retrieve")
    @patch("agents.compiler_fixer._fix_script")
    def test_pipeline_compiler_retry_loop(
        self,
        mock_fix,
        mock_compiler_rag,
        mock_tsc,
        mock_generate_script,
        mock_script_rag,
        mock_storyboard_llm,
        mock_storyboard_rag,
        mock_analyse_image,
        mock_intent_llm,
        video_intent,
        image_analysis,
        storyboard,
        tmp_path,
    ):
        """Test that the pipeline loops back to script generation/fixing when compilation fails, and terminates on failure."""
        mock_intent_client = MagicMock()
        mock_intent_client.chat.completions.create.return_value = video_intent
        mock_intent_llm.return_value = (mock_intent_client, "test-model")
        mock_analyse_image.return_value = image_analysis
        mock_storyboard_rag.return_value = ["Style guide content"]
        mock_storyboard_client = MagicMock()
        mock_storyboard_client.chat.completions.create.return_value = storyboard
        mock_storyboard_llm.return_value = (mock_storyboard_client, "test-model")
        mock_script_rag.return_value = ["API docs"]
        mock_generate_script.return_value = "export const EventReel = () => null;"

        # Mock compiler returning error every single time to trigger max retries
        from models.state import CompileError
        compile_error = CompileError(
            error_type="TypeScript",
            message="EventReel.tsx:1:1 - error TS1005: ';' expected.",
            line_number=1,
            relevant_api_snippet="Compiler helper docs"
        )
        mock_tsc.return_value = [compile_error]
        mock_compiler_rag.return_value = ["Compiler helper docs"]
        mock_fix.return_value = "export const EventReel = () => null; // Fixed but still failing"

        # Create input photo
        img = tmp_path / "photo.jpg"
        img.write_bytes(b"PHOTO_DATA")

        initial_state = {
            "image_paths": [str(img)],
            "raw_prompt": "Create a wedding video.",
            "retry_count": 0,
            "max_retries": 3,
        }

        remotion_dir = tmp_path / "remotion"
        output_dir = tmp_path / "out"

        with patch("agents.renderer.REMOTION_DIR", remotion_dir), \
             patch("agents.renderer.OUTPUT_DIR", output_dir):

            final_state = pipeline.invoke(initial_state)

        # Pipeline should fail after 3 attempts
        assert final_state.get("pipeline_status") == "failed"
        assert final_state.get("compile_success") is False
        assert final_state.get("retry_count") == 3
        assert isinstance(final_state.get("failure_report"), FailureReport)
        assert final_state.get("failure_report").total_retries == 3
        assert final_state.get("video_output_path") is None
