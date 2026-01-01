"""
Comprehensive Unused Code Analyzer

Performs deep analysis of unused code to determine:
1. Project stage and completion percentage
2. Architecture alignment
3. Related implementations comparison
4. Integration opportunities
5. Intelligent keep/merge/refactor/remove decisions
"""

import ast
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class UnusedCodeDecision(str, Enum):
    """Decision for handling unused code"""
    INTEGRATE = "integrate"  # Unused code should be integrated (it's better)
    MERGE = "merge"  # Merge with existing equivalent implementation
    KEEP = "keep"  # Keep for future use (part of planned architecture)
    REPORT = "report"  # Create issue report for developer review
    REMOVE = "remove"  # Safe to remove (truly redundant)


@dataclass
class UnusedCodeAnalysis:
    """Result of unused code analysis"""
    decision: UnusedCodeDecision
    confidence: float  # 0.0 to 1.0
    reasoning: str
    project_stage: str  # "early", "mid", "late"
    completion_percentage: float
    architecture_alignment: str  # "matches", "better", "equivalent", "inferior", "unrelated"
    related_files: List[str]
    integration_plan: Optional[str]
    refactoring_needed: bool
    
    def to_dict(self) -> Dict:
        return {
            'decision': self.decision,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'project_stage': self.project_stage,
            'completion_percentage': self.completion_percentage,
            'architecture_alignment': self.architecture_alignment,
            'related_files': self.related_files,
            'integration_plan': self.integration_plan,
            'refactoring_needed': self.refactoring_needed
        }


class UnusedCodeAnalyzer:
    """
    Comprehensive analyzer for unused code.
    
    Performs deep analysis to make intelligent decisions about
    whether to integrate, merge, keep, report, or remove unused code.
    """
    
    def __init__(self, project_dir: str, logger: Optional[logging.Logger] = None):
        self.project_dir = Path(project_dir)
        self.logger = logger or logging.getLogger(__name__)
        
    def analyze(self, unused_file: str, unused_item: str, item_type: str) -> UnusedCodeAnalysis:
        """
        Perform comprehensive analysis of unused code.
        
        Args:
            unused_file: Path to file containing unused code
            unused_item: Name of unused class/function
            item_type: Type of item ("class", "function", "method")
            
        Returns:
            UnusedCodeAnalysis with decision and reasoning
        """
        # 1. Analyze project stage and completion
        project_stage, completion_pct = self._analyze_project_stage()
        
        # 2. Check architecture alignment
        arch_alignment = self._check_architecture_alignment(unused_file, unused_item)
        
        # 3. Find related implementations
        related_files = self._find_related_implementations(unused_file, unused_item, item_type)
        
        # 4. Compare implementations
        comparison = self._compare_implementations(unused_file, unused_item, related_files)
        
        # 5. Determine integration opportunities
        integration_plan = self._analyze_integration_opportunities(
            unused_file, unused_item, related_files, comparison
        )
        
        # 6. Make decision
        decision, confidence, reasoning, refactoring_needed = self._make_decision(
            project_stage, completion_pct, arch_alignment, 
            comparison, integration_plan
        )
        
        return UnusedCodeAnalysis(
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            project_stage=project_stage,
            completion_percentage=completion_pct,
            architecture_alignment=arch_alignment,
            related_files=related_files,
            integration_plan=integration_plan,
            refactoring_needed=refactoring_needed
        )
    
    def _analyze_project_stage(self) -> Tuple[str, float]:
        """
        Analyze project stage and completion percentage.
        
        Returns:
            (stage, completion_percentage)
        """
        # Check for state file
        state_files = list(self.project_dir.rglob('.autonomy/state.json'))
        if state_files:
            try:
                import json
                with open(state_files[0], 'r') as f:
                    state = json.load(f)
                    completion = state.get('completion_percentage', 0)
                    
                    if completion < 30:
                        return "early", completion
                    elif completion < 70:
                        return "mid", completion
                    else:
                        return "late", completion
            except Exception as e:
                self.logger.debug(f"Could not read state file: {e}")
        
        # Fallback: estimate based on file count
        py_files = list(self.project_dir.rglob('*.py'))
        total_files = len([f for f in py_files if '.autonomy' not in str(f)])
        
        # Rough estimate: < 20 files = early, < 50 = mid, >= 50 = late
        if total_files < 20:
            return "early", 15.0
        elif total_files < 50:
            return "mid", 50.0
        else:
            return "late", 75.0
    
    def _check_architecture_alignment(self, unused_file: str, unused_item: str) -> str:
        """
        Check if unused code aligns with ARCHITECTURE.md.
        
        Returns:
            "matches", "better", "equivalent", "inferior", or "unrelated"
        """
        arch_file = self.project_dir / 'ARCHITECTURE.md'
        if not arch_file.exists():
            return "unrelated"
        
        try:
            arch_content = arch_file.read_text().lower()
            item_lower = unused_item.lower()
            file_lower = unused_file.lower()
            
            # Check if mentioned in architecture
            if item_lower in arch_content or any(part in arch_content for part in file_lower.split('/')):
                return "matches"
            
            # Check for related concepts
            related_terms = self._extract_related_terms(unused_item)
            if any(term in arch_content for term in related_terms):
                return "matches"
            
            return "unrelated"
        except Exception as e:
            self.logger.debug(f"Could not read ARCHITECTURE.md: {e}")
            return "unrelated"
    
    def _extract_related_terms(self, item_name: str) -> List[str]:
        """Extract related terms from item name for architecture matching"""
        # Split camelCase and snake_case
        import re
        parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)', item_name)
        parts.extend(item_name.split('_'))
        return [p.lower() for p in parts if len(p) > 2]
    
    def _find_related_implementations(self, unused_file: str, unused_item: str, item_type: str) -> List[str]:
        """
        Find files with similar/related implementations.
        
        Returns:
            List of file paths with related code
        """
        related = []
        unused_path = self.project_dir / unused_file
        
        # Extract terms from unused item name
        terms = self._extract_related_terms(unused_item)
        
        # Search for files with similar names or content
        for py_file in self.project_dir.rglob('*.py'):
            if '.autonomy' in str(py_file) or py_file == unused_path:
                continue
            
            try:
                content = py_file.read_text()
                # Check if file contains similar class/function names
                if any(term in content.lower() for term in terms):
                    related.append(str(py_file.relative_to(self.project_dir)))
            except Exception:
                continue
        
        return related[:10]  # Limit to top 10
    
    def _compare_implementations(self, unused_file: str, unused_item: str, related_files: List[str]) -> Dict:
        """
        Compare unused implementation with related implementations.
        
        Returns:
            Comparison results with quality scores
        """
        unused_path = self.project_dir / unused_file
        
        try:
            unused_content = unused_path.read_text()
            unused_tree = ast.parse(unused_content)
            
            # Find the unused item in AST
            unused_node = self._find_item_in_ast(unused_tree, unused_item)
            if not unused_node:
                return {'quality': 'unknown', 'comparison': []}
            
            # Score unused implementation
            unused_score = self._score_implementation(unused_node, unused_content)
            
            # Compare with related files
            comparisons = []
            for related_file in related_files:
                related_path = self.project_dir / related_file
                try:
                    related_content = related_path.read_text()
                    related_tree = ast.parse(related_content)
                    
                    # Find similar items
                    for node in ast.walk(related_tree):
                        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                            score = self._score_implementation(node, related_content)
                            comparisons.append({
                                'file': related_file,
                                'item': node.name,
                                'score': score,
                                'better_than_unused': score > unused_score
                            })
                except Exception:
                    continue
            
            return {
                'unused_score': unused_score,
                'comparisons': comparisons,
                'is_best': all(c['score'] <= unused_score for c in comparisons)
            }
        except Exception as e:
            self.logger.debug(f"Could not compare implementations: {e}")
            return {'quality': 'unknown', 'comparison': []}
    
    def _find_item_in_ast(self, tree: ast.AST, item_name: str) -> Optional[ast.AST]:
        """Find a class or function in AST by name"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                if node.name == item_name:
                    return node
        return None
    
    def _score_implementation(self, node: ast.AST, content: str) -> float:
        """
        Score implementation quality (0-100).
        
        Factors:
        - Documentation (docstrings)
        - Type hints
        - Error handling
        - Code complexity
        - Method count (for classes)
        """
        score = 50.0  # Base score
        
        # Check for docstring
        if ast.get_docstring(node):
            score += 15
        
        # Check for type hints
        if isinstance(node, ast.FunctionDef):
            if node.returns:
                score += 5
            if any(arg.annotation for arg in node.args.args):
                score += 10
        
        # Check for error handling
        has_try_except = any(isinstance(n, ast.Try) for n in ast.walk(node))
        if has_try_except:
            score += 10
        
        # Check complexity (lower is better)
        complexity = self._calculate_complexity(node)
        if complexity < 5:
            score += 10
        elif complexity > 15:
            score -= 10
        
        # For classes, check method count
        if isinstance(node, ast.ClassDef):
            methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
            if 3 <= len(methods) <= 10:
                score += 10
        
        return max(0, min(100, score))
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
    
    def _analyze_integration_opportunities(
        self, unused_file: str, unused_item: str, 
        related_files: List[str], comparison: Dict
    ) -> Optional[str]:
        """
        Analyze if and how unused code should be integrated.
        
        Returns:
            Integration plan or None
        """
        if not comparison.get('is_best'):
            return None
        
        # If unused implementation is best, generate integration plan
        plan_parts = []
        plan_parts.append(f"The unused {unused_item} in {unused_file} appears to be a superior implementation.")
        plan_parts.append("\nIntegration steps:")
        plan_parts.append(f"1. Review {unused_item} implementation for correctness")
        
        if related_files:
            plan_parts.append(f"2. Refactor the following files to use {unused_item}:")
            for rf in related_files[:5]:
                plan_parts.append(f"   - {rf}")
            plan_parts.append(f"3. Update imports to reference {unused_file}")
            plan_parts.append("4. Deprecate inferior implementations")
            plan_parts.append("5. Run tests to verify integration")
        else:
            plan_parts.append(f"2. Identify files that should use {unused_item}")
            plan_parts.append("3. Add imports and integrate into codebase")
        
        return "\n".join(plan_parts)
    
    def _make_decision(
        self, project_stage: str, completion_pct: float,
        arch_alignment: str, comparison: Dict, integration_plan: Optional[str]
    ) -> Tuple[UnusedCodeDecision, float, str, bool]:
        """
        Make final decision about unused code.
        
        Returns:
            (decision, confidence, reasoning, refactoring_needed)
        """
        reasoning_parts = []
        reasoning_parts.append(f"Project stage: {project_stage} ({completion_pct:.1f}% complete)")
        reasoning_parts.append(f"Architecture alignment: {arch_alignment}")
        
        # Early stage project - be very conservative
        if project_stage == "early":
            if arch_alignment in ["matches", "better"]:
                if comparison.get('is_best') and integration_plan:
                    return (
                        UnusedCodeDecision.INTEGRATE,
                        0.8,
                        "\n".join(reasoning_parts) + "\n\nThis appears to be a superior implementation that should be integrated into the codebase.",
                        True
                    )
                else:
                    return (
                        UnusedCodeDecision.KEEP,
                        0.9,
                        "\n".join(reasoning_parts) + "\n\nIn early-stage projects, code that aligns with architecture should be kept for future integration.",
                        False
                    )
            else:
                return (
                    UnusedCodeDecision.REPORT,
                    0.7,
                    "\n".join(reasoning_parts) + "\n\nRequires developer review to determine if this is planned functionality or orphaned code.",
                    False
                )
        
        # Mid/late stage - can be more aggressive
        if comparison.get('is_best') and integration_plan:
            return (
                UnusedCodeDecision.INTEGRATE,
                0.9,
                "\n".join(reasoning_parts) + "\n\nSuperior implementation found - should refactor existing code to use this.",
                True
            )
        elif arch_alignment == "unrelated" and project_stage == "late":
            return (
                UnusedCodeDecision.REPORT,
                0.8,
                "\n".join(reasoning_parts) + "\n\nUnrelated to architecture in late-stage project - likely orphaned code.",
                False
            )
        else:
            return (
                UnusedCodeDecision.REPORT,
                0.7,
                "\n".join(reasoning_parts) + "\n\nRequires developer review to make final decision.",
                False
            )