# Team Orchestrator System

## Overview

The Team Orchestrator System enables parallel execution of multiple specialist agents across multiple Ollama servers (ollama01 and ollama02) to solve complex problems efficiently. It provides intelligent load balancing, dependency management, and result synthesis.

## Architecture

### Components

1. **TeamOrchestrator** (`pipeline/team_orchestrator.py`)
   - Coordinates multiple specialists in parallel
   - Distributes work across servers
   - Manages execution waves
   - Synthesizes results

2. **Team Orchestrator Meta-Prompt** (`pipeline/prompts/team_orchestrator.py`)
   - Teaches AI how to coordinate teams
   - Provides coordination patterns
   - Defines load balancing strategies
   - Specifies output format

3. **Task & Wave Management**
   - Task: Single unit of work for a specialist
   - ExecutionWave: Group of parallel tasks
   - OrchestrationPlan: Complete execution plan

## Key Features

### 1. Parallel Execution
Execute multiple specialists simultaneously:
```python
Wave 1 (Parallel):
  - Syntax Analyst (ollama02) → Analyze syntax
  - Whitespace Analyst (ollama01) → Analyze indentation
  - Pattern Analyst (ollama02) → Analyze patterns
  - Root Cause Analyst (ollama01) → Analyze causes
```

### 2. Multi-Server Load Balancing
Distribute work across available servers:
- **ollama01.thiscluster.net** - Primary server
- **ollama02.thiscluster.net** - Secondary server
- Round-robin distribution
- Load-aware routing
- Automatic failover

### 3. Dependency Management
Handle task dependencies:
```python
Wave 1: Analysis (parallel)
  ↓
Wave 2: Synthesis (sequential, depends on Wave 1)
  ↓
Wave 3: Implementation (parallel, depends on Wave 2)
```

### 4. Result Synthesis
Combine results from multiple specialists:
- **merge_all**: Merge all results
- **use_first_result**: Use first successful result
- **consensus**: Build consensus from multiple opinions
- **custom**: Custom synthesis strategy

## Coordination Patterns

### Pattern 1: PARALLEL ANALYSIS
**Use When:** Multiple aspects need independent analysis

**Example:**
```python
orchestrator = TeamOrchestrator(client, specialist_team, logger)

plan = orchestrator.create_orchestration_plan(
    problem="Analyze complex error with multiple issues",
    context={'file': 'main.py', 'error': 'Multiple syntax and logic errors'}
)

results = orchestrator.execute_plan(plan, thread)
```

**Execution:**
```
Wave 1 (Parallel - 4 tasks):
├─ Syntax Analyst (ollama02) → 45s
├─ Whitespace Analyst (ollama01) → 38s
├─ Pattern Analyst (ollama02) → 52s
└─ Root Cause Analyst (ollama01) → 41s

Total: 52s (vs 176s sequential) → 3.4x speedup
```

### Pattern 2: DIVIDE AND CONQUER
**Use When:** Large problem can be split into independent parts

**Example:**
```python
plan = orchestrator.create_orchestration_plan(
    problem="Analyze 4 files simultaneously",
    context={'files': ['file1.py', 'file2.py', 'file3.py', 'file4.py']}
)
```

**Execution:**
```
Wave 1 (Parallel - 4 tasks):
├─ Analyst A (ollama01) → file1.py
├─ Analyst B (ollama02) → file2.py
├─ Analyst C (ollama01) → file3.py
└─ Analyst D (ollama02) → file4.py

Wave 2 (Sequential - 1 task):
└─ Integrator (ollama01) → Combine findings
```

### Pattern 3: PIPELINE
**Use When:** Tasks have sequential dependencies

**Example:**
```
Wave 1: Analysis (Parallel)
  ├─ Code Analyst (ollama01)
  └─ Requirements Analyst (ollama02)

Wave 2: Design (Sequential)
  └─ Architect (ollama01) [uses Wave 1 results]

Wave 3: Implementation (Parallel)
  ├─ Coder A (ollama01)
  └─ Coder B (ollama02)

Wave 4: Validation (Parallel)
  ├─ QA A (ollama01)
  └─ QA B (ollama02)
```

### Pattern 4: CONSENSUS BUILDING
**Use When:** Need multiple perspectives on same problem

**Example:**
```
Wave 1 (Parallel - 3 experts):
├─ Expert A (ollama01) → Propose solution
├─ Expert B (ollama02) → Propose solution
└─ Expert C (ollama01) → Propose solution

Wave 2 (Sequential):
└─ Synthesizer → Build consensus
```

## Load Balancing Strategies

### Strategy 1: Round Robin
Distribute tasks evenly:
```python
Task 1 → ollama01
Task 2 → ollama02
Task 3 → ollama01
Task 4 → ollama02
```

### Strategy 2: Capability-Based
Assign based on server strengths:
```python
Heavy computation → ollama02 (more powerful)
Quick analysis → ollama01 (faster response)
```

### Strategy 3: Load-Aware
Monitor server load and adjust:
```python
if server_load['ollama01'] < server_load['ollama02']:
    assign_to('ollama01')
else:
    assign_to('ollama02')
```

## Usage

### Basic Usage

```python
from pipeline.team_orchestrator import TeamOrchestrator
from pipeline.specialist_agents import SpecialistTeam
from pipeline.client import OllamaClient

# Initialize
client = OllamaClient(config)
specialist_team = SpecialistTeam(client, logger)
orchestrator = TeamOrchestrator(client, specialist_team, logger)

# Create plan
plan = orchestrator.create_orchestration_plan(
    problem="Fix complex error with multiple issues",
    context={'file': 'main.py', 'error_type': 'syntax_and_logic'}
)

# Execute plan
results = orchestrator.execute_plan(plan, thread)

# Check results
if results['success']:
    synthesis = results['synthesis']
    print(f"Completed in {results['duration']:.1f}s")
    print(f"Parallel efficiency: {results['statistics']['parallel_efficiency']:.1f}x")
```

### Advanced Usage

```python
# Custom orchestration plan
from pipeline.team_orchestrator import Task, ExecutionWave, OrchestrationPlan

# Define tasks
task1 = Task(
    task_id="syntax_analysis",
    specialist="Syntax Analyst",
    server="ollama02.thiscluster.net",
    input_data={'file': 'main.py'},
    timeout=300
)

task2 = Task(
    task_id="whitespace_analysis",
    specialist="Whitespace Analyst",
    server="ollama01.thiscluster.net",
    input_data={'file': 'main.py'},
    timeout=300
)

# Create wave
wave1 = ExecutionWave(wave_number=1, tasks=[task1, task2])

# Create plan
plan = OrchestrationPlan(
    problem="Analyze main.py",
    waves=[wave1],
    synthesis_strategy="merge_all",
    success_criteria="all_tasks_complete"
)

# Execute
results = orchestrator.execute_plan(plan)
```

## Integration with Debugging Phase

The TeamOrchestrator is integrated into the debugging phase for complex problems:

```python
class DebuggingPhase(BasePhase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ... other initialization ...
        
        # Initialize team orchestrator
        self.team_orchestrator = TeamOrchestrator(
            self.client,
            self.specialist_team,
            self.logger,
            max_workers=4
        )
    
    def _handle_complex_error(self, error, thread):
        """Use team orchestrator for complex errors"""
        # Create orchestration plan
        plan = self.team_orchestrator.create_orchestration_plan(
            problem=f"Fix {error['type']}: {error['message']}",
            context={'file': error['file'], 'thread': thread}
        )
        
        # Execute in parallel
        results = self.team_orchestrator.execute_plan(plan, thread)
        
        return results['synthesis']
```

## Performance Metrics

### Parallelism Factor
```
Parallelism Factor = Tasks executed simultaneously / Total tasks

Example:
- 4 tasks in Wave 1 (parallel)
- 1 task in Wave 2 (sequential)
- Total: 5 tasks
- Parallelism Factor = 4/5 = 0.8 (80%)
```

### Parallel Efficiency
```
Parallel Efficiency = Sequential Duration / Parallel Duration

Example:
- Sequential: 45s + 38s + 52s + 41s = 176s
- Parallel: max(45s, 38s, 52s, 41s) = 52s
- Efficiency = 176s / 52s = 3.4x speedup
```

### Server Utilization
```
Server Utilization = Active Time / Total Time

Example:
- ollama01: 79s active / 100s total = 79%
- ollama02: 97s active / 100s total = 97%
```

## Statistics Tracking

The orchestrator tracks comprehensive statistics:

```python
stats = orchestrator.get_statistics()

print(f"Total tasks: {stats['total_tasks']}")
print(f"Successful: {stats['successful_tasks']}")
print(f"Failed: {stats['failed_tasks']}")
print(f"Total duration: {stats['total_duration']:.1f}s")
print(f"Parallel efficiency: {stats['parallel_efficiency']:.1f}x")
```

## Failure Handling

### Task Failure
```python
If task fails:
  1. Log error
  2. Mark task as failed
  3. Continue with other tasks
  4. Include failure in synthesis
```

### Wave Failure
```python
If entire wave fails:
  1. Log wave failure
  2. Attempt retry (1 time)
  3. Continue to next wave if possible
  4. Mark dependencies as incomplete
```

### Server Failure
```python
If server unavailable:
  1. Route to other server
  2. Queue if both busy
  3. Timeout after configured duration
```

## Configuration

### Max Workers
```python
orchestrator = TeamOrchestrator(
    client, specialist_team, logger,
    max_workers=4  # Maximum parallel tasks
)
```

### Task Timeout
```python
task = Task(
    task_id="analysis",
    specialist="Syntax Analyst",
    server="ollama01.thiscluster.net",
    input_data={},
    timeout=300  # 5 minutes
)
```

### Synthesis Strategy
```python
plan = OrchestrationPlan(
    problem="...",
    waves=[...],
    synthesis_strategy="consensus",  # merge_all, use_first_result, consensus
    success_criteria="all_tasks_complete"
)
```

## Example Scenarios

### Scenario 1: Complex Error Analysis
```
Problem: Runtime error with syntax, indentation, and logic issues

Orchestration:
Wave 1 (Parallel - 4 specialists):
├─ Syntax Analyst (ollama02) → Find syntax errors
├─ Whitespace Analyst (ollama01) → Find indentation issues
├─ Logic Analyst (ollama02) → Find logic bugs
└─ Root Cause Analyst (ollama01) → Find underlying causes

Wave 2 (Sequential - 1 specialist):
└─ Architect (ollama01) → Synthesize findings, create fix plan

Result:
- Duration: 58s (vs 180s sequential)
- Speedup: 3.1x
- All issues identified and prioritized
```

### Scenario 2: Multi-File Analysis
```
Problem: Analyze 6 files for circular dependencies

Orchestration:
Wave 1 (Parallel - 6 analysts):
├─ Analyst A (ollama01) → file1.py
├─ Analyst B (ollama02) → file2.py
├─ Analyst C (ollama01) → file3.py
├─ Analyst D (ollama02) → file4.py
├─ Analyst E (ollama01) → file5.py
└─ Analyst F (ollama02) → file6.py

Wave 2 (Sequential - 1 analyst):
└─ Dependency Analyzer (ollama01) → Find circular dependencies

Result:
- Duration: 72s (vs 240s sequential)
- Speedup: 3.3x
- 2 circular dependencies found
```

### Scenario 3: Consensus Building
```
Problem: Choose best approach for complex refactoring

Orchestration:
Wave 1 (Parallel - 3 experts):
├─ Expert A (ollama01) → Propose approach A
├─ Expert B (ollama02) → Propose approach B
└─ Expert C (ollama01) → Propose approach C

Wave 2 (Sequential - 1 synthesizer):
└─ Synthesizer (ollama02) → Build consensus

Result:
- Duration: 95s (vs 180s sequential)
- Speedup: 1.9x
- Consensus: Approach B with elements from A and C
```

## Best Practices

### DO:
✅ Use parallel execution for independent tasks
✅ Balance load across servers
✅ Handle failures gracefully
✅ Synthesize results comprehensively
✅ Track statistics for optimization
✅ Use appropriate synthesis strategy
✅ Set reasonable timeouts

### DON'T:
❌ Create unnecessary dependencies
❌ Overload single server
❌ Ignore task failures
❌ Skip result synthesis
❌ Use parallel execution for sequential tasks
❌ Set timeouts too short
❌ Forget to track statistics

## Troubleshooting

### Low Parallel Efficiency
**Problem:** Efficiency < 2x
**Solutions:**
- Reduce dependencies between tasks
- Increase parallelism in waves
- Balance task durations
- Use more workers

### Server Overload
**Problem:** One server at 100%, other at 20%
**Solutions:**
- Improve load balancing
- Use round-robin distribution
- Monitor server load
- Adjust task assignments

### High Failure Rate
**Problem:** Many tasks failing
**Solutions:**
- Increase timeouts
- Check server availability
- Validate specialist configurations
- Add retry logic

## Future Enhancements

1. **Dynamic Load Balancing**
   - Real-time server monitoring
   - Adaptive task routing
   - Predictive load distribution

2. **Advanced Synthesis**
   - Machine learning-based synthesis
   - Conflict resolution strategies
   - Confidence scoring

3. **Caching & Optimization**
   - Result caching
   - Speculative execution
   - Early termination

4. **Monitoring Dashboard**
   - Real-time execution visualization
   - Performance metrics
   - Server utilization graphs

## Conclusion

The Team Orchestrator System enables efficient parallel execution of multiple specialist agents across multiple servers. It provides intelligent load balancing, dependency management, and result synthesis, achieving 2-4x speedup on complex problems while maintaining high quality results.