#!/usr/bin/env python3
"""
Developer Agent - Executes implementation plans

This agent:
1. Reads an ImplementationPlan (JSON)
2. Executes each AtomicTask in order
3. Makes actual code changes to files

Usage:
    python developer_agent.py <plan_json_file> [--dry-run]

    --dry-run: Show what would be done without actually modifying files
"""

import json
import sys
import os
import re
from typing import Dict, List
from pathlib import Path


# ============================================================================
# Developer Agent Logic
# ============================================================================

class DeveloperAgent:
    """Executes implementation plans by making code changes."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.project_root = Path(__file__).parent.parent
        self.results = []

    def execute_plan(self, plan: Dict) -> List[Dict]:
        """Execute all tasks in the implementation plan."""

        print(f"🔨 Developer Agent: Executing plan {plan['plan_id']}", file=sys.stderr)
        print(f"   JIRA: {plan['jira_issue']}", file=sys.stderr)
        print(f"   Tasks: {len(plan['tasks'])}", file=sys.stderr)
        print(f"   Mode: {'DRY RUN' if self.dry_run else 'LIVE'}\n", file=sys.stderr)

        # Execute in order
        for task_id in plan['execution_order']:
            task = self._find_task(plan['tasks'], task_id)
            if task:
                result = self.execute_task(task)
                self.results.append(result)

        return self.results

    def _find_task(self, tasks: List[Dict], task_id: str) -> Dict:
        """Find task by ID."""
        for task in tasks:
            if task['task_id'] == task_id:
                return task
        return None

    def execute_task(self, task: Dict) -> Dict:
        """Execute a single AtomicTask."""

        print(f"📝 Task {task['task_id']}: {task['description']}", file=sys.stderr)
        print(f"   File: {task['file_path']}", file=sys.stderr)
        print(f"   Operation: {task['operation']}", file=sys.stderr)

        result = {
            "task_id": task['task_id'],
            "status": "pending",
            "message": "",
            "changes_made": []
        }

        try:
            if task['operation'] == 'edit':
                result = self._execute_edit(task)
            elif task['operation'] == 'create':
                result = self._execute_create(task)
            elif task['operation'] == 'delete':
                result = self._execute_delete(task)
            else:
                result['status'] = 'error'
                result['message'] = f"Unknown operation: {task['operation']}"

            print(f"   Status: {result['status']}", file=sys.stderr)
            if result['message']:
                print(f"   {result['message']}", file=sys.stderr)
            print(file=sys.stderr)

        except Exception as e:
            result['status'] = 'error'
            result['message'] = str(e)
            print(f"   ❌ Error: {e}", file=sys.stderr)
            print(file=sys.stderr)

        return result

    def _execute_edit(self, task: Dict) -> Dict:
        """Execute an edit operation."""

        file_path = self.project_root / task['file_path']

        if not file_path.exists():
            return {
                "task_id": task['task_id'],
                "status": "error",
                "message": f"File not found: {file_path}",
                "changes_made": []
            }

        # Read file
        with open(file_path, 'r') as f:
            content = f.read()

        old_code = task.get('old_code', '')
        new_code = task.get('new_code', '')

        # Simple string replacement (in real implementation, use AST-based editing)
        if old_code and old_code in content:
            new_content = content.replace(old_code, new_code)
            changes_made = [{
                "type": "replace",
                "old": old_code[:100] + "..." if len(old_code) > 100 else old_code,
                "new": new_code[:100] + "..." if len(new_code) > 100 else new_code
            }]
        else:
            # Fallback: append to file
            new_content = content + "\n\n" + new_code
            changes_made = [{
                "type": "append",
                "content": new_code[:100] + "..." if len(new_code) > 100 else new_code
            }]

        # Write changes
        if not self.dry_run:
            with open(file_path, 'w') as f:
                f.write(new_content)
            message = f"Modified {len(changes_made)} location(s)"
        else:
            message = f"[DRY RUN] Would modify {len(changes_made)} location(s)"

        return {
            "task_id": task['task_id'],
            "status": "success",
            "message": message,
            "changes_made": changes_made
        }

    def _execute_create(self, task: Dict) -> Dict:
        """Execute a create operation."""

        file_path = self.project_root / task['file_path']

        if file_path.exists():
            return {
                "task_id": task['task_id'],
                "status": "error",
                "message": f"File already exists: {file_path}",
                "changes_made": []
            }

        new_code = task.get('new_code', '')

        if not self.dry_run:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(new_code)
            message = f"Created file with {len(new_code)} bytes"
        else:
            message = f"[DRY RUN] Would create file with {len(new_code)} bytes"

        return {
            "task_id": task['task_id'],
            "status": "success",
            "message": message,
            "changes_made": [{"type": "create", "size": len(new_code)}]
        }

    def _execute_delete(self, task: Dict) -> Dict:
        """Execute a delete operation."""

        file_path = self.project_root / task['file_path']

        if not file_path.exists():
            return {
                "task_id": task['task_id'],
                "status": "error",
                "message": f"File not found: {file_path}",
                "changes_made": []
            }

        if not self.dry_run:
            file_path.unlink()
            message = "Deleted file"
        else:
            message = "[DRY RUN] Would delete file"

        return {
            "task_id": task['task_id'],
            "status": "success",
            "message": message,
            "changes_made": [{"type": "delete"}]
        }


# ============================================================================
# CLI
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    plan_file = sys.argv[1]
    dry_run = '--dry-run' in sys.argv

    # Read plan
    with open(plan_file) as f:
        plan = json.load(f)

    # Execute
    agent = DeveloperAgent(dry_run=dry_run)
    results = agent.execute_plan(plan)

    # Summary
    print("=" * 80, file=sys.stderr)
    print("EXECUTION SUMMARY", file=sys.stderr)
    print("=" * 80, file=sys.stderr)

    success_count = sum(1 for r in results if r['status'] == 'success')
    error_count = sum(1 for r in results if r['status'] == 'error')

    print(f"✅ Successful: {success_count}", file=sys.stderr)
    print(f"❌ Errors: {error_count}", file=sys.stderr)
    print(f"📊 Total: {len(results)}", file=sys.stderr)

    # Output results as JSON
    print(json.dumps({
        "plan_id": plan['plan_id'],
        "results": results,
        "summary": {
            "total": len(results),
            "success": success_count,
            "errors": error_count
        }
    }, indent=2))


if __name__ == "__main__":
    main()
