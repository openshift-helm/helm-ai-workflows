# JIRA-to-Code: Agentic Workflow for Automated Code Generation

Automated code generation from JIRA issues using a two-stage agent architecture (Architect → Developer).

## Overview

This workflow demonstrates the modern SWE-agent pattern using **Pydantic models** for type-safe communication between agents.

```
JIRA Issue → Go AST Analysis → Pydantic Models → Implementation Plan → Code Changes
```

## Quick Start

```bash
# Test the complete pipeline (safe, no file changes)
./jira_to_code.sh example_jira.txt --dry-run

# View results
./view_latest_run.sh
```

All output is saved to `output/run_*/` directories.

## Architecture

### Two-Stage Agent Pattern

1. **Architect Agent** (Planning)
   - Reads Pydantic models (codebase understanding)
   - Analyzes JIRA acceptance criteria
   - Creates structured `ImplementationPlan`
   - Output: Type-safe plan with `AtomicTask[]`

2. **Developer Agent** (Execution)
   - Reads `ImplementationPlan`
   - Executes each task atomically
   - Generates actual code changes
   - Output: Modified files + results

### Why Pydantic Models?

Pydantic models provide **type-safe handoffs** between agents:
- ✅ Structured data, not unstructured text
- ✅ Schema validation at tool-call layer
- ✅ Self-documenting interfaces
- ✅ Easy to test and debug

## Scripts

| Script | Purpose |
|--------|---------|
| **jira_to_code.sh** | Complete end-to-end pipeline |
| **generate_models.sh** | Generate Pydantic models only |
| **view_latest_run.sh** | View latest pipeline run results |
| **jira_to_pydantic.py** | AST analysis + Pydantic model generation |
| **architect_agent.py** | Create implementation plans |
| **developer_agent.py** | Execute plans and generate code |
| **generate_helm_ast.go** | Parse Go code into JSON AST |

## Documentation

- 📖 **[QUICK_START.md](QUICK_START.md)** - Quick introduction and examples
- 📖 **[CODE_GENERATION_GUIDE.md](CODE_GENERATION_GUIDE.md)** - Complete usage guide
- 📖 **[README_JIRA_TO_PYDANTIC.md](README_JIRA_TO_PYDANTIC.md)** - Pydantic model generation details
- 📖 **[USAGE.md](USAGE.md)** - Basic usage patterns

## Example: HELM-480

The included example (`example_jira.txt`) demonstrates fixing HTTP status codes:

**Input:** JIRA issue about returning proper status codes (400, 404, 500 instead of 502)

**Output:**
1. Identifies relevant structs: `HelmRequest`, `helmHandlers`
2. Creates plan with 4 tasks:
   - Change `StatusBadGateway` → `StatusBadRequest` for invalid input
   - Add 404 handling for "not found" errors
   - Add helper function for status code logic
   - Add test cases
3. Generates actual code changes

Try it:
```bash
./jira_to_code.sh example_jira.txt --dry-run
./view_latest_run.sh plan
```

## Installation

### Prerequisites

- **Go 1.21+** (for AST generation)
- **Python 3.10+** (for agents)
- **Pydantic** (install: `pip install pydantic`)

### Setup

```bash
# 1. Clone this repo
git clone https://github.com/openshift-helm/helm-ai-workflows.git
cd helm-ai-workflows/jira-to-code

# 2. Make scripts executable
chmod +x *.sh *.py

# 3. Test with example
./jira_to_code.sh example_jira.txt --dry-run
```

## Usage

### Complete Pipeline

```bash
# Dry run (safe, shows what would be done)
./jira_to_code.sh path/to/jira_issue.txt --dry-run

# Apply changes for real
./jira_to_code.sh path/to/jira_issue.txt

# Review results
./view_latest_run.sh
git diff  # see actual code changes
```

### Individual Steps

```bash
# 1. Generate Pydantic models only
./generate_models.sh example_jira.txt output/models.py
cat output/models.py

# 2. Create implementation plan
python3 architect_agent.py output/models.py example_jira.txt output/plan.json
cat output/plan.json | jq .

# 3. Execute plan
python3 developer_agent.py output/plan.json --dry-run
python3 developer_agent.py output/plan.json  # for real
```

## Output Structure

```
output/
├── .gitignore              # Ignores generated files
├── README.md               # Output directory docs
├── helm_ast.json           # Latest AST (from generate_models.sh)
└── run_YYYYMMDD_HHMMSS/   # Timestamped runs
    ├── helm_ast.json              # Go code AST
    ├── pydantic_models.py         # Generated Pydantic models
    ├── implementation_plan.json   # Architect's plan
    └── execution_results.json     # Developer's results
```

## Integration with Claude API

For production use, integrate the Architect agent with Claude:

```python
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

response = client.messages.create(
    model="claude-sonnet-4-5",
    messages=[{"role": "user", "content": f"""
        JIRA: {jira_text}
        Relevant Structs: {pydantic_models}
        Create ImplementationPlan
    """}],
    tools=[{
        "name": "create_plan",
        "input_schema": ImplementationPlan.model_json_schema()
    }]
)

# Claude returns type-safe ImplementationPlan
plan = ImplementationPlan.model_validate(response.content[0].input)
```

See [CODE_GENERATION_GUIDE.md](CODE_GENERATION_GUIDE.md) for details.

## Status

🧪 **Experimental** - This is a proof-of-concept demonstrating the Architect/Developer agent pattern with Pydantic models.

Current implementation uses template-based planning. Production use would integrate with Claude API for AI-powered code generation.

## Contributing

Contributions welcome! Areas for improvement:
- AST-based code editing (vs string replacement)
- More sophisticated relevance scoring
- Support for other languages (TypeScript, Python, etc.)
- Integration tests
- Claude API integration examples

## License

Apache 2.0 (same as OpenShift Console)

## Related

- [OpenShift Console](https://github.com/openshift/console)
- [Console Dynamic Plugin SDK](https://github.com/openshift/console/tree/master/frontend/packages/console-dynamic-plugin-sdk)
