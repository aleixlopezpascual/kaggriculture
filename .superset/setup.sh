#!/usr/bin/env bash
set -euo pipefail
cd "$SUPERSET_WORKSPACE_PATH"

# Personal project: always use public PyPI, ignoring any corporate index
# configured via PIP_INDEX_URL/UV_INDEX_URL in the shell environment.
unset PIP_INDEX_URL UV_INDEX_URL

if command -v uv >/dev/null 2>&1; then
  uv venv .venv
  uv pip install --index-url https://pypi.org/simple --python .venv/bin/python -r requirements.txt
else
  python3 -m venv .venv
  .venv/bin/pip install --index-url https://pypi.org/simple --upgrade pip
  .venv/bin/pip install --index-url https://pypi.org/simple -r requirements.txt
fi
