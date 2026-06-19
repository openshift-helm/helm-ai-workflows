# 🚀 Quick Start: JIRA to Code Generation

Transform your JIRA issues into actual code changes automatically!

---

## One-Command Magic ✨

```bash
cd /Users/slakshmi/base/console

# Test it (safe, no file changes)
./scripts/jira_to_code.sh scripts/example_jira.txt --dry-run

# Apply it (generates real code)
./scripts/jira_to_code.sh scripts/example_jira.txt
```

---

## What Just Happened? 🤔

```
┌─────────────────────────────────────────────────────────────┐
│  JIRA Issue (HELM-480: Fix HTTP status codes)              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Parse Go Code AST                                  │
│  → Understands pkg/helm/*.go structure                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Generate Pydantic Models                           │
│  → Finds relevant structs: HelmRequest, helmHandlers        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 3: Architect Agent                                    │
│  → Creates implementation plan with 4 tasks                 │
│  → Task 1: Change StatusBadGateway → StatusBadRequest       │
│  → Task 2: Add 404 handling for "not found" errors         │
│  → Task 3: Add helper function                             │
│  → Task 4: Add tests                                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 4: Developer Agent                                    │
│  → Executes each task in order                             │
│  → Modifies pkg/helm/handlers/handlers.go                  │
│  → Creates tests                                            │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  ✅ Code Changes Ready!                                     │
│  → git diff to review                                       │
│  → git commit when satisfied                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Example Output

After running the command, you get:

### **1. Pydantic Models** (what structs are involved)

```python
class HelmRequest(BaseModel):
    name: str
    namespace: str
    chart_url: str
    basic_auth_secret_name: str
```

### **2. Implementation Plan** (what to change)

```json
{
  "task_1": {
    "file": "pkg/helm/handlers/handlers.go",
    "change": "StatusBadGateway → StatusBadRequest",
    "why": "Invalid input should return 400, not 502"
  }
}
```

### **3. Code Changes** (actual modifications)

```diff
// pkg/helm/handlers/handlers.go

- serverutils.SendResponse(w, http.StatusBadGateway, ...)
+ serverutils.SendResponse(w, http.StatusBadRequest, ...)
```

---

## 🎯 Try It Yourself

### **1. Test with Example JIRA (HELM-480)**

```bash
cd /Users/slakshmi/base/console
./scripts/jira_to_code.sh scripts/example_jira.txt --dry-run
```

Output saved to: `scripts/output/run_*/`

### **2. Check the Results**

```bash
# View the implementation plan (use the latest run directory)
cat scripts/output/run_*/implementation_plan.json | jq .

# View the generated Pydantic models
cat scripts/output/run_*/pydantic_models.py

# View execution results
cat scripts/output/run_*/execution_results.json | jq .

# Or use the most recent run explicitly
LATEST_RUN=$(ls -dt scripts/output/run_* | head -1)
cat $LATEST_RUN/implementation_plan.json | jq .
```

### **3. Use Your Own JIRA**

```bash
# Create your JIRA file
cat > /tmp/my_jira.txt <<'EOF'
HELM-999: Add retry logic to chart download

Acceptance Criteria:
- Retry up to 3 times on network failure
- Use exponential backoff
- Log each retry attempt
EOF

# Generate code
./scripts/jira_to_code.sh /tmp/my_jira.txt --dry-run
```

---

## 🛠️ Individual Steps (If You Want Control)

### **Just Generate Models** (understand codebase)

```bash
./scripts/generate_models.sh scripts/example_jira.txt /tmp/models.py
cat /tmp/models.py
```

### **Just Create Plan** (see approach)

```bash
python3 scripts/architect_agent.py /tmp/models.py scripts/example_jira.txt /tmp/plan.json
cat /tmp/plan.json | jq .
```

### **Just Execute Plan** (apply changes)

```bash
python3 scripts/developer_agent.py /tmp/plan.json --dry-run
python3 scripts/developer_agent.py /tmp/plan.json  # for real
```

---

## 🎓 What You're Actually Building

This demonstrates the **two-stage LangGraph SWE-agent pattern**:

1. **Architect Agent** (Planning)
   - Reads Pydantic models (codebase understanding)
   - Analyzes JIRA requirements
   - Creates structured `ImplementationPlan`
   - Output: Type-safe plan with `AtomicTask[]`

2. **Developer Agent** (Execution)
   - Reads `ImplementationPlan` (no ambiguity)
   - Executes each task atomically
   - Validates success criteria
   - Output: Code changes + results

**Key Benefit:** Type-safe communication via Pydantic models!

---

## 📚 Full Documentation

- **Complete Guide**: `scripts/CODE_GENERATION_GUIDE.md`
- **Pydantic Models**: `scripts/README_JIRA_TO_PYDANTIC.md`
- **Usage Tips**: `scripts/USAGE.md`

---

## ⚡ TL;DR

```bash
cd /Users/slakshmi/base/console

# 1. Test (safe)
./scripts/jira_to_code.sh scripts/example_jira.txt --dry-run

# 2. Review output
ls scripts/output/run_*/

# 3. Apply (real code changes)
./scripts/jira_to_code.sh scripts/example_jira.txt

# 4. Check changes
git diff
```

That's it! 🎉
