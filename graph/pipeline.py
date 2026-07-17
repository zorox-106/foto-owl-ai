"""
LangGraph StateGraph definition for the Image-to-Video pipeline.

Graph topology:
  intent_parser → image_analyser → storyboard_writer → script_generator
                                                              ↓
                                                      compiler_fixer
                                                      ↙            ↘
                                              [retry loop]    renderer (on success)
                                                                    ↓
                                                                  END

Conditional edges:
- After compiler_fixer: if compile_success → renderer, else if retry_count < MAX_RETRIES → script_generator, else → END (failure)
"""
from __future__ import annotations

import os
from typing import Literal

from langgraph.graph import END, StateGraph

from agents import (
    compiler_fixer_agent,
    image_analyser_agent,
    intent_parser_agent,
    renderer_agent,
    script_generator_agent,
    storyboard_writer_agent,
)
from models.state import PipelineState

MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))


def _route_after_compiler(state: PipelineState) -> Literal["script_generator", "renderer", "__end__"]:
    """Conditional routing after the compiler/fixer node.

    Returns:
        - 'renderer'        : compilation succeeded → proceed to render
        - 'script_generator': compilation failed but retries remain → re-generate and fix
        - '__end__'         : max retries exhausted → terminate with failure report
    """
    if state.get("compile_success"):
        return "renderer"

    if state.get("pipeline_status") == "failed":
        return END  # type: ignore[return-value]

    retry_count = state.get("retry_count", 0)
    if retry_count >= MAX_RETRIES:
        return END  # type: ignore[return-value]

    return "script_generator"


def build_graph() -> StateGraph:
    """Construct and compile the LangGraph StateGraph."""
    graph = StateGraph(PipelineState)

    # ── Register nodes ─────────────────────────────────────────────────────────
    graph.add_node("intent_parser", intent_parser_agent)
    graph.add_node("image_analyser", image_analyser_agent)
    graph.add_node("storyboard_writer", storyboard_writer_agent)
    graph.add_node("script_generator", script_generator_agent)
    graph.add_node("compiler_fixer", compiler_fixer_agent)
    graph.add_node("renderer", renderer_agent)

    # ── Linear edges ───────────────────────────────────────────────────────────
    graph.add_edge("intent_parser", "image_analyser")
    graph.add_edge("image_analyser", "storyboard_writer")
    graph.add_edge("storyboard_writer", "script_generator")
    graph.add_edge("script_generator", "compiler_fixer")
    graph.add_edge("renderer", END)

    # ── Conditional: compiler_fixer → (retry | render | end) ──────────────────
    graph.add_conditional_edges(
        "compiler_fixer",
        _route_after_compiler,
        {
            "renderer": "renderer",
            "script_generator": "script_generator",
            END: END,
        },
    )

    # ── Entry point ────────────────────────────────────────────────────────────
    graph.set_entry_point("intent_parser")

    return graph.compile()


# Singleton compiled graph — import and invoke from main.py
pipeline = build_graph()
