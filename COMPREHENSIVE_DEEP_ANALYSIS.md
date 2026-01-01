# COMPREHENSIVE DEEP ANALYSIS - Forcing AI to Fix Files

**Date**: 2024-01-01  
**Objective**: Analyze the entire system to understand how to force AI to iteratively examine every file and fix issues

---

## PHASE 1: SYSTEM ARCHITECTURE ANALYSIS

### Current System Components

1. **Phases** (8 primary vertices in 7D polytopic space)
   - Planning
   - Coding
   - QA
   - Debugging
   - Project Planning
   - Documentation
   - Refactoring
   - Investigation

2. **Inter-Process Communication (IPC)**
   - Strategic documents (MASTER_PLAN, ARCHITECTURE, ROADMAP)
   - Phase-to-phase messaging
   - Shared state management

3. **Task Management**
   - Task creation and tracking
   - Priority-based execution
   - Retry logic with max attempts

4. **Tool System**
   - 86 handlers
   - File operations (read, write, move, rename, merge)
   - Analysis tools (complexity, dead code, duplicates)
   - Validation tools (syntax, imports, types)

---

## PHASE 2: CURRENT LIMITATIONS IDENTIFIED

### Problem: AI Stops Too Early

**Current Behavior**:
- AI examines 1-2 files
- Makes a quick decision
- Moves on without deep analysis

**Why This Happens**:
1. **No tool to list ALL source files** - AI doesn't know what exists
2. **No cross-referencing mechanism** - Can't compare files systematically
3. **No iterative examination loop** - Stops after first pass
4. **No forced deep dive** - Can skip to "manual review" too easily

### Problem: Shallow Analysis

**Current Behavior**:
- Compares 2 files
- Sees 0% similarity
- Creates report without understanding WHY

**Missing Capabilities**:
1. **List all files in codebase** - Need inventory
2. **Cross-reference against ARCHITECTURE.md** - Validate placement
3. **Cross-reference against MASTER_PLAN.md** - Validate purpose
4. **Examine relationships** - Imports, dependencies, usage
5. **Iterative refinement** - Keep digging until answer found

---

## PHASE 3: REQUIRED NEW CAPABILITIES

### 1. Codebase Inventory Tool

**Purpose**: Give AI complete visibility of all source files

**Tool Definition**:
```python
{
    "name": "list_all_source_files",
    "description": "Get complete list of all source files in the codebase with metadata",
    "parameters": {
        "file_types": ["py", "js", "ts", "jsx", "tsx"],  # Filter by type
        "include_tests": false,  # Include test files
        "include_metadata": true  # Include size, lines, imports
    }
}
```

**Returns**:
```json
{
    "total_files": 150,
    "files": [
        {
            "path": "core/risk/risk_assessment.py",
            "size": 5432,
            "lines": 187,
            "imports": ["typing", "dataclasses", "core.models"],
            "classes": ["RiskAssessment", "RiskLevel"],
            "functions": ["calculate_risk", "assess_impact"]
        },
        ...
    ]
}
```

### 2. Cross-Reference Analysis Tool

**Purpose**: Compare file against architecture and master plan

**Tool Definition**:
```python
{
    "name": "cross_reference_file",
    "description": "Analyze file against ARCHITECTURE.md and MASTER_PLAN.md",
    "parameters": {
        "file_path": "core/risk/risk_assessment.py",
        "check_placement": true,  # Is it in right directory?
        "check_purpose": true,    # Does it match planned functionality?
        "check_naming": true,     # Does name follow conventions?
        "check_dependencies": true # Are dependencies appropriate?
    }
}
```

**Returns**:
```json
{
    "placement_valid": false,
    "placement_recommendation": "Should be in services/ not core/",
    "purpose_match": true,
    "purpose_description": "Implements risk assessment as per MASTER_PLAN section 3.2",
    "naming_valid": true,
    "dependency_issues": [
        "Imports from core.models but should use services.models"
    ]
}
```

### 3. Relationship Mapping Tool

**Purpose**: Understand how files relate to each other

**Tool Definition**:
```python
{
    "name": "map_file_relationships",
    "description": "Map all relationships for a file (imports, imported by, similar files)",
    "parameters": {
        "file_path": "core/risk/risk_assessment.py",
        "depth": 2  # How many levels deep to analyze
    }
}
```

**Returns**:
```json
{
    "imports": ["core.models", "typing", "dataclasses"],
    "imported_by": ["services/project_service.py", "api/risk_endpoints.py"],
    "similar_files": [
        {
            "path": "services/risk_assessment.py",
            "similarity": 0.3,
            "common_classes": ["RiskAssessment"],
            "differences": "services version has more methods"
        }
    ],
    "dependency_graph": {
        "direct": 3,
        "indirect": 12,
        "circular": false
    }
}
```

### 4. Iterative Deep Dive Tool

**Purpose**: Force AI to keep examining until it finds answer

**Tool Definition**:
```python
{
    "name": "deep_dive_analysis",
    "description": "Perform iterative deep analysis until determination reached",
    "parameters": {
        "issue_description": "Two files with similar names in different locations",
        "files_to_examine": ["core/risk/risk_assessment.py", "services/risk_assessment.py"],
        "max_iterations": 10,  # Keep going until answer found
        "required_checks": [
            "read_both_files",
            "check_architecture",
            "check_master_plan",
            "map_relationships",
            "cross_reference_all_similar_files"
        ]
    }
}
```

**Behavior**:
- Iteration 1: Read both files
- Iteration 2: Check ARCHITECTURE.md
- Iteration 3: Check MASTER_PLAN.md
- Iteration 4: Map relationships
- Iteration 5: Find all similar files
- Iteration 6: Cross-reference each similar file
- Iteration 7: Analyze import patterns
- Iteration 8: Check usage patterns
- Iteration 9: Determine purpose of each
- Iteration 10: Make final determination

**Must return one of**:
- MERGE: Files are duplicates, merge them
- KEEP_BOTH: Files serve different purposes, document why
- MOVE: One is misplaced, move to correct location
- REFACTOR: Both need refactoring to eliminate confusion

---

## PHASE 4: ENHANCED PROMPT STRATEGY

### Current Prompt Issues

**Too Permissive**:
- "You CAN compare files" → AI stops after comparing
- "If unclear, create report" → AI takes easy way out

**Needs to be**:
- "You MUST examine ALL related files"
- "You MUST cross-reference against architecture"
- "You MUST map all relationships"
- "You MUST make a determination, not just report"

### New Prompt Structure

```
🎯 REFACTORING TASK - DEEP ANALYSIS REQUIRED

⚠️ CRITICAL: You MUST perform COMPREHENSIVE analysis before deciding.

📋 MANDATORY ANALYSIS STEPS:

1️⃣ INVENTORY PHASE
   - Use list_all_source_files to see entire codebase
   - Identify ALL files related to this issue
   - Don't stop at just 2 files - find ALL similar files

2️⃣ CROSS-REFERENCE PHASE
   - Use cross_reference_file on EACH file
   - Check against ARCHITECTURE.md
   - Check against MASTER_PLAN.md
   - Validate placement, purpose, naming

3️⃣ RELATIONSHIP MAPPING PHASE
   - Use map_file_relationships on EACH file
   - Understand imports and dependencies
   - Find who uses each file
   - Identify circular dependencies

4️⃣ DEEP EXAMINATION PHASE
   - Read EVERY related file (not just 2)
   - Understand purpose of EACH file
   - Compare implementations
   - Identify differences and similarities

5️⃣ DETERMINATION PHASE
   - Based on ALL evidence gathered
   - Make ONE of these decisions:
     * MERGE: Duplicates → merge_file_implementations
     * KEEP_BOTH: Different purposes → update_architecture to clarify
     * MOVE: Misplaced → move_file to correct location
     * REFACTOR: Confusing → refactor to eliminate confusion

❌ FORBIDDEN ACTIONS:
- Examining only 2 files when more exist
- Skipping cross-reference checks
- Not reading ARCHITECTURE.md
- Not reading MASTER_PLAN.md
- Creating report without completing ALL analysis steps
- Saying "unclear" without exhausting all analysis

✅ REQUIRED ACTIONS:
- Complete ALL 5 phases above
- Examine EVERY related file
- Cross-reference EVERYTHING
- Make a determination based on evidence
- Take action (merge/move/keep/refactor)
```

---

## PHASE 5: CONVERSATION MANAGER ANALYSIS

### Current Conversation Flow

**File**: `pipeline/client.py` - OllamaClient class

**Current Behavior**:
1. Build prompt with context
2. Send to LLM
3. Get response
4. Extract tool calls
5. Execute tools
6. Return result

**Problem**: Single-pass execution, no forced iteration

### Required Enhancement: Forced Iteration Loop

**New Behavior**:
```python
def execute_with_forced_iteration(self, prompt, required_steps, max_iterations=10):
    """
    Force AI to complete all required steps before allowing completion.
    
    Args:
        prompt: Initial prompt
        required_steps: List of steps that MUST be completed
        max_iterations: Maximum iterations allowed
    
    Returns:
        Result only after all steps completed
    """
    completed_steps = set()
    iteration = 0
    
    while iteration < max_iterations:
        # Check if all required steps completed
        if completed_steps >= set(required_steps):
            break
        
        # Build prompt with progress
        remaining = set(required_steps) - completed_steps
        iteration_prompt = f"""
{prompt}

📊 PROGRESS: {len(completed_steps)}/{len(required_steps)} steps completed

✅ COMPLETED:
{chr(10).join(f"- {step}" for step in completed_steps)}

⚠️ REMAINING (YOU MUST COMPLETE THESE):
{chr(10).join(f"- {step}" for step in remaining)}

🎯 NEXT: Complete the next remaining step. You CANNOT finish until ALL steps are done.
"""
        
        # Get response
        response = self.chat(iteration_prompt)
        
        # Extract tool calls
        tool_calls = self.extract_tool_calls(response)
        
        # Execute tools and track completed steps
        for tool_call in tool_calls:
            tool_name = tool_call['function']['name']
            
            # Map tool to step
            if tool_name == 'list_all_source_files':
                completed_steps.add('inventory')
            elif tool_name == 'cross_reference_file':
                completed_steps.add('cross_reference')
            elif tool_name == 'map_file_relationships':
                completed_steps.add('relationship_mapping')
            elif tool_name == 'read_file':
                completed_steps.add('deep_examination')
            elif tool_name in ['merge_file_implementations', 'move_file', 'update_architecture']:
                completed_steps.add('determination')
        
        iteration += 1
    
    if completed_steps < set(required_steps):
        raise Exception(f"Failed to complete all required steps after {max_iterations} iterations")
    
    return response
```

---

## PHASE 6: TASK SYSTEM INTEGRATION

### Current Task Flow

**File**: `pipeline/phases/refactoring.py`

**Current Behavior**:
1. Select task
2. Build context
3. Call LLM once
4. Check if resolved
5. Move to next task

**Problem**: Single LLM call, no forced iteration

### Required Enhancement: Multi-Iteration Task Execution

**New Behavior**:
```python
def _work_on_task_with_forced_iteration(self, state: PipelineState, task: RefactoringTask):
    """
    Work on task with forced iteration until properly resolved.
    
    Forces AI to:
    1. List all related files
    2. Cross-reference each file
    3. Map relationships
    4. Read all files
    5. Make determination
    """
    # Define required steps based on task type
    if task.issue_type == RefactoringIssueType.CONFLICT:
        required_steps = [
            'list_all_source_files',
            'cross_reference_all_files',
            'map_relationships',
            'read_all_related_files',
            'check_architecture',
            'check_master_plan',
            'make_determination'
        ]
    elif task.issue_type == RefactoringIssueType.DUPLICATE:
        required_steps = [
            'list_all_source_files',
            'find_all_similar_files',
            'read_all_similar_files',
            'compare_implementations',
            'make_determination'
        ]
    # ... other task types
    
    # Execute with forced iteration
    iteration = 0
    completed_steps = set()
    
    while iteration < 10 and len(completed_steps) < len(required_steps):
        # Build context with progress
        context = self._build_task_context_with_progress(task, completed_steps, required_steps)
        
        # Build prompt
        prompt = self._build_task_prompt(task, context)
        
        # Call LLM
        content, tool_calls = self.client.chat_with_tools(
            messages=[{"role": "user", "content": prompt}],
            tools=self.tools
        )
        
        # Execute tools and track progress
        results = self.handler.process_tool_calls(tool_calls)
        
        # Update completed steps
        for result in results:
            tool_name = result.get('tool')
            if tool_name == 'list_all_source_files':
                completed_steps.add('list_all_source_files')
            # ... track other steps
        
        iteration += 1
    
    # Check if all steps completed
    if len(completed_steps) < len(required_steps):
        # Force completion with auto-report
        self.logger.warning(f"Task {task.task_id}: Not all steps completed after {iteration} iterations")
        # ... auto-report logic
    
    return result
```

---

## PHASE 7: IMPLEMENTATION PLAN

### Step 1: Create New Tools (Priority: CRITICAL)

**Files to Create**:
1. `pipeline/tool_modules/codebase_analysis_tools.py`
   - list_all_source_files
   - cross_reference_file
   - map_file_relationships
   - deep_dive_analysis

2. `pipeline/handlers.py` - Add handlers:
   - _handle_list_all_source_files
   - _handle_cross_reference_file
   - _handle_map_file_relationships
   - _handle_deep_dive_analysis

### Step 2: Enhance Conversation Manager (Priority: HIGH)

**File**: `pipeline/client.py`
- Add execute_with_forced_iteration method
- Add step tracking
- Add progress reporting

### Step 3: Enhance Task Execution (Priority: HIGH)

**File**: `pipeline/phases/refactoring.py`
- Add _work_on_task_with_forced_iteration method
- Add required_steps definition per task type
- Add progress tracking
- Add forced completion logic

### Step 4: Update Prompts (Priority: HIGH)

**File**: `pipeline/phases/refactoring.py`
- Add MANDATORY ANALYSIS STEPS section
- Add progress tracking in prompt
- Add FORBIDDEN ACTIONS section
- Remove permissive language

### Step 5: Integration Testing (Priority: MEDIUM)

**Test Cases**:
1. Integration conflict with 2 similar files
2. Integration conflict with 5+ similar files
3. Duplicate detection across multiple directories
4. Architecture violation with unclear placement

---

## PHASE 8: EXPECTED OUTCOMES

### Before Implementation

**Current Behavior**:
```
Task: Integration conflict - risk_assessment.py in 2 locations
AI: compare_file_implementations(file1, file2)
Result: 30% similar
AI: create_issue_report("manual review needed")
Status: ✅ COMPLETE (but nothing fixed)
```

### After Implementation

**New Behavior**:
```
Task: Integration conflict - risk_assessment.py in 2 locations

Iteration 1:
AI: list_all_source_files(file_types=["py"])
Result: Found 150 files, 3 contain "risk_assessment"
Progress: 1/7 steps completed

Iteration 2:
AI: cross_reference_file("core/risk/risk_assessment.py")
Result: Should be in services/ per ARCHITECTURE.md
Progress: 2/7 steps completed

Iteration 3:
AI: cross_reference_file("services/risk_assessment.py")
Result: Correct location per ARCHITECTURE.md
Progress: 3/7 steps completed

Iteration 4:
AI: map_file_relationships("core/risk/risk_assessment.py")
Result: Used by 2 files, imports core.models
Progress: 4/7 steps completed

Iteration 5:
AI: read_file("core/risk/risk_assessment.py")
AI: read_file("services/risk_assessment.py")
Result: services/ version is more complete
Progress: 5/7 steps completed

Iteration 6:
AI: read_file("ARCHITECTURE.md")
Result: services/ is correct location for business logic
Progress: 6/7 steps completed

Iteration 7:
AI: Determination: core/ version is misplaced
AI: move_file(
    source="core/risk/risk_assessment.py",
    destination="services/risk_assessment_legacy.py",
    reason="Misplaced, moving to services with legacy suffix"
)
Progress: 7/7 steps completed
Status: ✅ COMPLETE (actually fixed!)
```

---

## CONCLUSION

The system needs:

1. **New Tools** to give AI complete visibility
2. **Forced Iteration** to prevent premature stopping
3. **Progress Tracking** to ensure all steps completed
4. **Stricter Prompts** to eliminate easy outs
5. **Step Validation** to verify work done

**Result**: AI will be FORCED to:
- Examine EVERY related file
- Cross-reference EVERYTHING
- Map ALL relationships
- Make REAL determinations
- Take ACTUAL action

**No more lazy "manual review" reports!**