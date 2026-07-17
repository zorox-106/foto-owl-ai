"""
FotoOwl Image-to-Video Pipeline — main entry point.

Usage:
    python main.py --prompt "Cinematic wedding reel, warm and emotional" --images-dir ./images
    python main.py --prompt "Upbeat sports highlights" --images-dir . --max-images 8
    python main.py --seed-rag  # re-seed the vector store from documents/
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}


def collect_images(images_dir: str, max_images: int | None = None) -> list[str]:
    """Collect all image files from the specified directory."""
    base = Path(images_dir)
    if not base.exists():
        print(f"❌ Images directory not found: {images_dir}")
        sys.exit(1)

    paths = []
    for ext in IMAGE_EXTENSIONS:
        paths.extend(base.glob(f"*{ext}"))
        paths.extend(base.glob(f"*{ext.upper()}"))

    paths = sorted(set(str(p.resolve()) for p in paths))

    if not paths:
        print(f"❌ No images found in {images_dir}")
        sys.exit(1)

    if max_images:
        paths = paths[:max_images]

    return paths


def run_pipeline(prompt: str, images_dir: str, max_images: int | None = None) -> dict:
    """Run the full LangGraph pipeline and return the final state."""
    from graph.pipeline import pipeline
    from models.state import PipelineState

    image_paths = collect_images(images_dir, max_images)
    print(f"🖼️  Found {len(image_paths)} images in {images_dir}")
    print(f"📝 Prompt: {prompt}\n")

    initial_state: PipelineState = {  # type: ignore[typeddict-item]
        "image_paths": image_paths,
        "raw_prompt": prompt,
        "video_intent": None,
        "image_analyses": [],
        "selected_images": [],
        "storyboard": None,
        "remotion_script": "",
        "compile_success": False,
        "compile_errors": [],
        "retry_count": 0,
        "max_retries": int(os.getenv("MAX_RETRIES", "3")),
        "video_output_path": None,
        "failure_report": None,
        "pipeline_status": "running",
    }

    final_state = pipeline.invoke(initial_state)
    return final_state


def print_summary(final_state: dict) -> None:
    """Print a clean summary of the pipeline run."""
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)

    status = final_state.get("pipeline_status", "unknown")
    print(f"Status:     {status.upper()}")

    if storyboard := final_state.get("storyboard"):
        print(f"Title:      {storyboard.title}")
        print(f"Duration:   {storyboard.total_duration_seconds:.1f}s")
        print(f"Scenes:     {len(storyboard.scenes)}")

    if output := final_state.get("video_output_path"):
        print(f"Output:     {output}")

    if report := final_state.get("failure_report"):
        print(f"Failures:   {report.total_retries} retries exhausted")
        print(f"Recommendation: {report.recommendation}")

    retries = final_state.get("retry_count", 0)
    print(f"Retries:    {retries}")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="FotoOwl Image-to-Video Multiagent Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --prompt "Cinematic wedding reel, warm golden tones, slow and emotional"
  python main.py --prompt "Upbeat sports highlights" --images-dir . --max-images 8
  python main.py --seed-rag
        """,
    )
    parser.add_argument("--prompt", "-p", type=str, help="Video generation prompt")
    parser.add_argument(
        "--images-dir", "-d",
        type=str,
        default=os.getenv("IMAGES_DIR", "."),
        help="Directory containing event images (default: current directory)",
    )
    parser.add_argument(
        "--max-images", "-n",
        type=int,
        default=int(os.getenv("MAX_IMAGES", "12")),
        help="Maximum number of images to process (default: 12)",
    )
    parser.add_argument(
        "--seed-rag",
        action="store_true",
        help="Seed/refresh the vector store from documents/ then exit",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Optional path to write the final state as JSON",
    )

    args = parser.parse_args()

    if args.seed_rag:
        print("🌱 Seeding vector store...")
        from rag import seed_vector_store
        seed_vector_store(force=True)
        print("✅ Vector store seeded.")
        return

    if not args.prompt:
        parser.error("--prompt is required unless using --seed-rag")

    final_state = run_pipeline(args.prompt, args.images_dir, args.max_images)
    print_summary(final_state)

    if args.output_json:
        # Serialize to JSON (Pydantic models → dicts)
        import dataclasses

        def _default(obj):
            if hasattr(obj, "model_dump"):
                return obj.model_dump()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        with open(args.output_json, "w") as f:
            json.dump(final_state, f, indent=2, default=_default)
        print(f"\n📄 State written to {args.output_json}")


if __name__ == "__main__":
    main()
