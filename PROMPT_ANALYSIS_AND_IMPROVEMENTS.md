# Comprehensive Prompt Analysis and Improvements

## Current Prompt Inventory

### System Prompts (Static)
1. **planning** - Senior software architect creating implementation plan
2. **coding** - Expert Python developer implementing production code
3. **qa** - Senior code reviewer performing quality checks
4. **debugging** - Debugging expert fixing code issues
5. **documentation** - Technical writer creating documentation
6. **project_planning** - Project manager analyzing progress

### User Prompts (Dynamic)
1. `get_planning_prompt()` - Initial project planning
2. `get_coding_prompt()` - Code implementation
3. `get_qa_prompt()` - Code review
4. `get_debug_prompt()` - Bug fixing
5. `get_project_planning_prompt()` - Project expansion
6. `get_documentation_prompt()` - Documentation updates
7. `get_modification_decision_prompt()` - Modification decisions

## Critical Issues with Current Prompts

### Issue 1: Static System Prompts
**Problem**: System prompts are hardcoded and don't adapt to context

**Example**:
```python
"qa": """You are a senior code reviewer performing thorough quality checks.
...
"""
```

**Issues**:
- Same prompt for simple and complex files
- Doesn't consider recent failures
- No adaptation to model capabilities
- Ignores project-specific patterns

### Issue 2: Monolithic Prompts
**Problem**: Large prompts that could be chunked

**Example**: QA prompt is ~50 lines with all instructions at once

**Better Approach**:
```python
# Turn 1: Set context
"Review this file: {filepath}"

# Turn 2: Provide specific checks based on file type
"Check for: {relevant_checks_only}"

# Turn 3: Show examples if needed
"Here are examples of issues to look for: {examples}"
```

### Issue 3: No Context Awareness
**Problem**: Prompts don't use application state

**Missing Context**:
- Recent failures in this phase
- Project coding standards
- Dependencies between files
- User preferences
- Model performance history

### Issue 4: Tool Usage Not Emphasized Enough
**Problem**: Models often describe instead of using tools

**Current**:
```python
"Use report_issue for EACH problem found."
```

**Better**:
```python
"CRITICAL: You MUST call tools. Examples:
- Found syntax error? Call: report_issue(type='SyntaxError', ...)
- Code is perfect? Call: approve_code(filepath='...')
- Need to verify import? Call: read_file(filepath='...')

DO NOT just describe issues. USE THE TOOLS."
```

### Issue 5: No Model-Specific Optimization
**Problem**: Same prompt for 14b and 32b models

**14b Model Needs**:
- Simpler instructions
- More examples
- Explicit step-by-step
- Clear tool call format

**32b Model Can Handle**:
- Complex reasoning
- Implicit instructions
- Fewer examples
- More autonomy

## Proposed Improvements

### Improvement 1: Dynamic Prompt Construction

```python
class ContextAwarePromptBuilder:
    """
    Builds prompts dynamically based on:
    - Task complexity
    - Model capabilities
    - Recent failures
    - Project context
    - File characteristics
    """
    
    def build_qa_prompt(self, context: QAContext) -> Union[str, List[str]]:
        """
        Build QA prompt with context awareness.
        Returns single prompt or list of prompts for chunking.
        """
        builder = PromptBuilder()
        
        # 1. Role definition (adapt to model)
        if context.model_size == "14b":
            builder.add_role("You are a code reviewer. Your job is to find issues.")
        else:
            builder.add_role("You are a senior code reviewer performing thorough analysis.")
        
        # 2. File context
        builder.add_section(f"FILE: {context.filepath}")
        builder.add_section(f"```python\n{context.code}\n```")
        
        # 3. Relevant checks only (based on file type)
        checks = self.get_relevant_checks(context)
        builder.add_section("CHECK FOR:", checks)
        
        # 4. Examples (only if model has failed recently)
        if context.recent_failures:
            examples = self.get_examples_for_failures(context.recent_failures)
            builder.add_section("EXAMPLES:", examples)
        
        # 5. Tool usage (always emphasize)
        builder.add_tool_instructions(context.available_tools)
        
        # 6. Project-specific patterns
        if context.project_patterns:
            builder.add_section("PROJECT STANDARDS:", context.project_patterns)
        
        # Check if prompt is too large
        if builder.estimate_tokens() > context.model_limits.max_prompt:
            return builder.chunk(context.model_limits)
        
        return builder.build()
    
    def get_relevant_checks(self, context: QAContext) -> List[str]:
        """
        Return only relevant checks based on file characteristics.
        """
        checks = []
        
        # Always check syntax
        checks.append("Syntax errors")
        
        # Check imports if file has them
        if "import" in context.code:
            checks.append("Missing or incorrect imports")
        
        # Check error handling if file has try/except
        if "try:" in context.code or "except" in context.code:
            checks.append("Error handling completeness")
        
        # Check type hints if file uses them
        if "->" in context.code or ": " in context.code:
            checks.append("Type hint consistency")
        
        # Check for incomplete code
        if any(marker in context.code for marker in ["TODO", "pass", "NotImplementedError", "..."]):
            checks.append("Incomplete implementations")
        
        return checks
```

### Improvement 2: Chunked Prompts for Complex Tasks

```python
class ChunkedPromptStrategy:
    """
    Split complex tasks into multiple conversation turns.
    """
    
    def create_qa_conversation(self, context: QAContext) -> List[Message]:
        """
        Create a multi-turn conversation for QA.
        """
        messages = []
        
        # Turn 1: Set context and role
        messages.append({
            "role": "system",
            "content": self.get_role_prompt(context.model_size)
        })
        
        messages.append({
            "role": "user",
            "content": f"Review this file:\n\nFILE: {context.filepath}\n```python\n{context.code[:2000]}\n```"
        })
        
        # Turn 2: If file is large, continue in next message
        if len(context.code) > 2000:
            messages.append({
                "role": "assistant",
                "content": "I'll review this file. Please provide the rest of the code."
            })
            
            messages.append({
                "role": "user",
                "content": f"```python\n{context.code[2000:]}\n```"
            })
        
        # Turn 3: Provide specific checks
        messages.append({
            "role": "user",
            "content": self.get_check_instructions(context)
        })
        
        # Turn 4: Emphasize tool usage with examples
        messages.append({
            "role": "user",
            "content": self.get_tool_examples(context.available_tools)
        })
        
        return messages
```

### Improvement 3: Model-Specific Prompt Variants

```python
class ModelSpecificPrompts:
    """
    Different prompt strategies for different model sizes.
    """
    
    def get_qa_prompt_14b(self, context: QAContext) -> str:
        """
        Simplified prompt for 14b model.
        """
        return f"""
Review this Python file and find issues.

FILE: {context.filepath}
```python
{context.code}
```

STEP 1: Check for syntax errors
- Look for missing colons, brackets, quotes
- If found, call: report_issue(type="SyntaxError", description="...", line=X)

STEP 2: Check imports
- Are all imports at the top?
- Are all used modules imported?
- If issue found, call: report_issue(type="ImportError", ...)

STEP 3: Check for incomplete code
- Look for TODO, pass, NotImplementedError, ...
- If found, call: report_issue(type="incomplete", ...)

STEP 4: If no issues found
- Call: approve_code(filepath="{context.filepath}")

REMEMBER: Use the tools! Don't just describe issues.
"""
    
    def get_qa_prompt_32b(self, context: QAContext) -> str:
        """
        Advanced prompt for 32b model.
        """
        return f"""
Perform a comprehensive code review of this Python file.

FILE: {context.filepath}
```python
{context.code}
```

ANALYSIS FRAMEWORK:
1. Syntax & Structure: Validate Python syntax, indentation, and code structure
2. Imports & Dependencies: Verify all imports are present and correctly used
3. Logic & Completeness: Ensure implementations are complete and correct
4. Type Safety: Check type hints for consistency and correctness
5. Error Handling: Evaluate exception handling and edge cases
6. Code Quality: Assess readability, maintainability, and best practices

VERIFICATION TOOLS:
- read_file: Verify imported modules exist
- search_code: Check if referenced classes/functions exist
- list_directory: Validate project structure

REPORTING:
- Use report_issue for each problem (with type, description, line number)
- Use approve_code only if all checks pass
- Provide reasoning for your decisions

Begin your analysis.
"""
```

### Improvement 4: Context-Aware Examples

```python
class ExampleGenerator:
    """
    Generate relevant examples based on recent failures.
    """
    
    def get_examples_for_context(self, context: QAContext) -> str:
        """
        Generate examples based on what the model has struggled with.
        """
        examples = []
        
        # If model recently failed to detect syntax errors
        if "syntax_error" in context.recent_failures:
            examples.append("""
EXAMPLE - Syntax Error:
Code: if x > 5  # Missing colon
Tool Call: report_issue(type="SyntaxError", description="Missing colon after if statement", line=10)
""")
        
        # If model recently missed imports
        if "import_error" in context.recent_failures:
            examples.append("""
EXAMPLE - Missing Import:
Code: result = json.dumps(data)  # json not imported
Tool Call: report_issue(type="ImportError", description="Module 'json' is used but not imported", line=15)
""")
        
        # If model recently described instead of using tools
        if "no_tool_calls" in context.recent_failures:
            examples.append("""
WRONG: "I found a syntax error on line 10 where the colon is missing."
RIGHT: report_issue(type="SyntaxError", description="Missing colon after if statement", line=10)

WRONG: "The code looks good to me."
RIGHT: approve_code(filepath="example.py")
""")
        
        return "\n".join(examples)
```

### Improvement 5: Project-Specific Context

```python
class ProjectContextProvider:
    """
    Inject project-specific context into prompts.
    """
    
    def get_project_context(self, project_dir: Path) -> dict:
        """
        Extract project-specific patterns and standards.
        """
        context = {}
        
        # 1. Coding standards from existing files
        context["import_style"] = self.detect_import_style(project_dir)
        context["docstring_style"] = self.detect_docstring_style(project_dir)
        context["type_hint_usage"] = self.detect_type_hint_usage(project_dir)
        
        # 2. Common patterns
        context["common_imports"] = self.get_common_imports(project_dir)
        context["base_classes"] = self.get_base_classes(project_dir)
        context["utility_functions"] = self.get_utility_functions(project_dir)
        
        # 3. Project structure
        context["directory_structure"] = self.get_directory_structure(project_dir)
        
        return context
    
    def inject_into_prompt(self, base_prompt: str, context: dict) -> str:
        """
        Add project context to prompt.
        """
        additions = []
        
        if context.get("import_style"):
            additions.append(f"PROJECT STANDARD - Imports: {context['import_style']}")
        
        if context.get("common_imports"):
            additions.append(f"COMMON IMPORTS: {', '.join(context['common_imports'])}")
        
        if context.get("base_classes"):
            additions.append(f"BASE CLASSES: {', '.join(context['base_classes'])}")
        
        context_section = "\n".join(additions)
        return f"{base_prompt}\n\nPROJECT CONTEXT:\n{context_section}"
```

### Improvement 6: Failure-Adaptive Prompts

```python
class FailureAdaptivePrompts:
    """
    Adapt prompts based on recent failures.
    """
    
    def adapt_prompt(self, base_prompt: str, failure_history: List[dict]) -> str:
        """
        Modify prompt based on what has failed recently.
        """
        adaptations = []
        
        # Analyze failure patterns
        failure_types = [f["type"] for f in failure_history]
        
        # If model keeps generating empty tool names
        if failure_types.count("empty_tool_name") > 2:
            adaptations.append("""
CRITICAL: Your tool calls MUST have a name field.
WRONG: {"function": {"name": "", "arguments": {...}}}
RIGHT: {"function": {"name": "report_issue", "arguments": {...}}}
""")
        
        # If model keeps using wrong tools
        if failure_types.count("unknown_tool") > 2:
            adaptations.append(f"""
AVAILABLE TOOLS (use ONLY these):
{self.format_available_tools()}

DO NOT invent tool names. Use exactly these names.
""")
        
        # If model keeps describing instead of calling tools
        if failure_types.count("no_tool_calls") > 2:
            adaptations.append("""
YOU MUST CALL TOOLS. Descriptions are not enough.

Every response must include at least one tool call.
If you find an issue: call report_issue
If code is perfect: call approve_code
If you need more info: call read_file or search_code
""")
        
        if adaptations:
            adaptation_section = "\n\n".join(adaptations)
            return f"{base_prompt}\n\n⚠️ IMPORTANT REMINDERS:\n{adaptation_section}"
        
        return base_prompt
```

## Implementation Plan

### Phase 1: Dynamic Prompt Builder (Week 1)
```python
# File: pipeline/prompts/dynamic_builder.py

class DynamicPromptBuilder:
    def __init__(self, project_dir: Path):
        self.project_context = ProjectContextProvider(project_dir)
        self.example_generator = ExampleGenerator()
        self.failure_adapter = FailureAdaptivePrompts()
    
    def build_prompt(self, phase: str, context: dict) -> Union[str, List[dict]]:
        """
        Main entry point for building prompts.
        """
        # Get base prompt
        base_prompt = self.get_base_prompt(phase, context)
        
        # Add project context
        prompt = self.project_context.inject_into_prompt(base_prompt, context)
        
        # Add examples if needed
        if context.get("recent_failures"):
            examples = self.example_generator.get_examples_for_context(context)
            prompt = f"{prompt}\n\n{examples}"
        
        # Adapt based on failures
        prompt = self.failure_adapter.adapt_prompt(prompt, context.get("failure_history", []))
        
        # Check if chunking is needed
        if self.should_chunk(prompt, context.get("model_limits")):
            return self.chunk_prompt(prompt, context)
        
        return prompt
```

### Phase 2: Model-Specific Variants (Week 2)
```python
# File: pipeline/prompts/model_variants.py

class ModelSpecificPromptFactory:
    def get_prompt(self, phase: str, model_size: str, context: dict) -> str:
        """
        Get model-specific prompt variant.
        """
        if model_size in ["3b", "7b", "14b"]:
            return self.get_simple_prompt(phase, context)
        elif model_size in ["32b", "70b"]:
            return self.get_advanced_prompt(phase, context)
        else:
            return self.get_default_prompt(phase, context)
```

### Phase 3: Chunked Conversations (Week 3)
```python
# File: pipeline/prompts/chunked_strategy.py

class ChunkedConversationManager:
    def create_conversation(self, phase: str, context: dict) -> List[dict]:
        """
        Create multi-turn conversation for complex tasks.
        """
        messages = []
        
        # Turn 1: Role and context
        messages.extend(self.create_context_turn(phase, context))
        
        # Turn 2: Task details (chunked if needed)
        messages.extend(self.create_task_turns(context))
        
        # Turn 3: Tool instructions
        messages.extend(self.create_tool_turn(context))
        
        # Turn 4: Examples (if needed)
        if context.get("needs_examples"):
            messages.extend(self.create_example_turn(context))
        
        return messages
```

### Phase 4: Integration with Orchestration (Week 4)
```python
# File: pipeline/orchestration/prompt_coordinator.py

class PromptCoordinator:
    """
    Coordinates prompts across multiple models.
    """
    
    def get_prompt_for_model(self, model: str, phase: str, context: dict) -> Union[str, List[dict]]:
        """
        Get appropriate prompt for specific model in orchestration.
        """
        # Determine model capabilities
        model_info = self.get_model_info(model)
        
        # Build context-aware prompt
        builder = DynamicPromptBuilder(context.project_dir)
        prompt = builder.build_prompt(phase, {
            **context,
            "model_size": model_info.size,
            "model_limits": model_info.limits,
            "model_capabilities": model_info.capabilities
        })
        
        return prompt
```

## Testing Strategy

### Test 1: Prompt Effectiveness
```python
def test_prompt_effectiveness():
    """
    Measure how often models use tools correctly with new prompts.
    """
    test_cases = [
        {"file": "simple.py", "expected_tools": ["approve_code"]},
        {"file": "with_errors.py", "expected_tools": ["report_issue"]},
        {"file": "complex.py", "expected_tools": ["read_file", "search_code", "report_issue"]}
    ]
    
    for case in test_cases:
        # Test with old prompt
        old_result = run_qa_with_prompt(OLD_PROMPT, case["file"])
        
        # Test with new prompt
        new_result = run_qa_with_prompt(NEW_PROMPT, case["file"])
        
        # Compare tool usage
        assert new_result.tool_calls > old_result.tool_calls
        assert new_result.correct_tools > old_result.correct_tools
```

### Test 2: Context Adaptation
```python
def test_context_adaptation():
    """
    Verify prompts adapt to context correctly.
    """
    # Test with recent failures
    context_with_failures = {
        "recent_failures": ["empty_tool_name", "empty_tool_name"]
    }
    prompt = builder.build_prompt("qa", context_with_failures)
    assert "MUST have a name field" in prompt
    
    # Test without failures
    context_no_failures = {"recent_failures": []}
    prompt = builder.build_prompt("qa", context_no_failures)
    assert "MUST have a name field" not in prompt
```

## Expected Improvements

1. **Tool Usage**: 80%+ of responses should include tool calls (vs current ~50%)
2. **Correct Tools**: 90%+ of tool calls should be valid (vs current ~60%)
3. **Failure Recovery**: Prompts adapt after 2 failures (vs current never)
4. **Context Relevance**: Only relevant checks included (vs current all checks)
5. **Model Efficiency**: 14b models get simpler prompts, 32b get advanced

## Migration Path

1. **Week 1**: Implement dynamic builder alongside existing prompts
2. **Week 2**: A/B test new prompts vs old prompts
3. **Week 3**: Gradually migrate phases to new system
4. **Week 4**: Remove old static prompts, full dynamic system

This approach transforms prompts from static templates to intelligent, context-aware, adaptive instructions that maximize model effectiveness.