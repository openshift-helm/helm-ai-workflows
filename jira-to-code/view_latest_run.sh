#!/bin/bash
#
# View Latest Run - Quick helper to inspect the most recent pipeline run
#
# Usage:
#   ./view_latest_run.sh              # Show summary
#   ./view_latest_run.sh plan         # Show implementation plan
#   ./view_latest_run.sh models       # Show Pydantic models
#   ./view_latest_run.sh results      # Show execution results
#   ./view_latest_run.sh ast          # Show AST (large)
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/output"

# Find latest run
LATEST_RUN=$(ls -dt "$OUTPUT_DIR"/run_* 2>/dev/null | head -1)

if [ -z "$LATEST_RUN" ]; then
    echo "❌ No runs found in $OUTPUT_DIR"
    echo "Run the pipeline first: ./scripts/jira_to_code.sh scripts/example_jira.txt --dry-run"
    exit 1
fi

RUN_NAME=$(basename "$LATEST_RUN")

# Default: show summary
COMMAND="${1:-summary}"

case "$COMMAND" in
    summary)
        echo "📊 Latest Run: $RUN_NAME"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "📁 Location: $LATEST_RUN"
        echo ""
        echo "Files:"
        ls -lh "$LATEST_RUN" | tail -n +2 | awk '{printf "  %-30s %6s\n", $9, $5}'
        echo ""
        echo "Quick commands:"
        echo "  ./view_latest_run.sh plan      # View implementation plan"
        echo "  ./view_latest_run.sh models    # View Pydantic models"
        echo "  ./view_latest_run.sh results   # View execution results"
        echo ""
        echo "Or directly:"
        echo "  cat $LATEST_RUN/implementation_plan.json | jq ."
        ;;

    plan)
        if [ -f "$LATEST_RUN/implementation_plan.json" ]; then
            echo "📋 Implementation Plan ($RUN_NAME)"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            if command -v jq &> /dev/null; then
                cat "$LATEST_RUN/implementation_plan.json" | jq .
            else
                cat "$LATEST_RUN/implementation_plan.json"
            fi
        else
            echo "❌ implementation_plan.json not found in $LATEST_RUN"
        fi
        ;;

    models)
        if [ -f "$LATEST_RUN/pydantic_models.py" ]; then
            echo "🔍 Pydantic Models ($RUN_NAME)"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            cat "$LATEST_RUN/pydantic_models.py"
        else
            echo "❌ pydantic_models.py not found in $LATEST_RUN"
        fi
        ;;

    results)
        if [ -f "$LATEST_RUN/execution_results.json" ]; then
            echo "✅ Execution Results ($RUN_NAME)"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            if command -v jq &> /dev/null; then
                cat "$LATEST_RUN/execution_results.json" | jq .
            else
                cat "$LATEST_RUN/execution_results.json"
            fi
        else
            echo "❌ execution_results.json not found in $LATEST_RUN"
        fi
        ;;

    ast)
        if [ -f "$LATEST_RUN/helm_ast.json" ]; then
            echo "🌳 AST ($RUN_NAME)"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            if command -v jq &> /dev/null; then
                cat "$LATEST_RUN/helm_ast.json" | jq . | less
            else
                less "$LATEST_RUN/helm_ast.json"
            fi
        else
            echo "❌ helm_ast.json not found in $LATEST_RUN"
        fi
        ;;

    *)
        echo "Usage: $0 [summary|plan|models|results|ast]"
        exit 1
        ;;
esac
