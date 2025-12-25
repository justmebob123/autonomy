"""
Team Orchestrator - Coordinates multiple specialists in parallel

This module orchestrates teams of specialist agents working in parallel
across multiple Ollama servers to solve complex problems efficiently.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from pathlib import Path
from datetime import datetime

from pipeline.client import OllamaClient
from pipeline.specialist_agents import SpecialistTeam
from .prompts.team_orchestrator import get_team_orchestrator_prompt
from pipeline.conversation_thread import ConversationThread


@dataclass
class Task:
    """Represents a single task in the orchestration"""
    task_id: str
    specialist: str
    server: str
    input_data: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    timeout: int = None  # UNLIMITED - wait forever
    priority: str = "medium"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Get task duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def is_complete(self) -> bool:
        """Check if task is complete"""
        return self.result is not None or self.error is not None


@dataclass
class ExecutionWave:
    """Represents a wave of parallel tasks"""
    wave_number: int
    tasks: List[Task]
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Get wave duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def is_complete(self) -> bool:
        """Check if all tasks in wave are complete"""
        return all(task.is_complete for task in self.tasks)


@dataclass
class OrchestrationPlan:
    """Represents a complete orchestration plan"""
    problem: str
    waves: List[ExecutionWave]
    synthesis_strategy: str
    success_criteria: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class TeamOrchestrator:
    """
    Orchestrates teams of specialist agents working in parallel.
    
    Features:
    - Parallel specialist execution
    - Multi-server load balancing
    - Dependency management
    - Failure handling and retries
    - Result synthesis
    """
    
    def __init__(
        self,
        client: OllamaClient,
        specialist_team: SpecialistTeam,
        logger: logging.Logger,
        max_workers: int = 4
    ):
        """
        Initialize team orchestrator.
        
        Args:
            client: Ollama client for AI interactions
            specialist_team: Team of specialist agents
            logger: Logger instance
            max_workers: Maximum parallel workers
        """
        self.client = client
        self.specialist_team = specialist_team
        self.logger = logger
        self.max_workers = max_workers
        
        # Available servers
        self.servers = ["ollama01.thiscluster.net", "ollama02.thiscluster.net"]
        
        # Server load tracking
        self.server_load = defaultdict(int)
        
        # Execution statistics
        self.stats = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'total_duration': 0,
            'parallel_efficiency': 0
        }
    
    def create_orchestration_plan(
        self,
        problem: str,
        context: Optional[Dict[str, Any]] = None
    ) -> OrchestrationPlan:
        """
        Create an orchestration plan for a problem.
        
        Args:
            problem: Description of the problem
            context: Optional additional context
            
        Returns:
            OrchestrationPlan with execution waves
        """
        self.logger.info("🎭 Creating orchestration plan...")
        
        # Get available specialists
        available_specialists = list(self.specialist_team.specialists.keys())
        
        # Generate orchestration prompt
        prompt = get_team_orchestrator_prompt(
            problem=problem,
            available_specialists=available_specialists,
            available_servers=self.servers,
            context=context
        )
        
        # Get orchestration plan from AI
        response = self.client.generate(
            prompt=prompt,
            model="qwen2.5:14b",  # Use capable model for planning
            server="ollama01.thiscluster.net",
            timeout=None  # UNLIMITED
        )
        
        # Parse response to extract plan
        plan_data = self._parse_orchestration_response(response)
        
        # Build execution waves
        waves = self._build_execution_waves(plan_data)
        
        plan = OrchestrationPlan(
            problem=problem,
            waves=waves,
            synthesis_strategy=plan_data.get('synthesis_strategy', 'merge_all'),
            success_criteria=plan_data.get('success_criteria', 'all_tasks_complete'),
            metadata=plan_data.get('metadata', {})
        )
        
        self.logger.info(f"📋 Plan created: {len(waves)} waves, {sum(len(w.tasks) for w in waves)} tasks")
        
        return plan
    
    def execute_plan(
        self,
        plan: OrchestrationPlan,
        thread: Optional[ConversationThread] = None
    ) -> Dict[str, Any]:
        """
        Execute an orchestration plan.
        
        Args:
            plan: OrchestrationPlan to execute
            thread: Optional conversation thread for context
            
        Returns:
            Dictionary with execution results
        """
        self.logger.info("🚀 Executing orchestration plan...")
        
        start_time = time.time()
        all_results = {}
        
        # Execute each wave sequentially
        for wave in plan.waves:
            self.logger.info(f"🌊 Wave {wave.wave_number}: {len(wave.tasks)} tasks")
            
            wave.start_time = time.time()
            
            # Execute tasks in wave in parallel
            wave_results = self._execute_wave(wave, thread)
            
            wave.end_time = time.time()
            
            # Store results
            all_results[f"wave_{wave.wave_number}"] = wave_results
            
            # Check if wave succeeded
            failed_tasks = [t for t in wave.tasks if t.error]
            if failed_tasks:
                self.logger.warning(f"⚠️  Wave {wave.wave_number}: {len(failed_tasks)} tasks failed")
                for task in failed_tasks:
                    self.logger.warning(f"   - {task.task_id}: {task.error}")
            
            self.logger.info(f"✅ Wave {wave.wave_number} complete in {wave.duration:.1f}s")
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Synthesize results
        self.logger.info("🔄 Synthesizing results...")
        synthesis = self._synthesize_results(plan, all_results)
        
        # Update statistics
        self._update_statistics(plan, total_duration)
        
        return {
            'success': synthesis.get('success', True),
            'synthesis': synthesis,
            'wave_results': all_results,
            'statistics': self.stats.copy(),
            'duration': total_duration
        }
    
    def _execute_wave(
        self,
        wave: ExecutionWave,
        thread: Optional[ConversationThread] = None
    ) -> Dict[str, Any]:
        """
        Execute all tasks in a wave in parallel.
        
        Args:
            wave: ExecutionWave to execute
            thread: Optional conversation thread
            
        Returns:
            Dictionary mapping task_id to result
        """
        results = {}
        
        # Use ThreadPoolExecutor for parallel execution
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self._execute_task, task, thread): task
                for task in wave.tasks
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    task.result = result
                    results[task.task_id] = result
                    self.logger.info(f"   ✓ {task.task_id} complete ({task.duration:.1f}s)")
                except Exception as e:
                    task.error = str(e)
                    results[task.task_id] = {'error': str(e)}
                    self.logger.error(f"   ✗ {task.task_id} failed: {e}")
        
        return results
    
    def _execute_task(
        self,
        task: Task,
        thread: Optional[ConversationThread] = None
    ) -> Dict[str, Any]:
        """
        Execute a single task.
        
        Args:
            task: Task to execute
            thread: Optional conversation thread
            
        Returns:
            Task result
        """
        task.start_time = time.time()
        
        try:
            # Update server load
            self.server_load[task.server] += 1
            
            # Execute specialist consultation
            result = self.specialist_team.consult_specialist(
                specialist_name=task.specialist,
                thread=thread,
                tools=task.input_data.get('tools', []),
                context=task.input_data.get('context', {})
            )
            
            task.end_time = time.time()
            
            return result
            
        except Exception as e:
            task.end_time = time.time()
            raise
        finally:
            # Update server load
            self.server_load[task.server] -= 1
    
    def _parse_orchestration_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse AI response to extract orchestration plan.
        
        Args:
            response: AI response
            
        Returns:
            Parsed plan data
        """
        content = response.get('message', {}).get('content', '')
        
        # Try to extract JSON from response
        import json
        import re
        
        # Look for JSON block
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to parse entire content as JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Fallback: Create simple plan
        self.logger.warning("Could not parse orchestration plan, using fallback")
        return {
            'execution_waves': [
                {
                    'wave_number': 1,
                    'tasks': [
                        {
                            'task_id': 'fallback_task',
                            'specialist': 'Root Cause Analyst',
                            'server': 'ollama01.thiscluster.net',
                            'input': {},
                            'timeout': None  # UNLIMITED
                        }
                    ]
                }
            ],
            'synthesis_strategy': 'use_first_result',
            'success_criteria': 'any_task_complete'
        }
    
    def _build_execution_waves(self, plan_data: Dict[str, Any]) -> List[ExecutionWave]:
        """
        Build execution waves from plan data.
        
        Args:
            plan_data: Parsed plan data
            
        Returns:
            List of ExecutionWave objects
        """
        waves = []
        
        for wave_data in plan_data.get('execution_waves', []):
            tasks = []
            
            for task_data in wave_data.get('tasks', []):
                task = Task(
                    task_id=task_data.get('task_id', f"task_{len(tasks)}"),
                    specialist=task_data.get('specialist', 'Root Cause Analyst'),
                    server=task_data.get('server', 'ollama01.thiscluster.net'),
                    input_data=task_data.get('input', {}),
                    dependencies=task_data.get('dependencies', []),
                    timeout=task_data.get('timeout', None),  # UNLIMITED by default
                    priority=task_data.get('priority', 'medium')
                )
                tasks.append(task)
            
            wave = ExecutionWave(
                wave_number=wave_data.get('wave_number', len(waves) + 1),
                tasks=tasks
            )
            waves.append(wave)
        
        return waves
    
    def _synthesize_results(
        self,
        plan: OrchestrationPlan,
        all_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synthesize results from all waves.
        
        Args:
            plan: Original orchestration plan
            all_results: Results from all waves
            
        Returns:
            Synthesized results
        """
        strategy = plan.synthesis_strategy
        
        if strategy == 'merge_all':
            # Merge all results into single dictionary
            merged = {}
            for wave_results in all_results.values():
                merged.update(wave_results)
            return {'success': True, 'merged_results': merged}
        
        elif strategy == 'use_first_result':
            # Use first successful result
            for wave_results in all_results.values():
                for result in wave_results.values():
                    if not result.get('error'):
                        return {'success': True, 'result': result}
            return {'success': False, 'error': 'No successful results'}
        
        elif strategy == 'consensus':
            # Build consensus from multiple results
            findings = []
            for wave_results in all_results.values():
                for result in wave_results.values():
                    if result.get('findings'):
                        findings.extend(result['findings'])
            
            # Count agreement
            finding_counts = defaultdict(int)
            for finding in findings:
                finding_counts[finding] += 1
            
            # Return findings with majority agreement
            consensus = [f for f, count in finding_counts.items() if count >= 2]
            return {'success': True, 'consensus': consensus}
        
        else:
            # Default: return all results
            return {'success': True, 'all_results': all_results}
    
    def _update_statistics(self, plan: OrchestrationPlan, total_duration: float):
        """Update execution statistics"""
        total_tasks = sum(len(wave.tasks) for wave in plan.waves)
        successful_tasks = sum(
            sum(1 for task in wave.tasks if task.result and not task.error)
            for wave in plan.waves
        )
        failed_tasks = total_tasks - successful_tasks
        
        # Calculate parallel efficiency
        sequential_duration = sum(
            sum(task.duration or 0 for task in wave.tasks)
            for wave in plan.waves
        )
        parallel_efficiency = (sequential_duration / total_duration) if total_duration > 0 else 0
        
        self.stats.update({
            'total_tasks': self.stats['total_tasks'] + total_tasks,
            'successful_tasks': self.stats['successful_tasks'] + successful_tasks,
            'failed_tasks': self.stats['failed_tasks'] + failed_tasks,
            'total_duration': self.stats['total_duration'] + total_duration,
            'parallel_efficiency': parallel_efficiency
        })
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get execution statistics"""
        return self.stats.copy()
    
    def reset_statistics(self):
        """Reset execution statistics"""
        self.stats = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'total_duration': 0,
            'parallel_efficiency': 0
        }
    
    # ========================================================================
    # SELF-IMPROVEMENT VALIDATION METHODS
    # ========================================================================
    
