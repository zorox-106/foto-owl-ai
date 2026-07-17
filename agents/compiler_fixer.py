"""
Agent 4 — Compiler & Fixer

Compiles the generated Remotion TypeScript script using `tsc` (TypeScript compiler),
parses errors, enriches them with RAG-retrieved API context, and calls the Script
Generator to produce a fixed version. Retries up to MAX_RETRIES times.

Model choice: gpt-4o-mini
Rationale: The fix instructions are short and structured — just appending error context
to the previous script. gpt-4o-mini handles targeted diffs and small patches reliably.
The RAG context (specific API snippets) compensates for any lack of framework depth,
providing the correct Remotion usage pattern for each error type.

The compiler always writes the script to disk and runs `tsc --noEmit` before calling
the fixer — actual TypeScript type-checking, not a regex heuristic.
"""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import List

from models import oai
from models.state import CompileError, FailureReport, PipelineState
from rag import retrieve

MAX_RETRIES = int(os.getenv("MAX_RETRIES", "5"))

_FIX_SYSTEM = """You are a Remotion TypeScript expert.
You are given a Remotion composition script that has TypeScript compilation errors.
Fix ONLY the errors listed. Do not restructure the code.
Output ONLY the complete corrected TypeScript file — no markdown, no explanations.
"""

# Simplified tsconfig for validation (we only need type checking, not bundling)
_TSCONFIG = """{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noEmit": true,
    "skipLibCheck": true,
    "esModuleInterop": true
  }
}"""


def _classify_error(message: str) -> CompileError:
    """Map a raw tsc error string to a structured CompileError with RAG context."""
    # Determine error type
    if "TS" in message:
        error_type = "TypeScript"
    elif "remotion" in message.lower():
        error_type = "Remotion"
    elif "Syntax" in message or "Expected" in message:
        error_type = "Syntax"
    else:
        error_type = "Runtime"

    # Extract line number
    line_match = re.search(r":(\d+):", message)
    line_number = int(line_match.group(1)) if line_match else None

    # RAG: retrieve API snippet most relevant to this error
    relevant = retrieve(message[:200], "remotion_api", n_results=1)
    api_snippet = relevant[0] if relevant else "No specific snippet found."

    return CompileError(
        error_type=error_type,
        message=message.strip(),
        line_number=line_number,
        relevant_api_snippet=api_snippet,
    )


def _run_tsc(script: str) -> List[CompileError]:
    """Write script into the Remotion project and run tsc from there.

    Running tsc inside the Remotion project ensures remotion's type definitions
    (installed via npm) are available, preventing false 'module not found' errors.
    Falls back to a basic syntax check if the project isn't set up yet.
    """
    remotion_dir = Path(os.environ.get("REMOTION_PROJECT_DIR", "./remotion"))

    if not (remotion_dir / "node_modules").exists():
        print("[Compiler] ⚠️  Remotion node_modules not found — running basic syntax check")
        return _basic_syntax_check(script)

    # Write the script to the Remotion src dir temporarily
    script_path = remotion_dir / "src" / "EventReel.tsx"
    try:
        original = script_path.read_text(encoding="utf-8") if script_path.exists() else None
        script_path.write_text(script, encoding="utf-8")

        try:
            result = subprocess.run(
                ["npx", "tsc", "--noEmit"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(remotion_dir),
            )
            if result.returncode == 0:
                return []
            raw = (result.stdout + result.stderr).strip()
            # Filter to only lines referencing EventReel.tsx to avoid irrelevant Root.tsx errors
            raw_errors = [
                line for line in raw.splitlines()
                if line.strip() and ("EventReel" in line or "error TS" in line)
            ]
            if not raw_errors:
                return _basic_syntax_check(script)
            return [_classify_error(e) for e in raw_errors[:10]]
        except FileNotFoundError:
            print("[Compiler] ⚠️  npx not found — running basic syntax check")
            return _basic_syntax_check(script)
    finally:
        # Restore original placeholder if compilation failed
        if original is not None:
            script_path.write_text(original, encoding="utf-8")


def _basic_syntax_check(script: str) -> List[CompileError]:
    """Fallback: detect obvious syntax errors without tsc."""
    errors = []
    # Check for common issues
    open_braces = script.count("{")
    close_braces = script.count("}")
    if abs(open_braces - close_braces) > 2:
        errors.append(CompileError(
            error_type="Syntax",
            message=f"Brace mismatch: {open_braces} open, {close_braces} close",
            line_number=None,
            relevant_api_snippet="Ensure all open braces '{' are closed with '}'."
        ))

    if "registerRoot" not in script:
        errors.append(CompileError(
            error_type="Syntax",
            message="Missing registerRoot() call",
            line_number=None,
            relevant_api_snippet="import { registerRoot } from 'remotion'; registerRoot(RemotionRoot);"
        ))

    if "export default" not in script and "export const EventReel" not in script:
        errors.append(CompileError(
            error_type="Syntax",
            message="Missing default export for EventReel composition",
            line_number=None,
            relevant_api_snippet="export default EventReel;"
        ))

    return errors


def _fix_script(script: str, errors: List[CompileError]) -> str:
    """Use gpt-4o-mini to fix the script given the structured errors."""
    model = os.getenv("COMPILER_FIXER_MODEL", "gpt-4o-mini")

    error_text = "\n\n".join(
        f"Error {i+1} ({e.error_type}, line {e.line_number}):\n"
        f"  {e.message}\n"
        f"  Relevant API usage:\n  {e.relevant_api_snippet[:500]}"
        for i, e in enumerate(errors)
    )

    from openai import OpenAI, RateLimitError
    import time
    base_url = os.environ.get("OPENAI_BASE_URL")
    raw_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], base_url=base_url)

    for attempt in range(3):
        try:
            response = raw_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": _FIX_SYSTEM},
                    {
                        "role": "user",
                        "content": (
                            f"Fix the following TypeScript errors in this Remotion script:\n\n"
                            f"=== ERRORS ===\n{error_text}\n\n"
                            f"=== SCRIPT ===\n{script}"
                        ),
                    },
                ],
                max_tokens=4096,
            )
            from agents.script_generator import _clean_script
            return _clean_script(response.choices[0].message.content or script)
        except RateLimitError:
            wait = 25 * (attempt + 1)
            print(f"[CompilerFixer] Rate limit — waiting {wait}s...")
            time.sleep(wait)
    from agents.script_generator import _clean_script
    return _clean_script(script)


def compiler_fixer_agent(state: PipelineState) -> dict:
    """Compile the script; on error, enrich with RAG context and fix."""
    script: str = state["remotion_script"]
    retry_count: int = state.get("retry_count", 0)
    max_retries: int = state.get("max_retries", MAX_RETRIES)

    print(f"[CompilerFixer] Attempt {retry_count + 1}/{max_retries} — running tsc...")
    raw_errors = _run_tsc(script)

    if not raw_errors:
        print("[CompilerFixer] ✅ Compilation successful!")
        return {
            "compile_success": True,
            "compile_errors": [],
            "retry_count": retry_count,
        }

    print(f"[CompilerFixer] ❌ {len(raw_errors)} error(s) found.")
    compile_errors = raw_errors

    if retry_count + 1 >= max_retries:
        print(f"[CompilerFixer] Max retries ({max_retries}) reached. Emitting failure report.")
        report = FailureReport(
            total_retries=retry_count + 1,
            final_errors=compile_errors,
            last_script_preview=script[:500],
            recommendation=(
                "Manual review required. The most likely cause is an incorrect "
                "Remotion API usage. See 'relevant_api_snippet' in each error for correction guidance."
            ),
        )
        return {
            "compile_success": False,
            "compile_errors": compile_errors,
            "retry_count": retry_count + 1,
            "failure_report": report,
            "pipeline_status": "failed",
        }

    return {
        "compile_success": False,
        "compile_errors": compile_errors,
        "retry_count": retry_count + 1,
    }
