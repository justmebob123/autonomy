"""
Analysis Specialist

Expert model for quick analysis and pattern detection.
Uses qwen2.5:14b on ollama01 for fast, efficient analysis.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Types of analysis tasks"""
    CODE_REVIEW = "code_review"
    PATTERN_DETECTION = "pattern_detection"
    QUALITY_CHECK = "quality_check"
    SYNTAX_VALIDATION = "syntax_validation"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    PERFORMANCE_SCAN = "performance_scan"


@dataclass
class AnalysisTask:
    """Represents an analysis task"""
    analysis_type: AnalysisType
    target: str  # File path, code snippet, or data to analyze
    context: Dict[str, Any]
    quick_mode: bool = True  # Fast analysis vs thorough
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}


class AnalysisSpecialist:
    """
    Specialist for quick analysis and pattern detection.
    
    Capabilities:
    - Fast code review for obvious issues
    - Pattern detection in code and data
    - Quality checks (style, conventions)
    - Syntax validation
    - Dependency analysis
    - Performance scanning
    """
    
    def __init__(self, model_tool):
        """
        Initialize analysis specialist.
        
        Args:
            model_tool: ModelTool instance configured for analysis
        """
        self.model_tool = model_tool
        self.analysis_patterns = self._load_analysis_patterns()
        
    def _load_analysis_patterns(self) -> Dict[str, Any]:
        """Load common patterns to check for"""
        return {
            "code_smells": [
                "long_method",
                "large_class",
                "duplicate_code",
                "dead_code",
                "magic_numbers",
                "deep_nesting"
            ],
            "security_issues": [
                "hardcoded_credentials",
                "sql_injection",
                "command_injection",
                "unsafe_deserialization",
                "weak_crypto"
            ],
            "performance_issues": [
                "n_plus_one_queries",
                "inefficient_loops",
                "unnecessary_copies",
                "blocking_operations",
                "memory_leaks"
            ],
            "style_issues": [
                "inconsistent_naming",
                "missing_docstrings",
                "long_lines",
                "unused_imports",
                "missing_type_hints"
            ]
        }
    
    def get_system_prompt(self, task: AnalysisTask) -> str:
        """
        Generate specialized system prompt for analysis task.
        
        Args:
            task: The analysis task to perform
            
        Returns:
            Specialized system prompt
        """
        base_prompt = """You are an expert analysis specialist focused on quick, accurate assessments.

Your approach:
1. Scan quickly for obvious issues
2. Use pattern matching for common problems
3. Prioritize high-impact findings
4. Be concise and actionable
5. Flag issues with severity levels
6. Provide quick fixes when possible

"""
        
        # Add analysis type specific guidance
        type_guidance = self._get_type_guidance(task.analysis_type)
        
        # Add quick mode guidance
        mode_guidance = ""
        if task.quick_mode:
            mode_guidance = """
Mode: QUICK ANALYSIS
- Focus on obvious issues only
- Use heuristics and patterns
- Prioritize speed over thoroughness
- Flag items for deeper review if needed
"""
        else:
            mode_guidance = """
Mode: THOROUGH ANALYSIS
- Check all aspects carefully
- Look for subtle issues
- Provide detailed explanations
- Consider edge cases
"""
        
        return base_prompt + type_guidance + mode_guidance
    
    def _get_type_guidance(self, analysis_type: AnalysisType) -> str:
        """Get analysis type specific guidance"""
        guidance = {
            AnalysisType.CODE_REVIEW: """
Analysis Type: CODE REVIEW
Check for:
- Obvious bugs and errors
- Code smells and anti-patterns
- Style and convention violations
- Missing error handling
- Security vulnerabilities
""",
            AnalysisType.PATTERN_DETECTION: """
Analysis Type: PATTERN DETECTION
Look for:
- Repeated code patterns
- Common anti-patterns
- Design pattern opportunities
- Consistency issues
""",
            AnalysisType.QUALITY_CHECK: """
Analysis Type: QUALITY CHECK
Verify:
- Code style compliance
- Documentation completeness
- Test coverage indicators
- Naming conventions
- Import organization
""",
            AnalysisType.SYNTAX_VALIDATION: """
Analysis Type: SYNTAX VALIDATION
Check:
- Syntax errors
- Import errors
- Type errors (if type hints present)
- Undefined variables
""",
            AnalysisType.DEPENDENCY_ANALYSIS: """
Analysis Type: DEPENDENCY ANALYSIS
Analyze:
- Import dependencies
- Circular dependencies
- Unused dependencies
- Missing dependencies
- Dependency versions
""",
            AnalysisType.PERFORMANCE_SCAN: """
Analysis Type: PERFORMANCE SCAN
Scan for:
- Inefficient algorithms
- Unnecessary operations
- Resource leaks
- Blocking calls
- Optimization opportunities
"""
        }
        return guidance.get(analysis_type, "")
    
    def get_available_tools(self, task: AnalysisTask) -> List[Dict[str, Any]]:
        """
        Get tools available for this analysis task.
        
        Args:
            task: The analysis task
            
        Returns:
            List of tool definitions
        """
        # Base tools for all analysis
        base_tools = [
            {
                "name": "flag_issue",
                "description": "Flag an issue found during analysis",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "severity": {
                            "type": "string",
                            "enum": ["critical", "high", "medium", "low", "info"],
                            "description": "Severity level"
                        },
                        "category": {
                            "type": "string",
                            "description": "Issue category"
                        },
                        "description": {
                            "type": "string",
                            "description": "Issue description"
                        },
                        "location": {
                            "type": "string",
                            "description": "Location in code (line number, function, etc.)"
                        },
                        "suggestion": {
                            "type": "string",
                            "description": "Suggested fix"
                        }
                    },
                    "required": ["severity", "category", "description"]
                }
            },
            {
                "name": "check_pattern",
                "description": "Check for a specific pattern",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern_name": {
                            "type": "string",
                            "description": "Name of pattern to check"
                        },
                        "target": {
                            "type": "string",
                            "description": "Code or data to check"
                        }
                    },
                    "required": ["pattern_name", "target"]
                }
            }
        ]
        
        # Add type-specific tools
        if task.analysis_type == AnalysisType.DEPENDENCY_ANALYSIS:
            base_tools.append({
                "name": "analyze_imports",
                "description": "Analyze import statements",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to file"
                        }
                    },
                    "required": ["file_path"]
                }
            })
        
        if task.analysis_type == AnalysisType.SYNTAX_VALIDATION:
            base_tools.append({
                "name": "validate_syntax",
                "description": "Validate Python syntax",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Code to validate"
                        }
                    },
                    "required": ["code"]
                }
            })
        
        return base_tools
    
    def execute_task(self, task: AnalysisTask) -> Dict[str, Any]:
        """
        Execute an analysis task.
        
        Args:
            task: The analysis task to execute
            
        Returns:
            Result with findings and recommendations
        """
        logger.info(f"AnalysisSpecialist executing {task.analysis_type.value} task")
        
        # Build context message
        context_parts = [
            f"Analysis Task: {task.analysis_type.value.upper().replace('_', ' ')}",
            f"Target: {task.target[:100]}..." if len(task.target) > 100 else f"Target: {task.target}"
        ]
        
        if task.context:
            context_parts.append(f"\nContext:\n{self._format_context(task.context)}")
        
        context_message = "\n".join(context_parts)
        
        # Get system prompt and tools
        system_prompt = self.get_system_prompt(task)
        tools = self.get_available_tools(task)
        
        # Execute with model tool
        result = self.model_tool.execute(
            messages=[{"role": "user", "content": context_message}],
            system_prompt=system_prompt,
            tools=tools
        )
        
        # Extract findings
        findings = self._extract_findings(result, task)
        
        return {
            "success": result.get("success", False),
            "analysis": result.get("response", ""),
            "tool_calls": result.get("tool_calls", []),
            "findings": findings,
            "task": task
        }
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary for prompt"""
        lines = []
        for key, value in context.items():
            if isinstance(value, (list, dict)):
                lines.append(f"{key}:")
                if isinstance(value, list):
                    for item in value[:5]:  # Limit to 5 items for quick analysis
                        lines.append(f"  - {item}")
                    if len(value) > 5:
                        lines.append(f"  ... and {len(value) - 5} more")
                else:
                    for k, v in list(value.items())[:5]:
                        lines.append(f"  {k}: {v}")
                    if len(value) > 5:
                        lines.append(f"  ... and {len(value) - 5} more")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)
    
    def _extract_findings(self, result: Dict[str, Any], task: AnalysisTask) -> Dict[str, Any]:
        """
        Extract structured findings from result.
        
        Args:
            result: Result from model execution
            task: Original task
            
        Returns:
            Structured findings with issues and recommendations
        """
        findings = {
            "issues": [],
            "recommendations": [],
            "summary": "",
            "severity_counts": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0
            }
        }
        
        # Extract issues from tool calls
        tool_calls = result.get("tool_calls", [])
        for tc in tool_calls:
            if tc.get("name") == "flag_issue":
                params = tc.get("parameters", {})
                issue = {
                    "severity": params.get("severity", "medium"),
                    "category": params.get("category", "unknown"),
                    "description": params.get("description", ""),
                    "location": params.get("location", ""),
                    "suggestion": params.get("suggestion", "")
                }
                findings["issues"].append(issue)
                
                # Update severity counts
                severity = issue["severity"]
                if severity in findings["severity_counts"]:
                    findings["severity_counts"][severity] += 1
        
        # Extract recommendations from response
        response = result.get("response", "")
        for line in response.split('\n'):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['recommend', 'suggest', 'should', 'consider']):
                findings["recommendations"].append(line.strip())
        
        # Generate summary
        total_issues = len(findings["issues"])
        critical_count = findings["severity_counts"]["critical"]
        high_count = findings["severity_counts"]["high"]
        
        if total_issues == 0:
            findings["summary"] = "No issues found"
        else:
            findings["summary"] = f"Found {total_issues} issue(s)"
            if critical_count > 0:
                findings["summary"] += f" ({critical_count} critical)"
            elif high_count > 0:
                findings["summary"] += f" ({high_count} high priority)"
        
        return findings
    
    def review_code(self, file_path: str, code: str) -> Dict[str, Any]:
        """
        Review code for QA phase.
        
        Args:
            file_path: Path to the code file
            code: Code content to review
            
        Returns:
            Review result with tool calls
        """
        logger.info(f"AnalysisSpecialist reviewing {file_path}")
        
        task = AnalysisTask(
            analysis_type=AnalysisType.CODE_REVIEW,
            target=code,
            context={"file_path": file_path},
            quick_mode=False  # Thorough review for QA
        )
        
        return self.execute_task(task)
    
    def analyze_code(self, file_path: str, code: str, analysis_type: str = "investigation", context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze code for investigation or documentation.
        
        Args:
            file_path: Path to the code file
            code: Code content to analyze
            analysis_type: Type of analysis (investigation, documentation, etc.)
            context: Additional context
            
        Returns:
            Analysis result with tool calls
        """
        logger.info(f"AnalysisSpecialist analyzing {file_path} ({analysis_type})")
        
        # Map string analysis types to AnalysisType enum
        type_map = {
            "investigation": AnalysisType.CODE_REVIEW,
            "documentation": AnalysisType.CODE_REVIEW,
            "quality": AnalysisType.QUALITY_CHECK,
            "pattern": AnalysisType.PATTERN_DETECTION
        }
        
        task = AnalysisTask(
            analysis_type=type_map.get(analysis_type, AnalysisType.CODE_REVIEW),
            target=code,
            context={"file_path": file_path, **(context or {})},
            quick_mode=False
        )
        
        return self.execute_task(task)
    
    def quick_code_review(self, file_path: str, code: str) -> Dict[str, Any]:
        """
        Perform quick code review.
        
        Args:
            file_path: Path to the code file
            code: Code content to review
            
        Returns:
            Quick review with obvious issues
        """
        logger.info(f"AnalysisSpecialist performing quick review of {file_path}")
        
        task = AnalysisTask(
            analysis_type=AnalysisType.CODE_REVIEW,
            target=code,
            context={"file_path": file_path},
            quick_mode=True
        )
        
        result = self.execute_task(task)
        
        return {
            "file_path": file_path,
            "findings": result.get("findings", {}),
            "passed": len(result.get("findings", {}).get("issues", [])) == 0
        }
    
    def check_quality(self, file_path: str, code: str, standards: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check code quality against standards.
        
        Args:
            file_path: Path to the code file
            code: Code content to check
            standards: Quality standards to check against
            
        Returns:
            Quality check results
        """
        logger.info(f"AnalysisSpecialist checking quality of {file_path}")
        
        task = AnalysisTask(
            analysis_type=AnalysisType.QUALITY_CHECK,
            target=code,
            context={
                "file_path": file_path,
                "standards": standards
            },
            quick_mode=True
        )
        
        result = self.execute_task(task)
        findings = result.get("findings", {})
        
        # Calculate quality score
        total_issues = len(findings.get("issues", []))
        critical_issues = findings.get("severity_counts", {}).get("critical", 0)
        high_issues = findings.get("severity_counts", {}).get("high", 0)
        
        # Simple scoring: start at 100, deduct points
        score = 100.0
        score -= critical_issues * 20
        score -= high_issues * 10
        score -= (total_issues - critical_issues - high_issues) * 5
        score = max(0.0, score)
        
        return {
            "file_path": file_path,
            "quality_score": score,
            "findings": findings,
            "passed": score >= 70.0  # 70% threshold
        }
    
    def detect_patterns(self, code: str, pattern_types: List[str]) -> Dict[str, Any]:
        """
        Detect specific patterns in code.
        
        Args:
            code: Code to analyze
            pattern_types: Types of patterns to look for
            
        Returns:
            Detected patterns
        """
        logger.info(f"AnalysisSpecialist detecting patterns: {pattern_types}")
        
        task = AnalysisTask(
            analysis_type=AnalysisType.PATTERN_DETECTION,
            target=code,
            context={"pattern_types": pattern_types},
            quick_mode=True
        )
        
        result = self.execute_task(task)
        
        return {
            "patterns_found": self._extract_patterns(result.get("analysis", "")),
            "findings": result.get("findings", {})
        }
    
    def _extract_patterns(self, analysis: str) -> List[str]:
        """Extract detected patterns from analysis"""
        patterns = []
        for line in analysis.split('\n'):
            line_lower = line.lower()
            if 'pattern' in line_lower or 'detected' in line_lower:
                patterns.append(line.strip())
        return patterns


def create_analysis_specialist(model_tool) -> AnalysisSpecialist:
    """
    Factory function to create an analysis specialist.
    
    Args:
        model_tool: ModelTool instance configured for analysis
        
    Returns:
        AnalysisSpecialist instance
    """
    return AnalysisSpecialist(model_tool)