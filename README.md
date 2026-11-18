# Astraeus for Windows

Investigate local logs, group incidents, search local history and generate optional
diagnostic hypotheses with a CPU model on your computer.

Extract the Windows release ZIP, double-click **Install Astraeus.cmd**, choose a
setup profile, then double-click **Start Astraeus.cmd**. Python is installed
privately during setup. Setup requires internet. Prepared analysis runs locally.

Read [Windows quick start](WINDOWS_QUICKSTART.md) for setup, data locations,
offline operation, troubleshooting and current device requirements.

The application supports file/folder import, incident filters and timelines,
source evidence, per-project history, persistent diagnosis jobs, cancellation,
restart handling, and JSON/Markdown report export. Models are optional.

See [validation](VALIDATION.md), [architecture](docs/ARCHITECTURE.md),
[model evaluation](docs/MODEL_CARD.md), and [compatibility](docs/COMPATIBILITY.md).
Reports are diagnostic hypotheses. Verify suggested causes against the evidence.

## Development

Use Python 3.11-3.13 and uv 0.13.8:

    uv sync --frozen --python 3.11
    uv run python -m pytest -q
    uv run python scripts/package_release.py

The public sample demo is at https://astraeus-demo.onrender.com.
The Windows release candidate is unsigned and requires a full-folder extraction.
