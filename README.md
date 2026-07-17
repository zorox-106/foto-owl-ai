# FotoOwl AI Take-home: Image-to-Video Multiagent Pipeline

This repository implements a multiagent system orchestrated using **LangGraph** to convert a folder of event photos and a short text prompt into a rendered **Remotion** video reel.

## Pipeline Architecture

The workflow is modeled as a StateGraph with a double-loop compiler self-correction mechanism:

```mermaid
graph TD
    Start([Start]) --> IP[Intent Parser]
    IP --> IA[Image Analyser]
    IA --> SW[Storyboard Writer]
    SW --> SG[Script Generator]
    SG --> CF[Compiler & Fixer]
    
    CF --> Route{"compile_success?"}
    Route -- "Yes" --> R[Renderer]
    Route -- "No (retry < max)" --> SG
    Route -- "No (retry >= max)" --> FailEnd([END / Failure])
    
    R --> SuccessEnd([END / Success])
```

## Project Structure

- `agents/`: The five pipeline agents + intent parser:
  - `intent_parser.py`: Parses the raw user prompt into a structured creative brief.
  - `image_analyser.py`: Uses a vision model (`gpt-4o`) to score image quality and relevance.
  - `storyboard_writer.py`: Creates a narrative storyboard with transitions and animations.
  - `script_generator.py`: Generates the Remotion composition code using Claude Sonnet.
  - `compiler_fixer.py`: Compiles the TSX script and runs an iterative fix loop on compilation errors.
  - `renderer.py`: Invokes the Remotion CLI to render the composition.
- `graph/`: LangGraph orchestrator state-machine.
- `models/`: Shared Pydantic schemas and LLM clients.
- `rag/`: ChromaDB local vector store for loading style guides and Remotion code reference snippets.
- `remotion/`: The React-based Remotion video composition project.
- `tests/`: A full, mocked unit and integration test suite.
- `main.py`: The pipeline CLI command runner.

## Model Selection Rationale

The architecture follows a hybrid multi-model strategy to balance **cost, latency, and quality** across distinct agent steps:

| Agent | Default Model | Override Model (Groq) | Cost | Latency | Quality / Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Intent Parser** | `gpt-4o-mini` | `llama-4-scout-17b` | Very Low | Low | Straightforward text classification and extraction. Smaller models handle structured JSON parsing perfectly at a fraction of the cost. |
| **Image Analyser** | `gpt-4o` | `llama-4-scout-17b` | High | High | Vision capability is required. Requires high quality spatial/aesthetic understanding of images to construct narrative cues. Falls back to text heuristics when using keys without vision. |
| **Storyboard Writer** | `gpt-4o-mini` | `llama-4-scout-17b` | Low | Medium | Pure reasoning and sequence construction. Since images are already described, no vision is needed. Uses structured Pydantic formatting to map out the visual sequence. |
| **Script Generator** | Claude Sonnet | `llama-4-scout-17b` | High | High | Highly complex TSX code generation. Remotion-specific API rules are loaded from RAG, demanding a large context window and strong syntax compliance to minimize compile errors. |
| **Compiler & Fixer** | `gpt-4o-mini` | `llama-4-scout-17b` | Low | Low | Targeted diff repair. Relies on structured error traces and targeted code fixes. A fast, low-latency model is perfect for iterative compiler feedback loops. |

## Setup and Installation

1. Create a Python 3.11+ virtual environment and install the package:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -e ".[dev]"
   ```

2. Install Remotion project dependencies:
   ```bash
   cd remotion
   npm install
   ```

3. Create a `.env` file from the template and fill in your keys:
   ```bash
   cp .env.example .env
   ```

## Usage

### 1. Seed the RAG Store
Before running the pipeline, load the reference documentation and style guides into the vector store:
```bash
python main.py --seed-rag
```

### 2. Run the Pipeline
To generate a video from a folder of images, pass a prompt and the images directory:
```bash
python main.py --prompt "Cinematic wedding reel, slow and emotional, warm tones" --images-dir . --max-images 10
```

To run a sports reel from pickleball photos:
```bash
python main.py --prompt "Upbeat sports highlights, high energy, fast cuts" --images-dir . --max-images 12
```

The final rendered video will be saved in the `out/` folder (e.g. `out/Wedding_Highlights.mp4`).

## Test Suite
The repository includes a complete test suite with unit tests for every agent and integration tests for the full LangGraph loop. All external API calls and rendering steps are mocked so you do not need active API keys or credentials to run them:
```bash
pytest tests/ -v
```

## Pipeline Artifacts & Visuals

Here is a visual overview of the pipeline's outputs and structures:

### 1. Example Rendered Video Frame
Below is an example frame showing a wedding scene with the opening text overlay:

![Rendered Video Frame](assets/rendered_video_frame.png)

### 2. Output Folder Structure
After execution, the `out/` folder is structured as follows:
```text
out/
├── Wedding_Highlights.mp4    # Rendered MP4 video output (11.3 MB)
├── storyboard.json           # Narrative storyboard driving the rendering
├── EventReel.tsx             # Generated Remotion TypeScript script
└── pipeline_state.json       # Full serialized state from the LangGraph run
```

### 3. Example Storyboard Configuration (`storyboard.json`)
The generated storyboard contains metadata and scene descriptions mapping images to transitions/animations:

```json
{
  "title": "Wedding Highlights",
  "total_duration_seconds": 45.0,
  "narrative_arc": "open → build → close",
  "scenes": [
    {
      "order": 0,
      "image_path": "AHD_6008.jpg",
      "duration_seconds": 6.0,
      "caption": null,
      "transition_in": "fade",
      "animation": "ken_burns",
      "scene_note": "Establishing moment"
    },
    {
      "order": 1,
      "image_path": "AHD_6020.jpg",
      "duration_seconds": 5.0,
      "caption": "Their love shines bright",
      "transition_in": "dissolve",
      "animation": "zoom_in",
      "scene_note": "Building emotional resonance"
    },
    {
      "order": 2,
      "image_path": "AHD_6024.jpg",
      "duration_seconds": 6.0,
      "caption": null,
      "transition_in": "fade",
      "animation": "static",
      "scene_note": "Climactic moment"
    }
  ],
  "opening_text": "A moment to remember",
  "closing_text": "Forever begins"
}
```
