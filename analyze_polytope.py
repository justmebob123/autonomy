#!/usr/bin/env python3
"""
Hyperdimensional Polytopic Analysis - Depth 59 Recursion
Analyzes the complete structure of the Autonomy system
"""

import os
import json
import ast
from pathlib import Path
from collections import defaultdict, deque
import re

class PolytopicAnalyzer:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.vertices = []
        self.adjacency = {}
        self.dimensions = {}
        self.state_variables = {}
        self.integration_points = {}
        self.subsystems = {}
        
    def analyze_vertices(self):
        """Identify all phase vertices"""
        phases_dir = self.base_dir / "pipeline" / "phases"
        
        if phases_dir.exists():
            for file in phases_dir.glob("*.py"):
                if file.name not in ["__init__.py", "base.py"]:
                    self.vertices.append(file.stem)
        
        return self.vertices
    
    def analyze_adjacency(self):
        """Extract adjacency matrix from coordinator"""
        coordinator_file = self.base_dir / "pipeline" / "coordinator.py"
        
        if coordinator_file.exists():
            with open(coordinator_file, 'r') as f:
                content = f.read()
            
            # Extract polytope edges definition
            pattern = r"self\.polytope\['edges'\]\s*=\s*\{([^}]+)\}"
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                edges_content = match.group(1)
                # Parse each line
                for line in edges_content.split('\n'):
                    line = line.strip()
                    if ':' in line:
                        parts = line.split(':', 1)
                        phase = parts[0].strip().strip("'&quot;")
                        edges_str = parts[1].strip().rstrip(',')
                        
                        # Extract list items
                        edges_match = re.findall(r"'([^']+)'", edges_str)
                        if edges_match:
                            self.adjacency[phase] = edges_match
        
        return self.adjacency
    
    def analyze_dimensions(self):
        """Analyze 7-dimensional structure"""
        base_file = self.base_dir / "pipeline" / "phases" / "base.py"
        
        if base_file.exists():
            with open(base_file, 'r') as f:
                content = f.read()
            
            # Extract dimensional_profile definition
            pattern = r"self\.dimensional_profile\s*=\s*\{([^}]+)\}"
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                dims_content = match.group(1)
                for line in dims_content.split('\n'):
                    line = line.strip()
                    if ':' in line:
                        parts = line.split(':', 1)
                        dim = parts[0].strip().strip("'&quot;")
                        value = parts[1].strip().rstrip(',')
                        self.dimensions[dim] = value
        
        return self.dimensions
    
    def analyze_state_variables(self):
        """Analyze state variables across the system"""
        state_file = self.base_dir / "pipeline" / "state" / "manager.py"
        
        if state_file.exists():
            with open(state_file, 'r') as f:
                content = f.read()
            
            # Find PipelineState dataclass
            pattern = r"@dataclass\s+class\s+PipelineState:.*?(?=\n@|\nclass\s|\Z)"
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                state_content = match.group(0)
                # Extract field definitions
                field_pattern = r"(\w+):\s*([^\n=]+)"
                fields = re.findall(field_pattern, state_content)
                
                for field_name, field_type in fields:
                    if not field_name.startswith('_'):
                        self.state_variables[field_name] = field_type.strip()
        
        return self.state_variables
    
    def analyze_subsystems(self):
        """Identify major subsystems"""
        pipeline_dir = self.base_dir / "pipeline"
        
        subsystems = {
            "State Management": [],
            "Tool System": [],
            "Registry System": [],
            "Loop Detection": [],
            "Coordination": [],
            "Utilities": [],
            "Facades": []
        }
        
        if pipeline_dir.exists():
            for file in pipeline_dir.glob("*.py"):
                name = file.stem
                
                if "state" in name or "manager" in name:
                    subsystems["State Management"].append(name)
                elif "tool" in name or "handler" in name:
                    subsystems["Tool System"].append(name)
                elif "registry" in name:
                    subsystems["Registry System"].append(name)
                elif "loop" in name or "action" in name or "pattern" in name:
                    subsystems["Loop Detection"].append(name)
                elif "coordinator" in name or "orchestrator" in name:
                    subsystems["Coordination"].append(name)
                elif "utils" in name or "validator" in name:
                    subsystems["Utilities"].append(name)
                elif "facade" in name or name in ["loop_detection_system", "team_coordination", "phase_resources"]:
                    subsystems["Facades"].append(name)
        
        self.subsystems = {k: v for k, v in subsystems.items() if v}
        return self.subsystems
    
    def analyze_integration_points(self):
        """Analyze integration points between subsystems"""
        integration = defaultdict(list)
        
        # Analyze imports in each phase
        phases_dir = self.base_dir / "pipeline" / "phases"
        
        if phases_dir.exists():
            for file in phases_dir.glob("*.py"):
                if file.name not in ["__init__.py"]:
                    with open(file, 'r') as f:
                        content = f.read()
                    
                    # Extract imports
                    import_pattern = r"from\s+\.\.(\w+)\s+import"
                    imports = re.findall(import_pattern, content)
                    
                    for imp in imports:
                        integration[file.stem].append(imp)
        
        self.integration_points = dict(integration)
        return self.integration_points
    
    def calculate_reachability(self):
        """Calculate reachability matrix using BFS"""
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
            
            reachable[start] = len(visited) - 1  # Exclude self
        
        return reachable
    
    def find_critical_vertices(self):
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
            if total >= 5:  # High connectivity threshold
                critical.append((phase, in_degree[phase], out_degree[phase], total))
        
        return sorted(critical, key=lambda x: x[3], reverse=True)
    
    def analyze_emergent_properties(self):
        """Analyze emergent properties of the system"""
        properties = {}
        
        # 1. Self-awareness
        base_file = self.base_dir / "pipeline" / "phases" / "base.py"
        if base_file.exists():
            with open(base_file, 'r') as f:
                content = f.read()
            properties["self_awareness"] = "self_awareness_level" in content
        
        # 2. Learning capability
        properties["learning"] = "learn_pattern" in content if base_file.exists() else False
        
        # 3. Adaptation
        properties["adaptation"] = "adapt_to_situation" in content if base_file.exists() else False
        
        # 4. Loop detection
        loop_file = self.base_dir / "pipeline" / "loop_detection_system.py"
        properties["loop_detection"] = loop_file.exists()
        
        # 5. Tool development
        tool_design = self.base_dir / "pipeline" / "phases" / "tool_design.py"
        properties["tool_development"] = tool_design.exists()
        
        # 6. State persistence
        state_file = self.base_dir / "pipeline" / "state" / "manager.py"
        properties["state_persistence"] = state_file.exists()
        
        return properties
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
        print("="*80)
        print("HYPERDIMENSIONAL POLYTOPIC ANALYSIS - DEPTH 59 RECURSION")
        print("="*80)
        
        # Vertices
        vertices = self.analyze_vertices()
        print(f"\n📊 VERTICES (Phases): {len(vertices)}")
        for i, v in enumerate(sorted(vertices), 1):
            print(f"  {i:2d}. {v}")
        
        # Adjacency
        adjacency = self.analyze_adjacency()
        print(f"\n🔗 ADJACENCY MATRIX: {len(adjacency)} phases with edges")
        total_edges = sum(len(v) for v in adjacency.values())
        print(f"   Total directed edges: {total_edges}")
        if adjacency:
            print(f"   Average connectivity: {total_edges/len(adjacency):.2f} edges per vertex")
        
        print("\n   Detailed Adjacency:")
        for phase, edges in sorted(adjacency.items()):
            print(f"   {phase:25s} -> {', '.join(edges)}")
        
        # Dimensions
        dimensions = self.analyze_dimensions()
        print(f"\n📐 DIMENSIONAL STRUCTURE: {len(dimensions)} dimensions")
        for i, (dim, value) in enumerate(sorted(dimensions.items()), 1):
            print(f"   {i}. {dim:20s}: {value}")
        
        # State Variables
        state_vars = self.analyze_state_variables()
        print(f"\n💾 STATE VARIABLES: {len(state_vars)} tracked")
        for i, (var, type_) in enumerate(sorted(state_vars.items()), 1):
            print(f"   {i:3d}. {var:30s}: {type_}")
        
        # Subsystems
        subsystems = self.analyze_subsystems()
        print(f"\n🏗️  SUBSYSTEMS: {len(subsystems)} identified")
        for name, components in sorted(subsystems.items()):
            print(f"   {name:20s}: {len(components)} components")
            for comp in sorted(components):
                print(f"      - {comp}")
        
        # Integration Points
        integration = self.analyze_integration_points()
        print(f"\n🔌 INTEGRATION POINTS: {len(integration)} phases")
        total_integrations = sum(len(v) for v in integration.values())
        print(f"   Total integration points: {total_integrations}")
        
        # Reachability
        reachability = self.calculate_reachability()
        print(f"\n🎯 REACHABILITY ANALYSIS:")
        print(f"   Phases with full reachability: {sum(1 for r in reachability.values() if r == len(vertices)-1)}")
        print(f"   Average reachability: {sum(reachability.values())/len(reachability):.1f} phases")
        
        # Critical Vertices
        critical = self.find_critical_vertices()
        print(f"\n⭐ CRITICAL VERTICES (High Connectivity):")
        for phase, in_deg, out_deg, total in critical:
            print(f"   {phase:25s}: {in_deg} in, {out_deg} out, {total} total")
        
        # Emergent Properties
        properties = self.analyze_emergent_properties()
        print(f"\n✨ EMERGENT PROPERTIES:")
        for prop, active in sorted(properties.items()):
            status = "✅ ACTIVE" if active else "❌ INACTIVE"
            print(f"   {prop:25s}: {status}")
        
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)

if __name__ == "__main__":
    analyzer = PolytopicAnalyzer(".")
    analyzer.generate_report()