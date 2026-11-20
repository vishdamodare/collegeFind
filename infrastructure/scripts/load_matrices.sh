#!/usr/bin/env bash
# Load parsed CET seat-matrix PDFs into the database named by DATABASE_URL_UNPOOLED in .env.local (Neon).
# Usage: infrastructure/scripts/load_matrices.sh 2022 2023 2024
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
set -a; . "$ROOT/.env.local"; set +a
export DATABASE_URL="$DATABASE_URL_UNPOOLED"
cd "$ROOT/backend"
export PYTHONPATH=".:../data-engine"
for y in "$@"; do
  label="${y}-$(printf '%02d' $(( (y + 1) % 100 )))"
  echo "== seat matrix $y"
  "$ROOT/.venv/bin/python" ../data-engine/importers/seat_matrix_importer.py "$ROOT/data/raw/${y}SeatMatrix.pdf" \
      "http://fe2025.mahacet.org/${y}/${y}SeatMatrix.pdf" "$label"
done
echo MATRICES-DONE
