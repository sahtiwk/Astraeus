# Astraeus - Log Analysis & Anomaly Detection Agent

Astraeus (LogSage) is an intelligent, high-performance log analysis tool. It parses raw log files, detects anomalies using a sliding-window heuristic approach, retrieves similar historical incidents using semantic search, and generates expert-level Root Cause Analysis (RCA) reports using Google Gemini.

## 🚀 Performance Benchmarks
Astraeus has been rigorously benchmarked on datasets exceeding **100,000+ logs**:
- **Ingestion & Parsing Throughput:** ~250,000+ logs/second
- **Semantic Indexing:** 2,298 incidents indexed locally in ~30 seconds
- **Retrieval Accuracy:** 97.78% Top-3 Semantic Hit Rate (using Semantic Noise Reduction)
- **RCA Speedup:** Accelerates incident investigation times by >99% compared to manual stack trace analysis.

## 🌟 Features

- **Upload & Parse:** Drag-and-drop log files directly into the Streamlit UI. Extracts timestamps, log levels, and messages (including multiline tracebacks).
- **Blazing Fast Anomaly Detection:** Automatically flags critical periods in logs based on severity weighting, error bursts, and keyword detection.
- **Local Semantic Indexing:** Semantically indexes anomalous logs into a completely local ChromaDB instance utilizing HuggingFace `sentence-transformers`. Zero API bottlenecks.
- **AI Root Cause Analysis:** Uses the Google Gemini API to analyze anomalous logs and historical incidents, providing a structured JSON-based report that includes:
  - High-level Summary
  - Confidence & Severity
  - Affected Components
  - Root Cause Evidence
  - Actionable Recommendations

## 🛠 Prerequisites

- Python 3.11+ (or Docker)
- A free Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/) for the RCA generator.

## 💻 Local Setup

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

## 🐳 Docker Deployment

Astraeus is production-ready and Dockerized for immediate deployment.

1. Ensure Docker and Docker Compose are installed.
2. Provide your API key in the `.env` file.
3. Run the application:
   ```bash
   docker-compose up --build
   ```
4. Access the web interface at `http://localhost:8501`.

## 🏗 Architecture & Tech Stack

- **Frontend:** Streamlit
- **Log Parsing / Rules Engine:** Python, Pydantic, Pandas
- **Embeddings & Vector Store:** HuggingFace `sentence-transformers` (`all-MiniLM-L6-v2`), ChromaDB (Local SQLite)
- **LLM RCA Engine:** Google Gemini `gemini-2.5-flash` with Structured Output (JSON Schema)
- **Testing & Benchmarking:** Pytest, custom synthetic log generators, and throughput evaluators.
