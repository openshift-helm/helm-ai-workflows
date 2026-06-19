# JIRA to Code Generation - Complete Guide

This guide shows you how to **automatically generate code** from JIRA issues using the two-stage agent workflow (Architect → Developer).

---

## 🎯 Complete Workflow

```
JIRA Issue
    ↓
1. Generate AST (understand Go codebase structure)
    ↓
2. Generate Pydantic Models (identify relevant structs)
    ↓
3. Architect Agent (create implementation plan)
    ↓
4. Developer Agent (execute plan → generate code)
    ↓
Code Changes
```

---

## 🚀 Quick Start (One Command)

### **Test with Dry Run (Safe)**

```bash
cd /Users/slakshmi/base/console

# Test the complete pipeline without modifying files
./scripts/jira_to_code.sh scripts/example_jira.txt --dry-run
```

This will:
- ✅ Analyze your JIRA (HELM-480)
- ✅ Find relevant Go structs
- ✅ Create an implementation plan
- ✅ Show what code would be generated
- ❌ **NOT** modify any files

### **Generate Real Code**

```bash
cd /Users/slakshmi/base/console

# Generate and apply actual code changes
./scripts/jira_to_code.sh scripts/example_jira.txt

# Review changes
git diff
```

---

## 📋 Step-by-Step (Manual Control)

If you want more control over each step:

### **Step 1: Generate Pydantic Models**

```bash
cd /Users/slakshmi/base/console

# Generate models from your JIRA
./scripts/generate_models.sh scripts/example_jira.txt scripts/output/models.py

# Review the models
cat scripts/output/models.py
```

This shows you which Go structs are relevant to your JIRA issue.

### **Step 2: Create Implementation Plan (Architect Agent)**

```bash
cd /Users/slakshmi/base/console

# Architect analyzes and creates plan
python3 scripts/architect_agent.py scripts/output/models.py scripts/example_jira.txt scripts/output/plan.json

# Review the plan
cat scripts/output/plan.json | jq .
```

The plan contains:
- **Tasks**: What code changes to make
- **Files**: Which files to modify
- **Rationale**: Why each change is needed
- **Success Criteria**: How to verify it works

### **Step 3: Execute Plan (Developer Agent)**

```bash
cd /Users/slakshmi/base/console

# Dry run first (safe)
python3 scripts/developer_agent.py scripts/output/plan.json --dry-run

# Apply changes for real
python3 scripts/developer_agent.py scripts/output/plan.json > scripts/output/results.json

# Check what changed
git diff
```

---

## 📊 Understanding the Output

### **Pydantic Models** (`scripts/output/models.py`)

Shows relevant Go structs as Python/Pydantic models:

```python
class HelmRequest(BaseModel):
    """Generated from pkg/helm/handlers/request.go"""
    name: str
    namespace: str
    chart_url: str
    basic_auth_secret_name: str
    # ... more fields
```

**Use this to:**
- Understand which structs are affected
- See field types and structures
- Validate your understanding of the codebase

### **Implementation Plan** (`scripts/output/plan.json`)

Structured plan with atomic tasks:

```json
{
  "plan_id": "plan_helm480_001",
  "jira_issue": "HELM-480",
  "tasks": [
    {
      "task_id": "task_1",
      "file_path": "pkg/helm/handlers/handlers.go",
      "operation": "edit",
      "description": "Update HandleHelmInstall to return 400...",
      "old_code": "http.StatusBadGateway",
      "new_code": "http.StatusBadRequest",
      "success_criteria": "Returns 400 when request is invalid"
    }
  ]
}
```

**Use this to:**
- Review the approach before executing
- Modify the plan if needed
- Share with teammates for review

### **Execution Results** (`scripts/output/results.json`)

Results of each task execution:

```json
{
  "plan_id": "plan_helm480_001",
  "results": [
    {
      "task_id": "task_1",
      "status": "success",
      "message": "Modified 1 location(s)",
      "changes_made": [...]
    }
  ]
}
```

---

## 🎓 Real Example: HELM-480

Let's walk through the actual HELM-480 issue (HTTP status codes bug):

### **1. The JIRA Issue**

```
HELM-480: Helm API returns unexpected status codes

Problem: Returns 502 Bad Gateway for all errors
Expected: 400 for invalid input, 404 for not found, 500 for server errors
```

### **2. Run the Pipeline**

```bash
cd /Users/slakshmi/base/console
./scripts/jira_to_code.sh scripts/example_jira.txt --dry-run
```

### **3. What Gets Generated**

The Architect creates a plan with 4 tasks:

**Task 1:** Change `HandleHelmInstall` error to return `400 Bad Request`
```go
// OLD CODE:
serverutils.SendResponse(w, http.StatusBadGateway, ...)

// NEW CODE:
serverutils.SendResponse(w, http.StatusBadRequest, ...)
```

**Task 2:** Change `HandleGetRelease` to return `404 Not Found`
```go
// NEW CODE:
if strings.Contains(err.Error(), "not found") {
    serverutils.SendResponse(w, http.StatusNotFound, ...)
    return
}
```

**Task 3:** Add helper function for status code logic
```go
func determineErrorStatusCode(err error) int {
    if strings.Contains(err.Error(), "not found") {
        return http.StatusNotFound
    }
    // ... more cases
}
```

**Task 4:** Add tests

### **4. Review and Apply**

```bash
# Review the plan
cat scripts/output/run_*/implementation_plan.json | jq '.tasks'

# If it looks good, run without --dry-run
./scripts/jira_to_code.sh scripts/example_jira.txt

# Review changes
git diff pkg/helm/handlers/handlers.go
```

---

## 🔧 Customizing the Agents

### **Customize Architect Agent** (`architect_agent.py`)

The Architect creates the implementation plan. Edit the `create_status_code_fix_plan()` function to change:
- How tasks are structured
- What code changes to suggest
- Testing requirements

### **Customize Developer Agent** (`developer_agent.py`)

The Developer executes the plan. Currently it does simple string replacement. You can enhance it to:
- Use AST-based editing (more precise)
- Run tests after changes
- Format code automatically
- Create git commits

---

## 💡 Using with LLMs

In a real implementation, you'd use an LLM (Claude) for the Architect agent:

```python
# Pseudo-code
response = claude_client.messages.create(
    model="claude-sonnet-4-5",
    messages=[{
        "role": "user",
        "content": f"""
        You are an Architect Agent.
        
        JIRA Issue: {jira_text}
        
        Relevant Go Structs (as Pydantic models):
        {pydantic_models}
        
        Create an ImplementationPlan with AtomicTasks.
        Return ONLY valid JSON matching the ImplementationPlan schema.
        """
    }],
    tools=[{
        "name": "create_implementation_plan",
        "input_schema": ImplementationPlan.model_json_schema()
    }]
)

# Claude returns type-safe ImplementationPlan
plan = ImplementationPlan.model_validate(response.tool_calls[0].input)
```

The Pydantic models ensure:
- ✅ Type safety between agents
- ✅ Structured, predictable output
- ✅ Easy validation and debugging

---

## 🧪 Testing Your Changes

After generating code:

```bash
cd /Users/slakshmi/base/console

# Run tests
cd frontend && yarn test

# Build the project
./build.sh

# Check linting
cd frontend && yarn lint
```

---

## 📁 Files Created

| File | Purpose |
|------|---------|
| `jira_to_code.sh` | Complete end-to-end pipeline |
| `jira_to_pydantic.py` | Generate Pydantic models from AST |
| `architect_agent.py` | Create implementation plan |
| `developer_agent.py` | Execute plan and make code changes |
| `generate_models.sh` | Quick wrapper for Pydantic generation |

---

## 🎯 When to Use This

**Good for:**
- ✅ Structured bug fixes (like HELM-480)
- ✅ Repetitive changes across files
- ✅ Well-defined JIRA acceptance criteria
- ✅ Learning the codebase structure

**Not ideal for:**
- ❌ Exploratory changes (unclear requirements)
- ❌ Major refactoring (too complex)
- ❌ UI/visual changes (need manual verification)

---

## 🆘 Troubleshooting

### **"File not found" errors**

The Developer agent couldn't find a file. Check:
- File path in the plan is correct
- File exists in the repo

### **Plan looks wrong**

The Architect is currently template-based. For better results:
- Make JIRA acceptance criteria more detailed
- Add technical details to JIRA
- Edit the plan JSON manually before executing

### **Code changes broke tests**

The generated code is a starting point. You may need to:
- Review and refine the changes
- Run tests and fix issues
- Adjust the plan and re-run

---

## 🚀 Next Steps

1. **Try the dry run**: `./scripts/jira_to_code.sh scripts/example_jira.txt --dry-run`
2. **Review the outputs**: Check `/tmp/jira_to_code_*` directory
3. **Customize**: Edit `architect_agent.py` for your use case
4. **Integrate LLM**: Replace template logic with Claude API calls

---

## 📚 Learn More

- **Pydantic docs**: Understanding the models → `scripts/README_JIRA_TO_PYDANTIC.md`
- **Agent architecture**: How Architect/Developer communicate → This guide
- **OpenShift Console**: Contributing guide → `CONTRIBUTING.md`
