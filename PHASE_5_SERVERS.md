# Phase 5: Multi-Server Orchestration

**Timeline:** 2-3 weeks  
**Priority:** HIGH  
**Dependencies:** Phase 1 (Foundation), Phase 2 (Architecture)  
**Deliverables:** Intelligent multi-server workload distribution and parallel execution

---

## Overview

Phase 5 implements intelligent orchestration across both Ollama servers (ollama01 and ollama02), enabling parallel execution, load balancing, and optimal resource utilization. This addresses the current limitation where only ollama02 is actively used.

---

## Objectives

1. **Implement Load Balancing**: Distribute workload across both servers intelligently
2. **Enable Parallel Execution**: Run independent tasks simultaneously
3. **Create Server Affinity Rules**: Route tasks to optimal servers
4. **Build Failover Mechanisms**: Handle server failures gracefully
5. **Implement Resource Monitoring**: Track server health and capacity
6. **Optimize Performance**: Maximize throughput and minimize latency

---

## Current State Analysis

### Current Configuration
```python
# From config.py
servers = [
    ServerConfig(name="ollama01", host="ollama01.thiscluster.net"),
    ServerConfig(name="ollama02", host="ollama02.thiscluster.net")
]

model_assignments = {
    'planning': ("qwen2.5:14b", "ollama02.thiscluster.net"),
    'coding': ("qwen2.5-coder:32b", "ollama02.thiscluster.net"),
    'qa': ("qwen2.5:14b", "ollama02.thiscluster.net"),
    'debugging': ("qwen2.5-coder:32b", "ollama02.thiscluster.net"),
    # ALL assigned to ollama02!
}
```

### Problem
- **100% of workload on ollama02**
- **ollama01 completely idle**
- **No parallel execution**
- **Single point of failure**
- **Suboptimal resource utilization**

### Solution
Intelligent orchestration that:
- Distributes load across both servers
- Executes independent tasks in parallel
- Routes tasks based on server capabilities
- Handles failures gracefully
- Monitors and optimizes performance

---

## Component 1: Load Balancer

### Purpose
Intelligently distribute workload across available servers based on capacity, capabilities, and current load.

### Load Balancing Strategies

1. **Round Robin**: Simple rotation between servers
2. **Least Loaded**: Route to server with lowest current load
3. **Capability-Based**: Route based on server capabilities
4. **Weighted**: Distribute based on server capacity
5. **Hybrid**: Combine multiple strategies

### Implementation Details

#### File: `pipeline/orchestration/load_balancer.py`

```python
class LoadBalancer:
    """
    Intelligent load balancer for multi-server orchestration.
    
    Responsibilities:
    - Monitor server load and capacity
    - Route requests to optimal servers
    - Balance workload distribution
    - Handle server failures
    """
    
    def __init__(self, config: PipelineConfig, logger):
        self.config = config
        self.logger = logger
        
        # Server monitoring
        self.server_monitor = ServerMonitor(config.servers, logger)
        
        # Load tracking
        self.server_loads: Dict[str, ServerLoad] = {}
        
        # Strategy
        self.strategy = HybridLoadBalancingStrategy()
        
        # Initialize server loads
        for server in config.servers:
            self.server_loads[server.name] = ServerLoad(
                server_name=server.name,
                current_requests=0,
                total_capacity=self._estimate_capacity(server),
                available_models=server.models
            )
            
    def select_server(self, task: Dict, model: str) -> str:
        """
        Select optimal server for a task.
        
        Args:
            task: Task information
            model: Required model
            
        Returns:
            server_name: Name of selected server
        """
        
        # Get servers that have the required model
        capable_servers = self._get_capable_servers(model)
        
        if not capable_servers:
            raise ValueError(f"No server has model: {model}")
            
        # Get current server states
        server_states = {
            name: self.server_monitor.get_server_state(name)
            for name in capable_servers
        }
        
        # Filter out unhealthy servers
        healthy_servers = {
            name: state for name, state in server_states.items()
            if state['healthy']
        }
        
        if not healthy_servers:
            raise ValueError("No healthy servers available")
            
        # Select using strategy
        selected = self.strategy.select(
            task=task,
            model=model,
            server_states=healthy_servers,
            server_loads=self.server_loads
        )
        
        # Update load tracking
        self.server_loads[selected].current_requests += 1
        
        return selected
        
    def release_server(self, server_name: str):
        """Release server after task completion."""
        
        if server_name in self.server_loads:
            self.server_loads[server_name].current_requests -= 1
            
    def get_load_distribution(self) -> Dict:
        """
        Get current load distribution across servers.
        
        Returns:
            {
                'ollama01': {
                    'current_requests': 5,
                    'capacity': 10,
                    'utilization': 0.5
                },
                'ollama02': {
                    'current_requests': 8,
                    'capacity': 15,
                    'utilization': 0.53
                }
            }
        """
        
        distribution = {}
        
        for server_name, load in self.server_loads.items():
            distribution[server_name] = {
                'current_requests': load.current_requests,
                'capacity': load.total_capacity,
                'utilization': load.current_requests / load.total_capacity
            }
            
        return distribution
        
    def _get_capable_servers(self, model: str) -> List[str]:
        """Get servers that have the required model."""
        
        capable = []
        
        for server in self.config.servers:
            if model in server.models:
                capable.append(server.name)
                
        return capable
        
    def _estimate_capacity(self, server: ServerConfig) -> int:
        """Estimate server capacity based on available models."""
        
        # Heuristic: More models = higher capacity
        # Adjust based on actual server specs if known
        base_capacity = 10
        model_bonus = len(server.models) * 2
        
        return base_capacity + model_bonus


@dataclass
class ServerLoad:
    """Tracks load for a server."""
    
    server_name: str
    current_requests: int
    total_capacity: int
    available_models: List[str]
    
    @property
    def utilization(self) -> float:
        """Calculate current utilization (0.0 to 1.0)."""
        return self.current_requests / self.total_capacity if self.total_capacity > 0 else 0.0
        
    @property
    def available_capacity(self) -> int:
        """Calculate available capacity."""
        return max(0, self.total_capacity - self.current_requests)


class HybridLoadBalancingStrategy:
    """Hybrid load balancing strategy combining multiple approaches."""
    
    def select(self, task: Dict, model: str, server_states: Dict, 
               server_loads: Dict[str, ServerLoad]) -> str:
        """
        Select server using hybrid strategy.
        
        Strategy:
        1. Filter by capability (has required model)
        2. Filter by health (server is healthy)
        3. Consider current load (prefer less loaded)
        4. Consider task priority (high priority to faster server)
        5. Apply affinity rules (certain tasks prefer certain servers)
        """
        
        candidates = list(server_states.keys())
        
        # Apply affinity rules
        preferred = self._apply_affinity_rules(task, model, candidates)
        if preferred:
            candidates = preferred
            
        # Score each candidate
        scores = {}
        for server_name in candidates:
            score = self._calculate_score(
                server_name,
                server_states[server_name],
                server_loads[server_name],
                task
            )
            scores[server_name] = score
            
        # Select highest scoring server
        selected = max(scores.items(), key=lambda x: x[1])[0]
        
        return selected
        
    def _apply_affinity_rules(self, task: Dict, model: str, 
                             candidates: List[str]) -> List[str]:
        """
        Apply server affinity rules.
        
        Rules:
        - Large models (32b) prefer servers with more resources
        - Debugging tasks prefer faster servers
        - Parallel tasks distribute across servers
        """
        
        # Rule 1: Large models to ollama02 (assumed more powerful)
        if '32b' in model:
            if 'ollama02' in candidates:
                return ['ollama02']
                
        # Rule 2: Quick tasks can use any server
        if task.get('priority') == 'low':
            return candidates
            
        # Rule 3: High priority to fastest server
        if task.get('priority') == 'high':
            # Assume ollama02 is faster (adjust based on actual benchmarks)
            if 'ollama02' in candidates:
                return ['ollama02']
                
        return candidates
        
    def _calculate_score(self, server_name: str, server_state: Dict,
                        server_load: ServerLoad, task: Dict) -> float:
        """
        Calculate score for server selection.
        
        Higher score = better choice
        
        Factors:
        - Available capacity (40%)
        - Server health (30%)
        - Response time (20%)
        - Task affinity (10%)
        """
        
        score = 0.0
        
        # Factor 1: Available capacity (40%)
        capacity_score = server_load.available_capacity / server_load.total_capacity
        score += capacity_score * 0.4
        
        # Factor 2: Server health (30%)
        health_score = 1.0 if server_state['healthy'] else 0.0
        score += health_score * 0.3
        
        # Factor 3: Response time (20%)
        avg_response_time = server_state.get('avg_response_time', 5.0)
        response_score = 1.0 / (1.0 + avg_response_time / 10.0)  # Normalize
        score += response_score * 0.2
        
        # Factor 4: Task affinity (10%)
        affinity_score = self._calculate_affinity(server_name, task)
        score += affinity_score * 0.1
        
        return score
        
    def _calculate_affinity(self, server_name: str, task: Dict) -> float:
        """Calculate task-server affinity."""
        
        # Simple heuristic: prefer ollama02 for complex tasks
        if task.get('complexity') == 'high' and server_name == 'ollama02':
            return 1.0
        elif task.get('complexity') == 'low' and server_name == 'ollama01':
            return 1.0
        else:
            return 0.5
```

---

## Component 2: Parallel Execution Framework

### Purpose
Execute independent tasks simultaneously across multiple servers to maximize throughput.

### Parallelization Strategies

1. **Task-Level Parallelism**: Execute independent tasks in parallel
2. **Team-Level Parallelism**: Execute teams in parallel
3. **Phase-Level Parallelism**: Execute phases in parallel (when possible)
4. **Agent-Level Parallelism**: Multiple agents work simultaneously

### Implementation Details

#### File: `pipeline/orchestration/parallel_executor.py`

```python
class ParallelExecutor:
    """
    Executes tasks in parallel across multiple servers.
    
    Responsibilities:
    - Identify parallelizable tasks
    - Distribute tasks across servers
    - Coordinate parallel execution
    - Aggregate results
    """
    
    def __init__(self, load_balancer: LoadBalancer, logger):
        self.load_balancer = load_balancer
        self.logger = logger
        
        # Execution tracking
        self.active_tasks: Dict[str, TaskExecution] = {}
        
    def execute_parallel(self, tasks: List[Dict]) -> List[Dict]:
        """
        Execute tasks in parallel.
        
        Args:
            tasks: List of independent tasks
            
        Returns:
            List of results in same order as tasks
        """
        
        if not tasks:
            return []
            
        # Analyze dependencies
        dependency_graph = self._build_dependency_graph(tasks)
        
        # Determine execution order
        execution_plan = self._create_execution_plan(dependency_graph)
        
        # Execute in waves (tasks with no dependencies first)
        results = {}
        
        for wave in execution_plan:
            wave_results = self._execute_wave(wave, results)
            results.update(wave_results)
            
        # Return results in original order
        return [results[task['id']] for task in tasks]
        
    def _execute_wave(self, tasks: List[Dict], 
                     previous_results: Dict) -> Dict:
        """
        Execute a wave of independent tasks in parallel.
        
        Args:
            tasks: Tasks to execute (all independent)
            previous_results: Results from previous waves
            
        Returns:
            Dict mapping task_id to result
        """
        
        import concurrent.futures
        
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(tasks)) as executor:
            # Submit all tasks
            futures = {}
            
            for task in tasks:
                # Select server
                server = self.load_balancer.select_server(
                    task,
                    task['model']
                )
                
                # Submit task
                future = executor.submit(
                    self._execute_task,
                    task,
                    server,
                    previous_results
                )
                
                futures[task['id']] = future
                
            # Wait for all tasks to complete
            for task_id, future in futures.items():
                try:
                    result = future.result(timeout=3600)  # 1 hour timeout
                    results[task_id] = result
                except Exception as e:
                    self.logger.error(f"Task {task_id} failed: {e}")
                    results[task_id] = {'error': str(e)}
                    
        return results
        
    def _execute_task(self, task: Dict, server: str, 
                     context: Dict) -> Dict:
        """Execute a single task on specified server."""
        
        try:
            # Track execution
            execution = TaskExecution(
                task_id=task['id'],
                server=server,
                start_time=datetime.now()
            )
            self.active_tasks[task['id']] = execution
            
            # Execute task
            result = self._call_server(server, task, context)
            
            # Update execution
            execution.end_time = datetime.now()
            execution.success = True
            
            # Release server
            self.load_balancer.release_server(server)
            
            return result
            
        except Exception as e:
            # Update execution
            execution.end_time = datetime.now()
            execution.success = False
            execution.error = str(e)
            
            # Release server
            self.load_balancer.release_server(server)
            
            raise
            
    def _build_dependency_graph(self, tasks: List[Dict]) -> nx.DiGraph:
        """Build dependency graph for tasks."""
        
        graph = nx.DiGraph()
        
        # Add all tasks as nodes
        for task in tasks:
            graph.add_node(task['id'], task=task)
            
        # Add dependency edges
        for task in tasks:
            for dep_id in task.get('dependencies', []):
                graph.add_edge(dep_id, task['id'])
                
        return graph
        
    def _create_execution_plan(self, graph: nx.DiGraph) -> List[List[Dict]]:
        """
        Create execution plan with waves of independent tasks.
        
        Returns:
            List of waves, where each wave contains independent tasks
        """
        
        plan = []
        remaining = set(graph.nodes())
        
        while remaining:
            # Find tasks with no dependencies in remaining set
            wave = []
            for node in remaining:
                dependencies = set(graph.predecessors(node))
                if not dependencies.intersection(remaining):
                    wave.append(graph.nodes[node]['task'])
                    
            if not wave:
                # Circular dependency detected
                raise ValueError("Circular dependency detected in tasks")
                
            plan.append(wave)
            remaining -= {task['id'] for task in wave}
            
        return plan


@dataclass
class TaskExecution:
    """Tracks task execution."""
    
    task_id: str
    server: str
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    error: Optional[str] = None
    
    @property
    def duration(self) -> float:
        """Calculate execution duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
```

---

## Component 3: Server Monitor

### Purpose
Monitor server health, capacity, and performance in real-time.

### Monitoring Metrics

1. **Health Metrics**
   - Server availability
   - Response time
   - Error rate
   - Uptime

2. **Capacity Metrics**
   - Current load
   - Available capacity
   - Queue length
   - Resource usage

3. **Performance Metrics**
   - Average response time
   - Throughput (requests/sec)
   - Success rate
   - Model performance

### Implementation Details

#### File: `pipeline/orchestration/server_monitor.py`

```python
class ServerMonitor:
    """
    Monitors server health and performance.
    
    Responsibilities:
    - Check server availability
    - Track performance metrics
    - Detect anomalies
    - Alert on issues
    """
    
    def __init__(self, servers: List[ServerConfig], logger):
        self.servers = {s.name: s for s in servers}
        self.logger = logger
        
        # Metrics storage
        self.metrics: Dict[str, ServerMetrics] = {}
        
        # Initialize metrics
        for server in servers:
            self.metrics[server.name] = ServerMetrics(
                server_name=server.name,
                healthy=True,
                last_check=datetime.now()
            )
            
        # Start monitoring thread
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def get_server_state(self, server_name: str) -> Dict:
        """
        Get current server state.
        
        Returns:
            {
                'healthy': True/False,
                'available': True/False,
                'current_load': 5,
                'avg_response_time': 2.5,
                'error_rate': 0.02,
                'uptime': 0.99
            }
        """
        
        metrics = self.metrics.get(server_name)
        if not metrics:
            return {'healthy': False, 'available': False}
            
        return {
            'healthy': metrics.healthy,
            'available': metrics.available,
            'current_load': metrics.current_load,
            'avg_response_time': metrics.avg_response_time,
            'error_rate': metrics.error_rate,
            'uptime': metrics.uptime
        }
        
    def record_request(self, server_name: str, duration: float, 
                      success: bool):
        """Record a request for metrics."""
        
        metrics = self.metrics.get(server_name)
        if not metrics:
            return
            
        metrics.total_requests += 1
        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
            
        # Update average response time
        metrics.total_response_time += duration
        metrics.avg_response_time = (
            metrics.total_response_time / metrics.total_requests
        )
        
        # Update error rate
        metrics.error_rate = (
            metrics.failed_requests / metrics.total_requests
        )
        
    def _monitor_loop(self):
        """Background monitoring loop."""
        
        while self.monitoring:
            for server_name in self.servers.keys():
                self._check_server_health(server_name)
                
            time.sleep(30)  # Check every 30 seconds
            
    def _check_server_health(self, server_name: str):
        """Check if server is healthy."""
        
        server = self.servers[server_name]
        metrics = self.metrics[server_name]
        
        try:
            # Ping server
            response = requests.get(
                f"{server.base_url}/api/tags",
                timeout=5
            )
            
            if response.status_code == 200:
                metrics.healthy = True
                metrics.available = True
                metrics.last_check = datetime.now()
                metrics.consecutive_failures = 0
            else:
                metrics.consecutive_failures += 1
                if metrics.consecutive_failures >= 3:
                    metrics.healthy = False
                    self.logger.warning(f"Server {server_name} unhealthy")
                    
        except Exception as e:
            metrics.consecutive_failures += 1
            if metrics.consecutive_failures >= 3:
                metrics.healthy = False
                metrics.available = False
                self.logger.error(f"Server {server_name} unavailable: {e}")


@dataclass
class ServerMetrics:
    """Metrics for a server."""
    
    server_name: str
    healthy: bool
    last_check: datetime
    available: bool = True
    current_load: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    avg_response_time: float = 0.0
    error_rate: float = 0.0
    uptime: float = 1.0
    consecutive_failures: int = 0
```

---

## Component 4: Failover Handler

### Purpose
Handle server failures gracefully by rerouting tasks to healthy servers.

### Failover Strategies

1. **Immediate Retry**: Retry on different server immediately
2. **Graceful Degradation**: Continue with reduced capacity
3. **Queue and Retry**: Queue tasks and retry when server recovers
4. **Circuit Breaker**: Temporarily disable failing server

### Implementation Details

#### File: `pipeline/orchestration/failover.py`

```python
class FailoverHandler:
    """
    Handles server failures and failover.
    
    Responsibilities:
    - Detect failures
    - Reroute tasks
    - Implement retry logic
    - Manage circuit breakers
    """
    
    def __init__(self, load_balancer: LoadBalancer, 
                 server_monitor: ServerMonitor, logger):
        self.load_balancer = load_balancer
        self.server_monitor = server_monitor
        self.logger = logger
        
        # Circuit breakers
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
    def execute_with_failover(self, task: Dict, model: str, 
                             max_retries: int = 3) -> Dict:
        """
        Execute task with automatic failover.
        
        Args:
            task: Task to execute
            model: Required model
            max_retries: Maximum retry attempts
            
        Returns:
            Task result
        """
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Select server
                server = self.load_balancer.select_server(task, model)
                
                # Check circuit breaker
                if not self._check_circuit_breaker(server):
                    self.logger.warning(f"Circuit breaker open for {server}")
                    continue
                    
                # Execute task
                result = self._execute_on_server(task, server, model)
                
                # Success - reset circuit breaker
                self._record_success(server)
                
                return result
                
            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"Task failed on attempt {attempt + 1}: {e}"
                )
                
                # Record failure
                self._record_failure(server)
                
                # Release server
                self.load_balancer.release_server(server)
                
                # Wait before retry
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        # All retries failed
        raise Exception(f"Task failed after {max_retries} attempts: {last_error}")
        
    def _check_circuit_breaker(self, server: str) -> bool:
        """Check if circuit breaker allows requests."""
        
        if server not in self.circuit_breakers:
            self.circuit_breakers[server] = CircuitBreaker(server)
            
        return self.circuit_breakers[server].allow_request()
        
    def _record_success(self, server: str):
        """Record successful request."""
        
        if server in self.circuit_breakers:
            self.circuit_breakers[server].record_success()
            
    def _record_failure(self, server: str):
        """Record failed request."""
        
        if server not in self.circuit_breakers:
            self.circuit_breakers[server] = CircuitBreaker(server)
            
        self.circuit_breakers[server].record_failure()


class CircuitBreaker:
    """Circuit breaker for server failures."""
    
    def __init__(self, server_name: str, 
                 failure_threshold: int = 5,
                 timeout: int = 60):
        self.server_name = server_name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        
        self.state = 'closed'  # closed|open|half_open
        self.failure_count = 0
        self.last_failure_time = None
        
    def allow_request(self) -> bool:
        """Check if request is allowed."""
        
        if self.state == 'closed':
            return True
            
        if self.state == 'open':
            # Check if timeout has passed
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.timeout:
                    self.state = 'half_open'
                    return True
            return False
            
        if self.state == 'half_open':
            return True
            
        return False
        
    def record_success(self):
        """Record successful request."""
        
        if self.state == 'half_open':
            self.state = 'closed'
            self.failure_count = 0
            
    def record_failure(self):
        """Record failed request."""
        
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'open'
```

---

## Integration Strategy

### Phase 5A: Core Orchestration (Week 1)
1. Implement LoadBalancer
2. Implement ServerMonitor
3. Basic load distribution
4. Testing with both servers

### Phase 5B: Parallel Execution (Week 2)
1. Implement ParallelExecutor
2. Dependency analysis
3. Wave-based execution
4. Performance testing

### Phase 5C: Failover & Optimization (Week 3)
1. Implement FailoverHandler
2. Circuit breakers
3. Performance optimization
4. Complete documentation

---

## Success Criteria

### Functional Requirements
- ✅ Both servers actively used
- ✅ Load balanced effectively
- ✅ Parallel execution working
- ✅ Failover handling operational
- ✅ Server monitoring active

### Performance Requirements
- ✅ 2x throughput improvement
- ✅ 80%+ utilization on both servers
- ✅ < 5% load imbalance
- ✅ < 1 second failover time
- ✅ 99%+ availability

### Quality Requirements
- ✅ 90%+ code coverage
- ✅ All tests passing
- ✅ Documentation complete
- ✅ No critical bugs

---

## Next Phase

Upon completion of Phase 5, proceed to:
**[PHASE_6_INTEGRATION.md](PHASE_6_INTEGRATION.md)** - Integration & Testing

---

**Phase Owner:** Development Team  
**Reviewers:** Technical Lead, DevOps Engineer  
**Approval Required:** Yes  
**Estimated Effort:** 2-3 weeks (1 developer full-time)
</file_path>