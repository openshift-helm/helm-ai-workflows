#!/bin/bash
#
# Quick script to generate Pydantic models from JIRA issue
#
# Usage:
#   ./generate_models.sh <jira_text_file> [output_file]
#   cat jira.txt | ./generate_models.sh - [output_file]
#   ./generate_models.sh - output.py <<< "JIRA-123: Add feature..."
#
# If output_file is not specified, prints to stdout.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Create output directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/output"
AST_OUTPUT="$SCRIPT_DIR/output/helm_ast.json"

echo "🚀 Generating Helm AST..." >&2
cd "$SCRIPT_DIR"
go run generate_helm_ast.go > "$AST_OUTPUT"

echo "" >&2
echo "🔍 Analyzing JIRA and generating Pydantic models..." >&2
echo "" >&2

if [ $# -eq 0 ]; then
    echo "Usage: $0 <jira_text_file> [output_file]" >&2
    echo "   Or: cat jira.txt | $0 - [output_file]" >&2
    exit 1
fi

JIRA_INPUT="$1"
OUTPUT_FILE="${2:-}"

if [ -n "$OUTPUT_FILE" ]; then
    python3 "$SCRIPT_DIR/jira_to_pydantic.py" "$AST_OUTPUT" "$JIRA_INPUT" "$OUTPUT_FILE"
else
    python3 "$SCRIPT_DIR/jira_to_pydantic.py" "$AST_OUTPUT" "$JIRA_INPUT"
fi
