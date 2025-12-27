# Implementation Roadmap: Multi-Model Orchestration & Dynamic Prompts

## Overview

This roadmap integrates:
1. Multi-model orchestration architecture
2. Dynamic, context-aware prompts
3. Model-as-tool calling
4. FunctionGemma as mediator
5. Application as scaffold (not decision-maker)

## Architecture Vision

```
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION SCAFFOLD                      │
│  (Provides capabilities, executes tool calls, manages state) │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   ARBITER MODEL (14b)                        │
│              ollama01 - Fast Decision Making                 │
│  • Routes queries to specialists                             │
│  • Synthesizes responses                                     │
│  • Detects failures                                          │
│  • Decides phase transitions                                 │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   CODING     │    │  REASONING   │    │  ANALYSIS    │
│ SPECIALIST   │    │ SPECIALIST   │    │ SPECIALIST   │
│              │    │              │    │              │
│ 32b coder    │    │   32b model  │    │  14b model   │
│ ollama02     │    │   ollama02   │    │  ollama01    │
└──────────────┘    └──────────────┘    └──────────────┘
         │                    │                    │
         └────────────────────┴────────────────────┘
                              │
                              ▼
                    ┌──────────────┐
                    │ FUNCTIONGEMMA│
                    │  MEDIATOR    │
                    │              │
                    │ ollama01     │
                    └──────────────┘
```

## Phase 1: Foundation (Weeks 1-2)

### Week 1: Core Infrastructure

#### 1.1 Model-as-Tool Framework
```python
# File: pipeline/orchestration/model_tools.py

class ModelTool:
    """
    Wrapper that makes a model callable as a tool.
    """
    def __init__(self, model: str, server: str, role: str):
        self.model = model
        self.server = server
        self.role = role
        self.client = OllamaClient()
    
    def __call__(self, query: str, context: dict = None) -> dict:
        """
        Call this model with a query.
        Returns structured response.
        """
        # Build context-aware prompt
        prompt = self.build_prompt(query, context)
        
        # Call model
        response = self.client.chat(
            host=self.server,
            model=self.model,
            messages=[
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            tools=self.get_available_tools()
        )
        
        return {
            "model": self.model,
            "response": response,
            "tool_calls": self.extract_tool_calls(response)
        }

# Register models as tools
SPECIALIST_TOOLS = {
    "consult_coding_specialist": ModelTool(
        model="qwen2.5-coder:32b",
        server="ollama02.thiscluster.net",
        role="coding"
    ),
    "consult_reasoning_specialist": ModelTool(
        model="qwen2.5:32b",
        server="ollama02.thiscluster.net",
        role="reasoning"
    ),
    "consult_analysis_specialist": ModelTool(
        model="qwen2.5:14b",
        server="ollama01.thiscluster.net",
        role="analysis"
    ),
    "consult_functiongemma": ModelTool(
        model="functiongemma",
        server="ollama01.thiscluster.net",
        role="interpreter"
    )
}
```

#### 1.2 Conversation Thread Manager
```python
# File: pipeline/orchestration/conversation_manager.py

class ConversationThread:
    """
    Manages a conversation thread for a single model.
    """
    def __init__(self, model: str, role: str):
        self.model = model
        self.role = role
        self.messages = []
        self.metadata = {}
    
    def add_message(self, role: str, content: str, from_model: str = None):
        """Add a message to this thread."""
        self.messages.append({
            "role": role,
            "content": content,
            "from_model": from_model,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_context(self, max_tokens: int = 8192) -> List[dict]:
        """Get conversation context within token limit."""
        # Estimate tokens and truncate if needed
        context = []
        total_tokens = 0
        
        for msg in reversed(self.messages):
            msg_tokens = self.estimate_tokens(msg["content"])
            if total_tokens + msg_tokens > max_tokens:
                break
            context.insert(0, msg)
            total_tokens += msg_tokens
        
        return context

class MultiModelConversationManager:
    """
    Manages conversations across multiple models.
    """
    def __init__(self):
        self.threads = {}  # model -> ConversationThread
        self.shared_context = []
        self.arbiter = None
    
    def create_thread(self, model: str, role: str) -> ConversationThread:
        """Create a new conversation thread for a model."""
        thread = ConversationThread(model, role)
        self.threads[model] = thread
        return thread
    
    def route_message(self, from_model: str, to_model: str, 
                     message: str, filter_context: bool = True) -> dict:
        """
        Route a message from one model to another.
        Arbiter can filter/modify the message.
        """
        if filter_context and self.arbiter:
            # Arbiter reviews and potentially modifies message
            decision = self.arbiter.review_message(
                from_model=from_model,
                to_model=to_model,
                message=message,
                context=self.shared_context
            )
            
            if decision.should_modify:
                message = decision.modified_message
            
            if decision.should_redirect:
                to_model = decision.redirect_to
        
        # Add to recipient's thread
        self.threads[to_model].add_message(
            role="user",
            content=message,
            from_model=from_model
        )
        
        return {"routed_to": to_model, "message": message}
```

#### 1.3 Dynamic Prompt Builder
```python
# File: pipeline/prompts/dynamic_builder.py

class DynamicPromptBuilder:
    """
    Builds prompts dynamically based on context.
    """
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.project_context = self.load_project_context()
        self.failure_history = []
    
    def build_prompt(self, phase: str, task: dict, model_info: dict) -> Union[str, List[dict]]:
        """
        Build context-aware prompt for a specific model.
        """
        # Determine complexity
        complexity = self.assess_complexity(task)
        
        # Get base template
        template = self.get_template(phase, model_info["size"])
        
        # Build sections
        sections = []
        
        # 1. Role (model-specific)
        sections.append(self.build_role_section(phase, model_info))
        
        # 2. Task description
        sections.append(self.build_task_section(task))
        
        # 3. Context (filtered by relevance)
        sections.append(self.build_context_section(task, model_info))
        
        # 4. Tools (filtered by phase and task)
        sections.append(self.build_tools_section(phase, task))
        
        # 5. Examples (if needed)
        if self.needs_examples(model_info, self.failure_history):
            sections.append(self.build_examples_section(phase, self.failure_history))
        
        # 6. Project standards
        if self.project_context:
            sections.append(self.build_standards_section(self.project_context))
        
        # Assemble prompt
        prompt = template.format(**{
            section.name: section.content for section in sections
        })
        
        # Check if chunking needed
        if self.estimate_tokens(prompt) > model_info["context_window"] * 0.7:
            return self.chunk_prompt(sections, model_info)
        
        return prompt
    
    def assess_complexity(self, task: dict) -> int:
        """
        Assess task complexity (1-10).
        """
        complexity = 5  # baseline
        
        # File size
        if task.get("file_size", 0) > 1000:
            complexity += 2
        
        # Dependencies
        if task.get("dependencies", []):
            complexity += len(task["dependencies"]) * 0.5
        
        # Recent failures
        if task.get("attempts", 0) > 2:
            complexity += 2
        
        return min(10, complexity)
```

### Week 2: Arbiter Implementation

#### 2.1 Arbiter Model
```python
# File: pipeline/orchestration/arbiter.py

class ArbiterModel:
    """
    The arbiter coordinates all model interactions.
    Uses fast 14b model for quick decisions.
    """
    def __init__(self):
        self.model = "qwen2.5:14b"
        self.server = "ollama01.thiscluster.net"
        self.client = OllamaClient()
        self.conversation_manager = MultiModelConversationManager()
        self.specialist_tools = SPECIALIST_TOOLS
    
    def decide_action(self, state: PipelineState, context: dict) -> dict:
        """
        Decide what to do next.
        Returns action with specialist to consult if needed.
        """
        prompt = f"""
You are the arbiter coordinating an AI development pipeline.

CURRENT STATE:
- Phase: {state.current_phase}
- Tasks: {len(state.tasks)} total, {state.pending_tasks} pending
- Recent failures: {state.recent_failures}

CONTEXT:
{json.dumps(context, indent=2)}

AVAILABLE SPECIALISTS:
- consult_coding_specialist: For complex code generation (32b model)
- consult_reasoning_specialist: For strategic decisions (32b model)
- consult_analysis_specialist: For quick analysis (14b model)
- consult_functiongemma: For tool call interpretation

DECIDE:
1. What should happen next?
2. Which specialist(s) should be consulted?
3. Should we change phases?
4. Do we need user input?

Use tools to make your decision.
"""
        
        tools = [
            {
                "name": "consult_specialist",
                "description": "Consult a specialist model",
                "parameters": {
                    "specialist": "coding|reasoning|analysis|functiongemma",
                    "query": "The question for the specialist",
                    "context": "Relevant context"
                }
            },
            {
                "name": "change_phase",
                "description": "Change to a different phase",
                "parameters": {
                    "phase": "planning|coding|qa|debugging|documentation",
                    "reason": "Why this phase change"
                }
            },
            {
                "name": "request_user_input",
                "description": "Ask user for guidance",
                "parameters": {
                    "question": "What to ask the user"
                }
            }
        ]
        
        response = self.client.chat(
            host=self.server,
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an arbiter coordinating AI specialists."},
                {"role": "user", "content": prompt}
            ],
            tools=tools
        )
        
        return self.parse_decision(response)
    
    def consult_specialist(self, specialist: str, query: str, context: dict) -> dict:
        """
        Consult a specialist model and return response.
        """
        # Get specialist tool
        specialist_tool = self.specialist_tools.get(f"consult_{specialist}_specialist")
        
        if not specialist_tool:
            return {"error": f"Unknown specialist: {specialist}"}
        
        # Call specialist
        result = specialist_tool(query, context)
        
        # Arbiter reviews the response
        reviewed = self.review_specialist_response(specialist, result)
        
        return reviewed
    
    def review_specialist_response(self, specialist: str, response: dict) -> dict:
        """
        Review a specialist's response before returning it.
        Can modify, clarify, or redirect.
        """
        prompt = f"""
The {specialist} specialist responded:

{json.dumps(response, indent=2)}

Review this response:
1. Is it clear and actionable?
2. Does it need clarification?
3. Should we consult another specialist?

Use tools to indicate your decision.
"""
        
        tools = [
            {
                "name": "approve_response",
                "description": "Approve the response as-is"
            },
            {
                "name": "clarify_with_functiongemma",
                "description": "Use FunctionGemma to clarify tool calls",
                "parameters": {"response": "The response to clarify"}
            },
            {
                "name": "consult_another_specialist",
                "description": "Get a second opinion",
                "parameters": {
                    "specialist": "Which specialist",
                    "query": "What to ask"
                }
            }
        ]
        
        review = self.client.chat(
            host=self.server,
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            tools=tools
        )
        
        return self.apply_review_decision(response, review)
```

## Phase 2: Specialist Integration (Weeks 3-4)

### Week 3: Specialist Models

#### 3.1 Coding Specialist
```python
# File: pipeline/orchestration/specialists/coding.py

class CodingSpecialist:
    """
    32b coder model for complex implementations.
    """
    def __init__(self):
        self.model = "qwen2.5-coder:32b"
        self.server = "ollama02.thiscluster.net"
        self.prompt_builder = DynamicPromptBuilder(Path.cwd())
    
    def implement_task(self, task: dict, context: dict) -> dict:
        """
        Implement a coding task with full context.
        """
        # Build dynamic prompt
        prompt = self.prompt_builder.build_prompt(
            phase="coding",
            task=task,
            model_info={
                "size": "32b",
                "context_window": 16384,
                "capabilities": ["complex_reasoning", "code_generation"]
            }
        )
        
        # Get available tools
        tools = self.get_coding_tools()
        
        # Call model
        response = self.client.chat(
            host=self.server,
            model=self.model,
            messages=prompt if isinstance(prompt, list) else [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            tools=tools
        )
        
        return {
            "specialist": "coding",
            "task": task,
            "response": response,
            "tool_calls": self.extract_tool_calls(response)
        }
```

#### 3.2 Reasoning Specialist
```python
# File: pipeline/orchestration/specialists/reasoning.py

class ReasoningSpecialist:
    """
    32b model for complex reasoning and strategy.
    """
    def __init__(self):
        self.model = "qwen2.5:32b"
        self.server = "ollama02.thiscluster.net"
    
    def analyze_situation(self, situation: dict) -> dict:
        """
        Analyze a complex situation and provide strategic guidance.
        """
        prompt = f"""
Analyze this situation and provide strategic guidance:

SITUATION:
{json.dumps(situation, indent=2)}

ANALYZE:
1. What is the root cause?
2. What are the options?
3. What is the best approach?
4. What are the risks?
5. What should we do next?

Provide your analysis using tools.
"""
        
        tools = [
            {
                "name": "provide_analysis",
                "description": "Provide strategic analysis",
                "parameters": {
                    "root_cause": "Root cause of the issue",
                    "options": "List of possible approaches",
                    "recommendation": "Recommended approach",
                    "risks": "Potential risks",
                    "next_steps": "Specific next steps"
                }
            }
        ]
        
        response = self.client.chat(
            host=self.server,
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            tools=tools
        )
        
        return self.parse_analysis(response)
```

#### 3.3 FunctionGemma Mediator
```python
# File: pipeline/orchestration/specialists/functiongemma.py

class FunctionGemmaMediator:
    """
    Uses FunctionGemma to interpret and clarify tool calls.
    """
    def __init__(self):
        self.model = "functiongemma"
        self.server = "ollama01.thiscluster.net"
    
    def interpret_response(self, response: str, available_tools: List[dict]) -> dict:
        """
        Interpret a model's response and extract tool calls.
        """
        prompt = f"""
A model generated this response:

{response}

Available tools:
{json.dumps(available_tools, indent=2)}

Extract the tool call(s) from this response.
If the response is unclear, infer the intended tool calls.
"""
        
        result = self.client.chat(
            host=self.server,
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            tools=available_tools
        )
        
        return {
            "original_response": response,
            "interpreted_calls": self.extract_tool_calls(result),
            "confidence": self.assess_confidence(result)
        }
    
    def clarify_failed_call(self, failed_call: dict, error: str, 
                           available_tools: List[dict]) -> dict:
        """
        Fix a failed tool call.
        """
        prompt = f"""
This tool call failed:

{json.dumps(failed_call, indent=2)}

Error: {error}

Available tools:
{json.dumps(available_tools, indent=2)}

Correct the tool call to match the available tools.
"""
        
        result = self.client.chat(
            host=self.server,
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            tools=available_tools
        )
        
        return {
            "original_call": failed_call,
            "corrected_call": self.extract_tool_calls(result)[0],
            "explanation": self.extract_explanation(result)
        }
```

### Week 4: Integration & Testing

#### 4.1 Orchestrated Pipeline
```python
# File: pipeline/orchestration/orchestrated_pipeline.py

class OrchestratedPipeline:
    """
    Pipeline that uses arbiter and specialists.
    """
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.arbiter = ArbiterModel()
        self.specialists = {
            "coding": CodingSpecialist(),
            "reasoning": ReasoningSpecialist(),
            "analysis": AnalysisSpecialist(),
            "functiongemma": FunctionGemmaMediator()
        }
        self.state_manager = StateManager(project_dir)
    
    def run(self):
        """
        Main execution loop - arbiter-driven.
        """
        state = self.state_manager.load()
        
        while not state.is_complete:
            # Arbiter decides what to do
            decision = self.arbiter.decide_action(state, self.get_context())
            
            if decision["action"] == "consult_specialist":
                # Consult specialist
                specialist = decision["specialist"]
                result = self.specialists[specialist].execute(
                    decision["query"],
                    decision["context"]
                )
                
                # Process result
                self.process_specialist_result(result, state)
            
            elif decision["action"] == "change_phase":
                # Change phase
                state.current_phase = decision["phase"]
                self.state_manager.save(state)
            
            elif decision["action"] == "request_user_input":
                # Ask user
                response = self.ask_user(decision["question"])
                self.process_user_response(response, state)
            
            # Update state
            state = self.state_manager.load()
```

## Phase 3: Advanced Features (Weeks 5-6)

### Week 5: Model-to-Model Conversations

#### 5.1 Direct Model Dialogue
```python
# File: pipeline/orchestration/model_dialogue.py

class ModelDialogue:
    """
    Enables direct conversation between models.
    """
    def __init__(self, arbiter: ArbiterModel):
        self.arbiter = arbiter
        self.conversation_manager = MultiModelConversationManager()
    
    def start_dialogue(self, model_a: str, model_b: str, 
                      initial_query: str, max_turns: int = 5) -> dict:
        """
        Start a dialogue between two models.
        Arbiter monitors and can intervene.
        """
        # Create threads
        thread_a = self.conversation_manager.create_thread(model_a, "participant_a")
        thread_b = self.conversation_manager.create_thread(model_b, "participant_b")
        
        # Initial message to model_a
        thread_a.add_message("user", initial_query)
        
        for turn in range(max_turns):
            # Model A responds
            response_a = self.get_model_response(model_a, thread_a)
            
            # Arbiter reviews
            arbiter_decision = self.arbiter.review_dialogue_turn(
                from_model=model_a,
                to_model=model_b,
                message=response_a,
                turn=turn
            )
            
            if arbiter_decision["should_intervene"]:
                # Arbiter modifies or redirects
                response_a = arbiter_decision["modified_message"]
            
            if arbiter_decision["should_stop"]:
                # Dialogue complete
                break
            
            # Send to model B
            thread_b.add_message("user", response_a, from_model=model_a)
            
            # Model B responds
            response_b = self.get_model_response(model_b, thread_b)
            
            # Send back to model A
            thread_a.add_message("user", response_b, from_model=model_b)
        
        return {
            "dialogue": self.conversation_manager.get_full_dialogue(),
            "outcome": arbiter_decision.get("outcome"),
            "turns": turn + 1
        }
```

### Week 6: Self-Healing & Adaptation

#### 6.1 Model-Driven Failure Recovery
```python
# File: pipeline/orchestration/self_healing.py

class SelfHealingSystem:
    """
    Uses models to diagnose and recover from failures.
    """
    def __init__(self, arbiter: ArbiterModel, reasoning_specialist: ReasoningSpecialist):
        self.arbiter = arbiter
        self.reasoning = reasoning_specialist
    
    def handle_failure(self, failure: dict, state: PipelineState) -> dict:
        """
        Let models diagnose and fix failures.
        """
        # Step 1: Reasoning specialist analyzes
        analysis = self.reasoning.analyze_situation({
            "failure": failure,
            "state": state.to_dict(),
            "recent_history": state.get_recent_history(10)
        })
        
        # Step 2: Arbiter decides on action
        decision = self.arbiter.decide_recovery_action(analysis)
        
        # Step 3: Execute recovery
        if decision["action"] == "retry_with_changes":
            return self.retry_with_changes(decision["changes"], state)
        
        elif decision["action"] == "consult_specialist":
            return self.consult_for_solution(decision["specialist"], failure)
        
        elif decision["action"] == "request_user_help":
            return self.request_user_help(decision["question"])
        
        elif decision["action"] == "rollback":
            return self.rollback_to_safe_state(decision["checkpoint"])
```

## Testing & Validation

### Integration Tests
```python
# File: tests/test_orchestration.py

def test_arbiter_routing():
    """Test arbiter routes to correct specialist."""
    arbiter = ArbiterModel()
    
    # Complex coding task should route to coding specialist
    decision = arbiter.decide_action(state, {"task_type": "complex_implementation"})
    assert decision["specialist"] == "coding"
    
    # Strategic decision should route to reasoning specialist
    decision = arbiter.decide_action(state, {"task_type": "strategy"})
    assert decision["specialist"] == "reasoning"

def test_model_dialogue():
    """Test models can communicate."""
    dialogue = ModelDialogue(arbiter)
    
    result = dialogue.start_dialogue(
        model_a="qwen2.5-coder:32b",
        model_b="qwen2.5:32b",
        initial_query="How should we implement this feature?"
    )
    
    assert result["turns"] > 0
    assert result["outcome"] is not None

def test_dynamic_prompts():
    """Test prompts adapt to context."""
    builder = DynamicPromptBuilder(project_dir)
    
    # With failures
    prompt_with_failures = builder.build_prompt("qa", task, {
        "recent_failures": ["empty_tool_name"]
    })
    assert "MUST have a name field" in prompt_with_failures
    
    # Without failures
    prompt_no_failures = builder.build_prompt("qa", task, {
        "recent_failures": []
    })
    assert "MUST have a name field" not in prompt_no_failures
```

## Migration Strategy

### Phase 1: Parallel Operation (Week 7)
- Run new orchestration system alongside existing pipeline
- Compare results
- Identify issues

### Phase 2: Gradual Migration (Week 8)
- Migrate one phase at a time
- Start with QA (most problematic)
- Then coding, debugging, etc.

### Phase 3: Full Deployment (Week 9)
- Switch to orchestration by default
- Keep old system as fallback
- Monitor performance

### Phase 4: Optimization (Week 10)
- Tune arbiter decision-making
- Optimize specialist selection
- Refine dynamic prompts
- Improve failure recovery

## Success Metrics

1. **Tool Call Success Rate**: 90%+ (vs current ~60%)
2. **Failure Recovery Time**: < 2 iterations (vs current 20+)
3. **Model Utilization**: 80%+ optimal model selection
4. **Context Efficiency**: 50%+ reduction in prompt tokens
5. **Self-Healing**: 70%+ of failures resolved without user input

## Conclusion

This roadmap transforms the pipeline from a rigid, application-driven system to a flexible, model-driven orchestration platform where:

- **Models make decisions**, application provides capabilities
- **Specialists handle their domains**, arbiter coordinates
- **Prompts adapt to context**, not static templates
- **Failures trigger model-driven recovery**, not hardcoded logic
- **FunctionGemma clarifies ambiguity**, improving reliability

The result is a more intelligent, adaptive, and resilient system that leverages the full capabilities of your multi-server, multi-model infrastructure.