# Debug/QA Mode Redesign - Context-Aware Error Fixing

## Problem Statement

The current debug/QA mode uses the same pipeline designed for NEW CODE CREATION, but debugging requires a fundamentally different approach:

### Current Approach (Wrong for Debugging)
1. QA phase reviews a single file
2. Debugging phase tries to fix the error in isolation
3. No call chain analysis
4. No related file context
5. AI doesn't have tools to explore the codebase

### What Debugging Actually Needs
1. **Full call chain context** from traceback
2. **All related files** in the error chain
3. **Class/method definitions** that are referenced
4. **Tool calling** so AI can explore related code
5. **Decision making** - fix existing code OR create missing methods

## The Error We're Seeing

```
File: /home/logan/code/AI/test-automation/src/execution/job_executor.py
Line: 3010
Error: AttributeError: 'PipelineCoordinator' object has no attribute 'start_phase'
Code: self.coordinator.start_phase('integration', 'setup_and_language_detection')
```

### What the AI Needs to Know

1. **The calling code** (job_executor.py line 3010)
   - What is `self.coordinator`?
   - Where is it defined?
   - What type is it?

2. **The PipelineCoordinator class**
   - Where is it defined?
   - What methods does it have?
   - Is `start_phase` missing or renamed?

3. **Related files in the call chain**
   - How did we get to line 3010?
   - What called `_execute_integration_job_internal`?
   - Full traceback context

4. **The ability to explore**
   - Read PipelineCoordinator source
   - Search for similar method names
   - Check if method was renamed
   - Look at other usages

## Proposed Solution: Context-Aware Debug Pipeline

### Phase 1: Error Analysis & Context Gathering

```python
class DebugContextGatherer:
    def gather_context(self, error: Dict) -> DebugContext:
        """
        Gather all relevant context for an error.
        
        Returns:
            DebugContext with:
            - Full traceback with all files
            - Class definitions referenced
            - Method definitions referenced
            - Related imports
            - Similar code patterns
        """
        context = DebugContext()
        
        # 1. Parse traceback to get call chain
        call_chain = self.parse_traceback(error['context'])
        
        # 2. Load all files in call chain
        for frame in call_chain:
            context.add_file(frame.file, frame.line)
        
        # 3. Extract class/method references from error
        if "object has no attribute" in error['message']:
            obj_type, missing_attr = self.parse_attribute_error(error)
            
            # Find the class definition
            class_def = self.find_class_definition(obj_type)
            if class_def:
                context.add_class(class_def)
            
            # Search for similar attributes
            similar = self.find_similar_attributes(obj_type, missing_attr)
            context.add_similar_methods(similar)
        
        # 4. Find where the object is created/assigned
        obj_source = self.trace_object_origin(error['file'], error['line'])
        if obj_source:
            context.add_file(obj_source.file, obj_source.line)
        
        return context
```

### Phase 2: AI-Powered Analysis with Tool Calling

Instead of just running QA + Debugging phases, we need a specialized debug phase:

```python
class DebugPhase:
    def execute(self, error: Dict, context: DebugContext) -> DebugResult:
        """
        Use AI with tool calling to analyze and fix the error.
        
        The AI has access to:
        - read_file(path) - Read any file in the project
        - search_code(pattern) - Search for code patterns
        - find_definition(symbol) - Find where something is defined
        - list_methods(class_name) - List all methods in a class
        - get_call_chain(error) - Get full call chain
        """
        
        # Build comprehensive prompt
        prompt = self.build_debug_prompt(error, context)
        
        # Give AI tools to explore
        tools = [
            ReadFileTool(self.project_dir),
            SearchCodeTool(self.project_dir),
            FindDefinitionTool(self.project_dir),
            ListMethodsTool(self.project_dir),
        ]
        
        # Let AI analyze with tool calling
        result = self.ai_client.chat_with_tools(
            prompt=prompt,
            tools=tools,
            max_iterations=10  # Allow multiple tool calls
        )
        
        return result
```

### Phase 3: Smart Fix Decision

The AI should decide:

1. **Is the method missing?**
   - Create it in the target class
   - Implement based on usage context

2. **Was the method renamed?**
   - Update the calling code
   - Use the new method name

3. **Is the object wrong?**
   - Fix the object creation
   - Use the correct class

4. **Is this a design issue?**
   - Suggest refactoring
   - Explain the problem

## Implementation Plan

### Step 1: Create DebugContextGatherer
- Parse tracebacks to extract call chains
- Load all files in the chain
- Extract class/method references
- Find object origins
- Search for similar code

### Step 2: Create Tool System for AI
- ReadFileTool - Read any project file
- SearchCodeTool - Grep/search for patterns
- FindDefinitionTool - Find class/method definitions
- ListMethodsTool - List class methods
- GetCallChainTool - Parse and display call chains

### Step 3: Create Specialized DebugPhase
- Replace QA + Debugging with single DebugPhase
- Use tool calling for exploration
- Provide full context in prompt
- Let AI decide fix strategy

### Step 4: Integrate with Debug/QA Mode
- Use DebugContextGatherer before AI analysis
- Pass full context to DebugPhase
- Apply fixes based on AI decisions
- Re-run tests and iterate

## Example: How It Should Work

```
1. Error detected:
   AttributeError: 'PipelineCoordinator' object has no attribute 'start_phase'
   at job_executor.py:3010

2. Context gathering:
   ✓ Load job_executor.py
   ✓ Find PipelineCoordinator class definition
   ✓ List all PipelineCoordinator methods
   ✓ Find where self.coordinator is assigned
   ✓ Load full call chain files
   ✓ Search for similar method names

3. AI analysis with tools:
   AI: "Let me check the PipelineCoordinator class"
   Tool: read_file("src/pipeline/coordinator.py")
   AI: "I see it has 'begin_phase' not 'start_phase'"
   Tool: search_code("start_phase")
   AI: "Found 15 calls to start_phase, all should use begin_phase"

4. Fix decision:
   AI: "The method was renamed. I'll update all calls."
   Action: Replace start_phase → begin_phase in all files

5. Apply and test:
   ✓ Update 15 files
   ✓ Re-run tests
   ✓ Verify fix
```

## Benefits

1. **Comprehensive context** - AI sees the full picture
2. **Autonomous exploration** - AI can investigate as needed
3. **Smart decisions** - Fix vs create vs refactor
4. **Efficient** - One phase instead of two
5. **Accurate** - Full context reduces hallucination

## Next Steps

1. Implement DebugContextGatherer
2. Create tool system for AI
3. Build DebugPhase with tool calling
4. Test with the current error
5. Iterate and improve