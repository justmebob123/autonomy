"""
Refactoring Phase

Analyzes and refactors code architecture to eliminate duplicates, resolve conflicts,
and improve code organization based on MASTER_PLAN.md changes.
"""

from datetime import datetime
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import json

from .base import BasePhase, PhaseResult
from ..state.manager import PipelineState, TaskState, TaskStatus
from ..state.priority import TaskPriority
from ..tools import get_tools_for_phase
from ..prompts import SYSTEM_PROMPTS, get_refactoring_prompt
from ..handlers import ToolCallHandler
from .loop_detection_mixin import LoopDetectionMixin


class RefactoringPhase(BasePhase, LoopDetectionMixin):
    """
    Refactoring phase that analyzes and improves code architecture.
    
    Responsibilities:
    - Detect duplicate/similar implementations
    - Compare and merge conflicting files
    - Extract and consolidate features
    - Analyze MASTER_PLAN consistency
    - Generate refactoring plans
    - Execute safe refactoring operations
    - Update REFACTORING_STATE.md
    
    Integration Points:
    - Planning → Refactoring (architecture changes detected)
    - Coding → Refactoring (duplicates detected)
    - QA → Refactoring (conflicts detected)
    - Investigation → Refactoring (recommendations)
    - Project Planning → Refactoring (strategic refactoring)
    - Refactoring → Coding (new implementation needed)
    - Refactoring → QA (verification needed)
    """
    
    phase_name = "refactoring"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_loop_detection()
        
        # ARCHITECTURE CONFIG - Load project architecture configuration
        from ..architecture_parser import get_architecture_config
        self.architecture_config = get_architecture_config(self.project_dir)
        self.logger.info(f"  📐 Architecture config loaded: {len(self.architecture_config.library_dirs)} library dirs")
        
        # REFACTORING ANALYSIS CAPABILITIES - Direct integration
        from ..analysis.file_refactoring import (
            DuplicateDetector,
            FileComparator,
            FeatureExtractor,
            ArchitectureAnalyzer
        )
        from ..analysis.dead_code import DeadCodeDetector
        from ..analysis.integration_conflicts import ConflictDetector
        
        self.duplicate_detector = DuplicateDetector(str(self.project_dir), self.logger)
        self.file_comparator = FileComparator(str(self.project_dir), self.logger)
        self.feature_extractor = FeatureExtractor(str(self.project_dir), self.logger)
        self.architecture_analyzer = ArchitectureAnalyzer(str(self.project_dir), self.logger)
        self.dead_code_detector = DeadCodeDetector(str(self.project_dir), self.logger, self.architecture_config)
        self.conflict_detector = ConflictDetector(str(self.project_dir), self.logger)
        
        self.logger.info("  🔧 Refactoring phase initialized with analysis capabilities")
    
    def execute(self, state: PipelineState, 
                refactoring_type: str = None,
                target_files: List[str] = None,
                **kwargs) -> PhaseResult:
        """Execute the refactoring phase"""
        
        # IPC INTEGRATION: Initialize documents on first run
        self.initialize_ipc_documents()
        
        # IPC INTEGRATION: Read refactoring requests from REFACTORING_READ.md
        refactoring_requests = self.read_own_tasks()
        if refactoring_requests:
            self.logger.info(f"  📋 Read refactoring requests from REFACTORING_READ.md")
        
        # IPC INTEGRATION: Read strategic documents for context
        strategic_docs = self.read_strategic_docs()
        if strategic_docs:
            self.logger.debug(f"  📚 Loaded {len(strategic_docs)} strategic documents")
        
        # IPC INTEGRATION: Read other phases' outputs
        phase_outputs = self._read_relevant_phase_outputs()
        
        # Determine refactoring type
        if refactoring_type is None:
            refactoring_type = self._determine_refactoring_type(
                state, refactoring_requests, phase_outputs
            )
        
        self.logger.info(f"  🔧 Executing refactoring type: {refactoring_type}")
        
        # Execute appropriate refactoring workflow
        if refactoring_type == "duplicate_detection":
            return self._handle_duplicate_detection(state, target_files)
        elif refactoring_type == "conflict_resolution":
            return self._handle_conflict_resolution(state, target_files)
        elif refactoring_type == "architecture_consistency":
            return self._handle_architecture_consistency(state)
        elif refactoring_type == "feature_extraction":
            return self._handle_feature_extraction(state, target_files)
        elif refactoring_type == "comprehensive":
            return self._handle_comprehensive_refactoring(state)
        else:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Unknown refactoring type: {refactoring_type}"
            )
    
    def _determine_refactoring_type(self, state: PipelineState,
                                   refactoring_requests: str,
                                   phase_outputs: Dict) -> str:
        """Determine what type of refactoring is needed"""
        
        # Check for explicit requests in REFACTORING_READ.md
        if refactoring_requests:
            if "duplicate" in refactoring_requests.lower():
                return "duplicate_detection"
            elif "conflict" in refactoring_requests.lower():
                return "conflict_resolution"
            elif "architecture" in refactoring_requests.lower():
                return "architecture_consistency"
            elif "extract" in refactoring_requests.lower():
                return "feature_extraction"
        
        # Check phase outputs for recommendations
        if phase_outputs:
            qa_output = phase_outputs.get("qa", "")
            if "duplicate" in qa_output.lower():
                return "duplicate_detection"
            if "conflict" in qa_output.lower():
                return "conflict_resolution"
            
            investigation_output = phase_outputs.get("investigation", "")
            if "refactor" in investigation_output.lower():
                return "comprehensive"
        
        # Default to comprehensive analysis
        return "comprehensive"
    
    def _handle_duplicate_detection(self, state: PipelineState,
                                   target_files: List[str] = None) -> PhaseResult:
        """Detect and handle duplicate implementations"""
        
        self.logger.info("  🔍 Detecting duplicate implementations...")
        
        # Get all Python files if no targets specified
        if not target_files:
            target_files = self._get_all_python_files()
        
        # Build context for LLM
        context = self._build_duplicate_detection_context(target_files)
        
        # Get tools for this phase
        tools = get_tools_for_phase("refactoring")
        
        # Build prompt
        prompt = get_refactoring_prompt(
            refactoring_type="duplicate_detection",
            context=context,
            target_files=target_files
        )
        
        # Call LLM with tools
        result = self.call_llm_with_tools(
            system_prompt=SYSTEM_PROMPTS["refactoring"],
            user_prompt=prompt,
            tools=tools,
            state=state
        )
        
        if not result["success"]:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Duplicate detection failed: {result.get('error', 'Unknown error')}"
            )
        
        # Update REFACTORING_WRITE.md with results
        self._write_refactoring_results(
            refactoring_type="duplicate_detection",
            results=result.get("tool_results", []),
            recommendations=result.get("response", "")
        )
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message="Duplicate detection completed",
            next_phase="coding"  # May need new implementation
        )
    
    def _handle_conflict_resolution(self, state: PipelineState,
                                   target_files: List[str] = None) -> PhaseResult:
        """Detect and resolve conflicts between files"""
        
        self.logger.info("  ⚔️ Resolving file conflicts...")
        
        # Build context
        context = self._build_conflict_resolution_context(target_files)
        
        # Get tools
        tools = get_tools_for_phase("refactoring")
        
        # Build prompt
        prompt = get_refactoring_prompt(
            refactoring_type="conflict_resolution",
            context=context,
            target_files=target_files
        )
        
        # Call LLM
        result = self.call_llm_with_tools(
            system_prompt=SYSTEM_PROMPTS["refactoring"],
            user_prompt=prompt,
            tools=tools,
            state=state
        )
        
        if not result["success"]:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Conflict resolution failed: {result.get('error', 'Unknown error')}"
            )
        
        # Update REFACTORING_WRITE.md
        self._write_refactoring_results(
            refactoring_type="conflict_resolution",
            results=result.get("tool_results", []),
            recommendations=result.get("response", "")
        )
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message="Conflict resolution completed",
            next_phase="qa"  # Need verification
        )
    
    def _handle_architecture_consistency(self, state: PipelineState) -> PhaseResult:
        """Check and fix architecture consistency with MASTER_PLAN"""
        
        self.logger.info("  📐 Checking architecture consistency...")
        
        # Build context
        context = self._build_architecture_context()
        
        # Get tools
        tools = get_tools_for_phase("refactoring")
        
        # Build prompt
        prompt = get_refactoring_prompt(
            refactoring_type="architecture_consistency",
            context=context
        )
        
        # Call LLM
        result = self.call_llm_with_tools(
            system_prompt=SYSTEM_PROMPTS["refactoring"],
            user_prompt=prompt,
            tools=tools,
            state=state
        )
        
        if not result["success"]:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Architecture consistency check failed: {result.get('error', 'Unknown error')}"
            )
        
        # Update REFACTORING_WRITE.md
        self._write_refactoring_results(
            refactoring_type="architecture_consistency",
            results=result.get("tool_results", []),
            recommendations=result.get("response", "")
        )
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message="Architecture consistency check completed",
            next_phase="planning"  # May need new tasks
        )
    
    def _handle_feature_extraction(self, state: PipelineState,
                                  target_files: List[str] = None) -> PhaseResult:
        """Extract features from files for consolidation"""
        
        self.logger.info("  📦 Extracting features for consolidation...")
        
        # Build context
        context = self._build_feature_extraction_context(target_files)
        
        # Get tools
        tools = get_tools_for_phase("refactoring")
        
        # Build prompt
        prompt = get_refactoring_prompt(
            refactoring_type="feature_extraction",
            context=context,
            target_files=target_files
        )
        
        # Call LLM
        result = self.call_llm_with_tools(
            system_prompt=SYSTEM_PROMPTS["refactoring"],
            user_prompt=prompt,
            tools=tools,
            state=state
        )
        
        if not result["success"]:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Feature extraction failed: {result.get('error', 'Unknown error')}"
            )
        
        # Update REFACTORING_WRITE.md
        self._write_refactoring_results(
            refactoring_type="feature_extraction",
            results=result.get("tool_results", []),
            recommendations=result.get("response", "")
        )
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message="Feature extraction completed",
            next_phase="coding"  # Need new consolidated implementation
        )
    
    def _handle_comprehensive_refactoring(self, state: PipelineState) -> PhaseResult:
        """Perform comprehensive refactoring analysis"""
        
        self.logger.info("  🔬 Performing comprehensive refactoring analysis...")
        
        # Build comprehensive context
        context = self._build_comprehensive_context()
        
        # Get tools
        tools = get_tools_for_phase("refactoring")
        
        # Build prompt
        prompt = get_refactoring_prompt(
            refactoring_type="comprehensive",
            context=context
        )
        
        # Call LLM
        result = self.call_llm_with_tools(
            system_prompt=SYSTEM_PROMPTS["refactoring"],
            user_prompt=prompt,
            tools=tools,
            state=state
        )
        
        if not result["success"]:
            return PhaseResult(
                success=False,
                phase=self.phase_name,
                message=f"Comprehensive refactoring failed: {result.get('error', 'Unknown error')}"
            )
        
        # Update REFACTORING_WRITE.md
        self._write_refactoring_results(
            refactoring_type="comprehensive",
            results=result.get("tool_results", []),
            recommendations=result.get("response", "")
        )
        
        # Determine next phase based on recommendations
        next_phase = self._determine_next_phase(result.get("response", ""))
        
        return PhaseResult(
            success=True,
            phase=self.phase_name,
            message="Comprehensive refactoring analysis completed",
            next_phase=next_phase
        )
    
    def _get_all_python_files(self) -> List[str]:
        """Get all Python files in the project"""
        python_files = []
        for path in Path(self.project_dir).rglob("*.py"):
            if ".venv" not in str(path) and "__pycache__" not in str(path):
                python_files.append(str(path.relative_to(self.project_dir)))
        return python_files
    
    def _build_duplicate_detection_context(self, target_files: List[str]) -> str:
        """Build context for duplicate detection"""
        context_parts = []
        
        context_parts.append("# Duplicate Detection Context\n")
        context_parts.append(f"Target files: {len(target_files)}\n")
        
        # Add file summaries
        for filepath in target_files[:10]:  # Limit to first 10
            full_path = self.project_dir / filepath
            if full_path.exists():
                try:
                    with open(full_path, 'r') as f:
                        content = f.read()
                    context_parts.append(f"\n## {filepath}\n")
                    context_parts.append(f"Lines: {len(content.splitlines())}\n")
                    # Add first few lines
                    lines = content.splitlines()[:5]
                    context_parts.append("```python\n")
                    context_parts.append("\n".join(lines))
                    context_parts.append("\n...\n```\n")
                except Exception as e:
                    self.logger.warning(f"Could not read {filepath}: {e}")
        
        return "".join(context_parts)
    
    def _build_conflict_resolution_context(self, target_files: List[str]) -> str:
        """Build context for conflict resolution"""
        context_parts = []
        
        context_parts.append("# Conflict Resolution Context\n")
        
        if target_files:
            context_parts.append(f"Target files: {', '.join(target_files)}\n")
        
        return "".join(context_parts)
    
    def _build_architecture_context(self) -> str:
        """Build context for architecture consistency check"""
        context_parts = []
        
        context_parts.append("# Architecture Consistency Context\n")
        
        # Add MASTER_PLAN content
        master_plan = self.read_file("MASTER_PLAN.md")
        if master_plan:
            context_parts.append("\n## MASTER_PLAN.md\n")
            context_parts.append(master_plan[:2000])  # First 2000 chars
            context_parts.append("\n...\n")
        
        # Add ARCHITECTURE content
        architecture = self.read_file("ARCHITECTURE.md")
        if architecture:
            context_parts.append("\n## ARCHITECTURE.md\n")
            context_parts.append(architecture[:2000])  # First 2000 chars
            context_parts.append("\n...\n")
        
        return "".join(context_parts)
    
    def _build_feature_extraction_context(self, target_files: List[str]) -> str:
        """Build context for feature extraction"""
        context_parts = []
        
        context_parts.append("# Feature Extraction Context\n")
        
        if target_files:
            context_parts.append(f"Target files: {', '.join(target_files)}\n")
        
        return "".join(context_parts)
    
    def _build_comprehensive_context(self) -> str:
        """Build comprehensive context for full analysis"""
        context_parts = []
        
        context_parts.append("# Comprehensive Refactoring Context\n")
        
        # Add project structure
        python_files = self._get_all_python_files()
        context_parts.append(f"\n## Project Structure\n")
        context_parts.append(f"Total Python files: {len(python_files)}\n")
        
        # Add MASTER_PLAN
        master_plan = self.read_file("MASTER_PLAN.md")
        if master_plan:
            context_parts.append("\n## MASTER_PLAN.md (excerpt)\n")
            context_parts.append(master_plan[:1000])
            context_parts.append("\n...\n")
        
        return "".join(context_parts)
    
    def _write_refactoring_results(self, refactoring_type: str,
                                  results: List[Dict],
                                  recommendations: str):
        """Write refactoring results to REFACTORING_WRITE.md"""
        
        content_parts = []
        content_parts.append(f"# Refactoring Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        content_parts.append(f"## Type: {refactoring_type}\n\n")
        
        if results:
            content_parts.append("## Tool Results\n\n")
            for result in results:
                tool_name = result.get("tool", "unknown")
                success = result.get("success", False)
                message = result.get("message", "")
                content_parts.append(f"### {tool_name}\n")
                content_parts.append(f"Status: {'✅ Success' if success else '❌ Failed'}\n")
                content_parts.append(f"{message}\n\n")
        
        if recommendations:
            content_parts.append("## Recommendations\n\n")
            content_parts.append(recommendations)
            content_parts.append("\n")
        
        self.write_own_output("".join(content_parts))
    
    def _determine_next_phase(self, recommendations: str) -> str:
        """Determine next phase based on recommendations"""
        
        recommendations_lower = recommendations.lower()
        
        if "implement" in recommendations_lower or "create" in recommendations_lower:
            return "coding"
        elif "verify" in recommendations_lower or "test" in recommendations_lower:
            return "qa"
        elif "plan" in recommendations_lower or "task" in recommendations_lower:
            return "planning"
        else:
            return "investigation"
    
    def _read_relevant_phase_outputs(self) -> Dict[str, str]:
        """Read outputs from other phases that might trigger refactoring"""
        
        outputs = {}
        
        # Read QA output (might have conflict/duplicate warnings)
        qa_output = self.read_file(".ai/QA_WRITE.md")
        if qa_output:
            outputs["qa"] = qa_output
        
        # Read investigation output (might have refactoring recommendations)
        investigation_output = self.read_file(".ai/INVESTIGATION_WRITE.md")
        if investigation_output:
            outputs["investigation"] = investigation_output
        
        # Read planning output (might have architecture changes)
        planning_output = self.read_file(".ai/PLANNING_WRITE.md")
        if planning_output:
            outputs["planning"] = planning_output
        
        return outputs
    
    def generate_state_markdown(self, state: PipelineState) -> str:
        """Generate REFACTORING_STATE.md content"""
        lines = [
            "# Refactoring State",
            f"Updated: {self.format_timestamp()}",
            "",
            "## Current Session Stats",
            "",
        ]
        
        if 'refactoring' in state.phases:
            lines.extend([
                f"- Refactoring Analyses: {state.phases['refactoring'].successes}",
                f"- Failed Analyses: {state.phases['refactoring'].failures}",
                f"- Total Runs: {state.phases['refactoring'].runs}",
            ])
        else:
            lines.append("- Stats not available (phase not initialized)")
        
        lines.append("")
        
        # Add recent refactoring activities
        lines.extend([
            "## Recent Refactoring Activities",
            "",
        ])
        
        # Get recent refactoring results from REFACTORING_WRITE.md
        refactoring_output = self.read_file(".ai/REFACTORING_WRITE.md")
        if refactoring_output:
            lines.append("### Latest Analysis")
            lines.append("")
            # Add first 500 chars of latest output
            lines.append(refactoring_output[:500])
            if len(refactoring_output) > 500:
                lines.append("...")
        else:
            lines.append("No recent refactoring activities")
        
        lines.append("")
        
        # Add refactoring recommendations summary
        lines.extend([
            "## Pending Recommendations",
            "",
        ])
        
        # Check for pending refactoring tasks
        pending_refactoring = [
            task for task in state.tasks.values()
            if task.status in [TaskStatus.NEW, TaskStatus.IN_PROGRESS]
            and task.description and 'refactor' in task.description.lower()
        ]
        
        if pending_refactoring:
            lines.append(f"- {len(pending_refactoring)} refactoring task(s) pending")
            for task in pending_refactoring[:5]:  # Show first 5
                lines.append(f"  - {task.task_id}: {task.description[:80]}...")
        else:
            lines.append("No pending refactoring tasks")
        
        return "\n".join(lines)