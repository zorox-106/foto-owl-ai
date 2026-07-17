# FotoOwl AI Take-home: Image-to-Video Multiagent Pipeline

This repository implements a multiagent system orchestrated using **LangGraph** to convert a folder of event photos and a short text prompt into a rendered **Remotion** video reel.

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
