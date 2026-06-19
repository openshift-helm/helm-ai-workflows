# Quick Usage Guide

## ✅ Updated! Now Supports Output Files

The script has been updated to save results to a file.

---

## 🚀 How to Use

### **Method 1: Save to File (Recommended)**

```bash
cd /Users/slakshmi/base/console

# Save output to a file
./scripts/generate_models.sh scripts/example_jira.txt scripts/output/pydantic_models.py

# Or with custom path
./scripts/generate_models.sh scripts/example_jira.txt ~/Desktop/models.py
```

### **Method 2: Print to Terminal**

```bash
cd /Users/slakshmi/base/console

# Print to stdout (no output file specified)
./scripts/generate_models.sh scripts/example_jira.txt

# Or redirect manually
./scripts/generate_models.sh scripts/example_jira.txt > scripts/output/models.py
```

### **Method 3: With Your Own JIRA Text**

```bash
cd /Users/slakshmi/base/console

# Create your JIRA file
cat > /tmp/my_jira.txt <<'EOF'
HELM-999: Your issue title

Description:
Your description here

Acceptance Criteria:
- Criterion 1
- Criterion 2
EOF

# Generate and save
./scripts/generate_models.sh /tmp/my_jira.txt scripts/output/models.py
```

### **Method 4: From stdin**

```bash
cd /Users/slakshmi/base/console

# Pipe JIRA text and save to file
cat scripts/example_jira.txt | ./scripts/generate_models.sh - scripts/output/pydantic_models.py

# Or with heredoc
./scripts/generate_models.sh - scripts/output/pydantic_models.py <<'EOF'
JIRA-123: Issue title
Description and acceptance criteria...
EOF
```

---

## 📋 What Gets Generated

The output file contains:

1. **Analysis Section**: Top 10 most relevant structs with scores
2. **Pydantic Models**: Python code ready to copy/paste

Example output structure:
```python
================================================================================
TOP 10 MOST RELEVANT STRUCTS
================================================================================

1. ChartInfo (score: 13.00)
   📁 File: pkg/helm/actions/utility.go
   💡 Reasons: ...

================================================================================
GENERATED PYDANTIC MODELS
================================================================================

from pydantic import BaseModel
from typing import Optional, Any

class ChartInfo(BaseModel):
    """Generated from pkg/helm/actions/utility.go"""
    name: str
    version: str
    repository_name: str
    repository_namespace: str
```

---

## 🔧 Direct Python Usage

If you prefer using Python directly:

```bash
cd /Users/slakshmi/base/console

# Generate AST first
go run scripts/generate_helm_ast.go > /tmp/helm_ast.json

# With output file
python3 scripts/jira_to_pydantic.py /tmp/helm_ast.json scripts/example_jira.txt scripts/output/pydantic_models.py

# Without output file (prints to stdout)
python3 scripts/jira_to_pydantic.py /tmp/helm_ast.json scripts/example_jira.txt
```

---

## 📝 Example: Current HELM-480 Issue

```bash
cd /Users/slakshmi/base/console

# The example file now contains HELM-480 (status codes issue)
./scripts/generate_models.sh scripts/example_jira.txt /tmp/helm480_models.py

# View the output
cat /tmp/helm480_models.py
```

This will analyze the HELM-480 issue about HTTP status codes and find relevant structs like:
- `HelmRequest` - Request handling structures
- `helmHandlers` - HTTP handler structures
- `ChartInfo` - Chart-related data

---

## 💡 Tips

1. **More detailed JIRA = Better results**: Include acceptance criteria and technical details
2. **Keywords matter**: Use technical terms like "auth", "upgrade", "namespace", "repository"
3. **Check the scores**: Higher score = more relevant to your JIRA issue
4. **Output file is human-readable**: You can copy the Pydantic models directly

---

## 🎯 Quick Test

Try it now with the updated HELM-480 example:

```bash
cd /Users/slakshmi/base/console
./scripts/generate_models.sh scripts/example_jira.txt /tmp/test_output.py
cat /tmp/test_output.py
```
