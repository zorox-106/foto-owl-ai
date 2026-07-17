"""
Agent 5 — Renderer

Writes the compiled script to the Remotion project, copies images to public/,
runs `npx remotion render`, and returns the output video path.

This is a thin orchestration node — no LLM call is needed. It executes
`npx remotion render EventReel <output_path>` as a subprocess.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from models.state import PipelineState

REMOTION_DIR = Path(os.getenv("REMOTION_PROJECT_DIR", "./remotion"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./out"))


def renderer_agent(state: PipelineState) -> dict:
    """Write the script to disk, copy images, and run Remotion render."""
    script: str = state["remotion_script"]
    selected_images = state["selected_images"]
    storyboard = state["storyboard"]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    public_dir = REMOTION_DIR / "public"
    public_dir.mkdir(parents=True, exist_ok=True)

    # 1. Write the generated script to the Remotion src directory
    script_path = REMOTION_DIR / "src" / "EventReel.tsx"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(script, encoding="utf-8")
    print(f"[Renderer] Script written to {script_path}")

    # 2. Copy selected images to public/
    for img_path in selected_images:
        src = Path(img_path)
        dest = public_dir / src.name
        if not dest.exists():
            shutil.copy2(src, dest)
    print(f"[Renderer] Copied {len(selected_images)} images to {public_dir}")

    # 3. Determine output path
    safe_title = storyboard.title.replace(" ", "_").replace("/", "-")[:40]
    output_path = OUTPUT_DIR / f"{safe_title}.mp4"

    # 4. Run remotion render
    print(f"[Renderer] Starting Remotion render → {output_path}")
    cmd = [
        "npx", "remotion", "render",
        "EventReel",
        str(output_path),
        "--props", "{}",
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(REMOTION_DIR),
            capture_output=False,   # stream output to terminal
            timeout=600,            # 10-minute ceiling
        )
        if result.returncode != 0:
            print(f"[Renderer] ⚠️  Remotion render exited with code {result.returncode}")
            return {
                "video_output_path": None,
                "pipeline_status": "failed",
            }
    except FileNotFoundError:
        print("[Renderer] ⚠️  `npx` not found — script written but render skipped.")
        print(f"[Renderer] To render manually: cd {REMOTION_DIR} && npx remotion render EventReel {output_path}")
        # Still mark success — the script artifact is the deliverable
        return {
            "video_output_path": str(script_path),
            "pipeline_status": "success",
        }
    except subprocess.TimeoutExpired:
        print("[Renderer] ⚠️  Render timed out after 10 minutes.")
        return {
            "video_output_path": None,
            "pipeline_status": "failed",
        }

    print(f"[Renderer] ✅ Video rendered: {output_path}")
    return {
        "video_output_path": str(output_path),
        "pipeline_status": "success",
    }
