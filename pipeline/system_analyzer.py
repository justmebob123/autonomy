"""
System Analyzer

Integrated analysis tool for the Autonomy system.
Combines polytopic structure analysis and deep recursive analysis
into a unified tool accessible from phases.
"""

import ast
import os
from pathlib import Path
from collections import defaultdict, deque
import re
from typing import Dict, List, Set, Tuple, Optional, Any

from .logging_setup import get_logger


class SystemAnalyzer:
    """
    Unified system analyzer combining polytopic and deep recursive analysis.
    
    This tool can be used by phases for:
    - Architecture validation
    - Performance optimization
    - Debugging assistance
    - Refactoring guidance
    - Quality assessment
    """
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.logger = get_logger()
        
        # Polytopic analysis data
        self.vertices = []
        self.adjacency = {}
        self.dimensions = {}
        
        # Deep analysis data
        self.call_graph = defaultdict(set)
        self.class_hierarchy = {}
        self.method_signatures = {}
        self.variable_flow = defaultdict(set)
        self.state_transitions = defaultdict(list)
        
        # Cache
        self._analysis_cache = {}
    
    # ========================================================================
    # PUBLIC API - Methods accessible from phases
    # ========================================================================
    
    def analyze_connectivity(self) -> Dict[str, Any]:
        """
        Analyze polytopic connectivity.
        
        Returns:
            Dict with connectivity metrics and recommendations
        """
        if 'connectivity' in self._analysis_cache:
            return self._analysis_cache['connectivity']
        
        self._load_polytope_structure()
        
        # Calculate metrics
        total_vertices = len(self.vertices)
        connected_vertices = len(self.adjacency)
        total_edges = sum(len(v) for v in self.adjacency.values())
        
        # Calculate reachability
        reachability = self._calculate_reachability()
        avg_reachability = sum(reachability.values()) / len(reachability) if reachability else 0
        
        # Find critical vertices
        critical = self._find_critical_vertices()
        
        # Find isolated phases
        connected_set = set(self.adjacency.keys())
        for edges in self.adjacency.values():
            connected_set.update(edges)
        isolated = [v for v in self.vertices if v not in connected_set]
        
        result = {
            'total_vertices': total_vertices,
            'connected_vertices': connected_vertices,
            'connectivity_percent': (connected_vertices / total_vertices * 100) if total_vertices else 0,
            'total_edges': total_edges,
            'avg_connectivity': (total_edges / connected_vertices) if connected_vertices else 0,
            'avg_reachability': avg_reachability,
            'critical_vertices': critical,
            'isolated_phases': isolated,
            'recommendations': self._generate_connectivity_recommendations(isolated, avg_reachability)
        }
        
        self._analysis_cache['connectivity'] = result
        return result
    
    def analyze_integration_depth(self, phase_name: str) -> Dict[str, Any]:
        """
        Analyze integration depth for a specific phase.
        
        Args:
            phase_name: Name of the phase to analyze
            
        Returns:
            Dict with integration metrics
        """
        phase_file = self.base_dir / "pipeline" / "phases" / f"{phase_name}.py"
        
        if not phase_file.exists():
            return {'error': f'Phase file not found: {phase_name}'}
        
        with open(phase_file, 'r') as f:
            content = f.read()
        
        # Count imports
        relative_imports = len(re.findall(r'from\s+\.\.', content))
        absolute_imports = len(re.findall(r'from\s+pipeline\.', content))
        
        # Count method calls to other subsystems
        method_calls = len(re.findall(r'self\.\w+\.\w+\(', content))
        
        # Count tool calls
        tool_calls = len(re.findall(r'tool_calls', content))
        
        total = relative_imports + absolute_imports + method_calls
        
        return {
            'phase': phase_name,
            'relative_imports': relative_imports,
            'absolute_imports': absolute_imports,
            'method_calls': method_calls,
            'tool_calls': tool_calls,
            'total_integration_points': total,
            'complexity_level': self._assess_integration_complexity(total)
        }
    
    def trace_variable_flow(self, variable_name: str) -> Dict[str, Any]:
        """
        Trace how a variable flows through the system.
        
        Args:
            variable_name: Name of the variable to trace
            
        Returns:
            Dict with flow information
        """
        if not self.variable_flow:
            self._analyze_all_files()
        
        if variable_name not in self.variable_flow:
            return {
                'variable': variable_name,
                'found': False,
                'message': 'Variable not found in flow analysis'
            }
        
        functions = list(self.variable_flow[variable_name])
        
        return {
            'variable': variable_name,
            'found': True,
            'flows_through': len(functions),
            'functions': functions[:20],  # Limit to 20
            'criticality': 'HIGH' if len(functions) > 20 else 'MEDIUM' if len(functions) > 10 else 'LOW'
        }
    
    def find_recursive_patterns(self) -> Dict[str, Any]:
        """
        Find recursive and circular call patterns.
        
        Returns:
            Dict with recursive patterns
        """
        if not self.call_graph:
            self._analyze_all_files()
        
        recursive = []
        circular = []
        
        for func in self.call_graph:
            # Check for direct recursion
            if func in self.call_graph[func]:
                recursive.append(func)
            
            # Check for circular calls
            visited = set()
            stack = [func]
            
            while stack:
                current = stack.pop()
                if current in visited:
                    if current == func:
                        circular.append(func)
                    continue
                
                visited.add(current)
                
                if current in self.call_graph:
                    for called in self.call_graph[current]:
                        if called == func:
                            circular.append(func)
                        else:
                            stack.append(called)
        
        return {
            'direct_recursion': list(set(recursive)),
            'circular_calls': list(set(circular)),
            'total_recursive': len(set(recursive)),
            'total_circular': len(set(circular)),
            'warning': len(set(recursive)) > 5 or len(set(circular)) > 5
        }
    
    def assess_code_quality(self, filepath: str) -> Dict[str, Any]:
        """
        Assess code quality for a specific file.
        
        Args:
            filepath: Path to the file to analyze
            
        Returns:
            Dict with quality metrics
        """
        full_path = self.base_dir / filepath
        
        if not full_path.exists():
            return {'error': f'File not found: {filepath}'}
        
        try:
            with open(full_path, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Count various elements
            classes = sum(1 for _ in ast.walk(tree) if isinstance(_, ast.ClassDef))
            functions = sum(1 for _ in ast.walk(tree) if isinstance(_, ast.FunctionDef))
            lines = len(content.split('\n'))
            
            # Calculate complexity indicators
            imports = len(re.findall(r'^(from|import)\s+', content, re.MULTILINE))
            comments = len(re.findall(r'#.*$', content, re.MULTILINE))
            docstrings = len(re.findall(r'""".*?"""', content, re.DOTALL))
            
            # Calculate metrics
            comment_ratio = (comments / lines * 100) if lines else 0
            avg_function_length = (lines / functions) if functions else 0
            
            return {
                'filepath': filepath,
                'lines': lines,
                'classes': classes,
                'functions': functions,
                'imports': imports,
                'comments': comments,
                'docstrings': docstrings,
                'comment_ratio': comment_ratio,
                'avg_function_length': avg_function_length,
                'quality_score': self._calculate_quality_score(
                    comment_ratio, avg_function_length, imports
                )
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def get_refactoring_suggestions(self, phase_name: str) -> List[str]:
        """
        Get refactoring suggestions for a phase.
        
        Args:
            phase_name: Name of the phase
            
        Returns:
            List of refactoring suggestions
        """
        suggestions = []
        
        # Analyze integration depth
        integration = self.analyze_integration_depth(phase_name)
        
        if integration.get('total_integration_points', 0) > 100:
            suggestions.append(
                f"High integration complexity ({integration['total_integration_points']} points). "
                "Consider creating facade modules to reduce coupling."
            )
        
        if integration.get('relative_imports', 0) > 10:
            suggestions.append(
                f"Many relative imports ({integration['relative_imports']}). "
                "Consider consolidating related imports into facade modules."
            )
        
        # Check for recursive patterns
        patterns = self.find_recursive_patterns()
        if phase_name in patterns.get('circular_calls', []):
            suggestions.append(
                "Circular call pattern detected. Review call chain to prevent infinite loops."
            )
        
        # Check connectivity
        connectivity = self.analyze_connectivity()
        if phase_name in connectivity.get('isolated_phases', []):
            suggestions.append(
                "Phase is isolated from polytopic navigation. Add adjacency relationships."
            )
        
        if not suggestions:
            suggestions.append("No major refactoring needed. Code quality is good.")
        
        return suggestions
    
    # ========================================================================
    # PRIVATE METHODS - Internal analysis logic
    # ========================================================================
    
    def _load_polytope_structure(self):
        """Load polytopic structure from coordinator"""
        if self.vertices and self.adjacency:
            return  # Already loaded
        
        # Load vertices
        phases_dir = self.base_dir / "pipeline" / "phases"
        if phases_dir.exists():
            for file in phases_dir.glob("*.py"):
                if file.name not in ["__init__.py", "base.py"]:
                    self.vertices.append(file.stem)
        
        # Load adjacency
        coordinator_file = self.base_dir / "pipeline" / "coordinator.py"
        if coordinator_file.exists():
            with open(coordinator_file, 'r') as f:
                content = f.read()
            
            # Extract polytope edges
            pattern = r"self\.polytope\['edges'\]\s*=\s*\{([^}]+)\}"
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                edges_content = match.group(1)
                for line in edges_content.split('\n'):
                    line = line.strip()
                    if ':' in line and not line.startswith('#'):
                        parts = line.split(':', 1)
                        phase = parts[0].strip().strip("'&quot;")
                        edges_str = parts[1].strip().rstrip(',')
                        
                        edges_match = re.findall(r"'([^']+)'", edges_str)
                        if edges_match and phase:
                            self.adjacency[phase] = edges_match
    
    def _calculate_reachability(self) -> Dict[str, int]:
        """Calculate reachability for each vertex"""
        reachable = {}
        
        for start in self.vertices:
            visited = set()
            queue = deque([start])
            visited.add(start)
            
            while queue:
                current = queue.popleft()
                
                if current in self.adjacency:
                    for neighbor in self.adjacency[current]:
                        if neighbor not in visited and neighbor in self.vertices:
                            visited.add(neighbor)
                            queue.append(neighbor)
            
            reachable[start] = len(visited) - 1
        
        return reachable
    
    def _find_critical_vertices(self) -> List[Tuple[str, int, int, int]]:
        """Find vertices with highest connectivity"""
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)
        
        for phase, edges in self.adjacency.items():
            out_degree[phase] = len(edges)
            for edge in edges:
                in_degree[edge] += 1
        
        critical = []
        for phase in self.vertices:
            total = in_degree[phase] + out_degree[phase]
            if total >= 4:
                critical.append((phase, in_degree[phase], out_degree[phase], total))
        
        return sorted(critical, key=lambda x: x[3], reverse=True)
    
    def _generate_connectivity_recommendations(self, isolated: List[str], 
                                              avg_reachability: float) -> List[str]:
        """Generate connectivity improvement recommendations"""
        recommendations = []
        
        if isolated:
            recommendations.append(
                f"Connect {len(isolated)} isolated phases: {', '.join(isolated)}"
            )
        
        if avg_reachability < 3.0:
            recommendations.append(
                f"Low average reachability ({avg_reachability:.1f}). "
                "Add strategic edges to improve polytopic navigation."
            )
        
        if not recommendations:
            recommendations.append("Connectivity is good. No major improvements needed.")
        
        return recommendations
    
    def _assess_integration_complexity(self, total_points: int) -> str:
        """Assess integration complexity level"""
        if total_points > 100:
            return "VERY HIGH"
        elif total_points > 50:
            return "HIGH"
        elif total_points > 25:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_quality_score(self, comment_ratio: float, 
                                 avg_function_length: float, 
                                 imports: int) -> float:
        """Calculate overall quality score"""
        score = 100.0
        
        # Penalize low comment ratio
        if comment_ratio < 10:
            score -= (10 - comment_ratio) * 2
        
        # Penalize long functions
        if avg_function_length > 50:
            score -= (avg_function_length - 50) * 0.5
        
        # Penalize too many imports
        if imports > 20:
            score -= (imports - 20) * 1
        
        return max(0, min(100, score))
    
    def _analyze_all_files(self):
        """Analyze all Python files for deep analysis"""
        if self.call_graph:
            return  # Already analyzed
        
        for root, dirs, files in os.walk(self.base_dir / "pipeline"):
            for file in files:
                if file.endswith('.py'):
                    filepath = Path(root) / file
                    self._analyze_file(filepath)
    
    def _analyze_file(self, filepath: Path):
        """Analyze a single Python file"""
        try:
            with open(filepath, 'r') as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    self._analyze_function(node, filepath)
                elif isinstance(node, ast.Call):
                    self._analyze_call(node)
        
        except SyntaxError as e:
            self.logger.debug(f"Skipping {filepath} due to syntax error: {e}")
        except Exception as e:
            self.logger.warning(f"Failed to analyze {filepath}: {e}")
    
    def _analyze_function(self, node: ast.FunctionDef, filepath: Path):
        """Analyze a function definition"""
        func_name = node.name
        
        # Extract parameters
        params = [arg.arg for arg in node.args.args]
        
        self.method_signatures[func_name] = {
            'file': str(filepath),
            'params': params
        }
        
        # Analyze calls within function
        for item in ast.walk(node):
            if isinstance(item, ast.Call):
                called = self._get_name(item.func)
                if called:
                    self.call_graph[func_name].add(called)
    
    def _analyze_call(self, node: ast.Call):
        """Analyze a function call"""
        func_name = self._get_name(node.func)
        
        if func_name:
            for arg in node.args:
                if isinstance(arg, ast.Name):
                    self.variable_flow[arg.id].add(func_name)
    
    def _get_name(self, node) -> Optional[str]:
        """Extract name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_name(node.value)
            if value:
                return f"{value}.{node.attr}"
            return node.attr
        return None