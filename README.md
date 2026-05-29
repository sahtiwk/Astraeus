# Astraeus - Log Analysis & Anomaly Detection Agent

Astraeus is an intelligent, cloud-assisted log analysis tool. It parses log files, detects anomalies using a sliding-window heuristic approach, retrieves similar historical incidents using semantic search (ChromaDB), and generates expert-level Root Cause Analysis (RCA) reports using the Google Gemini LLM.

## Features

- **Upload & Parse:** Drag-and-drop log files directly into the Streamlit UI. Extracts timestamps, log levels, and messages (including multiline tracebacks).
- **Anomaly Detection:** Automatically flags critical periods in logs based on severity weighting, error bursts, and keyword detection.
- **Historical Context:** Semantically indexes anomalous logs into a local ChromaDB instance to retrieve similar past incidents.
- **AI Root Cause Analysis:** Uses the Google Gemini API to analyze anomalous logs and historical incidents, providing a structured JSON-based report that includes:
  - High-level Summary
  - Confidence & Severity
  - Affected Components
  - Root Cause Evidence
  - Actionable Recommendations

## Prerequisites

- Python 3.11+ (or Docker)
- A free Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/)

## Local Setup

1. **Clone the repository** (or navigate to the project directory).
2. **Set up your environment:**
   Rename `.env.example` to `.env` and insert your Gemini API Key:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the application:**
   ```bash
   streamlit run app.py
   ```
   *Note: If you don't use a `.env` file, you can also enter your API key directly in the app's sidebar configuration.*

## Docker Deployment

You can run Astraeus entirely in a Docker container to ensure all dependencies and vector databases are fully isolated.

1. Ensure Docker and Docker Compose are installed.
2. Provide your API key in the `.env` file.
3. Run the application:
   ```bash
   docker-compose up --build
   ```
4. Access the web interface at `http://localhost:8501`.

## Sample Data

You can find sample log files in the `data/samples/` directory to test the application immediately:
- `app_error.log`: Simulates application crashes and NullPointerExceptions.
- `db_timeout.log`: Simulates database connection pool exhaustion and timeouts.
- `nginx_500.log`: Simulates HTTP 500 server error spikes.

## Architecture & Tech Stack

- **Frontend:** Streamlit
- **Log Parsing / Rules Engine:** Python, Pydantic, Pandas
- **Embeddings & Vector Store:** Google Gemini `text-embedding-004`, ChromaDB (Local SQLite)
- **LLM RCA Engine:** Google Gemini `gemini-2.5-flash` with Structured Output (JSON Schema)
- **Testing:** Pytest with mocked LLM/Vector endpoints
