#!/usr/bin/env bash
set -euo pipefail

BAKE_URL="${BAKE_URL:-http://dev.localhost:8000}"
OUT="src/hitchhikers/schemas"
TMP=$(mktemp -d)
trap "rm -rf $TMP" EXIT

CODEGEN_ARGS=(
    --input-file-type openapi
    --target-python-version 3.11
    --use-standard-collections
    --use-union-operator
)

echo "Generating v1 models..."
curl -s "$BAKE_URL/api/v1/openapi.json" \
    | python3 scripts/filter_openapi.py \
        "/api/v1/dais/document/" \
    > "$TMP/v1.json"
uvx --from datamodel-code-generator datamodel-codegen \
    "${CODEGEN_ARGS[@]}" \
    --input "$TMP/v1.json" \
    --output "$OUT/v1.py"

echo "Generating v2 models..."
curl -s "$BAKE_URL/api/openapi.json" \
    | python3 scripts/filter_openapi.py \
        "/api/v2/dais/documents" \
        "/api/v2/dais/documents/{document_id}" \
        "/api/v2/dais/documents/{document_id}/attributes" \
    > "$TMP/v2.json"
uvx --from datamodel-code-generator datamodel-codegen \
    "${CODEGEN_ARGS[@]}" \
    --input "$TMP/v2.json" \
    --output "$OUT/v2.py"

echo "Done. Re-run this script when the bake API changes."
