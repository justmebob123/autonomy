# Phase 4: Issue Reporting Implementation Plan

## Overview
Implement tools and workflows for creating comprehensive issue reports when refactoring tasks are too complex for autonomous fixing.

## Goals
1. Detect when issues are too complex for autonomous fixing
2. Create detailed, actionable issue reports
3. Add developer review workflow
4. Generate REFACTORING_REPORT.md

## Components to Implement

### 1. Two New Tools

#### create_issue_report
**Purpose**: Create a comprehensive report for a complex issue
**Parameters**:
- task_id: RefactoringTask ID
- severity: critical/high/medium/low
- impact_analysis: What breaks if not fixed
- recommended_approach: How to fix it
- code_examples: Relevant code snippets
- estimated_effort: Time estimate

#### request_developer_review
**Purpose**: Request developer input on a blocked task
**Parameters**:
- task_id: RefactoringTask ID
- question: Specific question for developer
- options: List of possible approaches
- context: Additional context

### 2. Two New Handlers
- _handle_create_issue_report
- _handle_request_developer_review

### 3. Report Generation
**File**: REFACTORING_REPORT.md
**Sections**:
- Executive Summary
- Critical Issues (requires immediate attention)
- High Priority Issues
- Medium Priority Issues
- Low Priority Issues
- Blocked Tasks (needs developer review)
- Completed Tasks
- Progress Statistics

### 4. Complexity Detection
**Add to _work_on_task()**:
- Detect when task fails multiple times
- Detect when tools return errors repeatedly
- Detect when LLM says "too complex"
- Automatically create issue report

### 5. Developer Review Workflow
**Add to execute()**:
- Check for blocked tasks
- If blocked tasks exist, generate report
- Pause refactoring until developer reviews
- Resume after developer input

## Implementation Steps

### Step 1: Add Tools (30 min)
- Add tool definitions to refactoring_tools.py
- Define parameters and descriptions

### Step 2: Add Handlers (45 min)
- Implement _handle_create_issue_report
- Implement _handle_request_developer_review
- Register handlers

### Step 3: Add Report Generation (60 min)
- Create _generate_refactoring_report() method
- Format report in markdown
- Include all sections

### Step 4: Add Complexity Detection (30 min)
- Update _work_on_task() to detect complexity
- Automatically create reports for complex issues
- Mark tasks as needs_review

### Step 5: Add Developer Review Workflow (30 min)
- Update execute() to check for blocked tasks
- Generate report when blocked tasks exist
- Add pause/resume logic

### Step 6: Testing (30 min)
- Test issue report creation
- Test developer review workflow
- Test report generation

## Total Time: ~3.5 hours

## Success Criteria
1. ✅ Complex issues automatically detected
2. ✅ Issue reports created with full details
3. ✅ REFACTORING_REPORT.md generated
4. ✅ Developer review workflow functional
5. ✅ Refactoring pauses when blocked
6. ✅ Reports are comprehensive and actionable

## Next Steps After Phase 4
- Phase 5: Coordinator integration
- Add quality-based triggers
- Support refactoring continuation
- Handle developer review in coordinator