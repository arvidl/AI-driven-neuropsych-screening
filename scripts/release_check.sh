#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

echo "==> Running blinded smoke tests"
python -m pytest tests/test_blinded_pipeline.py

echo
echo "==> Regenerating manuscript-linked blinded outputs"
python scripts/neuropsych_subj_pipeline.py subj_001 subj_048

echo
echo "Release check passed."
