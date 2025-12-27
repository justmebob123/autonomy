# Multi-Model Orchestration Architecture Design

## Executive Summary

This document proposes a revolutionary architecture where:
1. Models can call other models as tools
2. An arbiter model orchestrates multi-model conversations
3. The application becomes a scaffold for tool calls
4. Models drive decision-making, the app provides capabilities
5. FunctionGemma acts as a tool-calling interpreter/clarifier

## Current State Analysis

### Server Configuration
- **ollama01**: 11GB VRAM - Fast, smaller models (qwen2.5:14b, functiongemma)
- **ollama02**: More VRAM - Larger models (qwen2.5:32b, qwen2.5-coder:32b)

### Current Limitations
1. **Single Model Per Phase**: Each phase uses one model
2. **No Model-to-Model Communication**: Models can't directly interact
3. **Static Prompts**: Prompts are hardcoded, not context-aware
4. **Application-Driven**: App makes decisions, models just respond
5. **Linear Conversations**: No parallel or branching model interactions

## Proposed Architecture: Multi-Model Orchestration System (MMOS)

### Core Concept: Models as Tools

```python
# Model A can call Model B as a tool
{
    "name": "consult_specialist",
    "description": "Consult a specialist model for specific tasks",
    "parameters": {
        "specialist": "coding|reasoning|analysis|debugging",
        "query": "The question or task for the specialist",
        "context": "Relevant context for the specialist"
    }
}

# Model B responds, Model A receives the response as tool result
{
    "tool": "consult_specialist",
    "success": true,
    "response": "The specialist's answer...",
    "reasoning": "Why this answer..."
}
```

### Architecture Layers

#### Layer 1: Arbiter (Orchestrator Model)
**Role**: High-level decision making and coordination
**Model**: qwen2.5:14b on ollama01 (fast decisions)
**Responsibilities**:
- Decide which models to involve
- Route queries to appropriate specialists
- Synthesize multi-model responses
- Detect when to escalate to larger models
- Monitor conversation health

**Tools Available to Arbiter**:
```python
arbiter_tools = [
    "consult_coding_specialist",      # 32b coder on ollama02
    "consult_reasoning_specialist",   # 32b reasoning on ollama02
    "consult_analysis_specialist",    # 14b fast analysis on ollama01
    "start_multi_model_conversation", # Initiate model-to-model dialogue
    "synthesize_responses",           # Combine multiple model outputs
    "escalate_to_user",              # Ask user for guidance
    "reinterpret_with_functiongemma", # Clarify tool calls
]
```

#### Layer 2: Specialist Models
**Coding Specialist**: qwen2.5-coder:32b on ollama02
- Deep code analysis
- Complex implementations
- Architecture decisions

**Reasoning Specialist**: qwen2.5:32b on ollama02
- Complex problem solving
- Multi-step reasoning
- Strategic planning

**Fast Analysis**: qwen2.5:14b on ollama01
- Quick checks
- Simple validations
- Rapid iterations

**FunctionGemma**: functiongemma on ollama01
- Tool call interpretation
- Response clarification
- Format conversion

#### Layer 3: Application Scaffold
**Role**: Provide capabilities, not decisions
**Responsibilities**:
- Execute tool calls
- Manage conversation threads
- Track model interactions
- Provide system information
- Handle failures gracefully

### Multi-Model Conversation Protocol

#### Approach 1: Direct Model-to-Model (Recommended)

```python
class ModelConversation:
    """
    Manages a conversation between multiple models.
    Each model maintains its own thread, but can see others' responses.
    """
    
    def __init__(self, arbiter_model, participant_models):
        self.arbiter = arbiter_model
        self.participants = participant_models
        self.threads = {model: [] for model in participant_models}
        self.shared_context = []
    
    def route_message(self, from_model, to_model, message, include_history=False):
        """
        Route a message from one model to another.
        Arbiter can modify/filter the message.
        """
        # Arbiter reviews the message
        arbiter_decision = self.arbiter.review_message(message)
        
        if arbiter_decision.should_modify:
            message = arbiter_decision.modified_message
        
        if arbiter_decision.should_redirect:
            to_model = arbiter_decision.redirect_to
        
        # Add to recipient's thread
        if include_history:
            # Include full conversation history
            self.threads[to_model].extend(self.shared_context)
        
        self.threads[to_model].append({
            "role": "user",  # Or custom role like "model_specialist"
            "content": message,
            "from": from_model
        })
        
        return to_model
    
    def get_response(self, model, tools=None):
        """Get response from a model with its conversation thread"""
        response = self.call_model(model, self.threads[model], tools)
        
        # Add to shared context
        self.shared_context.append({
            "model": model,
            "response": response
        })
        
        return response
```

#### Approach 2: Arbiter-Mediated (For Complex Scenarios)

```python
class ArbitratedConversation:
    """
    All model interactions go through the arbiter.
    Arbiter decides what each model sees.
    """
    
    def __init__(self, arbiter_model):
        self.arbiter = arbiter_model
        self.model_contexts = {}
        self.full_history = []
    
    def consult_model(self, model, query, context_filter=None):
        """
        Arbiter consults a model with filtered context.
        """
        # Arbiter decides what context to provide
        filtered_context = self.arbiter.filter_context(
            self.full_history, 
            model, 
            query,
            context_filter
        )
        
        # Build model-specific prompt
        messages = [
            {"role": "system", "content": self.get_specialist_prompt(model)},
            *filtered_context,
            {"role": "user", "content": query}
        ]
        
        response = self.call_model(model, messages)
        
        # Arbiter reviews response before returning
        reviewed = self.arbiter.review_response(model, response)
        
        return reviewed
```

### Dynamic Prompt Construction

#### Context-Aware Prompt Builder

```python
class DynamicPromptBuilder:
    """
    Constructs prompts based on:
    - Current phase
    - Task complexity
    - Available context
    - Model capabilities
    - Recent failures
    - User preferences
    """
    
    def build_prompt(self, phase, task, context):
        prompt_parts = []
        
        # 1. Role definition (based on phase and model)
        prompt_parts.append(self.get_role_definition(phase, context.model))
        
        # 2. Task-specific instructions
        if context.is_complex:
            prompt_parts.append(self.get_detailed_instructions(task))
        else:
            prompt_parts.append(self.get_simple_instructions(task))
        
        # 3. Available tools (filtered by relevance)
        relevant_tools = self.filter_tools_by_task(task, context.all_tools)
        prompt_parts.append(self.format_tool_descriptions(relevant_tools))
        
        # 4. Examples (if model has failed recently)
        if context.recent_failures:
            prompt_parts.append(self.get_examples_for_failures(context.recent_failures))
        
        # 5. Context chunking strategy
        if context.is_large:
            # Split into multiple prompts
            return self.chunk_prompt(prompt_parts, context.model_limits)
        
        return "\n\n".join(prompt_parts)
    
    def chunk_prompt(self, parts, model_limits):
        """
        Split large prompts into multiple conversation turns.
        Each chunk builds on the previous.
        """
        chunks = []
        current_chunk = []
        current_size = 0
        
        for part in parts:
            part_size = self.estimate_tokens(part)
            
            if current_size + part_size > model_limits.max_prompt_tokens:
                chunks.append(current_chunk)
                current_chunk = [part]
                current_size = part_size
            else:
                current_chunk.append(part)
                current_size += part_size
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
```

#### Prompt Templates with Placeholders

```python
class PromptTemplate:
    """
    Templates with dynamic sections based on context.
    """
    
    CODING_TEMPLATE = """
    You are a {expertise_level} Python developer.
    
    {complexity_instructions}
    
    TASK: {task_description}
    
    {context_section}
    
    {tools_section}
    
    {examples_section}
    
    {constraints_section}
    """
    
    def render(self, **kwargs):
        # Only include sections that have content
        template = self.CODING_TEMPLATE
        
        for key, value in kwargs.items():
            if value:
                template = template.replace(f"{{{key}}}", value)
            else:
                # Remove empty sections
                template = template.replace(f"{{{key}}}", "")
        
        return template.strip()
```

### FunctionGemma Integration

#### Role 1: Tool Call Interpreter

```python
class FunctionGemmaInterpreter:
    """
    Uses FunctionGemma to clarify ambiguous tool calls.
    """
    
    def interpret_tool_call(self, raw_response, available_tools):
        """
        When a model's response is unclear, use FunctionGemma to interpret.
        """
        prompt = f"""
        A model generated this response:
        {raw_response}
        
        Available tools:
        {json.dumps(available_tools, indent=2)}
        
        Extract the tool call(s) from this response.
        """
        
        result = self.call_functiongemma(prompt, available_tools)
        return result.tool_calls
    
    def clarify_failed_call(self, failed_call, error, available_tools):
        """
        When a tool call fails, ask FunctionGemma to fix it.
        """
        prompt = f"""
        This tool call failed:
        {json.dumps(failed_call, indent=2)}
        
        Error: {error}
        
        Available tools:
        {json.dumps(available_tools, indent=2)}
        
        Correct the tool call to match the available tools.
        """
        
        result = self.call_functiongemma(prompt, available_tools)
        return result.corrected_call
```

#### Role 2: Response Mediator

```python
class ResponseMediator:
    """
    Uses FunctionGemma to mediate between models.
    """
    
    def translate_response(self, from_model_response, to_model_context):
        """
        Translate one model's response for another model's understanding.
        """
        prompt = f"""
        Model A said:
        {from_model_response}
        
        Model B needs to understand this in the context of:
        {to_model_context}
        
        Reformat Model A's response as tool calls that Model B can process.
        """
        
        return self.call_functiongemma(prompt)
```

### Failure Handling with Model Assistance

```python
class ModelAssistedFailureHandler:
    """
    When the application doesn't know what to do, ask a model.
    """
    
    def diagnose_failure(self, failure_context):
        """
        Use reasoning model to diagnose why something failed.
        """
        prompt = f"""
        The application encountered this failure:
        
        Phase: {failure_context.phase}
        Error: {failure_context.error}
        Recent actions: {failure_context.recent_actions}
        System state: {failure_context.state}
        
        Analyze:
        1. What likely caused this failure?
        2. What should be tried next?
        3. Should we change phases?
        4. Do we need user input?
        
        Provide your analysis as tool calls.
        """
        
        tools = [
            "suggest_retry_with_changes",
            "suggest_phase_change",
            "request_user_input",
            "suggest_rollback",
            "suggest_alternative_approach"
        ]
        
        response = self.reasoning_model.analyze(prompt, tools)
        return response.tool_calls
    
    def reinterpret_response(self, original_response, failure_reason):
        """
        Ask a model to reinterpret another model's response.
        """
        prompt = f"""
        Model A generated this response:
        {original_response}
        
        But it failed because:
        {failure_reason}
        
        Reinterpret what Model A was trying to do and suggest the correct tool calls.
        """
        
        return self.reasoning_model.reinterpret(prompt)
```

### Implementation Roadmap

#### Phase 1: Foundation (Week 1)
- [ ] Implement model-as-tool infrastructure
- [ ] Create conversation thread management
- [ ] Build dynamic prompt builder
- [ ] Add arbiter model integration

#### Phase 2: Multi-Model Communication (Week 2)
- [ ] Implement direct model-to-model routing
- [ ] Add arbiter-mediated conversations
- [ ] Create response filtering/modification
- [ ] Build context management for multiple threads

#### Phase 3: FunctionGemma Integration (Week 3)
- [ ] Tool call interpretation
- [ ] Response mediation
- [ ] Failure clarification
- [ ] Format conversion

#### Phase 4: Model-Driven Decision Making (Week 4)
- [ ] Phase selection by models
- [ ] Failure diagnosis by models
- [ ] Dynamic strategy adjustment
- [ ] Self-healing workflows

### Configuration Example

```yaml
orchestration:
  arbiter:
    model: qwen2.5:14b
    server: ollama01
    role: coordinator
    
  specialists:
    coding:
      model: qwen2.5-coder:32b
      server: ollama02
      context_window: 16384
      
    reasoning:
      model: qwen2.5:32b
      server: ollama02
      context_window: 16384
      
    analysis:
      model: qwen2.5:14b
      server: ollama01
      context_window: 8192
      
    interpreter:
      model: functiongemma
      server: ollama01
      context_window: 8192
  
  routing:
    # When to use which model
    rules:
      - condition: "task.complexity > 7"
        specialist: reasoning
        
      - condition: "task.type == 'code_generation'"
        specialist: coding
        
      - condition: "task.requires_speed"
        specialist: analysis
        
      - condition: "response.unclear_tool_calls"
        specialist: interpreter
  
  conversation:
    max_models_per_conversation: 3
    include_full_history: false  # Arbiter filters context
    allow_model_to_model: true
    arbiter_reviews_all: true
```

### Benefits of This Architecture

1. **Optimal Resource Usage**
   - Fast models (ollama01) for quick decisions
   - Powerful models (ollama02) for complex reasoning
   - Multiple models can work in parallel

2. **Better Decision Making**
   - Models drive strategy, not hardcoded logic
   - Specialists handle their domains
   - Arbiter coordinates overall flow

3. **Improved Reliability**
   - Models can diagnose failures
   - FunctionGemma clarifies ambiguity
   - Self-healing through model consultation

4. **Scalability**
   - Easy to add new specialist models
   - Conversation threads are independent
   - Context chunking handles large tasks

5. **Flexibility**
   - Dynamic prompts adapt to context
   - Models can change strategies mid-task
   - Application becomes a capability provider

### Next Steps

1. **Prototype the arbiter system**
2. **Implement model-as-tool calling**
3. **Build conversation thread manager**
4. **Create dynamic prompt builder**
5. **Integrate FunctionGemma as mediator**
6. **Test with real workflows**

This architecture transforms the application from a decision-maker to a scaffold that enables models to collaborate, reason, and self-correct.