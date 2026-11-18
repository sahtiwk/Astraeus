#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
# Install uv 0.13.8 first using the official uv instructions.
command -v uv >/dev/null || { echo "Install uv 0.13.8 first"; exit 1; }
[ "$(uv --version)" = "uv 0.13.8" ] || { echo "Use uv 0.13.8"; exit 1; }
uv sync --frozen --python 3.11 --no-dev
uv pip check --python .venv/bin/python
printf 'Installed. Run .venv/bin/python -m src.launcher\n'
