"""
Depth-59 Recursive Polytopic Structure Analysis

This script performs a comprehensive recursive analysis of the hyperdimensional
polytopic system, examining all vertices, faces, adjacency relationships, and
integration points across all subsystems.
"""

import ast
import inspect
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict
import json

class PolytopicAnalyzer:
    """Deep recursive analyzer for polytopic structure."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.vertices = {}  # All classes/functions as vertices
        self.edges = defaultdict(list)  # Adjacency relationships
        self.call_stacks = []  # All call stacks
        self.variable_states = defaultdict(list)  # Variable state changes
        self.integration_points = []  # Cross-system integration points
        self.emergent_properties = []  # Discovered emergent properties
        self.depth_limit = 59
        
    def analyze_all_systems(self):
        """Perform depth-59 recursive analysis of all systems."""
        print("=" * 80)
        print("DEPTH-59 POLYTOPIC STRUCTURE ANALYSIS")
        print("=" * 80)
        
        # Phase 1: Discover all vertices (classes, functions, methods)
        print("\n[PHASE 1] Discovering vertices...")
        self.discover_vertices()
        print(f"  Found {len(self.vertices)} vertices")
        
        # Phase 2: Map adjacency relationships
        print("\n[PHASE 2] Mapping adjacency relationships...")
        self.map_adjacency()
        print(f"  Found {sum(len(v) for v in self.edges.values())} edges")
        
        # Phase 3: Trace call stacks to depth 59
        print("\n[PHASE 3] Tracing call stacks to depth 59...")
        self.trace_call_stacks()
        print(f"  Traced {len(self.call_stacks)} call stacks")
        
        # Phase 4: Track variable state changes
        print("\n[PHASE 4] Tracking variable state changes...")
        self.track_variable_states()
        print(f"  Tracked {len(self.variable_states)} variables")
        
        # Phase 5: Identify integration points
        print("\n[PHASE 5] Identifying integration points...")
        self.identify_integration_points()
        print(f"  Found {len(self.integration_points)} integration points")
        
        # Phase 6: Analyze emergent properties
        print("\n[PHASE 6] Analyzing emergent properties...")
        self.analyze_emergent_properties()
        print(f"  Discovered {len(self.emergent_properties)} emergent properties")
        
        # Phase 7: Generate comprehensive report
        print("\n[PHASE 7] Generating comprehensive report...")
        self.generate_report()
        
    def discover_vertices(self):
        """Discover all vertices (classes, functions, methods) in the system."""
        python_files = list(self.project_root.rglob("*.py"))
        
        for file_path in python_files:
            if "__pycache__" in str(file_path) or "test" in str(file_path):
                continue
                
            try:
                with open(file_path, 'r') as f:
                    tree = ast.parse(f.read(), filename=str(file_path))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        vertex_id = f"{file_path.stem}.{node.name}"
                        self.vertices[vertex_id] = {
                            'type': 'class',
                            'name': node.name,
                            'file': str(file_path),
                            'methods': [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                            'bases': [self._get_name(b) for b in node.bases],
                            'line': node.lineno
                        }
                    elif isinstance(node, ast.FunctionDef):
                        vertex_id = f"{file_path.stem}.{node.name}"
                        self.vertices[vertex_id] = {
                            'type': 'function',
                            'name': node.name,
                            'file': str(file_path),
                            'args': [arg.arg for arg in node.args.args],
                            'line': node.lineno
                        }
            except Exception as e:
                pass
    
    def map_adjacency(self):
        """Map adjacency relationships between vertices."""
        python_files = list(self.project_root.rglob("*.py"))
        
        for file_path in python_files:
            if "__pycache__" in str(file_path) or "test" in str(file_path):
                continue
                
            try:
                with open(file_path, 'r') as f:
                    tree = ast.parse(f.read(), filename=str(file_path))
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                        source_id = f"{file_path.stem}.{node.name}"
                        
                        # Find all calls within this vertex
                        for child in ast.walk(node):
                            if isinstance(child, ast.Call):
                                target_name = self._get_call_name(child)
                                if target_name:
                                    self.edges[source_id].append(target_name)
                            
                            # Track attribute access (dimensional_profile, etc.)
                            elif isinstance(child, ast.Attribute):
                                attr_name = child.attr
                                self.edges[source_id].append(f"attr:{attr_name}")
            except Exception as e:
                pass
    
    def trace_call_stacks(self):
        """Trace call stacks recursively to depth 59."""
        # Start from key entry points
        entry_points = [
            'coordinator.PhaseCoordinator',
            'coordinator._determine_next_action_strategic',
            'polytopic_manager.PolytopicObjectiveManager',
            'polytopic_objective.PolytopicObjective',
            'dimensional_space.DimensionalSpace',
            'message_bus.MessageBus'
        ]
        
        for entry in entry_points:
            if entry in self.vertices:
                stack = self._trace_recursive(entry, depth=0, visited=set())
                if stack:
                    self.call_stacks.append(stack)
    
    def _trace_recursive(self, vertex_id: str, depth: int, visited: Set[str]) -> List[str]:
        """Recursively trace call stack to depth limit."""
        if depth >= self.depth_limit or vertex_id in visited:
            return []
        
        visited.add(vertex_id)
        stack = [vertex_id]
        
        # Get adjacent vertices
        adjacent = self.edges.get(vertex_id, [])
        
        for adj in adjacent[:5]:  # Limit branching factor
            if not adj.startswith("attr:"):
                sub_stack = self._trace_recursive(adj, depth + 1, visited.copy())
                if sub_stack:
                    stack.extend(sub_stack)
        
        return stack
    
    def track_variable_states(self):
        """Track variable state changes throughout call stacks."""
        key_variables = [
            'dimensional_profile',
            'polytopic_position',
            'complexity_score',
            'risk_score',
            'readiness_score',
            'dimensional_velocity',
            'objective',
            'state',
            'health'
        ]
        
        python_files = list(self.project_root.rglob("*.py"))
        
        for file_path in python_files:
            if "__pycache__" in str(file_path) or "test" in str(file_path):
                continue
                
            try:
                with open(file_path, 'r') as f:
                    tree = ast.parse(f.read(), filename=str(file_path))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id in key_variables:
                                self.variable_states[target.id].append({
                                    'file': str(file_path),
                                    'line': node.lineno,
                                    'context': 'assignment'
                                })
                            elif isinstance(target, ast.Attribute) and target.attr in key_variables:
                                self.variable_states[target.attr].append({
                                    'file': str(file_path),
                                    'line': node.lineno,
                                    'context': 'attribute_assignment'
                                })
            except Exception as e:
                pass
    
    def identify_integration_points(self):
        """Identify cross-system integration points."""
        # Key integration patterns to look for
        patterns = [
            ('coordinator', 'polytopic'),
            ('coordinator', 'messaging'),
            ('polytopic', 'objective_manager'),
            ('phases', 'messaging'),
            ('phases', 'polytopic'),
            ('dimensional_space', 'polytopic_objective')
        ]
        
        for source_pattern, target_pattern in patterns:
            for vertex_id, adjacent in self.edges.items():
                if source_pattern in vertex_id:
                    for adj in adjacent:
                        if target_pattern in adj:
                            self.integration_points.append({
                                'source': vertex_id,
                                'target': adj,
                                'type': f"{source_pattern}→{target_pattern}"
                            })
    
    def analyze_emergent_properties(self):
        """Analyze emergent properties from the polytopic structure."""
        # Property 1: Dimensional convergence
        dimensional_refs = sum(1 for v in self.variable_states.get('dimensional_profile', []))
        if dimensional_refs > 10:
            self.emergent_properties.append({
                'property': 'dimensional_convergence',
                'description': 'Multiple subsystems converge on dimensional profiles',
                'strength': dimensional_refs / 10.0
            })
        
        # Property 2: Health propagation
        health_refs = sum(1 for v in self.variable_states.get('health', []))
        if health_refs > 5:
            self.emergent_properties.append({
                'property': 'health_propagation',
                'description': 'Health state propagates through system',
                'strength': health_refs / 5.0
            })
        
        # Property 3: Polytopic clustering
        polytopic_vertices = [v for v in self.vertices if 'polytopic' in v]
        if len(polytopic_vertices) > 3:
            self.emergent_properties.append({
                'property': 'polytopic_clustering',
                'description': 'Polytopic subsystem forms cohesive cluster',
                'strength': len(polytopic_vertices) / 3.0
            })
        
        # Property 4: Message flow network
        message_edges = sum(1 for edges in self.edges.values() for e in edges if 'message' in e.lower())
        if message_edges > 20:
            self.emergent_properties.append({
                'property': 'message_flow_network',
                'description': 'Complex message flow network emerges',
                'strength': message_edges / 20.0
            })
    
    def generate_report(self):
        """Generate comprehensive analysis report."""
        report = {
            'analysis_depth': self.depth_limit,
            'vertices': {
                'total': len(self.vertices),
                'by_type': self._count_by_type(),
                'polytopic_vertices': [v for v in self.vertices if 'polytopic' in v]
            },
            'edges': {
                'total': sum(len(v) for v in self.edges.values()),
                'by_source': {k: len(v) for k, v in list(self.edges.items())[:10]}
            },
            'call_stacks': {
                'total': len(self.call_stacks),
                'max_depth': max(len(s) for s in self.call_stacks) if self.call_stacks else 0,
                'avg_depth': sum(len(s) for s in self.call_stacks) / len(self.call_stacks) if self.call_stacks else 0
            },
            'variable_states': {
                'tracked_variables': len(self.variable_states),
                'total_state_changes': sum(len(v) for v in self.variable_states.values()),
                'by_variable': {k: len(v) for k, v in self.variable_states.items()}
            },
            'integration_points': {
                'total': len(self.integration_points),
                'by_type': self._count_integration_types()
            },
            'emergent_properties': {
                'total': len(self.emergent_properties),
                'properties': self.emergent_properties
            }
        }
        
        # Save report
        with open(self.project_root / 'DEPTH_59_ANALYSIS_REPORT.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "=" * 80)
        print("ANALYSIS SUMMARY")
        print("=" * 80)
        print(f"\nVertices: {report['vertices']['total']}")
        print(f"Edges: {report['edges']['total']}")
        print(f"Call Stacks: {report['call_stacks']['total']}")
        print(f"  Max Depth: {report['call_stacks']['max_depth']}")
        print(f"  Avg Depth: {report['call_stacks']['avg_depth']:.1f}")
        print(f"\nVariable State Changes: {report['variable_states']['total_state_changes']}")
        print(f"Integration Points: {report['integration_points']['total']}")
        print(f"Emergent Properties: {report['emergent_properties']['total']}")
        
        print("\nTop Emergent Properties:")
        for prop in sorted(self.emergent_properties, key=lambda x: x['strength'], reverse=True)[:5]:
            print(f"  • {prop['property']}: {prop['description']} (strength: {prop['strength']:.2f})")
        
        print("\n" + "=" * 80)
        print("Report saved to: DEPTH_59_ANALYSIS_REPORT.json")
        print("=" * 80)
    
    def _get_name(self, node):
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return str(node)
    
    def _get_call_name(self, node):
        """Get function name from Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None
    
    def _count_by_type(self):
        """Count vertices by type."""
        counts = defaultdict(int)
        for vertex in self.vertices.values():
            counts[vertex['type']] += 1
        return dict(counts)
    
    def _count_integration_types(self):
        """Count integration points by type."""
        counts = defaultdict(int)
        for point in self.integration_points:
            counts[point['type']] += 1
        return dict(counts)


if __name__ == "__main__":
    analyzer = PolytopicAnalyzer(".")
    analyzer.analyze_all_systems()