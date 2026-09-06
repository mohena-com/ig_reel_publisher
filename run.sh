#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f ".env" ]; then
  echo "ERROR: .env not found."
  echo "Create it from .env.example first."
  exit 1
fi

docker compose run --rm reel-publisher "$@"
