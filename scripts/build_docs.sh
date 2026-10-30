#!/usr/bin/env bash
# Build the proposal and technical appendix as .docx and .pdf from the Markdown sources.
# Usage: scripts/build_docs.sh [outdir]   (default: docs/build)
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${1:-docs/build}"
mkdir -p "$OUT"
build () {
  local name="$1" ref="$2"
  pandoc "docs/${name}.md" --from markdown+smart --to docx --output "$OUT/${name}.docx" \
    --resource-path=docs:results/pilot_codex:. --reference-doc="$ref"
  if command -v soffice >/dev/null 2>&1; then
    soffice --headless --convert-to pdf --outdir "$OUT" "$OUT/${name}.docx" >/dev/null 2>&1 || echo "pdf conversion failed for $name"
  fi
}
build proposal docs/reference_proposal.docx
build technical_appendix docs/reference_appendix.docx
ls -la "$OUT"
