#!/bin/bash
#
# Complete JIRA to Code Workflow
#
# This script orchestrates the full pipeline:
#   JIRA Issue → Pydantic Models → Implementation Plan → Code Changes
#
# Usage:
#   ./jira_to_code.sh <jira_text_file> [--dry-run]
#
# Example:
#   ./jira_to_code.sh scripts/example_jira.txt
#   ./jira_to_code.sh scripts/example_jira.txt --dry-run
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

JIRA_FILE="$1"
DRY_RUN_FLAG=""

if [ "$2" == "--dry-run" ]; then
    DRY_RUN_FLAG="--dry-run"
fi

if [ -z "$JIRA_FILE" ]; then
    echo "Usage: $0 <jira_text_file> [--dry-run]"
    exit 1
fi

# Output directory
OUTPUT_DIR="$SCRIPT_DIR/output/run_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_DIR"

echo "🚀 JIRA to Code Pipeline"
echo "========================"
echo "JIRA: $JIRA_FILE"
echo "Output: $OUTPUT_DIR"
if [ -n "$DRY_RUN_FLAG" ]; then
    echo "Mode: DRY RUN (no files will be modified)"
else
    echo "Mode: LIVE (files will be modified)"
fi
echo ""

# Step 1: Generate AST
echo "📊 Step 1/4: Generating Go AST..."
cd "$SCRIPT_DIR"
go run generate_helm_ast.go > "$OUTPUT_DIR/helm_ast.json"
echo "   ✓ AST saved to $OUTPUT_DIR/helm_ast.json"
echo ""

# Step 2: Generate Pydantic Models
echo "🔍 Step 2/4: Analyzing JIRA and generating Pydantic models..."
python3 "$SCRIPT_DIR/jira_to_pydantic.py" \
    "$OUTPUT_DIR/helm_ast.json" \
    "$JIRA_FILE" \
    "$OUTPUT_DIR/pydantic_models.py"
echo "   ✓ Models saved to $OUTPUT_DIR/pydantic_models.py"
echo ""

# Step 3: Create Implementation Plan (Architect Agent)
echo "🏗️  Step 3/4: Creating implementation plan (Architect Agent)..."
python3 "$SCRIPT_DIR/architect_agent.py" \
    "$OUTPUT_DIR/pydantic_models.py" \
    "$JIRA_FILE" \
    "$OUTPUT_DIR/implementation_plan.json"
echo "   ✓ Plan saved to $OUTPUT_DIR/implementation_plan.json"
echo ""

# Step 4: Execute Plan (Developer Agent)
echo "🔨 Step 4/4: Executing plan (Developer Agent)..."
python3 "$SCRIPT_DIR/developer_agent.py" \
    "$OUTPUT_DIR/implementation_plan.json" \
    $DRY_RUN_FLAG \
    > "$OUTPUT_DIR/execution_results.json"
echo "   ✓ Results saved to $OUTPUT_DIR/execution_results.json"
echo ""

# Summary
echo "═══════════════════════════════════════════════════════════════"
echo "✅ PIPELINE COMPLETE"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📁 All outputs saved to: $OUTPUT_DIR"
echo ""
echo "Files generated:"
echo "  1. helm_ast.json             - Go code AST"
echo "  2. pydantic_models.py        - Relevant structs as Pydantic models"
echo "  3. implementation_plan.json  - Architect's implementation plan"
echo "  4. execution_results.json    - Developer's execution results"
echo ""
echo "Next steps:"
echo "  • Review the plan: cat $OUTPUT_DIR/implementation_plan.json | jq ."
echo "  • View results: cat $OUTPUT_DIR/execution_results.json | jq ."
echo "  • Review models: cat $OUTPUT_DIR/pydantic_models.py"
echo ""

if [ -n "$DRY_RUN_FLAG" ]; then
    echo "💡 This was a DRY RUN. To apply changes, run without --dry-run"
else
    echo "⚠️  Code changes have been applied! Review with git diff"
fi
