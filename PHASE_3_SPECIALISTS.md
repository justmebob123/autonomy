# Phase 3: Specialist Roles & Dynamic Systems

**Timeline:** 2-3 weeks  
**Priority:** HIGH  
**Dependencies:** Phase 1 (Foundation), Phase 2 (Architecture)  
**Deliverables:** Dynamic role creation, prompt optimization, enhanced FunctionGemma integration

---

## Overview

Phase 3 introduces dynamic systems for creating specialized roles and optimizing prompts on-demand. This enables the system to adapt to novel problems by creating custom specialists and optimizing their prompts for maximum effectiveness.

---

## Objectives

1. **Implement Prompt Specialist**: Agent that designs and optimizes prompts
2. **Implement Role Specialist**: Agent that creates custom roles dynamically
3. **Create Role Template Library**: Reusable role templates
4. **Build Prompt Optimization Engine**: Automated prompt improvement
5. **Enhance FunctionGemma Integration**: Use for all tool calling assistance
6. **Create Specialist Coordination**: Enable specialists to work together

---

## Component 1: Prompt Specialist Agent

### Purpose
Design, optimize, and validate prompts for specific tasks and roles. Ensures all agents have effective, well-crafted prompts.

### Responsibilities

1. **Prompt Design**
   - Create prompts for new roles
   - Design task-specific prompts
   - Incorporate best practices
   - Include clear instructions

2. **Prompt Optimization**
   - Analyze prompt effectiveness
   - Identify improvement opportunities
   - Test variations
   - Measure performance

3. **Prompt Validation**
   - Ensure clarity and completeness
   - Check for ambiguity
   - Validate tool usage instructions
   - Test with target models

4. **Prompt Library Management**
   - Maintain prompt templates
   - Version control
   - Document best practices
   - Share successful patterns

### Implementation Details

#### File: `pipeline/agents/prompt_specialist.py`

```python
class PromptSpecialist:
    """
    Specialist agent for prompt design and optimization.
    
    Responsibilities:
    - Design prompts for new roles
    - Optimize existing prompts
    - Validate prompt effectiveness
    - Maintain prompt library
    """
    
    def __init__(self, client, config: PipelineConfig, logger):
        self.client = client
        self.config = config
        self.logger = logger
        
        # Prompt library
        self.prompt_library = PromptLibrary()
        
        # Optimization engine
        self.optimizer = PromptOptimizer()
        
        # Validation engine
        self.validator = PromptValidator()
        
        # Performance tracker
        self.performance_tracker = PromptPerformanceTracker()
        
    def design_prompt(self, role_spec: Dict) -> Dict:
        """
        Design a prompt for a new role.
        
        Args:
            role_spec: {
                'role_name': 'CustomDebugger',
                'purpose': 'Debug specific type of error',
                'responsibilities': [...],
                'tools': [...],
                'context': {...},
                'examples': [...]
            }
            
        Returns:
            {
                'prompt': '...',
                'system_prompt': '...',
                'user_prompt_template': '...',
                'tool_instructions': '...',
                'examples': [...],
                'metadata': {...}
            }
        """
        
        # Analyze role requirements
        requirements = self._analyze_requirements(role_spec)
        
        # Generate base prompt
        base_prompt = self._generate_base_prompt(role_spec, requirements)
        
        # Add tool instructions
        tool_instructions = self._generate_tool_instructions(role_spec['tools'])
        
        # Add examples
        examples = self._generate_examples(role_spec)
        
        # Combine into complete prompt
        complete_prompt = self._combine_prompt_components(
            base_prompt, tool_instructions, examples
        )
        
        # Validate prompt
        validation = self.validator.validate(complete_prompt, role_spec)
        
        if not validation['valid']:
            # Refine based on validation feedback
            complete_prompt = self._refine_prompt(complete_prompt, validation)
            
        return {
            'prompt': complete_prompt,
            'system_prompt': base_prompt,
            'user_prompt_template': self._create_user_template(role_spec),
            'tool_instructions': tool_instructions,
            'examples': examples,
            'metadata': {
                'role_name': role_spec['role_name'],
                'created': datetime.now().isoformat(),
                'validation': validation
            }
        }
        
    def optimize_prompt(self, prompt: str, performance_data: Dict) -> Dict:
        """
        Optimize an existing prompt based on performance data.
        
        Args:
            prompt: Current prompt text
            performance_data: {
                'success_rate': 0.75,
                'avg_response_time': 5.2,
                'tool_call_accuracy': 0.82,
                'common_failures': [...],
                'user_feedback': [...]
            }
            
        Returns:
            {
                'optimized_prompt': '...',
                'changes': [...],
                'expected_improvement': 0.15,
                'rationale': '...'
            }
        """
        
        # Analyze current performance
        analysis = self.optimizer.analyze_performance(prompt, performance_data)
        
        # Identify improvement opportunities
        opportunities = self.optimizer.identify_opportunities(analysis)
        
        # Generate optimized version
        optimized = self.optimizer.optimize(prompt, opportunities)
        
        # Validate improvements
        validation = self.validator.validate_improvements(
            prompt, optimized, performance_data
        )
        
        return {
            'optimized_prompt': optimized,
            'changes': self._document_changes(prompt, optimized),
            'expected_improvement': validation['expected_improvement'],
            'rationale': validation['rationale']
        }
        
    def _generate_base_prompt(self, role_spec: Dict, requirements: Dict) -> str:
        """
        Generate base system prompt for a role.
        
        Template structure:
        1. Role identity and purpose
        2. Core responsibilities
        3. Available tools and when to use them
        4. Decision-making guidelines
        5. Output format requirements
        6. Critical instructions
        """
        
        prompt_parts = []
        
        # 1. Identity and purpose
        prompt_parts.append(f"You are {role_spec['role_name']} - {role_spec['purpose']}.")
        prompt_parts.append("")
        
        # 2. Responsibilities
        prompt_parts.append("Your responsibilities:")
        for i, resp in enumerate(role_spec['responsibilities'], 1):
            prompt_parts.append(f"{i}. {resp}")
        prompt_parts.append("")
        
        # 3. Tools
        if role_spec.get('tools'):
            prompt_parts.append("Available tools:")
            for tool in role_spec['tools']:
                prompt_parts.append(f"- {tool['name']}: {tool['description']}")
            prompt_parts.append("")
            
        # 4. Guidelines
        if requirements.get('guidelines'):
            prompt_parts.append("Guidelines:")
            for guideline in requirements['guidelines']:
                prompt_parts.append(f"- {guideline}")
            prompt_parts.append("")
            
        # 5. Output format
        if requirements.get('output_format'):
            prompt_parts.append(f"Output format: {requirements['output_format']}")
            prompt_parts.append("")
            
        # 6. Critical instructions
        if requirements.get('critical_instructions'):
            prompt_parts.append("CRITICAL INSTRUCTIONS:")
            for instruction in requirements['critical_instructions']:
                prompt_parts.append(f"⚠️ {instruction}")
                
        return "\n".join(prompt_parts)
        
    def _generate_tool_instructions(self, tools: List[Dict]) -> str:
        """
        Generate detailed tool usage instructions.
        
        For each tool:
        - When to use it
        - How to use it
        - What to expect
        - Common pitfalls
        """
        
        instructions = ["TOOL USAGE INSTRUCTIONS:", ""]
        
        for tool in tools:
            instructions.append(f"## {tool['name']}")
            instructions.append(f"Purpose: {tool['description']}")
            instructions.append("")
            
            if tool.get('when_to_use'):
                instructions.append(f"When to use: {tool['when_to_use']}")
                
            if tool.get('parameters'):
                instructions.append("Parameters:")
                for param in tool['parameters']:
                    required = "REQUIRED" if param.get('required') else "optional"
                    instructions.append(f"  - {param['name']} ({required}): {param['description']}")
                    
            if tool.get('example'):
                instructions.append(f"Example: {tool['example']}")
                
            if tool.get('pitfalls'):
                instructions.append("Common pitfalls:")
                for pitfall in tool['pitfalls']:
                    instructions.append(f"  ⚠️ {pitfall}")
                    
            instructions.append("")
            
        return "\n".join(instructions)
        
    def _generate_examples(self, role_spec: Dict) -> List[Dict]:
        """
        Generate example interactions for the role.
        
        Examples show:
        - Typical inputs
        - Expected reasoning
        - Tool usage
        - Output format
        """
        
        examples = []
        
        if role_spec.get('examples'):
            for ex in role_spec['examples']:
                examples.append({
                    'input': ex['input'],
                    'reasoning': ex.get('reasoning', ''),
                    'tool_calls': ex.get('tool_calls', []),
                    'output': ex['output']
                })
                
        # Generate synthetic examples if needed
        if len(examples) < 3:
            synthetic = self._generate_synthetic_examples(role_spec)
            examples.extend(synthetic)
            
        return examples


class PromptOptimizer:
    """Optimizes prompts based on performance data."""
    
    def analyze_performance(self, prompt: str, data: Dict) -> Dict:
        """Analyze prompt performance."""
        
        analysis = {
            'strengths': [],
            'weaknesses': [],
            'metrics': data
        }
        
        # Analyze success rate
        if data['success_rate'] < 0.8:
            analysis['weaknesses'].append('Low success rate')
            
        # Analyze tool call accuracy
        if data['tool_call_accuracy'] < 0.9:
            analysis['weaknesses'].append('Poor tool call accuracy')
            
        # Analyze common failures
        if data.get('common_failures'):
            failure_patterns = self._analyze_failure_patterns(data['common_failures'])
            analysis['failure_patterns'] = failure_patterns
            
        return analysis
        
    def identify_opportunities(self, analysis: Dict) -> List[Dict]:
        """Identify optimization opportunities."""
        
        opportunities = []
        
        for weakness in analysis['weaknesses']:
            if 'success rate' in weakness.lower():
                opportunities.append({
                    'type': 'clarity',
                    'description': 'Improve instruction clarity',
                    'priority': 'high'
                })
                
            if 'tool call' in weakness.lower():
                opportunities.append({
                    'type': 'tool_instructions',
                    'description': 'Enhance tool usage instructions',
                    'priority': 'high'
                })
                
        return opportunities
        
    def optimize(self, prompt: str, opportunities: List[Dict]) -> str:
        """Apply optimizations to prompt."""
        
        optimized = prompt
        
        for opp in opportunities:
            if opp['type'] == 'clarity':
                optimized = self._improve_clarity(optimized)
            elif opp['type'] == 'tool_instructions':
                optimized = self._enhance_tool_instructions(optimized)
            elif opp['type'] == 'examples':
                optimized = self._add_examples(optimized)
                
        return optimized


class PromptValidator:
    """Validates prompt quality and effectiveness."""
    
    def validate(self, prompt: str, role_spec: Dict) -> Dict:
        """
        Validate a prompt.
        
        Checks:
        - Clarity and completeness
        - Tool instructions present
        - Examples included
        - No ambiguity
        - Appropriate length
        """
        
        validation = {
            'valid': True,
            'issues': [],
            'warnings': [],
            'score': 0.0
        }
        
        # Check clarity
        clarity_score = self._check_clarity(prompt)
        if clarity_score < 0.7:
            validation['issues'].append('Prompt lacks clarity')
            validation['valid'] = False
            
        # Check completeness
        completeness_score = self._check_completeness(prompt, role_spec)
        if completeness_score < 0.8:
            validation['issues'].append('Prompt incomplete')
            validation['valid'] = False
            
        # Check tool instructions
        if role_spec.get('tools') and 'tool' not in prompt.lower():
            validation['warnings'].append('Tool instructions may be missing')
            
        # Calculate overall score
        validation['score'] = (clarity_score + completeness_score) / 2
        
        return validation
```

#### Prompt Specialist System Prompt

```python
PROMPT_SPECIALIST_PROMPT = """You are the Prompt Specialist - an expert in designing and optimizing prompts for AI agents.

Your expertise:
1. Prompt engineering best practices
2. Clear instruction writing
3. Tool usage documentation
4. Example creation
5. Performance optimization

When designing a prompt:
1. Start with clear role identity and purpose
2. List specific, actionable responsibilities
3. Provide detailed tool instructions with examples
4. Include decision-making guidelines
5. Add concrete examples of expected behavior
6. Highlight critical instructions
7. Ensure clarity and completeness

Prompt structure template:
```
You are [ROLE] - [PURPOSE].

Your responsibilities:
1. [Responsibility 1]
2. [Responsibility 2]
...

Available tools:
- [tool_name]: [description]
  When to use: [when]
  Example: [example]

Guidelines:
- [Guideline 1]
- [Guideline 2]

CRITICAL INSTRUCTIONS:
⚠️ [Critical instruction 1]
⚠️ [Critical instruction 2]

Examples:
[Example 1]
[Example 2]
```

When optimizing a prompt:
1. Analyze performance data
2. Identify weaknesses
3. Improve clarity
4. Enhance tool instructions
5. Add missing examples
6. Test improvements

Always ensure prompts are:
- Clear and unambiguous
- Complete and comprehensive
- Actionable and specific
- Well-structured and organized
- Tested and validated
"""
```

---

## Component 2: Role Specialist Agent

### Purpose
Create custom specialized roles dynamically based on problem requirements. Enables system to adapt to novel situations.

### Responsibilities

1. **Role Analysis**
   - Analyze problem requirements
   - Identify needed expertise
   - Determine role specifications
   - Define responsibilities

2. **Role Design**
   - Create role specifications
   - Define capabilities
   - Specify tools needed
   - Design interactions

3. **Role Creation**
   - Work with Prompt Specialist
   - Create role implementation
   - Configure agent
   - Test role

4. **Role Management**
   - Maintain role library
   - Version control
   - Update roles
   - Retire obsolete roles

### Implementation Details

#### File: `pipeline/agents/role_specialist.py`

```python
class RoleSpecialist:
    """
    Specialist agent for creating custom roles dynamically.
    
    Responsibilities:
    - Analyze problem requirements
    - Design custom roles
    - Create role implementations
    - Manage role library
    """
    
    def __init__(self, client, config: PipelineConfig, logger):
        self.client = client
        self.config = config
        self.logger = logger
        
        # Role library
        self.role_library = RoleLibrary()
        
        # Prompt specialist for prompt creation
        self.prompt_specialist = PromptSpecialist(client, config, logger)
        
        # Role templates
        self.templates = RoleTemplateLibrary()
        
    def analyze_requirements(self, problem: Dict) -> Dict:
        """
        Analyze problem to determine role requirements.
        
        Args:
            problem: {
                'description': '...',
                'error': {...},
                'context': {...},
                'attempted_solutions': [...],
                'constraints': [...]
            }
            
        Returns:
            {
                'needed_expertise': ['loop_detection', 'verification_logic'],
                'required_tools': ['loop_detector', 'code_analyzer'],
                'role_type': 'debugger|analyzer|coordinator',
                'complexity': 'simple|moderate|complex',
                'similar_roles': [...]
            }
        """
        
        requirements = {
            'needed_expertise': [],
            'required_tools': [],
            'role_type': 'specialist',
            'complexity': 'moderate'
        }
        
        # Analyze problem type
        if 'loop' in problem['description'].lower():
            requirements['needed_expertise'].append('loop_detection')
            requirements['required_tools'].append('loop_detector')
            
        if 'verification' in problem['description'].lower():
            requirements['needed_expertise'].append('verification_logic')
            requirements['required_tools'].append('code_analyzer')
            
        # Determine role type
        if problem.get('error'):
            requirements['role_type'] = 'debugger'
        elif 'analyze' in problem['description'].lower():
            requirements['role_type'] = 'analyzer'
        else:
            requirements['role_type'] = 'specialist'
            
        # Check for similar existing roles
        similar = self.role_library.find_similar_roles(requirements)
        requirements['similar_roles'] = similar
        
        return requirements
        
    def design_role(self, requirements: Dict, problem: Dict) -> Dict:
        """
        Design a custom role based on requirements.
        
        Returns:
            {
                'role_name': 'LoopDetectionDebugger',
                'purpose': 'Debug issues related to infinite loops',
                'responsibilities': [...],
                'tools': [...],
                'model': 'qwen2.5-coder:32b',
                'temperature': 0.2,
                'prompt_spec': {...}
            }
        """
        
        # Check if we can reuse existing role
        if requirements.get('similar_roles'):
            similar = requirements['similar_roles'][0]
            if similar['similarity'] > 0.9:
                self.logger.info(f"Reusing existing role: {similar['name']}")
                return self.role_library.get_role(similar['name'])
                
        # Create new role
        role_spec = {
            'role_name': self._generate_role_name(requirements),
            'purpose': self._generate_purpose(requirements, problem),
            'responsibilities': self._generate_responsibilities(requirements),
            'tools': self._select_tools(requirements),
            'model': self._select_model(requirements),
            'temperature': self._select_temperature(requirements),
            'examples': self._generate_examples(requirements, problem)
        }
        
        return role_spec
        
    def create_role(self, role_spec: Dict) -> 'CustomAgent':
        """
        Create and instantiate a custom role.
        
        Returns:
            CustomAgent instance ready to use
        """
        
        # Generate prompt using Prompt Specialist
        prompt_data = self.prompt_specialist.design_prompt(role_spec)
        
        # Create agent configuration
        agent_config = {
            'name': role_spec['role_name'],
            'model': role_spec['model'],
            'temperature': role_spec['temperature'],
            'system_prompt': prompt_data['prompt'],
            'tools': role_spec['tools']
        }
        
        # Instantiate agent
        agent = CustomAgent(
            self.client,
            agent_config,
            self.logger
        )
        
        # Register in role library
        self.role_library.register_role(role_spec, agent)
        
        return agent
        
    def _generate_role_name(self, requirements: Dict) -> str:
        """Generate descriptive role name."""
        
        expertise = requirements['needed_expertise']
        role_type = requirements['role_type']
        
        if len(expertise) == 1:
            return f"{expertise[0].title()}{role_type.title()}"
        else:
            return f"Multi{role_type.title()}"
            
    def _generate_purpose(self, requirements: Dict, problem: Dict) -> str:
        """Generate role purpose statement."""
        
        expertise = requirements['needed_expertise']
        
        if len(expertise) == 1:
            return f"Specialized in {expertise[0]} for {problem['description']}"
        else:
            return f"Multi-specialist for complex problems involving {', '.join(expertise)}"
            
    def _generate_responsibilities(self, requirements: Dict) -> List[str]:
        """Generate role responsibilities."""
        
        responsibilities = []
        
        for expertise in requirements['needed_expertise']:
            if expertise == 'loop_detection':
                responsibilities.extend([
                    'Detect infinite loops and circular dependencies',
                    'Analyze loop patterns and causes',
                    'Recommend loop-breaking strategies'
                ])
            elif expertise == 'verification_logic':
                responsibilities.extend([
                    'Analyze verification logic',
                    'Identify false positives/negatives',
                    'Recommend verification improvements'
                ])
                
        return responsibilities
        
    def _select_tools(self, requirements: Dict) -> List[Dict]:
        """Select appropriate tools for role."""
        
        tools = []
        
        for tool_name in requirements['required_tools']:
            tool_def = self._get_tool_definition(tool_name)
            if tool_def:
                tools.append(tool_def)
                
        return tools
        
    def _select_model(self, requirements: Dict) -> str:
        """Select appropriate model for role."""
        
        complexity = requirements['complexity']
        role_type = requirements['role_type']
        
        if complexity == 'complex' or role_type == 'debugger':
            return 'qwen2.5-coder:32b'  # Best coding model
        elif role_type == 'analyzer':
            return 'qwen2.5:14b'  # Good reasoning
        else:
            return 'qwen2.5-coder:14b'  # Balanced
            
    def _select_temperature(self, requirements: Dict) -> float:
        """Select appropriate temperature for role."""
        
        role_type = requirements['role_type']
        
        if role_type == 'debugger':
            return 0.2  # Deterministic
        elif role_type == 'analyzer':
            return 0.3  # Slightly creative
        else:
            return 0.5  # Balanced


class CustomAgent:
    """Dynamically created custom agent."""
    
    def __init__(self, client, config: Dict, logger):
        self.client = client
        self.config = config
        self.logger = logger
        self.name = config['name']
        
    def execute(self, task: Dict, context: Dict) -> Dict:
        """Execute task using custom role."""
        
        # Build messages
        messages = [
            {'role': 'system', 'content': self.config['system_prompt']},
            {'role': 'user', 'content': self._format_task(task, context)}
        ]
        
        # Call model
        response = self.client.chat(
            self.config.get('host', 'ollama02.thiscluster.net'),
            self.config['model'],
            messages,
            self.config.get('tools', []),
            temperature=self.config['temperature']
        )
        
        return self._process_response(response)


class RoleLibrary:
    """Library of available roles."""
    
    def __init__(self):
        self.roles: Dict[str, Dict] = {}
        self.role_instances: Dict[str, CustomAgent] = {}
        
    def register_role(self, role_spec: Dict, agent: CustomAgent):
        """Register a new role."""
        
        role_name = role_spec['role_name']
        self.roles[role_name] = role_spec
        self.role_instances[role_name] = agent
        
    def get_role(self, role_name: str) -> Dict:
        """Get role specification."""
        return self.roles.get(role_name)
        
    def get_agent(self, role_name: str) -> CustomAgent:
        """Get role agent instance."""
        return self.role_instances.get(role_name)
        
    def find_similar_roles(self, requirements: Dict) -> List[Dict]:
        """Find similar existing roles."""
        
        similar = []
        
        for role_name, role_spec in self.roles.items():
            similarity = self._calculate_similarity(requirements, role_spec)
            if similarity > 0.7:
                similar.append({
                    'name': role_name,
                    'similarity': similarity,
                    'spec': role_spec
                })
                
        return sorted(similar, key=lambda x: x['similarity'], reverse=True)
```

#### Role Specialist System Prompt

```python
ROLE_SPECIALIST_PROMPT = """You are the Role Specialist - an expert in designing custom specialized roles for AI agents.

Your expertise:
1. Problem analysis and requirement extraction
2. Role design and specification
3. Capability mapping
4. Tool selection
5. Agent configuration

When analyzing a problem:
1. Identify required expertise areas
2. Determine needed tools and capabilities
3. Assess complexity level
4. Check for similar existing roles
5. Decide: reuse, adapt, or create new

When designing a role:
1. Create clear, descriptive role name
2. Define specific purpose
3. List concrete responsibilities
4. Select appropriate tools
5. Choose optimal model and temperature
6. Generate relevant examples

Role design principles:
- Single Responsibility: Each role has one clear purpose
- Tool-Equipped: Provide necessary tools for the job
- Well-Prompted: Clear instructions and examples
- Right-Sized: Not too broad, not too narrow
- Reusable: Design for potential reuse

When creating a role:
1. Work with Prompt Specialist for prompt design
2. Configure agent with appropriate model
3. Test role with sample tasks
4. Register in role library
5. Document usage and examples

Always consider:
- Can we reuse an existing role?
- Is this role too specialized or too general?
- Does it have the right tools?
- Is the model appropriate?
- Are the instructions clear?
"""
```

---

## Component 3: Enhanced FunctionGemma Integration

### Purpose
Use FunctionGemma across all agents for tool calling assistance, validation, and correction.

### Integration Points

1. **Tool Call Generation**
   - Help agents format tool calls correctly
   - Suggest appropriate tools
   - Validate parameters

2. **Tool Call Validation**
   - Check tool call syntax
   - Validate parameters
   - Detect errors

3. **Tool Call Correction**
   - Fix malformed tool calls
   - Correct parameter types
   - Suggest alternatives

### Implementation Details

#### File: `pipeline/agents/tool_advisor.py` (Enhanced)

```python
class EnhancedToolAdvisor:
    """
    Enhanced tool advisor using FunctionGemma.
    
    Provides:
    - Tool call assistance
    - Syntax validation
    - Error correction
    - Tool recommendations
    """
    
    def __init__(self, client, config: PipelineConfig, logger):
        self.client = client
        self.config = config
        self.logger = logger
        
        # FunctionGemma configuration
        self.functiongemma_model = 'functiongemma'
        self.functiongemma_host = 'ollama02.thiscluster.net'
        
    def assist_tool_call(self, agent_response: str, available_tools: List[Dict]) -> Dict:
        """
        Assist agent in making tool calls.
        
        Args:
            agent_response: Agent's response text
            available_tools: List of available tool definitions
            
        Returns:
            {
                'tool_calls': [...],
                'confidence': 0.95,
                'suggestions': [...]
            }
        """
        
        # Use FunctionGemma to extract/format tool calls
        prompt = self._create_assistance_prompt(agent_response, available_tools)
        
        response = self.client.chat(
            self.functiongemma_host,
            self.functiongemma_model,
            [{'role': 'user', 'content': prompt}],
            available_tools,
            temperature=0.1  # Very deterministic
        )
        
        return self._process_assistance_response(response)
        
    def validate_tool_call(self, tool_call: Dict, tool_definition: Dict) -> Dict:
        """
        Validate a tool call against its definition.
        
        Returns:
            {
                'valid': True/False,
                'errors': [...],
                'warnings': [...]
            }
        """
        
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required parameters
        required_params = [
            p['name'] for p in tool_definition.get('parameters', {}).get('properties', {}).values()
            if p.get('required', False)
        ]
        
        provided_params = tool_call.get('arguments', {}).keys()
        
        for param in required_params:
            if param not in provided_params:
                validation['valid'] = False
                validation['errors'].append(f"Missing required parameter: {param}")
                
        # Check parameter types
        for param_name, param_value in tool_call.get('arguments', {}).items():
            expected_type = self._get_parameter_type(param_name, tool_definition)
            actual_type = type(param_value).__name__
            
            if not self._types_compatible(expected_type, actual_type):
                validation['warnings'].append(
                    f"Parameter {param_name} type mismatch: expected {expected_type}, got {actual_type}"
                )
                
        return validation
        
    def correct_tool_call(self, malformed_call: Dict, tool_definition: Dict) -> Dict:
        """
        Correct a malformed tool call.
        
        Returns:
            {
                'corrected_call': {...},
                'corrections_made': [...],
                'confidence': 0.85
            }
        """
        
        # Use FunctionGemma to correct the call
        prompt = self._create_correction_prompt(malformed_call, tool_definition)
        
        response = self.client.chat(
            self.functiongemma_host,
            self.functiongemma_model,
            [{'role': 'user', 'content': prompt}],
            [tool_definition],
            temperature=0.1
        )
        
        return self._process_correction_response(response)
        
    def recommend_tools(self, task_description: str, available_tools: List[Dict]) -> List[Dict]:
        """
        Recommend appropriate tools for a task.
        
        Returns:
            [
                {
                    'tool': {...},
                    'relevance': 0.92,
                    'reason': '...'
                }
            ]
        """
        
        recommendations = []
        
        # Use FunctionGemma to analyze task and recommend tools
        prompt = f"""Given this task: "{task_description}"

Which of these tools would be most appropriate?

Available tools:
{json.dumps(available_tools, indent=2)}

Recommend the most relevant tools and explain why."""

        response = self.client.chat(
            self.functiongemma_host,
            self.functiongemma_model,
            [{'role': 'user', 'content': prompt}],
            available_tools,
            temperature=0.2
        )
        
        # Parse recommendations from response
        recommendations = self._parse_recommendations(response, available_tools)
        
        return sorted(recommendations, key=lambda x: x['relevance'], reverse=True)
```

### Integration with All Agents

```python
# In each agent's execute method:

class AnyAgent:
    def __init__(self, client, config, logger):
        # ...
        self.tool_advisor = EnhancedToolAdvisor(client, config, logger)
        
    def execute(self, task: Dict, context: Dict) -> Dict:
        # Get response from model
        response = self.client.chat(...)
        
        # Use tool advisor to assist with tool calls
        if self._needs_tool_assistance(response):
            assistance = self.tool_advisor.assist_tool_call(
                response['content'],
                self.available_tools
            )
            
            # Validate tool calls
            for tool_call in assistance['tool_calls']:
                validation = self.tool_advisor.validate_tool_call(
                    tool_call,
                    self._get_tool_definition(tool_call['name'])
                )
                
                if not validation['valid']:
                    # Correct the tool call
                    corrected = self.tool_advisor.correct_tool_call(
                        tool_call,
                        self._get_tool_definition(tool_call['name'])
                    )
                    tool_call = corrected['corrected_call']
                    
        return self._process_response(response)
```

---

## Component 4: Specialist Coordination

### Purpose
Enable specialists to work together effectively, sharing insights and coordinating activities.

### Coordination Patterns

1. **Sequential Consultation**
   - Prompt Specialist → Role Specialist
   - Role Specialist → Custom Agent

2. **Parallel Consultation**
   - Multiple specialists analyze same problem
   - Results synthesized by coordinator

3. **Iterative Refinement**
   - Specialist provides initial solution
   - Other specialists review and refine
   - Iterate until consensus

### Implementation Details

#### File: `pipeline/agents/specialist_coordinator.py`

```python
class SpecialistCoordinator:
    """Coordinates specialist agent activities."""
    
    def __init__(self, client, config: PipelineConfig, logger):
        self.client = client
        self.config = config
        self.logger = logger
        
        # Specialists
        self.prompt_specialist = PromptSpecialist(client, config, logger)
        self.role_specialist = RoleSpecialist(client, config, logger)
        self.tool_advisor = EnhancedToolAdvisor(client, config, logger)
        
    def create_custom_role_for_problem(self, problem: Dict) -> CustomAgent:
        """
        Create a custom role for a specific problem.
        
        Workflow:
        1. Role Specialist analyzes requirements
        2. Role Specialist designs role
        3. Prompt Specialist creates prompt
        4. Tool Advisor recommends tools
        5. Role Specialist creates agent
        """
        
        # Step 1: Analyze requirements
        requirements = self.role_specialist.analyze_requirements(problem)
        
        # Step 2: Design role
        role_spec = self.role_specialist.design_role(requirements, problem)
        
        # Step 3: Get tool recommendations
        tool_recommendations = self.tool_advisor.recommend_tools(
            problem['description'],
            self._get_available_tools()
        )
        
        # Add recommended tools to role spec
        role_spec['tools'] = [t['tool'] for t in tool_recommendations[:5]]
        
        # Step 4: Create agent (includes prompt creation)
        agent = self.role_specialist.create_role(role_spec)
        
        return agent
        
    def optimize_existing_role(self, role_name: str, performance_data: Dict) -> Dict:
        """
        Optimize an existing role based on performance.
        
        Workflow:
        1. Get current role specification
        2. Prompt Specialist analyzes performance
        3. Prompt Specialist optimizes prompt
        4. Update role with new prompt
        """
        
        # Get current role
        role_spec = self.role_specialist.role_library.get_role(role_name)
        
        # Get current prompt
        current_prompt = role_spec.get('prompt', '')
        
        # Optimize prompt
        optimization = self.prompt_specialist.optimize_prompt(
            current_prompt,
            performance_data
        )
        
        # Update role
        role_spec['prompt'] = optimization['optimized_prompt']
        
        return {
            'role_name': role_name,
            'optimization': optimization,
            'updated_spec': role_spec
        }
```

---

## Integration Strategy

### Phase 3A: Specialists (Week 1)
1. Implement Prompt Specialist
2. Implement Role Specialist
3. Create role templates
4. Basic testing

### Phase 3B: FunctionGemma (Week 2)
1. Enhance Tool Advisor
2. Integrate with all agents
3. Test tool calling improvements
4. Performance validation

### Phase 3C: Coordination (Week 3)
1. Implement Specialist Coordinator
2. Create coordination workflows
3. Integration testing
4. Documentation

---

## Success Criteria

### Functional Requirements
- ✅ Prompt Specialist operational
- ✅ Role Specialist operational
- ✅ Custom roles can be created
- ✅ FunctionGemma integrated everywhere
- ✅ Specialist coordination working

### Performance Requirements
- ✅ Role creation < 30 seconds
- ✅ Prompt optimization < 20 seconds
- ✅ Tool call accuracy > 95%
- ✅ Custom roles effective

### Quality Requirements
- ✅ 90%+ code coverage
- ✅ All tests passing
- ✅ Documentation complete
- ✅ No critical bugs

---

## Next Phase

Upon completion of Phase 3, proceed to:
**[PHASE_4_TOOLS.md](PHASE_4_TOOLS.md)** - Tool Development Framework

---

**Phase Owner:** Development Team  
**Reviewers:** Technical Lead, AI/ML Engineer  
**Approval Required:** Yes  
**Estimated Effort:** 2-3 weeks (1 developer full-time)
</file_path>