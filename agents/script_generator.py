"""
Agent 3 — Script Generator

Converts the Storyboard into a complete, runnable Remotion TypeScript composition.
Uses RAG to retrieve relevant Remotion API snippets before generating code.

Model choice: claude-sonnet-4-5 (Claude Sonnet)
Rationale: Code generation is the most complex task in the pipeline. It requires:
  1. Deep understanding of a niche framework API (Remotion)
  2. Long-form TypeScript output with precise syntax
  3. Faithful translation of the Storyboard JSON into working animation logic
Claude Sonnet outperforms GPT-4o on long-form, instruction-dense code generation tasks
and handles the Remotion API patterns (hooks, interpolate, spring) more reliably.
We use RAG-retrieved snippets in the system prompt to ground the generation in
correct Remotion v4 API usage rather than relying solely on training data.

Fallback: If ANTHROPIC_API_KEY is not set, falls back to gpt-4o.
"""
from __future__ import annotations

import os
from pathlib import Path
from textwrap import dedent
from typing import List

from models.state import PipelineState, Scene, Storyboard, VideoIntent
from rag import retrieve

FPS = 30
REMOTION_PROJECT_DIR = os.getenv("REMOTION_PROJECT_DIR", "./remotion")


def _frames(seconds: float) -> int:
    return max(1, round(seconds * FPS))


def _build_rag_context() -> str:
    """Pull the most relevant Remotion API snippets from the vector store."""
    queries = [
        "Sequence durationInFrames from frames",
        "useCurrentFrame interpolate fade animation",
        "Img staticFile image loading",
        "AbsoluteFill spring caption overlay",
    ]
    snippets: List[str] = []
    for q in queries:
        results = retrieve(q, "remotion_api", n_results=1)
        if results:
            snippets.extend(results)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for s in snippets:
        if s not in seen:
            seen.add(s)
            unique.append(s)
    return "\n\n---\n\n".join(unique)


def _storyboard_to_prompt(storyboard: Storyboard, intent: VideoIntent) -> str:
    """Render the storyboard as a human-readable prompt for the code generator."""
    lines = [
        f"Title: {storyboard.title}",
        f"Narrative arc: {storyboard.narrative_arc}",
        f"Total duration: {storyboard.total_duration_seconds}s",
        f"FPS: {FPS}",
        f"Total frames: {_frames(storyboard.total_duration_seconds)}",
        f"Visual style: {intent.visual_style}",
        f"Color treatment: {intent.color_treatment}",
        "",
        f"Opening text: {storyboard.opening_text or 'None'}",
        f"Closing text: {storyboard.closing_text or 'None'}",
        "",
        "=== SCENES ===",
    ]
    cumulative = 0
    for scene in storyboard.scenes:
        dur_frames = _frames(scene.duration_seconds)
        lines += [
            f"\nScene {scene.order + 1}:",
            f"  Image filename: {Path(scene.image_path).name}",
            f"  Start frame: {cumulative}",
            f"  Duration frames: {dur_frames}  ({scene.duration_seconds}s)",
            f"  Transition in: {scene.transition_in}",
            f"  Animation: {scene.animation}",
            f"  Caption: {scene.caption or 'None'}",
            f"  Director note: {scene.scene_note}",
        ]
        cumulative += dur_frames
    return "\n".join(lines)


_SYSTEM_ANTHROPIC = dedent("""\
You are an expert Remotion v4 TypeScript developer.
Generate a complete, runnable Remotion composition for an event highlight reel.

Output ONLY valid TypeScript/TSX code — no markdown fences, no explanations.
The output must be a single self-contained file that can be dropped into a Remotion project.

Constraints:
- Use ONLY the following Remotion imports: {AbsoluteFill, Sequence, Img, interpolate, spring,
  useCurrentFrame, useVideoConfig, staticFile} from 'remotion'
- Use React.FC with explicit return types
- All images must be loaded via staticFile('<filename>') — just the basename, no path
- Every scene must implement its animation using interpolate() and useCurrentFrame()
- Implement fade transitions using opacity interpolation at scene boundaries (first/last 15 frames)
- Do NOT create separate transition components (like FadeInTransition/FadeOutTransition) that reference undefined variables (like durationFrames). Either pass durationFrames/durationInFrames as props to them, or inline the opacity interpolation directly inside the SceneFrame/EventReel components.
- If you declare any transition components with a children prop, make it optional (e.g. children?: React.ReactNode) so it doesn't fail compilation when invoked without children.
- If you declare a static configurations array (like const SCENES = [...]), always append 'as const' at the end (e.g. const SCENES = [...] as const;) to prevent TypeScript string-assignability type errors on literal properties like animation.
- Ken Burns: scale interpolated from 1.0 → 1.08 over scene duration
- Slide in: translateX from 10% → 0% over 20 frames
- Captions: positioned at bottom-center with textShadow, animated opacity in
- If opening_text is provided (and is not 'None'), define it as a local constant variable inside or outside EventReel (e.g. const opening_text = "...") and use it. Do NOT reference it unless it is defined.
- If closing_text is provided (and is not 'None'), define it as a local constant variable inside or outside EventReel (e.g. const closing_text = "...") and use it. Do NOT reference it unless it is defined.
- The main composition component must be declared as: export const EventReel: React.FC = () => { ... }
- At the bottom of the file, export it as default: export default EventReel;
- Do NOT add redundant declarations or assignments like export const EventReel = EventReel; at the end.
- Register the composition with id="EventReel", fps=30, width=1920, height=1080
- The durationInFrames must equal the exact sum of all scene durations in frames
""")

_SYSTEM_OPENAI = _SYSTEM_ANTHROPIC  # Same instructions, same constraints


def _generate_with_anthropic(prompt: str, rag_context: str) -> str:
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    model = os.getenv("SCRIPT_GENERATOR_MODEL", "claude-sonnet-4-5")

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=_SYSTEM_ANTHROPIC + f"\n\n=== REMOTION API REFERENCE ===\n{rag_context}",
        messages=[
            {"role": "user", "content": f"Generate the Remotion composition script:\n\n{prompt}"}
        ],
    )
    return _clean_script(response.content[0].text)  # type: ignore[index]


def _generate_with_openai(prompt: str, rag_context: str) -> str:
    import time
    from openai import OpenAI, RateLimitError
    # Honour OPENAI_BASE_URL so Groq / other OpenAI-compatible providers work
    base_url = os.environ.get("OPENAI_BASE_URL")
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], base_url=base_url)
    model = os.getenv("SCRIPT_GENERATOR_MODEL", "gpt-4o")

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": _SYSTEM_OPENAI + f"\n\n=== REMOTION API REFERENCE ===\n{rag_context}",
                    },
                    {
                        "role": "user",
                        "content": f"Generate the Remotion composition script:\n\n{prompt}",
                    },
                ],
                max_tokens=4096,
            )
            return _clean_script(response.choices[0].message.content or "")
        except RateLimitError as e:
            wait = 25 * (attempt + 1)  # 25s, 50s, 75s
            print(f"[ScriptGenerator] Rate limit hit — waiting {wait}s before retry {attempt + 1}/3...")
            time.sleep(wait)
    # Last attempt without catching
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM_OPENAI + f"\n\n=== REMOTION API REFERENCE ===\n{rag_context}"},
            {"role": "user", "content": f"Generate the Remotion composition script:\n\n{prompt}"},
        ],
        max_tokens=4096,
    )
    return _clean_script(response.choices[0].message.content or "")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": _SYSTEM_OPENAI + f"\n\n=== REMOTION API REFERENCE ===\n{rag_context}",
            },
            {
                "role": "user",
                "content": f"Generate the Remotion composition script:\n\n{prompt}",
            },
        ],
        max_tokens=4096,
    )
    return _clean_script(response.choices[0].message.content or "")


def _clean_script(script: str) -> str:
    """Strip markdown fences and patch common LLM omissions."""
    import re
    # Remove markdown code fences (```typescript, ```tsx, ```)
    script = re.sub(r'^```[\w]*\n?', '', script.strip(), flags=re.MULTILINE)
    script = re.sub(r'\n?```$', '', script.strip(), flags=re.MULTILINE)
    script = script.strip()

    # Ensure React is imported (required for JSX in TS strict mode)
    if "React" in script and "import React" not in script:
        script = "import React from 'react';\n" + script

    # Ensure EventReel is exported as a named export
    script = re.sub(r'(?<!export\s)const\s+EventReel', 'export const EventReel', script)

    # Clean up duplicate export const EventReel = EventReel statement if the LLM outputted it
    script = re.sub(r'export\s+const\s+EventReel\s*=\s*EventReel;?', '', script)

    # Ensure EventReel is exported as a default export
    if "export default" not in script and "EventReel" in script:
        script += "\n\nexport default EventReel;\n"

    return script


def script_generator_agent(state: PipelineState) -> dict:
    """Generate the Remotion TypeScript composition from the storyboard or fix compile errors."""
    storyboard: Storyboard = state["storyboard"]
    intent: VideoIntent = state["video_intent"]
    compile_errors = state.get("compile_errors", [])

    if compile_errors:
        print(f"[ScriptGenerator] Fixing compile errors (retry attempt {state.get('retry_count', 0)})...")
        from agents.compiler_fixer import _fix_script
        script = _fix_script(state["remotion_script"], compile_errors)
    else:
        print("[ScriptGenerator] Retrieving Remotion API context from RAG...")
        rag_context = _build_rag_context()

        print("[ScriptGenerator] Generating Remotion composition script...")
        prompt = _storyboard_to_prompt(storyboard, intent)

        # Route: prefer Claude Sonnet; fall back to GPT-4o if no Anthropic key
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        if anthropic_key and not anthropic_key.startswith("sk-ant-placeholder"):
            script = _generate_with_anthropic(prompt, rag_context)
            print("[ScriptGenerator] Script generated via Claude Sonnet.")
        else:
            script = _generate_with_openai(prompt, rag_context)
            print("[ScriptGenerator] Script generated via GPT-4o (fallback).")

    return {
        "remotion_script": script,
        "compile_success": False,
        "compile_errors": [],  # clear errors for the next compile check
        "retry_count": state.get("retry_count", 0),
    }
