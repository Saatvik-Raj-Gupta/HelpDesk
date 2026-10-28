# HelpDesk AI

This repository contains the local HelpDesk AI prototype foundation and the Gemini configuration layer required for AI-backed generation.

## Local setup

1. Open a shell and activate the project conda environment:
   ```bash
   source /home/sattu/miniconda3/etc/profile.d/conda.sh
   conda activate helpdesk-ai
   ```
2. Install the project dependencies:
   ```bash
   cd /home/sattu/HelpDesk
   pip install -r requirements.txt
   ```
3. Copy the environment template and add your Gemini API key:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and set:
   ```dotenv
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-3.8-flash
   ```
4. Start the app:
   ```bash
   streamlit run app.py --server.headless true --server.port 8501
   ```
5. Open http://localhost:8501

## Gemini configuration

- The project uses the official `google-genai` SDK instead of adding LangChain for this configuration-only step.
- The application reads `GEMINI_API_KEY` and `GEMINI_MODEL` from `.env` through `src/config.py`.
- The embedding model remains `sentence-transformers/all-MiniLM-L6-v2` for local document and query embeddings.
- The provider is isolated behind a small interface in `src/llm_provider.py` so a stub provider can be used in tests.

## Current status

This repository currently includes the Gemini configuration and startup checks, but not the full RAG or agent workflow yet.
