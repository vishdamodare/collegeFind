#!/usr/bin/env bash
# Load parsed CET cut-off PDFs into the database named by DATABASE_URL_UNPOOLED in .env.local (Neon).
# Usage: infrastructure/scripts/load_cutoffs.sh 2022:1 2022:2 ...   (YEAR:ROUND pairs)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
set -a; . "$ROOT/.env.local"; set +a
export DATABASE_URL="$DATABASE_URL_UNPOOLED"        # bulk work uses the direct (unpooled) connection
cd "$ROOT/backend"
export PYTHONPATH=".:../data-engine"
PY="$ROOT/.venv/bin/python"
"$ROOT/.venv/bin/alembic" upgrade head
"$PY" scripts/seed.py
for pair in "$@"; do
  y="${pair%%:*}"; r="${pair##*:}"
  f="$ROOT/data/raw/${y}ENGG_CAP${r}_CutOff.pdf"
  label="${y}-$(printf '%02d' $(( (y + 1) % 100 )))"
  extra=()
  # The CET Cell titled its 2022 Round I Maharashtra list "All India Seats"; see KNOWN_LIMITATIONS.md.
  if [ "$y" = "2022" ] && [ "$r" = "1" ]; then
    extra=(--allow-header-mismatch "2022 CAP-I file is mis-titled 'All India'; content has Home University sections and matches 2022 CAP-II scale (see KNOWN_LIMITATIONS.md)")
  fi
  echo "== $y round $r"
  "$PY" ../data-engine/importers/cet_cutoff_importer.py "$f" "http://fe2025.mahacet.org/${y}/${y}ENGG_CAP${r}_CutOff.pdf" "$label" "$r" ${extra[@]+"${extra[@]}"}
done
echo ALL-DONE
