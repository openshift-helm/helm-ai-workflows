# JIRA to Pydantic Model Generator

This tool analyzes the Go code AST from `pkg/helm` and generates relevant Pydantic models based on JIRA issue descriptions.

## Quick Start

### 1. Generate the AST JSON

First, generate the AST from the Go code:

```bash
cd /Users/slakshmi/base/console
go run scripts/generate_helm_ast.go > /tmp/helm_ast.json
```

### 2. Run the Pydantic Generator

#### Option A: From a JIRA text file

```bash
cd /Users/slakshmi/base/console
python3 scripts/jira_to_pydantic.py /tmp/helm_ast.json scripts/example_jira.txt
```

#### Option B: From stdin (pipe JIRA text directly)

```bash
cat scripts/example_jira.txt | python3 scripts/jira_to_pydantic.py /tmp/helm_ast.json -
```

#### Option C: From a heredoc

```bash
python3 scripts/jira_to_pydantic.py /tmp/helm_ast.json - <<EOF
HELM-800: Add rollback functionality to Helm releases

Acceptance Criteria:
- Users can rollback a Helm release to a previous revision
- Rollback should preserve the original values
- Support rollback from both UI and API
EOF
```

## Output

The tool generates:

1. **Top 10 Most Relevant Structs** - ranked by relevance score with reasons
2. **Pydantic Models** - Python/Pydantic code for the top 10 structs

## Example Usage

```bash
# 1. Generate AST
cd /Users/slakshmi/base/console
go run scripts/generate_helm_ast.go > /tmp/helm_ast.json

# 2. Run with example JIRA
python3 scripts/jira_to_pydantic.py /tmp/helm_ast.json scripts/example_jira.txt

# Or save output to a file
python3 scripts/jira_to_pydantic.py /tmp/helm_ast.json scripts/example_jira.txt > /tmp/models.py
```

## How It Works

### Intelligence Extraction

The tool analyzes JIRA text to extract:
- **Keywords**: Technical terms (auth, secret, upgrade, chart, etc.)
- **Action**: Type of change (create, update, delete, fix)
- **File Hints**: Likely relevant files (upgrade_release.go, auth.go, etc.)
- **Concepts**: Domain concepts (helm, auth, repository, namespace)

### Relevance Scoring

Each Go struct is scored based on multiple signals:

| Signal | Weight | Description |
|--------|--------|-------------|
| Struct name match | 3.0 | Struct name contains JIRA keyword |
| Field name match | 1.0 each | Field names match keywords (max 3) |
| File path match | 4.0 | File path matches inferred hints |
| Concept alignment | 2.0 | Struct aligns with domain concepts |
| Documentation match | 0.5 | Docstring mentions keywords |
| Input/Request pattern | 1.5 | Struct looks like input type |
| Generic name penalty | -1.0 | Penalize overly generic names |

### Type Mapping

Go types are mapped to Python/Pydantic types:

| Go Type | Python Type |
|---------|-------------|
| `string` | `str` |
| `int`, `int64` | `int` |
| `bool` | `bool` |
| `[]string` | `list[str]` |
| `map[string]string` | `dict[str, str]` |
| `*Type` | `Optional[Type]` |
| `interface{}` | `Any` |

Fields with `omitempty` JSON tag or pointer types become `Optional`.

## Customization

Edit `scripts/jira_to_pydantic.py` to adjust:

- **Scoring weights**: Modify the weights in `calculate_relevance_score()`
- **File hints**: Add more patterns in `extract_jira_intelligence()`
- **Concepts**: Extend `concept_map` with new domain concepts
- **Top N**: Change the `[:10]` slice to show more/fewer results

## Integration with Agent Workflows

Use the generated Pydantic models to:

1. **Type-safe agent communication**: Pass models between Architect/Developer agents
2. **Validation**: Ensure generated plans reference real structs
3. **Code generation**: Use field information to generate correct code
4. **Documentation**: Models serve as documentation of affected types

## Example Output

```
=================================================================================
TOP 10 MOST RELEVANT STRUCTS
=================================================================================

1. ChartInfo (score: 9.50)
   📁 File: pkg/helm/actions/utility.go
   💡 Reasons: File path matches hint 'upgrade', Struct aligns with concept 'helm'

2. UserCredentials (score: 7.00)
   📁 File: pkg/helm/actions/get_registry.go
   💡 Reasons: Struct name contains 'credentials', Struct aligns with concept 'auth'

...

=================================================================================
GENERATED PYDANTIC MODELS
=================================================================================

from pydantic import BaseModel
from typing import Optional, Any


class ChartInfo(BaseModel):
    """
    Generated from pkg/helm/actions/utility.go
    
    Relevance Score: 9.50
    Reasons: File path matches hint 'upgrade', Struct aligns with concept 'helm'
    """

    name: str
    version: str
    repository_name: str
    repository_namespace: str
```

## Troubleshooting

### Error: No module named 'pydantic'

The script doesn't require pydantic to run - it only generates the code. However, if you want to validate the generated models:

```bash
pip3 install pydantic
```

### Error: File not found

Make sure you generated the AST first:

```bash
cd /Users/slakshmi/base/console
go run scripts/generate_helm_ast.go > /tmp/helm_ast.json
```

### Empty or wrong results

Check that:
1. Your JIRA text is detailed enough (include acceptance criteria)
2. Keywords match the actual Go code (use technical terms)
3. The AST JSON is valid and complete
