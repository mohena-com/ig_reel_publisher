#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
PYTHON_EXE="$REPO_ROOT/.venv/bin/python"

if [ ! -x "$PYTHON_EXE" ]; then
    echo "Missing virtual environment at $PYTHON_EXE. Run: python3 -m venv .venv"
    exit 1
fi

CAROUSEL_ROOT="$REPO_ROOT/../output_carousel"

if [ ! -d "$CAROUSEL_ROOT" ]; then
    echo "Folder not found: $CAROUSEL_ROOT"
    exit 1
fi

shopt -s nullglob
job_dirs=("$CAROUSEL_ROOT"/*)

echo "Found ${#job_dirs[@]} job folders under $CAROUSEL_ROOT"

for job_dir in "${job_dirs[@]}"; do
    if [ ! -d "$job_dir" ]; then
        continue
    fi

    slide_count=$(find "$job_dir" -maxdepth 1 -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.webp' \) | wc -l)

    if [ "$slide_count" -lt 6 ]; then
        echo "Skipping $(basename "$job_dir") - only $slide_count slide files found"
        continue
    fi

    echo
    echo "===== Creating reel for: $(basename "$job_dir") ====="

    (
        cd "$REPO_ROOT"
        "$PYTHON_EXE" run.py create --input-dir "$job_dir"
    )
done

echo

echo "Finished processing all job folders."
