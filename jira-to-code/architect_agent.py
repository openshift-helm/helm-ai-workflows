#!/usr/bin/env python3
"""
Architect Agent - Creates implementation plans using Pydantic models

This agent:
1. Reads the generated Pydantic models (understanding of codebase structures)
2. Analyzes the JIRA requirements
3. Creates an ImplementationPlan with AtomicTasks

Usage:
    python architect_agent.py <pydantic_models_file> <jira_text_file>
"""

import json
import sys
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field


# ============================================================================
# Pydantic Models for Agent Communication (The Core Framework)
# ============================================================================

class AtomicTask(BaseModel):
    """A single, indivisible unit of code modification."""

    task_id: str = Field(..., description="Unique identifier for this task")

    # Target
    file_path: str = Field(..., description="Path to the file to modify")
    operation: Literal["create", "edit", "delete"] = Field(
        ...,
        description="Type of file operation"
    )

    # Intent and implementation
    description: str = Field(
        ...,
        description="Human-readable description of what this task does"
    )
    rationale: str = Field(
        ...,
        description="Why this change is needed (links back to JIRA)"
    )
    old_code: Optional[str] = Field(
        None,
        description="For edits: exact code to replace (can be approximate for planning)"
    )
    new_code: Optional[str] = Field(
        None,
        description="For edits/creates: exact code to insert"
    )
    line_range: Optional[tuple[int, int]] = Field(
        None,
        description="For edits: (start_line, end_line)"
    )

    # Dependencies
    depends_on: List[str] = Field(
        default_factory=list,
        description="List of task_ids that must complete before this task"
    )

    # Validation
    success_criteria: str = Field(
        ...,
        description="How to verify this task succeeded"
    )
    affected_structs: List[str] = Field(
        default_factory=list,
        description="Go struct names that this task modifies or references"
    )


class ImplementationPlan(BaseModel):
    """Complete implementation plan from the Architect agent."""

    plan_id: str = Field(..., description="Unique plan identifier")

    # Context
    jira_issue: str = Field(..., description="JIRA issue key (e.g., HELM-480)")
    requirement: str = Field(
        ...,
        description="Original user requirement/request"
    )
    analysis: str = Field(
        ...,
        description="Architect's analysis of the problem and approach"
    )
    affected_files: List[str] = Field(
        default_factory=list,
        description="List of all files that will be modified"
    )
    relevant_structs: List[Dict] = Field(
        default_factory=list,
        description="Structs from Pydantic models that are relevant to this plan"
    )

    # Execution
    tasks: List[AtomicTask] = Field(
        ...,
        description="All atomic tasks in this plan"
    )
    execution_order: List[str] = Field(
        ...,
        description="task_ids in dependency-resolved execution order"
    )

    # Risk management
    risks: List[str] = Field(
        default_factory=list,
        description="Potential risks or breaking changes"
    )
    mitigation_strategies: List[str] = Field(
        default_factory=list,
        description="How to mitigate identified risks"
    )

    # Testing
    test_requirements: List[str] = Field(
        default_factory=list,
        description="Testing requirements for this plan"
    )

    # Metadata
    estimated_complexity: Literal["low", "medium", "high"] = Field(
        ...,
        description="Estimated complexity of implementation"
    )
    requires_human_review: bool = Field(
        default=True,
        description="Whether human approval is needed before execution"
    )


# ============================================================================
# Architect Agent Logic
# ============================================================================

def create_implementation_plan(
    jira_text: str,
    pydantic_models_content: str,
    jira_issue_key: str = "UNKNOWN"
) -> ImplementationPlan:
    """
    Architect Agent: Analyze JIRA and create implementation plan.

    In a real implementation, this would use an LLM (Claude) to:
    1. Read the Pydantic models to understand codebase structures
    2. Analyze JIRA requirements
    3. Create a structured plan

    For this example, we'll create a template plan for HELM-480.
    """

    # Parse the JIRA to extract key information
    is_status_code_issue = "status code" in jira_text.lower() or "statuscode" in jira_text.lower()
    is_error_handling = "error" in jira_text.lower()

    # Extract relevant struct names from the Pydantic models
    relevant_structs = extract_struct_names(pydantic_models_content)

    # Create the plan
    if is_status_code_issue and is_error_handling:
        plan = create_status_code_fix_plan(jira_issue_key, jira_text, relevant_structs)
    else:
        plan = create_generic_plan(jira_issue_key, jira_text, relevant_structs)

    return plan


def extract_struct_names(pydantic_content: str) -> List[Dict]:
    """Extract struct information from generated Pydantic models."""
    structs = []
    lines = pydantic_content.split('\n')

    current_struct = None
    for i, line in enumerate(lines):
        if line.startswith('class ') and '(BaseModel)' in line:
            struct_name = line.split('class ')[1].split('(')[0].strip()
            current_struct = {"name": struct_name, "fields": []}
        elif current_struct and line.strip().startswith('"""Generated from'):
            file_path = line.split('Generated from ')[1].split('"""')[0].strip()
            current_struct["file_path"] = file_path
        elif current_struct and ':' in line and not line.strip().startswith('"""'):
            # Field definition
            if '=' in line:
                field_name = line.split(':')[0].strip()
                if field_name and not field_name.startswith('"""'):
                    current_struct["fields"].append(field_name)
        elif current_struct and line.strip() == '' and i > 0:
            # End of class
            if current_struct.get("file_path"):
                structs.append(current_struct)
            current_struct = None

    return structs


def create_status_code_fix_plan(
    jira_key: str,
    jira_text: str,
    relevant_structs: List[Dict]
) -> ImplementationPlan:
    """Create plan for fixing HTTP status codes (HELM-480 example)."""

    # Find the handlers file
    handlers_file = "pkg/helm/handlers/handlers.go"

    tasks = [
        AtomicTask(
            task_id="task_1",
            file_path=handlers_file,
            operation="edit",
            description="Update HandleHelmInstall to return 400 for invalid request body",
            rationale="JIRA AC: Return proper status codes. Invalid request = 400 Bad Request, not 502",
            old_code="""serverutils.SendResponse(w, http.StatusBadGateway, serverutils.ApiError{Err: fmt.Sprintf("Failed to parse request: %v", err)})""",
            new_code="""serverutils.SendResponse(w, http.StatusBadRequest, serverutils.ApiError{Err: fmt.Sprintf("Failed to parse request: %v", err)})""",
            depends_on=[],
            success_criteria="HandleHelmInstall returns 400 when request body is invalid",
            affected_structs=["HelmRequest", "helmHandlers"]
        ),
        AtomicTask(
            task_id="task_2",
            file_path=handlers_file,
            operation="edit",
            description="Update HandleGetRelease to return 404 for release not found",
            rationale="JIRA AC: Return 404 when release doesn't exist, not 502",
            old_code="""serverutils.SendResponse(w, http.StatusBadGateway, serverutils.ApiError{Err: fmt.Sprintf("Failed to find helm release: %v", err)})""",
            new_code="""if strings.Contains(err.Error(), "not found") || strings.Contains(err.Error(), "no revision") {
    serverutils.SendResponse(w, http.StatusNotFound, serverutils.ApiError{Err: fmt.Sprintf("Failed to find helm release: %v", err)})
    return
}
serverutils.SendResponse(w, http.StatusInternalServerError, serverutils.ApiError{Err: fmt.Sprintf("Failed to get helm release: %v", err)})""",
            depends_on=[],
            success_criteria="HandleGetRelease returns 404 when release is not found",
            affected_structs=["helmHandlers"]
        ),
        AtomicTask(
            task_id="task_3",
            file_path=handlers_file,
            operation="edit",
            description="Add helper function to determine appropriate HTTP status code",
            rationale="DRY principle: centralize status code logic",
            new_code="""// determineErrorStatusCode returns the appropriate HTTP status code based on error type
func determineErrorStatusCode(err error) int {
    errMsg := err.Error()

    // 404 Not Found
    if strings.Contains(errMsg, "not found") || strings.Contains(errMsg, "no revision") {
        return http.StatusNotFound
    }

    // 400 Bad Request - validation/parsing errors
    if strings.Contains(errMsg, "invalid") || strings.Contains(errMsg, "parse") {
        return http.StatusBadRequest
    }

    // 500 Internal Server Error - default for unexpected errors
    return http.StatusInternalServerError
}""",
            depends_on=[],
            success_criteria="Helper function correctly maps errors to status codes",
            affected_structs=[]
        ),
        AtomicTask(
            task_id="task_4",
            file_path="pkg/helm/handlers/handlers_test.go",
            operation="edit",
            description="Add test cases for status code handling",
            rationale="Ensure status codes are correct and prevent regression",
            new_code="""func TestHandleGetRelease_NotFound(t *testing.T) {
    // Test that non-existent release returns 404
    // ... test implementation
}

func TestHandleHelmInstall_InvalidRequest(t *testing.T) {
    // Test that invalid request body returns 400
    // ... test implementation
}""",
            depends_on=["task_1", "task_2", "task_3"],
            success_criteria="All status code tests pass",
            affected_structs=["HelmRequest"]
        )
    ]

    return ImplementationPlan(
        plan_id="plan_helm480_001",
        jira_issue=jira_key,
        requirement=jira_text[:200] + "...",
        analysis="""
The issue is that pkg/helm/handlers uses http.StatusBadGateway (502) for all errors,
including client errors (invalid input) and not-found errors. According to HTTP spec:
- 400 = Client sent invalid data
- 404 = Resource not found
- 500 = Server unexpected error
- 502 = Bad Gateway (proxy/upstream issue)

Current code uses 502 everywhere, which is semantically incorrect and causes the frontend
to show a generic error instead of proper 404/400 pages.

Solution: Update all error responses to use appropriate status codes based on error type.
""",
        affected_files=[
            handlers_file,
            "pkg/helm/handlers/handlers_test.go"
        ],
        relevant_structs=relevant_structs[:3],  # Top 3 most relevant
        tasks=tasks,
        execution_order=["task_1", "task_2", "task_3", "task_4"],
        risks=[
            "Frontend may be expecting 502 status code in error handling",
            "Changing status codes could break existing integrations"
        ],
        mitigation_strategies=[
            "Check frontend status-box.tsx to ensure it handles 400/404 properly",
            "Add comprehensive tests before merging",
            "Review all callers of SendResponse in handlers"
        ],
        test_requirements=[
            "Unit tests for each handler with different error scenarios",
            "Integration test: non-existent release returns 404",
            "Integration test: invalid request body returns 400"
        ],
        estimated_complexity="medium",
        requires_human_review=True
    )


def create_generic_plan(
    jira_key: str,
    jira_text: str,
    relevant_structs: List[Dict]
) -> ImplementationPlan:
    """Create a generic template plan."""

    return ImplementationPlan(
        plan_id=f"plan_{jira_key.lower().replace('-', '_')}_001",
        jira_issue=jira_key,
        requirement=jira_text[:200] + "...",
        analysis="Generic plan - needs LLM to analyze properly",
        affected_files=["TODO: Determine from analysis"],
        relevant_structs=relevant_structs[:5],
        tasks=[
            AtomicTask(
                task_id="task_1",
                file_path="TODO",
                operation="edit",
                description="TODO: Define based on JIRA analysis",
                rationale="TODO",
                depends_on=[],
                success_criteria="TODO",
                affected_structs=[]
            )
        ],
        execution_order=["task_1"],
        risks=["TODO: Identify risks"],
        mitigation_strategies=["TODO: Define mitigation"],
        test_requirements=["TODO: Define tests"],
        estimated_complexity="medium",
        requires_human_review=True
    )


# ============================================================================
# CLI
# ============================================================================

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    pydantic_models_file = sys.argv[1]
    jira_text_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None

    # Read inputs
    with open(pydantic_models_file) as f:
        pydantic_content = f.read()

    with open(jira_text_file) as f:
        jira_text = f.read()

    # Extract JIRA key from text
    jira_key = "UNKNOWN"
    first_line = jira_text.split('\n')[0]
    if ':' in first_line:
        jira_key = first_line.split(':')[0].strip()

    print(f"🏗️  Architect Agent: Creating implementation plan for {jira_key}...\n", file=sys.stderr)

    # Create plan
    plan = create_implementation_plan(jira_text, pydantic_content, jira_key)

    # Output
    plan_json = plan.model_dump_json(indent=2)

    if output_file:
        with open(output_file, 'w') as f:
            f.write(plan_json)
        print(f"✅ Plan saved to {output_file}", file=sys.stderr)
        print(f"\n📋 Plan Summary:", file=sys.stderr)
        print(f"   Tasks: {len(plan.tasks)}", file=sys.stderr)
        print(f"   Files: {len(plan.affected_files)}", file=sys.stderr)
        print(f"   Complexity: {plan.estimated_complexity}", file=sys.stderr)
    else:
        print(plan_json)


if __name__ == "__main__":
    main()
