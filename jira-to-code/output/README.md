# Output Directory

This directory contains generated files from the JIRA to Code pipeline.

## Structure

Each run creates a timestamped subdirectory:

```
scripts/output/
├── run_20260619_143022/
│   ├── helm_ast.json              # Go code AST
│   ├── pydantic_models.py         # Generated Pydantic models
│   ├── implementation_plan.json   # Architect's plan
│   └── execution_results.json     # Developer's results
├── run_20260619_143155/
│   └── ...
└── helm_ast.json                  # Latest AST (from generate_models.sh)
```

## Files

- **`helm_ast.json`** - Abstract Syntax Tree of pkg/helm Go code
- **`pydantic_models.py`** - Relevant Go structs as Pydantic models
- **`implementation_plan.json`** - Structured plan with atomic tasks
- **`execution_results.json`** - Results from executing the plan

## Cleanup

This directory is git-ignored. To clean up old runs:

```bash
# Remove all runs
rm -rf scripts/output/run_*

# Remove runs older than 7 days
find scripts/output -name "run_*" -type d -mtime +7 -exec rm -rf {} \;

# Keep only the 5 most recent runs
ls -dt scripts/output/run_* | tail -n +6 | xargs rm -rf
```
