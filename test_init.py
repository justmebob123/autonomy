#!/usr/bin/env python3
"""
Test script to identify where object.__init__() error occurs
"""
import sys
import traceback
from pathlib import Path

def test_step(step_name, func):
    """Test a step and report results"""
    print(f"\n{'='*70}")
    print(f"Testing: {step_name}")
    print('='*70)
    try:
        result = func()
        print(f"✓ SUCCESS: {step_name}")
        return result
    except Exception as e:
        print(f"✗ FAILED: {step_name}")
        print(f"Error: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)

# Step 1: Import basic modules
def step1():
    from dataclasses import dataclass, field
    from pathlib import Path
    from typing import Dict, List, Optional
    return "Basic imports OK"

test_step("Step 1: Basic imports", step1)

# Step 2: Import config module
def step2():
    from pipeline.config import ServerConfig, PipelineConfig
    return "Config imports OK"

test_step("Step 2: Import config", step2)

# Step 3: Create ServerConfig
def step3():
    from pipeline.config import ServerConfig
    server = ServerConfig(
        name="test",
        host="localhost"
    )
    return f"ServerConfig created: {server.name}"

test_step("Step 3: Create ServerConfig", step3)

# Step 4: Create PipelineConfig with defaults
def step4():
    from pipeline.config import PipelineConfig
    config = PipelineConfig()
    return f"PipelineConfig created with {len(config.servers)} servers"

test_step("Step 4: Create PipelineConfig (defaults)", step4)

# Step 5: Create PipelineConfig with project_dir
def step5():
    from pipeline.config import PipelineConfig
    config = PipelineConfig(project_dir=Path("/tmp/test"))
    return f"PipelineConfig created with project_dir={config.project_dir}"

test_step("Step 5: Create PipelineConfig (with project_dir)", step5)

# Step 6: Import state manager
def step6():
    from pipeline.state.manager import StateManager, PipelineState
    return "StateManager imports OK"

test_step("Step 6: Import StateManager", step6)

# Step 7: Create PipelineState
def step7():
    from pipeline.state.manager import PipelineState
    state = PipelineState()
    return f"PipelineState created: version={state.version}"

test_step("Step 7: Create PipelineState", step7)

# Step 8: Create StateManager
def step8():
    from pipeline.state.manager import StateManager
    manager = StateManager(Path("/tmp/test"))
    return f"StateManager created"

test_step("Step 8: Create StateManager", step8)

# Step 9: Import client
def step9():
    from pipeline.client import OllamaClient
    return "OllamaClient import OK"

test_step("Step 9: Import OllamaClient", step9)

# Step 10: Create OllamaClient
def step10():
    from pipeline.client import OllamaClient
    from pipeline.config import PipelineConfig
    config = PipelineConfig()
    client = OllamaClient(config)
    return f"OllamaClient created"

test_step("Step 10: Create OllamaClient", step10)

# Step 11: Import BasePhase
def step11():
    from pipeline.phases.base import BasePhase
    return "BasePhase import OK"

test_step("Step 11: Import BasePhase", step11)

# Step 12: Import a concrete phase
def step12():
    from pipeline.phases.planning import PlanningPhase
    return "PlanningPhase import OK"

test_step("Step 12: Import PlanningPhase", step12)

# Step 13: Create a phase instance
def step13():
    from pipeline.phases.planning import PlanningPhase
    from pipeline.client import OllamaClient
    from pipeline.config import PipelineConfig
    
    config = PipelineConfig(project_dir=Path("/tmp/test"))
    client = OllamaClient(config)
    phase = PlanningPhase(config, client)
    return f"PlanningPhase created: {phase.phase_name}"

test_step("Step 13: Create PlanningPhase instance", step13)

# Step 14: Import Pipeline
def step14():
    from pipeline.pipeline import Pipeline
    return "Pipeline import OK"

test_step("Step 14: Import Pipeline", step14)

# Step 15: Create Pipeline
def step15():
    from pipeline.pipeline import Pipeline
    from pipeline.config import PipelineConfig
    
    config = PipelineConfig(project_dir=Path("/tmp/test"))
    pipeline = Pipeline(config)
    return f"Pipeline created"

test_step("Step 15: Create Pipeline instance", step15)

print("\n" + "="*70)
print("✓ ALL TESTS PASSED!")
print("="*70)