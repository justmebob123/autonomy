"""
Specialist Models

Each specialist is an expert in a specific domain:
- CodingSpecialist: Complex code implementation (32b)
- ReasoningSpecialist: Strategic analysis (32b)
- AnalysisSpecialist: Quick checks (14b)
- FunctionGemmaMediator: Tool call interpretation
"""

from .coding_specialist import (
    CodingSpecialist,
    CodingTask,
    create_coding_specialist
)

from .reasoning_specialist import (
    ReasoningSpecialist,
    ReasoningTask,
    ReasoningType,
    create_reasoning_specialist
)

from .analysis_specialist import (
    AnalysisSpecialist,
    AnalysisTask,
    AnalysisType,
    create_analysis_specialist
)

from .function_gemma_mediator import (
    FunctionGemmaMediator,
    InterpretationRequest,
    create_function_gemma_mediator
)

__all__ = [
    # Coding Specialist
    'CodingSpecialist',
    'CodingTask',
    'create_coding_specialist',
    
    # Reasoning Specialist
    'ReasoningSpecialist',
    'ReasoningTask',
    'ReasoningType',
    'create_reasoning_specialist',
    
    # Analysis Specialist
    'AnalysisSpecialist',
    'AnalysisTask',
    'AnalysisType',
    'create_analysis_specialist',
    
    # FunctionGemma Mediator
    'FunctionGemmaMediator',
    'InterpretationRequest',
    'create_function_gemma_mediator',
]