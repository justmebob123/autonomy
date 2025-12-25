# Phase 2: Multi-Agent Architecture Enhancement

**Timeline:** 3-4 weeks  
**Priority:** HIGH  
**Dependencies:** Phase 1 (Foundation tools)  
**Deliverables:** Hierarchical multi-agent system with Architect coordination

---

## Overview

Phase 2 transforms the current phase-based system into a sophisticated hierarchical multi-agent architecture with an Architect agent providing system-wide coordination, strategic oversight, and intelligent problem-solving.

---

## Objectives

1. **Implement Architect Agent**: Create high-level coordinator with system-wide visibility
2. **Establish Hierarchical Structure**: Organize agents into teams with clear reporting
3. **Enable Team Coordination**: Allow teams to work in parallel with coordination
4. **Implement Communication Protocols**: Define how agents communicate and share context
5. **Create State Management**: Maintain consistent state across all agents
6. **Build Conflict Resolution**: Handle disagreements and conflicting recommendations

---

## Architecture Overview

### Current Architecture (Phase-Based)
```
User Request
    ↓
Coordinator (Sequential)
    ↓
Planning Phase → Coding Phase → QA Phase → Debugging Phase
    ↓
Result
```

**Limitations:**
- Sequential execution (slow)
- No system-wide oversight
- Limited context sharing
- No parallel work
- Single point of failure

### Proposed Architecture (Hierarchical Multi-Agent)
```
                    User Request
                         ↓
                  Architect Agent
                  (System-wide coordination)
                         ↓
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
   Planning Team    Development Team   Quality Team
   (Strategy)       (Implementation)   (Validation)
        ↓                ↓                ↓
   - Planner       - Coder           - QA Agent
   - Analyzer      - Debugger        - Tester
   - Designer      - Refactorer      - Reviewer
        ↓                ↓                ↓
                  Shared State
                  (Conversation Threads, Context, Results)
```

**Benefits:**
- Parallel execution (fast)
- System-wide oversight
- Rich context sharing
- Parallel work streams
- Resilient to failures

---

## Component 1: Architect Agent

### Purpose
High-level coordinator that analyzes the entire system, traces problems to root causes, coordinates teams, and makes strategic decisions.

### Responsibilities

1. **System Analysis**
   - Analyze entire codebase structure
   - Identify architectural patterns
   - Detect design issues
   - Understand system boundaries

2. **Problem Diagnosis**
   - Trace errors to root causes
   - Identify systemic issues
   - Detect patterns across problems
   - Understand problem context

3. **Strategic Planning**
   - Develop fix strategies
   - Coordinate team activities
   - Prioritize work
   - Allocate resources

4. **Team Coordination**
   - Assign tasks to teams
   - Monitor progress
   - Resolve conflicts
   - Synthesize results

5. **Quality Oversight**
   - Review team outputs
   - Ensure consistency
   - Validate solutions
   - Approve changes

### Implementation Details

#### File: `pipeline/agents/architect.py`

```python
class ArchitectAgent:
    """
    High-level coordinator with system-wide oversight.
    
    The Architect Agent is responsible for:
    - Analyzing system architecture
    - Diagnosing complex problems
    - Coordinating team activities
    - Making strategic decisions
    - Ensuring quality and consistency
    """
    
    def __init__(self, client, config: PipelineConfig, logger):
        self.client = client
        self.config = config
        self.logger = logger
        
        # Analysis tools from Phase 1
        self.file_analyzer = FileStructureAnalyzer(config.project_dir)
        self.schema_inspector = SchemaInspector(config.project_dir)
        self.call_tracer = CallFlowTracer(config.project_dir)
        self.loop_detector = LoopDetector(config.project_dir)
        self.pattern_recognizer = PatternRecognizer(config.project_dir)
        self.dependency_graph = DependencyGraphBuilder(config.project_dir)
        
        # Team management
        self.teams = {
            'planning': PlanningTeam(client, config, logger),
            'development': DevelopmentTeam(client, config, logger),
            'quality': QualityTeam(client, config, logger)
        }
        
        # State management
        self.system_state = SystemState()
        self.conversation_context = ConversationContext()
        
    def analyze_system(self) -> Dict:
        """
        Perform comprehensive system analysis.
        
        Returns:
            {
                'architecture': {
                    'pattern': 'layered|mvc|microservices',
                    'quality': 0.85,
                    'issues': [...]
                },
                'dependencies': {
                    'health': 0.78,
                    'circular': [...],
                    'coupling': {...}
                },
                'complexity': {
                    'total_loc': 12000,
                    'avg_complexity': 5.2,
                    'hotspots': [...]
                },
                'recommendations': [...]
            }
        """
        
        # Use Phase 1 tools for analysis
        structure = self.file_analyzer.analyze_structure()
        schema = self.schema_inspector.analyze_class_hierarchy()
        dependencies = self.dependency_graph.analyze_dependencies()
        
        # Synthesize analysis
        analysis = {
            'architecture': self._analyze_architecture(structure, schema),
            'dependencies': dependencies,
            'complexity': self._analyze_complexity(structure),
            'recommendations': self._generate_recommendations(structure, dependencies)
        }
        
        return analysis
        
    def diagnose_problem(self, error: Dict, context: Dict) -> Dict:
        """
        Diagnose a problem using comprehensive analysis.
        
        Args:
            error: Error information
            context: Current context (file, function, state)
            
        Returns:
            {
                'root_cause': 'verification_logic_bug',
                'contributing_factors': [...],
                'call_chain': [...],
                'related_files': [...],
                'similar_errors': [...],
                'loop_detected': True/False,
                'pattern_matched': {...},
                'recommended_strategy': 'fix_verification_logic',
                'team_assignments': {
                    'development': ['fix_handlers.py'],
                    'quality': ['verify_fix']
                }
            }
        """
        
        diagnosis = {}
        
        # 1. Check for loops (CRITICAL)
        loop_check = self.loop_detector.detect_action_loop(context)
        if loop_check and loop_check['loop_detected']:
            diagnosis['loop_detected'] = True
            diagnosis['loop_info'] = loop_check
            diagnosis['root_cause'] = loop_check.get('root_cause', 'unknown')
            
        # 2. Trace call chain
        if 'function' in context:
            call_chain = self.call_tracer.trace_call_chain(context['function'])
            diagnosis['call_chain'] = call_chain
            
        # 3. Find related files
        if 'file' in context:
            related = self.file_analyzer.get_file_relationships(context['file'])
            diagnosis['related_files'] = related
            
        # 4. Check for similar errors
        similar = self.pattern_recognizer.recognize_error_pattern(error)
        if similar and similar['pattern_matched']:
            diagnosis['pattern_matched'] = similar
            diagnosis['known_fixes'] = similar.get('known_fixes', [])
            
        # 5. Analyze root cause
        diagnosis['root_cause'] = self._determine_root_cause(
            error, context, loop_check, similar
        )
        
        # 6. Develop strategy
        diagnosis['recommended_strategy'] = self._develop_strategy(diagnosis)
        
        # 7. Assign teams
        diagnosis['team_assignments'] = self._assign_teams(diagnosis)
        
        return diagnosis
        
    def coordinate_teams(self, task: Dict) -> Dict:
        """
        Coordinate team activities for a task.
        
        Args:
            task: Task information with team assignments
            
        Returns:
            {
                'team_results': {
                    'planning': {...},
                    'development': {...},
                    'quality': {...}
                },
                'conflicts': [...],
                'resolution': {...},
                'final_decision': {...}
            }
        """
        
        results = {}
        
        # Execute teams in parallel or sequence based on dependencies
        if self._can_parallelize(task):
            results = self._execute_parallel(task)
        else:
            results = self._execute_sequential(task)
            
        # Check for conflicts
        conflicts = self._detect_conflicts(results)
        
        # Resolve conflicts
        if conflicts:
            resolution = self._resolve_conflicts(conflicts, results)
            results['resolution'] = resolution
            
        # Make final decision
        final_decision = self._make_final_decision(results)
        results['final_decision'] = final_decision
        
        return results
        
    def _determine_root_cause(self, error: Dict, context: Dict, 
                              loop_check: Dict, pattern: Dict) -> str:
        """
        Determine root cause using all available information.
        
        Uses:
        - Error message and traceback
        - Loop detection results
        - Pattern matching results
        - Call chain analysis
        - File relationship analysis
        """
        
        # If loop detected, that's likely the root cause
        if loop_check and loop_check.get('loop_detected'):
            return loop_check.get('root_cause', 'infinite_loop')
            
        # If pattern matched, use known root cause
        if pattern and pattern.get('pattern_matched'):
            return pattern.get('root_cause', 'known_pattern')
            
        # Analyze error message
        error_msg = error.get('message', '')
        
        # Common patterns
        if 'returned ERR' in error_msg:
            return 'initialization_error'
        elif 'not found' in error_msg:
            return 'missing_dependency'
        elif 'syntax' in error_msg.lower():
            return 'syntax_error'
        elif 'type' in error_msg.lower():
            return 'type_error'
            
        return 'unknown'
        
    def _develop_strategy(self, diagnosis: Dict) -> str:
        """
        Develop fix strategy based on diagnosis.
        
        Strategies:
        - fix_root_cause: Direct fix of identified root cause
        - break_loop: Break detected loop with alternative approach
        - apply_pattern: Apply known successful pattern
        - refactor: Refactor problematic code
        - escalate: Escalate to user for guidance
        """
        
        root_cause = diagnosis.get('root_cause')
        
        if diagnosis.get('loop_detected'):
            return 'break_loop'
            
        if diagnosis.get('pattern_matched'):
            return 'apply_pattern'
            
        if root_cause in ['verification_logic_bug', 'initialization_error']:
            return 'fix_root_cause'
            
        if root_cause == 'unknown':
            return 'escalate'
            
        return 'fix_root_cause'
        
    def _assign_teams(self, diagnosis: Dict) -> Dict:
        """
        Assign teams based on diagnosis and strategy.
        
        Returns:
            {
                'planning': ['analyze_alternatives', 'design_solution'],
                'development': ['implement_fix', 'test_locally'],
                'quality': ['review_changes', 'validate_fix']
            }
        """
        
        strategy = diagnosis.get('recommended_strategy')
        
        assignments = {}
        
        if strategy == 'break_loop':
            assignments['planning'] = ['analyze_loop', 'design_alternative']
            assignments['development'] = ['implement_alternative']
            assignments['quality'] = ['verify_no_loop']
            
        elif strategy == 'apply_pattern':
            assignments['development'] = ['apply_known_fix']
            assignments['quality'] = ['verify_pattern_application']
            
        elif strategy == 'fix_root_cause':
            assignments['planning'] = ['analyze_root_cause']
            assignments['development'] = ['implement_fix']
            assignments['quality'] = ['comprehensive_testing']
            
        elif strategy == 'escalate':
            assignments['planning'] = ['prepare_escalation_report']
            
        return assignments
        
    def _execute_parallel(self, task: Dict) -> Dict:
        """Execute teams in parallel using multi-threading."""
        
        import concurrent.futures
        
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            
            for team_name, team_tasks in task['team_assignments'].items():
                team = self.teams[team_name]
                future = executor.submit(team.execute, team_tasks, task)
                futures[team_name] = future
                
            for team_name, future in futures.items():
                try:
                    results[team_name] = future.result(timeout=3600)  # 1 hour
                except Exception as e:
                    results[team_name] = {'error': str(e)}
                    
        return results
        
    def _execute_sequential(self, task: Dict) -> Dict:
        """Execute teams sequentially with dependency management."""
        
        results = {}
        
        # Determine execution order based on dependencies
        order = self._determine_execution_order(task['team_assignments'])
        
        for team_name in order:
            team_tasks = task['team_assignments'][team_name]
            team = self.teams[team_name]
            
            # Pass previous results as context
            context = {
                'previous_results': results,
                'task': task
            }
            
            results[team_name] = team.execute(team_tasks, context)
            
        return results
        
    def _detect_conflicts(self, results: Dict) -> List[Dict]:
        """
        Detect conflicts in team results.
        
        Conflicts:
        - Contradictory recommendations
        - Incompatible changes
        - Resource conflicts
        """
        
        conflicts = []
        
        # Check for contradictory recommendations
        recommendations = []
        for team_name, result in results.items():
            if 'recommendations' in result:
                recommendations.extend([
                    (team_name, rec) for rec in result['recommendations']
                ])
                
        # Find contradictions
        for i, (team1, rec1) in enumerate(recommendations):
            for team2, rec2 in recommendations[i+1:]:
                if self._are_contradictory(rec1, rec2):
                    conflicts.append({
                        'type': 'contradictory_recommendations',
                        'team1': team1,
                        'team2': team2,
                        'recommendation1': rec1,
                        'recommendation2': rec2
                    })
                    
        return conflicts
        
    def _resolve_conflicts(self, conflicts: List[Dict], results: Dict) -> Dict:
        """
        Resolve conflicts using architect's judgment.
        
        Resolution strategies:
        - Priority-based (some teams have higher priority)
        - Evidence-based (choose recommendation with more evidence)
        - Synthesis (combine recommendations)
        - Escalation (ask user)
        """
        
        resolution = {
            'conflicts_resolved': [],
            'conflicts_escalated': []
        }
        
        for conflict in conflicts:
            if conflict['type'] == 'contradictory_recommendations':
                # Use evidence-based resolution
                rec1 = conflict['recommendation1']
                rec2 = conflict['recommendation2']
                
                # Compare evidence
                evidence1 = self._evaluate_evidence(rec1, results)
                evidence2 = self._evaluate_evidence(rec2, results)
                
                if evidence1 > evidence2:
                    resolution['conflicts_resolved'].append({
                        'conflict': conflict,
                        'chosen': rec1,
                        'reason': 'stronger_evidence'
                    })
                elif evidence2 > evidence1:
                    resolution['conflicts_resolved'].append({
                        'conflict': conflict,
                        'chosen': rec2,
                        'reason': 'stronger_evidence'
                    })
                else:
                    # Escalate to user
                    resolution['conflicts_escalated'].append(conflict)
                    
        return resolution
        
    def _make_final_decision(self, results: Dict) -> Dict:
        """
        Make final decision based on all team results.
        
        Returns:
            {
                'decision': 'approve|reject|modify',
                'actions': [...],
                'rationale': '...',
                'confidence': 0.85
            }
        """
        
        # Synthesize all results
        all_recommendations = []
        all_concerns = []
        
        for team_name, result in results.items():
            if 'recommendations' in result:
                all_recommendations.extend(result['recommendations'])
            if 'concerns' in result:
                all_concerns.extend(result['concerns'])
                
        # Evaluate overall quality
        quality_score = self._evaluate_quality(results)
        
        # Make decision
        if quality_score > 0.8 and not all_concerns:
            decision = 'approve'
        elif quality_score > 0.6:
            decision = 'modify'
        else:
            decision = 'reject'
            
        return {
            'decision': decision,
            'actions': self._determine_actions(decision, results),
            'rationale': self._generate_rationale(decision, quality_score, all_concerns),
            'confidence': quality_score
        }
```

#### Architect Prompt

```python
ARCHITECT_PROMPT = """You are the Architect Agent - the highest-level coordinator in the system.

Your responsibilities:
1. Analyze the entire system architecture and codebase
2. Diagnose complex problems by tracing to root causes
3. Coordinate multiple teams (Planning, Development, Quality)
4. Make strategic decisions about approaches and priorities
5. Resolve conflicts between teams
6. Ensure system-wide consistency and quality

You have access to comprehensive analysis tools:
- File structure analyzer
- Schema inspector
- Call flow tracer
- Loop detector (CRITICAL - use this frequently!)
- Pattern recognizer
- Dependency graph builder

When analyzing a problem:
1. Use loop detector FIRST to check for infinite loops
2. Use call flow tracer to understand execution paths
3. Use pattern recognizer to find similar past issues
4. Use file structure analyzer to understand context
5. Synthesize all information to determine root cause
6. Develop a strategic approach
7. Assign tasks to appropriate teams
8. Coordinate team activities
9. Review and approve final solution

When coordinating teams:
1. Assign clear, specific tasks
2. Provide comprehensive context
3. Monitor progress
4. Resolve conflicts
5. Synthesize results
6. Make final decision

CRITICAL: Always check for loops before proceeding with fixes!
If loop detected, develop alternative strategy immediately.

You are the system's strategic brain - think holistically and long-term.
"""
```

### Testing Requirements
- Test with complex multi-file problems
- Test loop detection integration
- Test team coordination
- Test conflict resolution
- Benchmark decision-making quality

---

## Component 2: Team Structure

### Team Organization

#### Planning Team
**Purpose:** Strategic planning and analysis

**Members:**
- **Planner Agent**: Creates implementation plans
- **Analyzer Agent**: Analyzes requirements and constraints
- **Designer Agent**: Designs solutions and architectures

**Responsibilities:**
- Analyze requirements
- Design solutions
- Create implementation plans
- Identify risks
- Estimate effort

#### Development Team
**Purpose:** Implementation and fixing

**Members:**
- **Coder Agent**: Implements new features
- **Debugger Agent**: Fixes bugs and errors
- **Refactorer Agent**: Improves code quality

**Responsibilities:**
- Implement features
- Fix bugs
- Refactor code
- Write tests
- Document changes

#### Quality Team
**Purpose:** Validation and quality assurance

**Members:**
- **QA Agent**: Reviews code quality
- **Tester Agent**: Tests functionality
- **Reviewer Agent**: Reviews changes

**Responsibilities:**
- Review code
- Test functionality
- Validate fixes
- Ensure quality
- Approve changes

### Implementation Details

#### File: `pipeline/agents/teams.py`

```python
class BaseTeam:
    """Base class for agent teams."""
    
    def __init__(self, client, config: PipelineConfig, logger):
        self.client = client
        self.config = config
        self.logger = logger
        self.members = {}
        
    def execute(self, tasks: List[str], context: Dict) -> Dict:
        """
        Execute assigned tasks.
        
        Args:
            tasks: List of task descriptions
            context: Execution context
            
        Returns:
            {
                'results': [...],
                'recommendations': [...],
                'concerns': [...],
                'confidence': 0.85
            }
        """
        raise NotImplementedError


class PlanningTeam(BaseTeam):
    """Team responsible for strategic planning."""
    
    def __init__(self, client, config, logger):
        super().__init__(client, config, logger)
        
        self.members = {
            'planner': PlannerAgent(client, config, logger),
            'analyzer': AnalyzerAgent(client, config, logger),
            'designer': DesignerAgent(client, config, logger)
        }
        
    def execute(self, tasks: List[str], context: Dict) -> Dict:
        """Execute planning tasks."""
        
        results = []
        
        for task in tasks:
            if 'analyze' in task.lower():
                result = self.members['analyzer'].analyze(context)
            elif 'design' in task.lower():
                result = self.members['designer'].design(context)
            elif 'plan' in task.lower():
                result = self.members['planner'].plan(context)
            else:
                result = self._delegate_task(task, context)
                
            results.append(result)
            
        # Synthesize results
        return self._synthesize_results(results)


class DevelopmentTeam(BaseTeam):
    """Team responsible for implementation."""
    
    def __init__(self, client, config, logger):
        super().__init__(client, config, logger)
        
        self.members = {
            'coder': CoderAgent(client, config, logger),
            'debugger': DebuggerAgent(client, config, logger),
            'refactorer': RefactorerAgent(client, config, logger)
        }
        
    def execute(self, tasks: List[str], context: Dict) -> Dict:
        """Execute development tasks."""
        
        results = []
        
        for task in tasks:
            if 'implement' in task.lower() or 'code' in task.lower():
                result = self.members['coder'].implement(context)
            elif 'fix' in task.lower() or 'debug' in task.lower():
                result = self.members['debugger'].debug(context)
            elif 'refactor' in task.lower():
                result = self.members['refactorer'].refactor(context)
            else:
                result = self._delegate_task(task, context)
                
            results.append(result)
            
        return self._synthesize_results(results)


class QualityTeam(BaseTeam):
    """Team responsible for quality assurance."""
    
    def __init__(self, client, config, logger):
        super().__init__(client, config, logger)
        
        self.members = {
            'qa': QAAgent(client, config, logger),
            'tester': TesterAgent(client, config, logger),
            'reviewer': ReviewerAgent(client, config, logger)
        }
        
    def execute(self, tasks: List[str], context: Dict) -> Dict:
        """Execute quality tasks."""
        
        results = []
        
        for task in tasks:
            if 'review' in task.lower():
                result = self.members['reviewer'].review(context)
            elif 'test' in task.lower():
                result = self.members['tester'].test(context)
            elif 'qa' in task.lower() or 'quality' in task.lower():
                result = self.members['qa'].check_quality(context)
            else:
                result = self._delegate_task(task, context)
                
            results.append(result)
            
        return self._synthesize_results(results)
```

---

## Component 3: Communication Protocols

### Message Types

```python
class MessageType(Enum):
    """Types of messages agents can send."""
    
    # Requests
    REQUEST_ANALYSIS = "request_analysis"
    REQUEST_IMPLEMENTATION = "request_implementation"
    REQUEST_REVIEW = "request_review"
    
    # Responses
    ANALYSIS_COMPLETE = "analysis_complete"
    IMPLEMENTATION_COMPLETE = "implementation_complete"
    REVIEW_COMPLETE = "review_complete"
    
    # Notifications
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    
    # Coordination
    CONFLICT_DETECTED = "conflict_detected"
    DECISION_REQUIRED = "decision_required"
    ESCALATION = "escalation"
```

### Message Format

```python
@dataclass
class AgentMessage:
    """Standard message format for agent communication."""
    
    message_id: str
    sender: str  # Agent name
    recipient: str  # Agent name or "broadcast"
    message_type: MessageType
    content: Dict
    timestamp: datetime
    priority: int  # 1-10, 10 being highest
    requires_response: bool = False
    parent_message_id: Optional[str] = None
```

### Communication Bus

#### File: `pipeline/agents/communication.py`

```python
class CommunicationBus:
    """Central communication bus for agent messages."""
    
    def __init__(self):
        self.messages: List[AgentMessage] = []
        self.subscribers: Dict[str, List[Callable]] = {}
        self.message_history: deque = deque(maxlen=1000)
        
    def send_message(self, message: AgentMessage):
        """Send a message to recipient(s)."""
        
        self.messages.append(message)
        self.message_history.append(message)
        
        # Notify subscribers
        if message.recipient == "broadcast":
            for subscribers in self.subscribers.values():
                for callback in subscribers:
                    callback(message)
        elif message.recipient in self.subscribers:
            for callback in self.subscribers[message.recipient]:
                callback(message)
                
    def subscribe(self, agent_name: str, callback: Callable):
        """Subscribe to messages for an agent."""
        
        if agent_name not in self.subscribers:
            self.subscribers[agent_name] = []
        self.subscribers[agent_name].append(callback)
        
    def get_conversation(self, message_id: str) -> List[AgentMessage]:
        """Get full conversation thread for a message."""
        
        conversation = []
        
        # Find root message
        root = self._find_root_message(message_id)
        if root:
            conversation.append(root)
            # Find all descendants
            conversation.extend(self._find_descendants(root.message_id))
            
        return conversation
```

---

## Component 4: State Management

### Shared State

```python
class SystemState:
    """Shared state across all agents."""
    
    def __init__(self):
        self.current_task: Optional[Dict] = None
        self.active_agents: Set[str] = set()
        self.completed_tasks: List[Dict] = []
        self.pending_decisions: List[Dict] = []
        self.system_metrics: Dict = {}
        self.conversation_threads: Dict[str, ConversationThread] = {}
        
    def update_task(self, task: Dict):
        """Update current task."""
        self.current_task = task
        
    def register_agent(self, agent_name: str):
        """Register an active agent."""
        self.active_agents.add(agent_name)
        
    def unregister_agent(self, agent_name: str):
        """Unregister an agent."""
        self.active_agents.discard(agent_name)
        
    def add_pending_decision(self, decision: Dict):
        """Add a decision that requires architect approval."""
        self.pending_decisions.append(decision)
        
    def get_context(self) -> Dict:
        """Get current system context."""
        return {
            'current_task': self.current_task,
            'active_agents': list(self.active_agents),
            'pending_decisions': len(self.pending_decisions),
            'completed_tasks': len(self.completed_tasks),
            'metrics': self.system_metrics
        }
```

### Context Sharing

```python
class ConversationContext:
    """Shared conversation context for all agents."""
    
    def __init__(self):
        self.global_context: Dict = {}
        self.agent_contexts: Dict[str, Dict] = {}
        
    def update_global(self, key: str, value: Any):
        """Update global context available to all agents."""
        self.global_context[key] = value
        
    def update_agent(self, agent_name: str, key: str, value: Any):
        """Update agent-specific context."""
        if agent_name not in self.agent_contexts:
            self.agent_contexts[agent_name] = {}
        self.agent_contexts[agent_name][key] = value
        
    def get_context_for_agent(self, agent_name: str) -> Dict:
        """Get complete context for an agent."""
        context = self.global_context.copy()
        if agent_name in self.agent_contexts:
            context.update(self.agent_contexts[agent_name])
        return context
```

---

## Component 5: Conflict Resolution

### Conflict Types

```python
class ConflictType(Enum):
    """Types of conflicts that can occur."""
    
    CONTRADICTORY_RECOMMENDATIONS = "contradictory_recommendations"
    RESOURCE_CONFLICT = "resource_conflict"
    PRIORITY_CONFLICT = "priority_conflict"
    APPROACH_DISAGREEMENT = "approach_disagreement"
    QUALITY_CONCERN = "quality_concern"
```

### Resolution Strategies

```python
class ConflictResolver:
    """Resolves conflicts between agents."""
    
    def __init__(self, architect: ArchitectAgent):
        self.architect = architect
        
    def resolve(self, conflict: Dict) -> Dict:
        """
        Resolve a conflict.
        
        Returns:
            {
                'resolution': 'accepted|rejected|modified',
                'chosen_option': {...},
                'rationale': '...',
                'confidence': 0.85
            }
        """
        
        conflict_type = conflict['type']
        
        if conflict_type == ConflictType.CONTRADICTORY_RECOMMENDATIONS:
            return self._resolve_contradictory_recommendations(conflict)
        elif conflict_type == ConflictType.RESOURCE_CONFLICT:
            return self._resolve_resource_conflict(conflict)
        elif conflict_type == ConflictType.PRIORITY_CONFLICT:
            return self._resolve_priority_conflict(conflict)
        elif conflict_type == ConflictType.APPROACH_DISAGREEMENT:
            return self._resolve_approach_disagreement(conflict)
        else:
            return self._escalate_to_architect(conflict)
            
    def _resolve_contradictory_recommendations(self, conflict: Dict) -> Dict:
        """Resolve contradictory recommendations using evidence."""
        
        rec1 = conflict['recommendation1']
        rec2 = conflict['recommendation2']
        
        # Evaluate evidence for each
        evidence1 = self._evaluate_evidence(rec1)
        evidence2 = self._evaluate_evidence(rec2)
        
        if evidence1 > evidence2 * 1.2:  # 20% threshold
            return {
                'resolution': 'accepted',
                'chosen_option': rec1,
                'rationale': f'Stronger evidence (score: {evidence1} vs {evidence2})',
                'confidence': evidence1
            }
        elif evidence2 > evidence1 * 1.2:
            return {
                'resolution': 'accepted',
                'chosen_option': rec2,
                'rationale': f'Stronger evidence (score: {evidence2} vs {evidence1})',
                'confidence': evidence2
            }
        else:
            # Too close - escalate to architect
            return self._escalate_to_architect(conflict)
```

---

## Integration Strategy

### Phase 2A: Core Architecture (Week 1-2)
1. Implement ArchitectAgent
2. Implement team structure
3. Create communication bus
4. Implement state management
5. Basic integration testing

### Phase 2B: Coordination (Week 2-3)
1. Implement team coordination
2. Implement conflict resolution
3. Integrate with Phase 1 tools
4. Advanced testing

### Phase 2C: Optimization (Week 3-4)
1. Optimize parallel execution
2. Improve decision-making
3. Enhance communication
4. Performance testing
5. Documentation

---

## Success Criteria

### Functional Requirements
- ✅ Architect agent operational
- ✅ All three teams functional
- ✅ Communication bus working
- ✅ State management consistent
- ✅ Conflict resolution effective

### Performance Requirements
- ✅ Parallel execution 2x faster than sequential
- ✅ Decision-making < 30 seconds
- ✅ Communication latency < 100ms
- ✅ State consistency 100%

### Quality Requirements
- ✅ 90%+ code coverage
- ✅ All integration tests passing
- ✅ Documentation complete
- ✅ No critical bugs

---

## Next Phase

Upon completion of Phase 2, proceed to:
**[PHASE_3_SPECIALISTS.md](PHASE_3_SPECIALISTS.md)** - Specialist Roles & Dynamic Systems

---

**Phase Owner:** Development Team  
**Reviewers:** Technical Lead, Architect  
**Approval Required:** Yes  
**Estimated Effort:** 3-4 weeks (1 developer full-time)
</file_path>