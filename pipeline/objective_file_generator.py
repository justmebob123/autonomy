"""
Objective File Generator

Automatically creates and maintains objective files (PRIMARY_OBJECTIVES.md,
SECONDARY_OBJECTIVES.md, TERTIARY_OBJECTIVES.md) during project planning.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass

from .objective_manager import ObjectiveLevel, ObjectiveStatus
from .state.manager import PipelineState, TaskState
from .logging_setup import get_logger


@dataclass
class ExtractedObjective:
    """Objective extracted from project requirements"""
    title: str
    description: str
    level: ObjectiveLevel
    success_criteria: List[str]
    dependencies: List[str]
    dimensional_profile: Dict[str, float]
    tasks: List[str]  # Task IDs


class ObjectiveFileGenerator:
    """
    Generates objective files from project requirements and tasks.
    
    Analyzes project context to extract objectives, categorizes them by priority,
    calculates dimensional profiles, and creates properly formatted objective files.
    """
    
    def __init__(self, project_dir: Path):
        """Initialize generator with project directory"""
        self.project_dir = Path(project_dir)
        self.logger = get_logger()
        
    def generate_objective_files(
        self, 
        state: PipelineState,
        project_context: str,
        tasks: List[TaskState]
    ) -> Dict[str, str]:
        """
        Generate objective files from project context and tasks.
        
        Args:
            state: Current pipeline state
            project_context: Complete project context (MASTER_PLAN, ARCHITECTURE, etc.)
            tasks: List of tasks being created
            
        Returns:
            Dictionary mapping filename to content
        """
        self.logger.info("🎯 Generating objective files...")
        
        # Extract objectives from project context
        objectives = self._extract_objectives(project_context, tasks)
        
        if not objectives:
            self.logger.warning("No objectives extracted from project context")
            return {}
        
        # Categorize by level
        primary = [obj for obj in objectives if obj.level == ObjectiveLevel.PRIMARY]
        secondary = [obj for obj in objectives if obj.level == ObjectiveLevel.SECONDARY]
        tertiary = [obj for obj in objectives if obj.level == ObjectiveLevel.TERTIARY]
        
        self.logger.info(f"  📊 Extracted: {len(primary)} PRIMARY, {len(secondary)} SECONDARY, {len(tertiary)} TERTIARY")
        
        # Generate files
        files = {}
        
        if primary:
            files['PRIMARY_OBJECTIVES.md'] = self._generate_objective_file(
                primary, ObjectiveLevel.PRIMARY, state
            )
            
        if secondary:
            files['SECONDARY_OBJECTIVES.md'] = self._generate_objective_file(
                secondary, ObjectiveLevel.SECONDARY, state
            )
            
        if tertiary:
            files['TERTIARY_OBJECTIVES.md'] = self._generate_objective_file(
                tertiary, ObjectiveLevel.TERTIARY, state
            )
        
        return files
    
    def _extract_objectives(
        self, 
        project_context: str, 
        tasks: List[TaskState]
    ) -> List[ExtractedObjective]:
        """
        Extract objectives from project context.
        
        Analyzes MASTER_PLAN, ARCHITECTURE, and other context to identify
        strategic objectives and categorize them by priority.
        """
        objectives = []
        
        # Extract from MASTER_PLAN if present
        master_plan_match = re.search(
            r'MASTER_PLAN\.md.*?```(?:markdown)?\n(.*?)```',
            project_context,
            re.DOTALL | re.IGNORECASE
        )
        
        if master_plan_match:
            master_plan = master_plan_match.group(1)
            objectives.extend(self._extract_from_master_plan(master_plan, tasks))
        
        # Extract from ARCHITECTURE if present
        architecture_match = re.search(
            r'ARCHITECTURE\.md.*?```(?:markdown)?\n(.*?)```',
            project_context,
            re.DOTALL | re.IGNORECASE
        )
        
        if architecture_match:
            architecture = architecture_match.group(1)
            objectives.extend(self._extract_from_architecture(architecture, tasks))
        
        # If no objectives found, create default from tasks
        if not objectives and tasks:
            objectives.extend(self._create_default_objectives(tasks))
        
        return objectives
    
    def _extract_from_master_plan(
        self, 
        master_plan: str, 
        tasks: List[TaskState]
    ) -> List[ExtractedObjective]:
        """Extract objectives from MASTER_PLAN content"""
        objectives = []
        
        # Look for sections like "## Core Features", "## Phase 1", etc.
        sections = re.findall(
            r'##\s+([^\n]+)\n(.*?)(?=##|\Z)',
            master_plan,
            re.DOTALL
        )
        
        for section_title, section_content in sections:
            # Skip meta sections
            if any(skip in section_title.lower() for skip in ['overview', 'timeline', 'status']):
                continue
            
            # Determine level based on keywords
            level = self._determine_objective_level(section_title, section_content)
            
            # Extract success criteria
            criteria = self._extract_success_criteria(section_content)
            
            # Extract dependencies
            dependencies = self._extract_dependencies(section_content)
            
            # Match tasks to this objective
            matched_tasks = self._match_tasks_to_objective(
                section_title, section_content, tasks
            )
            
            # Calculate dimensional profile
            profile = self._calculate_dimensional_profile(
                section_title, section_content, matched_tasks
            )
            
            objectives.append(ExtractedObjective(
                title=section_title.strip(),
                description=self._extract_description(section_content),
                level=level,
                success_criteria=criteria,
                dependencies=dependencies,
                dimensional_profile=profile,
                tasks=[t.task_id for t in matched_tasks]
            ))
        
        return objectives
    
    def _extract_from_architecture(
        self, 
        architecture: str, 
        tasks: List[TaskState]
    ) -> List[ExtractedObjective]:
        """Extract objectives from ARCHITECTURE content"""
        objectives = []
        
        # Look for component/module sections
        sections = re.findall(
            r'##\s+([^\n]+)\n(.*?)(?=##|\Z)',
            architecture,
            re.DOTALL
        )
        
        for section_title, section_content in sections:
            # Skip meta sections
            if any(skip in section_title.lower() for skip in ['overview', 'diagram', 'stack']):
                continue
            
            # Architecture objectives are typically SECONDARY
            level = ObjectiveLevel.SECONDARY
            
            # Extract details
            criteria = self._extract_success_criteria(section_content)
            dependencies = self._extract_dependencies(section_content)
            matched_tasks = self._match_tasks_to_objective(
                section_title, section_content, tasks
            )
            profile = self._calculate_dimensional_profile(
                section_title, section_content, matched_tasks
            )
            
            objectives.append(ExtractedObjective(
                title=f"Implement {section_title.strip()}",
                description=self._extract_description(section_content),
                level=level,
                success_criteria=criteria,
                dependencies=dependencies,
                dimensional_profile=profile,
                tasks=[t.task_id for t in matched_tasks]
            ))
        
        return objectives
    
    def _create_default_objectives(self, tasks: List[TaskState]) -> List[ExtractedObjective]:
        """Create default objectives when no context available"""
        # Group tasks by target file directory
        by_directory = {}
        for task in tasks:
            dir_name = Path(task.target_file).parent.name or "root"
            if dir_name not in by_directory:
                by_directory[dir_name] = []
            by_directory[dir_name].append(task)
        
        objectives = []
        for dir_name, dir_tasks in by_directory.items():
            objectives.append(ExtractedObjective(
                title=f"Implement {dir_name.replace('_', ' ').title()} Module",
                description=f"Complete implementation of {dir_name} module with {len(dir_tasks)} tasks",
                level=ObjectiveLevel.PRIMARY,
                success_criteria=[
                    "All module files created",
                    "All tests passing",
                    "Documentation complete"
                ],
                dependencies=[],
                dimensional_profile=self._calculate_dimensional_profile(
                    dir_name, "", dir_tasks
                ),
                tasks=[t.task_id for t in dir_tasks]
            ))
        
        return objectives
    
    def _determine_objective_level(self, title: str, content: str) -> ObjectiveLevel:
        """Determine objective priority level from title and content"""
        title_lower = title.lower()
        content_lower = content.lower()
        
        # PRIMARY indicators
        primary_keywords = [
            'core', 'critical', 'essential', 'must', 'required',
            'phase 1', 'mvp', 'foundation', 'base'
        ]
        
        # TERTIARY indicators
        tertiary_keywords = [
            'optional', 'nice to have', 'enhancement', 'polish',
            'future', 'phase 3', 'advanced', 'extra'
        ]
        
        # Check for PRIMARY
        if any(kw in title_lower or kw in content_lower for kw in primary_keywords):
            return ObjectiveLevel.PRIMARY
        
        # Check for TERTIARY
        if any(kw in title_lower or kw in content_lower for kw in tertiary_keywords):
            return ObjectiveLevel.TERTIARY
        
        # Default to SECONDARY
        return ObjectiveLevel.SECONDARY
    
    def _extract_description(self, content: str) -> str:
        """Extract description from section content"""
        # Get first paragraph
        lines = content.strip().split('\n')
        description_lines = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('-') or line.startswith('*'):
                if description_lines:
                    break
                continue
            description_lines.append(line)
        
        description = ' '.join(description_lines)
        return description[:500] if description else "No description available"
    
    def _extract_success_criteria(self, content: str) -> List[str]:
        """Extract success criteria from content"""
        criteria = []
        
        # Look for bullet points or numbered lists
        lines = content.split('\n')
        in_criteria_section = False
        
        for line in lines:
            line = line.strip()
            
            # Check if we're in a criteria section
            if 'success' in line.lower() or 'criteria' in line.lower() or 'requirements' in line.lower():
                in_criteria_section = True
                continue
            
            # Extract criteria items
            if in_criteria_section and (line.startswith('-') or line.startswith('*') or re.match(r'^\d+\.', line)):
                criterion = re.sub(r'^[-*\d.]\s*', '', line).strip()
                if criterion:
                    criteria.append(criterion)
            elif in_criteria_section and line and not line.startswith('#'):
                # End of criteria section
                break
        
        # If no explicit criteria found, create generic ones
        if not criteria:
            criteria = [
                "Implementation complete",
                "Tests passing",
                "Documentation updated"
            ]
        
        return criteria[:5]  # Limit to 5 criteria
    
    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract dependencies from content"""
        dependencies = []
        
        # Look for dependency mentions
        dep_patterns = [
            r'depends on\s+([^\n]+)',
            r'requires\s+([^\n]+)',
            r'needs\s+([^\n]+)',
            r'after\s+([^\n]+)'
        ]
        
        for pattern in dep_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            dependencies.extend(matches)
        
        return dependencies[:3]  # Limit to 3 dependencies
    
    def _match_tasks_to_objective(
        self, 
        title: str, 
        content: str, 
        tasks: List[TaskState]
    ) -> List[TaskState]:
        """Match tasks to objective based on title and content"""
        matched = []
        
        # Extract keywords from title and content
        keywords = set()
        for word in re.findall(r'\b\w+\b', title.lower()):
            if len(word) > 3:
                keywords.add(word)
        
        for task in tasks:
            # Check if task description or file matches keywords
            task_text = f"{task.description} {task.target_file}".lower()
            
            if any(kw in task_text for kw in keywords):
                matched.append(task)
        
        return matched
    
    def _calculate_dimensional_profile(
        self, 
        title: str, 
        content: str, 
        tasks: List[TaskState]
    ) -> Dict[str, float]:
        """
        Calculate 7D dimensional profile for objective.
        
        Dimensions:
        1. Temporal - Time urgency (0.0 = low, 1.0 = high)
        2. Functional - Feature complexity (0.0 = simple, 1.0 = complex)
        3. Data - Dependencies (0.0 = none, 1.0 = many)
        4. State - State management needs (0.0 = stateless, 1.0 = stateful)
        5. Error - Risk level (0.0 = low risk, 1.0 = high risk)
        6. Context - Context requirements (0.0 = isolated, 1.0 = integrated)
        7. Integration - Integration complexity (0.0 = standalone, 1.0 = highly integrated)
        """
        text = f"{title} {content}".lower()
        
        # Temporal - based on urgency keywords
        temporal_keywords = ['urgent', 'asap', 'critical', 'immediate', 'priority', 'phase 1', 'mvp']
        temporal = min(1.0, sum(0.2 for kw in temporal_keywords if kw in text))
        
        # Functional - based on complexity indicators
        functional_keywords = ['complex', 'advanced', 'sophisticated', 'algorithm', 'optimization']
        functional = min(1.0, 0.3 + sum(0.15 for kw in functional_keywords if kw in text))
        
        # Data - based on number of tasks and dependencies
        data = min(1.0, len(tasks) * 0.1)
        
        # State - based on state management keywords
        state_keywords = ['state', 'session', 'cache', 'store', 'persist', 'database']
        state = min(1.0, sum(0.2 for kw in state_keywords if kw in text))
        
        # Error - based on risk keywords
        error_keywords = ['risk', 'critical', 'security', 'validation', 'error handling']
        error = min(1.0, 0.3 + sum(0.15 for kw in error_keywords if kw in text))
        
        # Context - based on integration keywords
        context_keywords = ['integrate', 'connect', 'interface', 'api', 'service']
        context = min(1.0, sum(0.2 for kw in context_keywords if kw in text))
        
        # Integration - based on system-wide keywords
        integration_keywords = ['system', 'architecture', 'framework', 'platform', 'infrastructure']
        integration = min(1.0, sum(0.2 for kw in integration_keywords if kw in text))
        
        return {
            'temporal': round(temporal, 2),
            'functional': round(functional, 2),
            'data': round(data, 2),
            'state': round(state, 2),
            'error': round(error, 2),
            'context': round(context, 2),
            'integration': round(integration, 2)
        }
    
    def _generate_objective_file(
        self, 
        objectives: List[ExtractedObjective],
        level: ObjectiveLevel,
        state: PipelineState
    ) -> str:
        """Generate objective file content"""
        level_name = level.value.upper()
        
        content = [
            f"# {level_name} OBJECTIVES",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Objectives**: {len(objectives)}",
            "",
            "---",
            ""
        ]
        
        for i, obj in enumerate(objectives, 1):
            obj_id = f"{level_name}_{i:03d}"
            
            content.extend([
                f"## Objective {i}: {obj.title}",
                f"**ID**: `{obj_id}`",
                f"**Status**: ACTIVE",
                f"**Priority**: {level_name}",
                "",
                "### Description",
                obj.description,
                "",
                "### Success Criteria",
            ])
            
            for criterion in obj.success_criteria:
                content.append(f"- [ ] {criterion}")
            
            content.append("")
            
            if obj.dependencies:
                content.extend([
                    "### Dependencies",
                ])
                for dep in obj.dependencies:
                    content.append(f"- {dep}")
                content.append("")
            else:
                content.extend([
                    "### Dependencies",
                    "- None",
                    ""
                ])
            
            content.extend([
                "### Dimensional Profile",
                f"- **Temporal**: {obj.dimensional_profile['temporal']:.2f} (Time urgency)",
                f"- **Functional**: {obj.dimensional_profile['functional']:.2f} (Feature complexity)",
                f"- **Data**: {obj.dimensional_profile['data']:.2f} (Dependencies)",
                f"- **State**: {obj.dimensional_profile['state']:.2f} (State management)",
                f"- **Error**: {obj.dimensional_profile['error']:.2f} (Risk level)",
                f"- **Context**: {obj.dimensional_profile['context']:.2f} (Context requirements)",
                f"- **Integration**: {obj.dimensional_profile['integration']:.2f} (Integration complexity)",
                "",
                "### Tasks",
            ])
            
            if obj.tasks:
                for task_id in obj.tasks:
                    if task_id in state.tasks:
                        task = state.tasks[task_id]
                        status_icon = "✅" if task.status == "completed" else "⏳"
                        content.append(f"- {status_icon} `{task_id}`: {task.description}")
                    else:
                        content.append(f"- ⏳ `{task_id}`: (Task details pending)")
            else:
                content.append("- No tasks assigned yet")
            
            content.extend([
                "",
                "### Issues",
                "- None",
                "",
                "### Metrics",
                f"- **Created**: {datetime.now().strftime('%Y-%m-%d')}",
                f"- **Last Updated**: {datetime.now().strftime('%Y-%m-%d')}",
                "- **Success Rate**: 0%",
                "- **Open Issues**: 0",
                "- **Critical Issues**: 0",
                "",
                "---",
                ""
            ])
        
        return '\n'.join(content)
    
    def write_objective_files(self, files: Dict[str, str]) -> List[str]:
        """
        Write objective files to project directory.
        
        Args:
            files: Dictionary mapping filename to content
            
        Returns:
            List of created file paths
        """
        created = []
        
        for filename, content in files.items():
            filepath = self.project_dir / filename
            
            try:
                filepath.write_text(content, encoding='utf-8')
                created.append(str(filepath))
                self.logger.info(f"  ✅ Created {filename}")
            except Exception as e:
                self.logger.error(f"  ❌ Failed to create {filename}: {e}")
        
        return created
    
    def link_tasks_to_objectives(
        self, 
        state: PipelineState,
        objective_files: Dict[str, str]
    ) -> int:
        """
        Link tasks to objectives by updating task.objective_id.
        
        Args:
            state: Pipeline state with tasks
            objective_files: Generated objective files
            
        Returns:
            Number of tasks linked
        """
        linked_count = 0
        
        # Parse objective files to extract task-to-objective mappings
        for filename, content in objective_files.items():
            level = filename.replace('_OBJECTIVES.md', '').lower()
            
            # Extract objective IDs and their tasks
            obj_pattern = r'\*\*ID\*\*:\s*`([^`]+)`.*?### Tasks\n(.*?)(?=###|\Z)'
            matches = re.findall(obj_pattern, content, re.DOTALL)
            
            for obj_id, tasks_section in matches:
                # Extract task IDs from tasks section
                task_ids = re.findall(r'`(task_\d+)`', tasks_section)
                
                for task_id in task_ids:
                    if task_id in state.tasks:
                        state.tasks[task_id].objective_id = obj_id
                        state.tasks[task_id].objective_level = level
                        linked_count += 1
                        self.logger.debug(f"  🔗 Linked {task_id} to {obj_id}")
        
        if linked_count > 0:
            self.logger.info(f"  ✅ Linked {linked_count} tasks to objectives")
        
        return linked_count