#!/usr/bin/env bash
# Build the proposal and technical appendix as .docx and .pdf from the Markdown sources.
# Usage: scripts/build_docs.sh [outdir]   (default: docs/build)
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${1:-docs/build}"
mkdir -p "$OUT"
for name in proposal technical_appendix; do
  src="docs/${name}.md"
  pandoc "$src" --from markdown+smart --to docx --output "$OUT/${name}.docx" \
    --resource-path=docs:results/pilot_codex:. ${REFERENCE_DOCX:+--reference-doc="$REFERENCE_DOCX"}
  if command -v soffice >/dev/null 2>&1; then
    soffice --headless --convert-to pdf --outdir "$OUT" "$OUT/${name}.docx" >/dev/null 2>&1 || echo "pdf conversion failed for $name"
  fi
done
ls -la "$OUT"
