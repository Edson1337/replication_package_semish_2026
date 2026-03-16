# MIRA — Multi-Agent System for NFR and Test Scenario Generation

Replication package submitted to **SEMISH — Seminário Integrado de Software e Hardware**, part of **CSBC 2026 — Congresso da Sociedade Brasileira de Computação**.

This repository contains the multi-agent architecture implementation using CrewAI for the MIRA project, which automatically generates Non-Functional Requirements (NFRs) and Test Scenarios from User Stories.

## Features

- 🤖 **Multi-Agent Pipeline**: Three specialized agents (Integration, NFR Specialist, QA Engineer) with hierarchical orchestration
- 🗄️ **Vector Storage**: Qdrant for semantic storage and retrieval of user stories, NFRs, and test scenarios
- 🤖 **Embeddings**: Sentence Transformers for creating semantic embeddings
- 🔌 **JIRA Integration**: Fetch user stories directly from JIRA via MCP Server
- 📄 **Document Generation**: Automatic export of results as JSON and `.docx`
- ⚙️ **Hybrid Configuration**: YAML for structure + `.env` for sensitive credentials
- 🐳 **Docker Support**: Easy Qdrant deployment with Docker Compose

## 📋 Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) installed.
- LLM API key configured in `.env` file (`LLM_API_KEY`) — supports Gemini, OpenRouter, or compatible.
- Qdrant instance running (Localhost or Cloud).

## 🛠️ Installation

This project uses `uv` for dependency management.

```bash
# In the multi-agents-core folder
uv sync
```

This will install all dependencies listed in `pyproject.toml` and create the virtual environment.

## ⚙️ Configuration

Edit the `.env` file to customize:

- `LLM_API_KEY`: LLM provider API key (Gemini: [get it here](https://aistudio.google.com/app/apikey))
- `LLM_MODEL`: Model name (e.g. `gemini-2.0-flash-exp`)
- `LLM_BASE_URL`: Optional, for OpenRouter or compatible endpoints
- `QDRANT_URL`: Qdrant server URL (default: `http://localhost:6333`)
- `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`: Required if `story_source: jira` in `config.yaml`

Structural settings are managed in `config.yaml`. Variables with `${VAR}` syntax are resolved automatically from `.env`.

## 🐳 Start Qdrant Database

Using Docker Compose:
```bash
docker-compose up -d
```

Or directly with Docker:
```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

Access the Qdrant web interface at: http://localhost:6333/dashboard

## 🚀 How to Run

To start the agent orchestration via CLI:

```bash
uv run crew_main.py
```

Or via the Streamlit web interface:

```bash
uv run streamlit run streamlit_app.py
```

This will:
1. Fetch user stories (from local JSON or JIRA, based on `config.yaml`)
2. Generate NFRs from the user stories
3. Generate test scenarios from the NFRs
4. Save individual and consolidated results to `data/`
5. Generate a `.docx` requirements document

## 📂 Structure

- `crew_main.py`: Main file that configures and executes the Crew.
- `agents.py`: Agent definitions (Roles, Goals, Backstories).
- `tasks.py`: Task definitions and integration with the original prompts.
- `config.py`: Centralized config loader (`config.yaml` + `.env`).
- `config.yaml`: Structural configuration (collections, models, providers).
- `models/`: DTOs for User Stories, NFRs, and Test Scenarios.
- `tools/`: Custom tools (Qdrant, File Reading, JIRA, Data Output, Doc Generator).
- `mcp_servers/`: MCP Server for JIRA integration.
- `prompts/`: Prompts for NFR and test scenario generation.
- `data/`: Generated results (not versioned).

## 📚 Dependencies

- **crewai** — Multi-agent orchestration framework
- **qdrant-client** — Vector database client
- **sentence-transformers** — For generating embeddings
- **python-dotenv** — Environment configuration
- **pyyaml** — YAML configuration parsing
- **pydantic** — DTOs and data validation
- **python-docx** — `.docx` document generation
- **python-jira** — JIRA integration
- **mcp** — Model Context Protocol for MCP tools

## 🧪 Experiment Results

The `experiments/results/` directory contains the outputs obtained from our experiment, where the pipeline generated a requirements document containing User Stories, NFRs, and Test Scenarios. This document (`requirements_document.pdf`) was used in the study conducted with software professionals to evaluate the quality of the generated artifacts.

## License

This project is part of the MIRA research project — SEMISH/CSBC 2026.
