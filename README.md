# HelpDesk AI

HelpDesk AI is a local Streamlit prototype for IT support ticket triage. It classifies a ticket, searches a local troubleshooting knowledge base, produces a grounded suggested resolution, and records a human review decision for the current session.

This is a learning and portfolio project. It is not a production IT service-management platform and does not send emails, modify tickets, or change production systems.

## Current implementation

The current implementation includes:

- Streamlit user interface
- Environment-based configuration with `.env`
- Optional Gemini provider integration through the official `google-genai` SDK
- Local `sentence-transformers/all-MiniLM-L6-v2` embeddings
- Markdown and TXT knowledge-base loading
- Configurable chunking with stable chunk IDs
- Persistent local ChromaDB storage
- Cached embedding-model and vector-store resources for Streamlit reruns
- Explicit knowledge-base upload and indexing controls
- Deterministic ticket classification and priority recommendation
- LangGraph workflow with controlled local tools
- Retrieved passage and source visibility
- Grounded, uncertainty-aware suggested resolutions
- Session-local approve and reject/revise review actions
- Focused pytest coverage for ingestion, indexing, agent execution, and answer formatting

The evaluation tab is present in the UI but is not implemented yet. A formal evaluation dataset and evaluation runner remain future work.

## Architecture

The main data flow is:

1. Streamlit loads configuration and displays startup status.
2. Markdown/TXT files are loaded from `data/knowledge_base/`.
3. Documents are split into chunks with stable IDs.
4. Chunks are embedded locally using the configured sentence-transformers model.
5. Chunks are stored in a persistent ChromaDB collection under `storage/chroma/`.
6. A ticket is classified using the deterministic triage classifier.
7. The local vector store retrieves relevant passages.
8. The answer builder creates a structured, evidence-aware suggested resolution.
9. The user can review, edit, approve, or reject the suggestion locally.

The agent workflow in `src/agent/graph.py` uses these controlled tools:

- `get_ticket_details(ticket)`
- `calculate_priority(signals)`
- `search_knowledge_base(query)`

The workflow has conditional retrieval routing and a bounded execution configuration. A greeting or unrelated input does not intentionally trigger retrieval.

## Project structure

```text
app.py
requirements.txt
.env.example
data/
  knowledge_base/
storage/
  chroma/
src/
  agent/
    tools.py
    graph.py
  ingestion/
    loaders.py
    chunking.py
    indexer.py
  retrieval/
    vector_store.py
    retriever.py
  services/
    answer_generator.py
  triage/
    schemas.py
    classifier.py
    sample_tickets.py
tests/
```

## Local setup

The project uses the dedicated conda environment `helpdesk-ai` and Python 3.11.

```bash
source /home/sattu/miniconda3/etc/profile.d/conda.sh
conda activate helpdesk-ai
cd /home/sattu/HelpDesk
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Create the local environment file:

```bash
cp .env.example .env
```

Edit `.env` and set your values:

```dotenv
APP_ENV=development
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-3.8-flash
GEMINI_API_KEY=your_gemini_api_key_here
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

The `.env` file is ignored by Git. Never commit a real API key.

## Run the application

From the activated environment:

```bash
streamlit run app.py --server.headless true --server.port 8501 --server.address 127.0.0.1
```

Open [http://127.0.0.1:8501](http://127.0.0.1:8501).

On the first use of the local embedding model, sentence-transformers may download and initialize the model. Subsequent Streamlit reruns reuse the cached model and persistent Chroma store for the running process.

## Using the application

### Ticket triage

1. Select an example ticket or enter a custom ticket.
2. Select **Run Triage**.
3. Review:
   - category
   - priority recommendation
   - evidence terms
   - confidence explanation
   - retrieved passages and source filenames
   - suggested diagnostic steps
   - proposed resolution
   - missing information
   - citations
4. Edit the suggested resolution if needed.
5. Select **Approve** or **Reject / Revise**.

Approval only records a decision in the current Streamlit session. It does not perform an external action.

The **Run Agent Workflow** action additionally shows the tool activity recorded by the LangGraph workflow.

### Knowledge base

The Knowledge base tab supports:

- uploading `.md` and `.txt` files
- viewing the number of available local documents
- explicitly indexing or re-indexing the knowledge base
- searching the persistent local vector index
- inspecting retrieved excerpts and source names

Indexing is not performed automatically on every UI interaction. The local Chroma collection is reused when it already contains indexed chunks.

## Configuration

Configuration is loaded by [src/config.py](src/config.py) from `.env` and environment variables.

Important settings:

| Variable | Purpose | Default |
|---|---|---|
| `APP_ENV` | Application environment | `development` |
| `STREAMLIT_SERVER_PORT` | Configured application port | `8501` |
| `LLM_PROVIDER` | Provider selection | `gemini` |
| `GEMINI_MODEL` | Gemini model name | `gemini-3.8-flash` |
| `GEMINI_API_KEY` | Gemini API credential | unset |
| `EMBEDDING_MODEL` | Local embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| `KNOWLEDGE_BASE_DIR` | Knowledge-base directory | `data/knowledge_base` |
| `STORAGE_DIR` | Persistent Chroma directory | `storage/chroma` |
| `EVALUATION_DIR` | Reserved evaluation-data directory | `data/evaluation` |

The embedding model is local and does not require a Hugging Face token for the current public model configuration.

## Gemini provider status

The Gemini provider is isolated behind the interface in [src/llm_provider.py](src/llm_provider.py). It reads the API key and model from configuration and does not display the key.

The application performs a provider health check during startup when Gemini is configured. A missing key or API failure is reported as a warning so the local deterministic classification and retrieval features can still be inspected.

The current grounded answer builder is deterministic and uses retrieved passages directly. Gemini provider connectivity is available as a separate provider capability but is not required for the local retrieval/classification path.

## Testing

Run the current test suite with:

```bash
python -m pytest -q
```

The tests cover the current ingestion/indexing flow, agent workflow, and grounded-answer structure. The formal evaluation dataset and broader failure-mode tests are not implemented yet.

## Known limitations and remaining work

- The evaluation tab is currently a placeholder.
- No fixed 10-case evaluation dataset or evaluation runner exists yet.
- Retrieval does not yet apply a documented semantic relevance threshold for weak matches.
- Similarity values are displayed as scores derived from Chroma cosine distances; they should be treated as retrieval signals, not proof of correctness.
- Re-indexing updates or upserts current chunks but does not yet remove stale chunks for documents deleted from the knowledge-base directory.
- The grounded answer builder is deterministic rather than Gemini-generated.
- Gemini API availability depends on the configured model, account, quota, and service status.
- Human approval is session-local and does not update an external ticketing system.
- The project is not production-ready.
