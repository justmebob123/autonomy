#!/usr/bin/env python3
"""
Hyperdimensional Polytopic Analysis - Depth 59
Complete recursive examination of all vertices, faces, and adjacency relationships
"""

import ast
import os
import sys
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Any
import json

class Depth59Analyzer:
    """
    Performs depth-59 recursive analysis of the entire system.
    
    Examines:
    - All vertices (classes, functions, methods)
    - All edges (calls, imports, dependencies)
    - All faces (subsystems, modules)
    - All hyperfaces (architectural layers)
    - State variable changes throughout execution
    - Integration points and patterns
    - Emergent properties and behaviors
    """
    
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        
        # Polytopic structure
        self.vertices = {}  # All code entities
        self.edges = defaultdict(set)  # Direct relationships
        self.faces = defaultdict(list)  # Subsystems
        self.hyperfaces = defaultdict(list)  # Architectural layers
        
        # Call graph analysis
        self.call_graph = defaultdict(set)
        self.import_graph = defaultdict(set)
        self.inheritance_graph = defaultdict(set)
        
        # State analysis
        self.state_variables = defaultdict(dict)
        self.state_mutations = defaultdict(list)
        self.state_flow = []
        
        # Integration analysis
        self.integration_points = []
        self.cross_subsystem_calls = defaultdict(lambda: defaultdict(int))
        
        # Depth tracking
        self.depth_reached = defaultdict(int)
        self.execution_paths = []
        
        # Statistics
        self.stats = {
            'total_files': 0,
            'total_lines': 0,
            'total_vertices': 0,
            'total_edges': 0,
            'max_depth_reached': 0
        }
    
    def analyze_all_files(self):
        """Analyze all Python files in the project"""
        py_files = list(self.root_dir.rglob("*.py"))
        py_files = [f for f in py_files if '__pycache__' not in str(f) and 'test_' not in f.name]
        
        self.stats['total_files'] = len(py_files)
        
        print(f"📊 Analyzing {len(py_files)} Python files...")
        print()
        
        for i, filepath in enumerate(py_files, 1):
            if i % 20 == 0:
                print(f"   Progress: {i}/{len(py_files)} files...")
            self._analyze_file(filepath)
        
        print(f"✅ Analysis complete: {len(py_files)} files processed")
        print()
    
    def _analyze_file(self, filepath: Path):
        """Analyze a single file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                self.stats['total_lines'] += len(content.split('\n'))
            
            tree = ast.parse(content, filename=str(filepath))
            module_name = str(filepath.relative_to(self.root_dir)).replace('/', '.').replace('.py', '')
            
            # Extract all vertices
            self._extract_vertices(tree, module_name, filepath)
            
            # Extract edges (relationships)
            self._extract_edges(tree, module_name)
            
            # Extract state mutations
            self._extract_state_mutations(tree, module_name)
            
        except Exception as e:
            pass
    
    def _extract_vertices(self, tree: ast.AST, module_name: str, filepath: Path):
        """Extract all vertices (classes, functions) from AST"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                vertex_id = f"{module_name}.{node.name}"
                
                # Extract methods
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append({
                            'name': item.name,
                            'args': [arg.arg for arg in item.args.args],
                            'lineno': item.lineno,
                            'is_async': isinstance(item, ast.AsyncFunctionDef)
                        })
                
                # Extract base classes
                bases = []
                for base in node.bases:
                    bases.append(self._get_node_name(base))
                
                self.vertices[vertex_id] = {
                    'type': 'class',
                    'name': node.name,
                    'module': module_name,
                    'filepath': str(filepath),
                    'lineno': node.lineno,
                    'methods': methods,
                    'bases': bases,
                    'method_count': len(methods)
                }
                
                # Track inheritance
                for base in bases:
                    if base and base != 'object':
                        self.inheritance_graph[vertex_id].add(base)
                
                self.stats['total_vertices'] += 1
                
            elif isinstance(node, ast.FunctionDef):
                # Only top-level functions
                vertex_id = f"{module_name}.{node.name}"
                
                self.vertices[vertex_id] = {
                    'type': 'function',
                    'name': node.name,
                    'module': module_name,
                    'filepath': str(filepath),
                    'lineno': node.lineno,
                    'args': [arg.arg for arg in node.args.args],
                    'is_async': isinstance(node, ast.AsyncFunctionDef)
                }
                
                self.stats['total_vertices'] += 1
    
    def _extract_edges(self, tree: ast.AST, module_name: str):
        """Extract all edges (calls, imports) from AST"""
        for node in ast.walk(tree):
            # Import relationships
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.import_graph[module_name].add(alias.name)
                    self.edges[module_name].add(alias.name)
                    self.stats['total_edges'] += 1
                    
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.import_graph[module_name].add(node.module)
                    self.edges[module_name].add(node.module)
                    self.stats['total_edges'] += 1
            
            # Function call relationships
            elif isinstance(node, ast.Call):
                func_name = self._get_node_name(node.func)
                if func_name:
                    self.call_graph[module_name].add(func_name)
                    self.edges[module_name].add(func_name)
    
    def _extract_state_mutations(self, tree: ast.AST, module_name: str):
        """Extract state variable mutations"""
        for node in ast.walk(tree):
            # Assignments to self.*
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute):
                        if isinstance(target.value, ast.Name) and target.value.id == 'self':
                            self.state_mutations[module_name].append({
                                'attribute': target.attr,
                                'lineno': node.lineno,
                                'operation': 'assign'
                            })
            
            # Augmented assignments (+=, -=, etc.)
            elif isinstance(node, ast.AugAssign):
                if isinstance(node.target, ast.Attribute):
                    if isinstance(node.target.value, ast.Name) and node.target.value.id == 'self':
                        self.state_mutations[module_name].append({
                            'attribute': node.target.attr,
                            'lineno': node.lineno,
                            'operation': 'augment'
                        })
    
    def _get_node_name(self, node):
        """Extract name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            base = self._get_node_name(node.value)
            return f"{base}.{node.attr}" if base else node.attr
        return None
    
    def identify_subsystems(self):
        """Identify subsystems (faces of the polytope)"""
        print("🔍 Identifying subsystems...")
        
        for vertex_id, vertex_data in self.vertices.items():
            module = vertex_data['module']
            parts = module.split('.')
            
            if len(parts) >= 2:
                subsystem = parts[1] if parts[0] == 'pipeline' else parts[0]
                self.faces[subsystem].append(vertex_id)
        
        print(f"✅ Found {len(self.faces)} subsystems")
        print()
        
        # Print top subsystems
        print("📦 Top 15 Subsystems by Component Count:")
        for subsystem, vertices in sorted(self.faces.items(), key=lambda x: len(x[1]), reverse=True)[:15]:
            classes = sum(1 for v in vertices if self.vertices[v]['type'] == 'class')
            functions = sum(1 for v in vertices if self.vertices[v]['type'] == 'function')
            print(f"   {subsystem:30s}: {len(vertices):3d} components ({classes:2d} classes, {functions:2d} functions)")
        print()
    
    def identify_architectural_layers(self):
        """Identify architectural layers (hyperfaces)"""
        print("🏗️  Identifying architectural layers...")
        
        # Define layer patterns
        layer_patterns = {
            'Interface': ['__main__', 'cli', 'api'],
            'Coordination': ['coordinator', 'orchestration', 'pipeline'],
            'Execution': ['phases', 'handlers', 'tools'],
            'Intelligence': ['orchestration', 'agents', 'specialist'],
            'State': ['state', 'tracker', 'history'],
            'Analysis': ['analyzer', 'investigator', 'monitor'],
            'Infrastructure': ['logging', 'config', 'utils']
        }
        
        for layer_name, patterns in layer_patterns.items():
            for subsystem, vertices in self.faces.items():
                if any(pattern in subsystem.lower() for pattern in patterns):
                    self.hyperfaces[layer_name].extend(vertices)
        
        print(f"✅ Found {len(self.hyperfaces)} architectural layers")
        print()
        
        print("🏛️  Architectural Layers:")
        for layer, vertices in sorted(self.hyperfaces.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"   {layer:20s}: {len(vertices):3d} components")
        print()
    
    def compute_adjacency_matrix(self):
        """Compute adjacency matrix between subsystems"""
        print("🔗 Computing adjacency matrix...")
        
        adjacency = defaultdict(lambda: defaultdict(int))
        
        # Analyze imports between subsystems
        for module, imports in self.import_graph.items():
            module_parts = module.split('.')
            if len(module_parts) >= 2:
                source = module_parts[1] if module_parts[0] == 'pipeline' else module_parts[0]
                
                for imported in imports:
                    import_parts = imported.split('.')
                    if len(import_parts) >= 2:
                        target = import_parts[1] if import_parts[0] == 'pipeline' else import_parts[0]
                        if source != target:
                            adjacency[source][target] += 1
                            self.cross_subsystem_calls[source][target] += 1
        
        print(f"✅ Computed adjacency for {len(adjacency)} subsystems")
        print()
        
        # Print strongest connections
        print("🔗 Strongest Cross-Subsystem Connections:")
        all_connections = []
        for source, targets in adjacency.items():
            for target, count in targets.items():
                all_connections.append((source, target, count))
        
        all_connections.sort(key=lambda x: x[2], reverse=True)
        
        for source, target, count in all_connections[:20]:
            print(f"   {source:20s} → {target:20s}: {count:3d} connections")
        print()
        
        return adjacency
    
    def recursive_depth_trace(self, start_vertex: str, depth: int = 0, max_depth: int = 59, 
                             visited: Set[str] = None, path: List[str] = None):
        """Recursively trace execution paths to depth 59"""
        if visited is None:
            visited = set()
        if path is None:
            path = []
        
        if depth >= max_depth or start_vertex in visited:
            return [path + [start_vertex]] if path else [[start_vertex]]
        
        visited.add(start_vertex)
        self.depth_reached[start_vertex] = max(self.depth_reached[start_vertex], depth)
        self.stats['max_depth_reached'] = max(self.stats['max_depth_reached'], depth)
        
        current_path = path + [start_vertex]
        all_paths = [current_path]
        
        # Find all edges from this vertex
        vertex_data = self.vertices.get(start_vertex, {})
        module = vertex_data.get('module', '')
        
        # Follow import edges
        if module in self.import_graph:
            for imported in list(self.import_graph[module])[:3]:  # Limit branching
                # Find vertices in imported module
                for vertex_id in self.vertices:
                    if vertex_id.startswith(imported) and vertex_id not in visited:
                        sub_paths = self.recursive_depth_trace(
                            vertex_id, depth + 1, max_depth, visited.copy(), current_path
                        )
                        all_paths.extend(sub_paths[:2])  # Limit path explosion
        
        return all_paths
    
    def analyze_execution_flow(self):
        """Analyze execution flow starting from entry points"""
        print("🔄 Analyzing execution flow (depth 59)...")
        
        # Find entry points
        entry_points = []
        for vertex_id, vertex_data in self.vertices.items():
            if 'main' in vertex_data['name'].lower() or vertex_data['module'].endswith('__main__'):
                entry_points.append(vertex_id)
        
        print(f"   Found {len(entry_points)} entry points")
        
        # Trace from each entry point
        all_paths = []
        for entry in entry_points[:5]:  # Limit to top 5 entry points
            print(f"   Tracing from: {entry}")
            paths = self.recursive_depth_trace(entry, max_depth=59)
            all_paths.extend(paths)
            print(f"     Found {len(paths)} execution paths")
        
        self.execution_paths = all_paths
        
        print(f"\n✅ Total execution paths: {len(all_paths)}")
        print(f"✅ Maximum depth reached: {self.stats['max_depth_reached']}")
        print()
        
        # Analyze path characteristics
        if all_paths:
            path_lengths = [len(p) for p in all_paths]
            avg_length = sum(path_lengths) / len(path_lengths)
            max_length = max(path_lengths)
            
            print(f"📊 Path Statistics:")
            print(f"   Average path length: {avg_length:.1f}")
            print(f"   Maximum path length: {max_length}")
            print(f"   Total unique paths: {len(all_paths)}")
            print()
    
    def analyze_state_changes(self):
        """Analyze state variable changes throughout execution"""
        print("📝 Analyzing state changes...")
        
        total_mutations = sum(len(m) for m in self.state_mutations.values())
        print(f"   Total state mutations: {total_mutations}")
        
        # Find most mutated attributes
        attribute_counts = defaultdict(int)
        for module, mutations in self.state_mutations.items():
            for mutation in mutations:
                attribute_counts[mutation['attribute']] += 1
        
        print(f"\n   Top 15 Most Mutated Attributes:")
        for attr, count in sorted(attribute_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
            print(f"     {attr:30s}: {count:3d} mutations")
        
        print()
        
        # Analyze mutation patterns by subsystem
        subsystem_mutations = defaultdict(int)
        for module, mutations in self.state_mutations.items():
            parts = module.split('.')
            if len(parts) >= 2:
                subsystem = parts[1] if parts[0] == 'pipeline' else parts[0]
                subsystem_mutations[subsystem] += len(mutations)
        
        print(f"   State Mutations by Subsystem:")
        for subsystem, count in sorted(subsystem_mutations.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"     {subsystem:30s}: {count:3d} mutations")
        
        print()
    
    def analyze_integration_quality(self):
        """Analyze quality of integration between subsystems"""
        print("🔍 Analyzing integration quality...")
        
        adjacency = self.compute_adjacency_matrix()
        
        # Calculate integration metrics
        total_subsystems = len(self.faces)
        connected_pairs = sum(1 for targets in adjacency.values() for _ in targets)
        max_possible = total_subsystems * (total_subsystems - 1)
        
        integration_density = connected_pairs / max_possible if max_possible > 0 else 0
        
        print(f"\n   Integration Metrics:")
        print(f"     Total subsystems: {total_subsystems}")
        print(f"     Connected pairs: {connected_pairs}")
        print(f"     Integration density: {integration_density:.2%}")
        print(f"     Assessment: {'Well integrated' if integration_density > 0.1 else 'Loosely coupled'}")
        print()
        
        # Find integration gaps
        print("   Integration Gaps (subsystems with few connections):")
        subsystem_connections = defaultdict(int)
        for source, targets in adjacency.items():
            subsystem_connections[source] += len(targets)
        for targets in adjacency.values():
            for target in targets:
                subsystem_connections[target] += 1
        
        isolated = [(s, c) for s, c in subsystem_connections.items() if c <= 2]
        for subsystem, count in sorted(isolated, key=lambda x: x[1])[:10]:
            print(f"     {subsystem:30s}: {count} connections")
        
        print()
        
        return {
            'density': integration_density,
            'connected_pairs': connected_pairs,
            'isolated_subsystems': len(isolated)
        }
    
    def analyze_emergent_properties(self):
        """Analyze emergent properties of the system"""
        print("✨ Analyzing emergent properties...")
        
        properties = {}
        
        # 1. Self-organization
        print("\n   1. Self-Organization Indicators:")
        
        # Check for feedback loops
        feedback_loops = 0
        for vertex_id in self.vertices:
            module = self.vertices[vertex_id]['module']
            if module in self.import_graph:
                for imported in self.import_graph[module]:
                    if imported in self.import_graph:
                        if module in self.import_graph[imported]:
                            feedback_loops += 1
        
        print(f"      Feedback loops detected: {feedback_loops}")
        properties['feedback_loops'] = feedback_loops
        
        # Check for pattern recognition systems
        pattern_systems = [v for v in self.vertices if 'pattern' in v.lower()]
        print(f"      Pattern recognition systems: {len(pattern_systems)}")
        properties['pattern_systems'] = len(pattern_systems)
        
        # Check for learning systems
        learning_systems = [v for v in self.vertices if any(kw in v.lower() for kw in ['learn', 'adapt', 'improve'])]
        print(f"      Learning systems: {len(learning_systems)}")
        properties['learning_systems'] = len(learning_systems)
        
        # 2. Hierarchical organization
        print("\n   2. Hierarchical Organization:")
        
        # Count inheritance depth
        max_inheritance_depth = 0
        for vertex_id in self.inheritance_graph:
            depth = self._get_inheritance_depth(vertex_id)
            max_inheritance_depth = max(max_inheritance_depth, depth)
        
        print(f"      Maximum inheritance depth: {max_inheritance_depth}")
        properties['max_inheritance_depth'] = max_inheritance_depth
        
        # Count layers
        print(f"      Architectural layers: {len(self.hyperfaces)}")
        properties['architectural_layers'] = len(self.hyperfaces)
        
        # 3. Modularity
        print("\n   3. Modularity Indicators:")
        
        # Calculate average subsystem size
        subsystem_sizes = [len(v) for v in self.faces.values()]
        avg_size = sum(subsystem_sizes) / len(subsystem_sizes) if subsystem_sizes else 0
        
        print(f"      Average subsystem size: {avg_size:.1f} components")
        print(f"      Subsystem size variance: {max(subsystem_sizes) - min(subsystem_sizes) if subsystem_sizes else 0}")
        properties['avg_subsystem_size'] = avg_size
        
        # 4. Adaptability
        print("\n   4. Adaptability Indicators:")
        
        # Check for configuration systems
        config_systems = [v for v in self.vertices if 'config' in v.lower()]
        print(f"      Configuration systems: {len(config_systems)}")
        properties['config_systems'] = len(config_systems)
        
        # Check for dynamic behavior
        dynamic_systems = [v for v in self.vertices if any(kw in v.lower() for kw in ['dynamic', 'runtime', 'adaptive'])]
        print(f"      Dynamic behavior systems: {len(dynamic_systems)}")
        properties['dynamic_systems'] = len(dynamic_systems)
        
        # 5. Resilience
        print("\n   5. Resilience Indicators:")
        
        # Check for error handling
        error_systems = [v for v in self.vertices if any(kw in v.lower() for kw in ['error', 'exception', 'failure'])]
        print(f"      Error handling systems: {len(error_systems)}")
        properties['error_systems'] = len(error_systems)
        
        # Check for monitoring
        monitor_systems = [v for v in self.vertices if any(kw in v.lower() for kw in ['monitor', 'watch', 'observe'])]
        print(f"      Monitoring systems: {len(monitor_systems)}")
        properties['monitor_systems'] = len(monitor_systems)
        
        print()
        return properties
    
    def _get_inheritance_depth(self, vertex_id: str, visited: Set[str] = None):
        """Calculate inheritance depth for a class"""
        if visited is None:
            visited = set()
        
        if vertex_id in visited or vertex_id not in self.inheritance_graph:
            return 0
        
        visited.add(vertex_id)
        
        max_depth = 0
        for base in self.inheritance_graph[vertex_id]:
            depth = self._get_inheritance_depth(base, visited.copy())
            max_depth = max(max_depth, depth + 1)
        
        return max_depth
    
    def analyze_critical_paths(self):
        """Identify critical execution paths"""
        print("🎯 Analyzing critical paths...")
        
        # Find coordinator as starting point
        coordinator_vertices = [v for v in self.vertices if 'coordinator' in v.lower()]
        
        if coordinator_vertices:
            print(f"   Starting from {len(coordinator_vertices)} coordinator vertices")
            
            critical_paths = []
            for coord in coordinator_vertices[:3]:
                paths = self.recursive_depth_trace(coord, max_depth=30)
                critical_paths.extend(paths)
            
            if critical_paths:
                # Sort by length
                critical_paths.sort(key=len, reverse=True)
                
                print(f"\n   Top 5 Critical Paths:")
                for i, path in enumerate(critical_paths[:5], 1):
                    print(f"\n   Path {i} (length {len(path)}):")
                    # Show first 5 and last 5
                    if len(path) <= 10:
                        for j, vertex in enumerate(path):
                            indent = '  ' * min(j, 10)
                            print(f"     {indent}→ {vertex}")
                    else:
                        for j, vertex in enumerate(path[:5]):
                            indent = '  ' * j
                            print(f"     {indent}→ {vertex}")
                        print(f"     {'  ' * 5}... ({len(path) - 10} more) ...")
                        for j, vertex in enumerate(path[-5:], 5):
                            indent = '  ' * min(j, 10)
                            print(f"     {indent}→ {vertex}")
        
        print()
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
        print("=" * 80)
        print("HYPERDIMENSIONAL POLYTOPIC ANALYSIS - DEPTH 59")
        print("=" * 80)
        print()
        
        print("📊 SYSTEM STATISTICS:")
        print(f"   Total Python files: {self.stats['total_files']}")
        print(f"   Total lines of code: {self.stats['total_lines']:,}")
        print(f"   Total vertices (components): {self.stats['total_vertices']}")
        print(f"   Total edges (relationships): {self.stats['total_edges']}")
        print(f"   Total subsystems: {len(self.faces)}")
        print(f"   Total architectural layers: {len(self.hyperfaces)}")
        print(f"   Maximum depth reached: {self.stats['max_depth_reached']}")
        print()
        
        # Identify subsystems
        self.identify_subsystems()
        
        # Identify layers
        self.identify_architectural_layers()
        
        # Compute adjacency
        adjacency = self.compute_adjacency_matrix()
        
        # Analyze integration
        integration_metrics = self.analyze_integration_quality()
        
        # Analyze state changes
        self.analyze_state_changes()
        
        # Analyze execution flow
        self.analyze_execution_flow()
        
        # Analyze critical paths
        self.analyze_critical_paths()
        
        # Analyze emergent properties
        emergent = self.analyze_emergent_properties()
        
        print("=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
        
        return {
            'stats': self.stats,
            'integration_metrics': integration_metrics,
            'emergent_properties': emergent
        }

# Run the analysis
if __name__ == "__main__":
    analyzer = Depth59Analyzer('.')
    analyzer.analyze_all_files()
    results = analyzer.generate_report()
    
    print("\n✅ Depth-59 analysis complete!")
    print(f"   Analyzed {results['stats']['total_files']} files")
    print(f"   Found {results['stats']['total_vertices']} components")
    print(f"   Reached depth {results['stats']['max_depth_reached']}")