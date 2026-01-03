#!/usr/bin/env python3
"""
Architecture Flow Analysis
Analyzes execution flows, dependencies, and architectural patterns
across the entire codebase.
"""

import ast
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

class ArchitectureFlowAnalyzer:
    """Analyzes architectural patterns and execution flows"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.phases_dir = project_root / "pipeline" / "phases"
        self.core_dir = project_root / "pipeline" / "core"
        self.learning_dir = project_root / "pipeline" / "learning"
        
        self.results = {
            "phase_dependencies": defaultdict(set),
            "tool_usage": defaultdict(list),
            "ipc_patterns": defaultdict(list),
            "execution_flows": [],
            "architectural_patterns": {},
            "integration_gaps": []
        }
    
    def analyze_phase_dependencies(self):
        """Analyze dependencies between phases"""
        print("🔍 Analyzing phase dependencies...")
        
        for phase_file in self.phases_dir.glob("*.py"):
            if phase_file.name.startswith("__"):
                continue
            
            try:
                with open(phase_file, 'r') as f:
                    content = f.read()
                
                phase_name = phase_file.stem
                
                # Find imports from other phases
                imports = re.findall(r'from pipeline\.phases\.(\w+) import', content)
                for imp in imports:
                    self.results["phase_dependencies"][phase_name].add(imp)
                
                # Find phase transitions
                transitions = re.findall(r'next_phase\s*=\s*["\'](\w+)["\']', content)
                for trans in transitions:
                    self.results["phase_dependencies"][phase_name].add(trans)
                
            except Exception as e:
                print(f"Error analyzing {phase_file}: {e}")
        
        print(f"✅ Analyzed dependencies for {len(self.results['phase_dependencies'])} phases")
    
    def analyze_tool_usage(self):
        """Analyze tool usage patterns across phases"""
        print("\n🔧 Analyzing tool usage patterns...")
        
        for phase_file in self.phases_dir.glob("*.py"):
            if phase_file.name.startswith("__"):
                continue
            
            try:
                with open(phase_file, 'r') as f:
                    content = f.read()
                
                phase_name = phase_file.stem
                
                # Find tool calls
                tool_calls = re.findall(r'self\.tools\.(\w+)', content)
                for tool in tool_calls:
                    self.results["tool_usage"][phase_name].append(tool)
                
                # Find tool registrations
                tool_regs = re.findall(r'register_tool\(["\'](\w+)["\']', content)
                for tool in tool_regs:
                    self.results["tool_usage"][phase_name].append(f"register:{tool}")
                
            except Exception as e:
                print(f"Error analyzing tools in {phase_file}: {e}")
        
        total_tools = sum(len(tools) for tools in self.results["tool_usage"].values())
        print(f"✅ Found {total_tools} tool usage instances across phases")
    
    def analyze_ipc_patterns(self):
        """Analyze IPC communication patterns"""
        print("\n📡 Analyzing IPC patterns...")
        
        for phase_file in self.phases_dir.glob("*.py"):
            if phase_file.name.startswith("__"):
                continue
            
            try:
                with open(phase_file, 'r') as f:
                    content = f.read()
                
                phase_name = phase_file.stem
                
                # Find document operations
                reads = re.findall(r'read_document\(["\'](\w+)["\']', content)
                writes = re.findall(r'write_document\(["\'](\w+)["\']', content)
                updates = re.findall(r'update_document\(["\'](\w+)["\']', content)
                
                for doc in reads:
                    self.results["ipc_patterns"][phase_name].append(f"READ:{doc}")
                for doc in writes:
                    self.results["ipc_patterns"][phase_name].append(f"WRITE:{doc}")
                for doc in updates:
                    self.results["ipc_patterns"][phase_name].append(f"UPDATE:{doc}")
                
            except Exception as e:
                print(f"Error analyzing IPC in {phase_file}: {e}")
        
        total_ipc = sum(len(ops) for ops in self.results["ipc_patterns"].values())
        print(f"✅ Found {total_ipc} IPC operations across phases")
    
    def analyze_execution_flows(self):
        """Analyze execution flow patterns"""
        print("\n🔄 Analyzing execution flows...")
        
        # Analyze coordinator
        coordinator_file = self.core_dir / "coordinator.py"
        if coordinator_file.exists():
            try:
                with open(coordinator_file, 'r') as f:
                    content = f.read()
                
                # Find phase execution order
                phase_order = re.findall(r'PHASE_ORDER\s*=\s*\[(.*?)\]', content, re.DOTALL)
                if phase_order:
                    phases = re.findall(r'["\'](\w+)["\']', phase_order[0])
                    self.results["execution_flows"].append({
                        "type": "standard_flow",
                        "phases": phases
                    })
                
                # Find conditional flows
                conditionals = re.findall(r'if.*?next_phase\s*=\s*["\'](\w+)["\']', content)
                if conditionals:
                    self.results["execution_flows"].append({
                        "type": "conditional_flow",
                        "phases": conditionals
                    })
                
            except Exception as e:
                print(f"Error analyzing coordinator: {e}")
        
        print(f"✅ Identified {len(self.results['execution_flows'])} execution flow patterns")
    
    def identify_architectural_patterns(self):
        """Identify key architectural patterns"""
        print("\n🏗️ Identifying architectural patterns...")
        
        patterns = {}
        
        # 1. Phase coordination pattern
        if self.results["phase_dependencies"]:
            patterns["phase_coordination"] = {
                "type": "Dependency-based coordination",
                "phases_with_deps": len(self.results["phase_dependencies"]),
                "total_dependencies": sum(len(deps) for deps in self.results["phase_dependencies"].values())
            }
        
        # 2. Tool system pattern
        if self.results["tool_usage"]:
            patterns["tool_system"] = {
                "type": "Shared tool registry",
                "phases_using_tools": len(self.results["tool_usage"]),
                "total_tool_calls": sum(len(tools) for tools in self.results["tool_usage"].values())
            }
        
        # 3. IPC pattern
        if self.results["ipc_patterns"]:
            patterns["ipc_system"] = {
                "type": "Document-based IPC",
                "phases_using_ipc": len(self.results["ipc_patterns"]),
                "total_operations": sum(len(ops) for ops in self.results["ipc_patterns"].values())
            }
        
        # 4. Learning system pattern
        learning_files = list(self.learning_dir.glob("*.py"))
        patterns["learning_system"] = {
            "type": "Multi-engine learning",
            "components": len(learning_files),
            "engines": ["adaptive_prompts", "pattern_recognition", "correlation", "optimizer"]
        }
        
        self.results["architectural_patterns"] = patterns
        print(f"✅ Identified {len(patterns)} architectural patterns")
    
    def identify_integration_gaps(self):
        """Identify integration gaps and opportunities"""
        print("\n🎯 Identifying integration gaps...")
        
        gaps = []
        
        # 1. Phases without tool usage
        phases_with_tools = set(self.results["tool_usage"].keys())
        all_phases = set(p.stem for p in self.phases_dir.glob("*.py") 
                        if not p.name.startswith("__") 
                        and not p.stem.endswith("_mixin")
                        and not p.stem.endswith("_builder"))
        
        phases_without_tools = all_phases - phases_with_tools
        if phases_without_tools:
            gaps.append({
                "type": "Tool Integration",
                "severity": "MEDIUM",
                "description": f"{len(phases_without_tools)} phases don't use tools",
                "phases": list(phases_without_tools)
            })
        
        # 2. Phases without IPC
        phases_with_ipc = set(self.results["ipc_patterns"].keys())
        phases_without_ipc = all_phases - phases_with_ipc
        if phases_without_ipc:
            gaps.append({
                "type": "IPC Integration",
                "severity": "LOW",
                "description": f"{len(phases_without_ipc)} phases don't use IPC",
                "phases": list(phases_without_ipc)
            })
        
        # 3. Isolated phases (no dependencies)
        phases_with_deps = set(self.results["phase_dependencies"].keys())
        isolated_phases = all_phases - phases_with_deps
        if isolated_phases:
            gaps.append({
                "type": "Phase Coordination",
                "severity": "LOW",
                "description": f"{len(isolated_phases)} phases have no dependencies",
                "phases": list(isolated_phases)
            })
        
        self.results["integration_gaps"] = gaps
        print(f"✅ Identified {len(gaps)} integration gaps")
    
    def generate_report(self) -> str:
        """Generate comprehensive architecture analysis report"""
        report = []
        report.append("# 🏗️ Architecture Flow Analysis Report")
        report.append("")
        report.append("## 📊 Executive Summary")
        report.append("")
        
        # Summary statistics
        report.append(f"- **Phases Analyzed**: {len(list(self.phases_dir.glob('*.py'))) - 1}")
        report.append(f"- **Phase Dependencies**: {sum(len(deps) for deps in self.results['phase_dependencies'].values())}")
        report.append(f"- **Tool Usage Instances**: {sum(len(tools) for tools in self.results['tool_usage'].values())}")
        report.append(f"- **IPC Operations**: {sum(len(ops) for ops in self.results['ipc_patterns'].values())}")
        report.append(f"- **Execution Flows**: {len(self.results['execution_flows'])}")
        report.append(f"- **Integration Gaps**: {len(self.results['integration_gaps'])}")
        report.append("")
        
        # Architectural patterns
        report.append("## 🏗️ Architectural Patterns")
        report.append("")
        
        for pattern_name, pattern_data in self.results["architectural_patterns"].items():
            report.append(f"### {pattern_name.replace('_', ' ').title()}")
            report.append(f"**Type**: {pattern_data['type']}")
            for key, value in pattern_data.items():
                if key != 'type':
                    if isinstance(value, list):
                        report.append(f"- **{key.replace('_', ' ').title()}**: {', '.join(value)}")
                    else:
                        report.append(f"- **{key.replace('_', ' ').title()}**: {value}")
            report.append("")
        
        # Phase dependencies
        report.append("## 🔗 Phase Dependencies")
        report.append("")
        
        if self.results["phase_dependencies"]:
            for phase in sorted(self.results["phase_dependencies"].keys()):
                deps = self.results["phase_dependencies"][phase]
                if deps:
                    report.append(f"### {phase}")
                    report.append(f"**Depends on**: {', '.join(sorted(deps))}")
                    report.append("")
        else:
            report.append("_No explicit phase dependencies found_")
            report.append("")
        
        # Tool usage
        report.append("## 🔧 Tool Usage Patterns")
        report.append("")
        
        if self.results["tool_usage"]:
            # Top tool users
            top_users = sorted(self.results["tool_usage"].items(), 
                             key=lambda x: len(x[1]), reverse=True)[:5]
            
            report.append("### Top Tool Users")
            for phase, tools in top_users:
                unique_tools = len(set(tools))
                report.append(f"- **{phase}**: {len(tools)} calls ({unique_tools} unique tools)")
            report.append("")
        
        # IPC patterns
        report.append("## 📡 IPC Communication Patterns")
        report.append("")
        
        if self.results["ipc_patterns"]:
            for phase in sorted(self.results["ipc_patterns"].keys()):
                ops = self.results["ipc_patterns"][phase]
                if ops:
                    reads = [op.split(':')[1] for op in ops if op.startswith('READ:')]
                    writes = [op.split(':')[1] for op in ops if op.startswith('WRITE:')]
                    updates = [op.split(':')[1] for op in ops if op.startswith('UPDATE:')]
                    
                    report.append(f"### {phase}")
                    if reads:
                        report.append(f"- **Reads**: {', '.join(set(reads))}")
                    if writes:
                        report.append(f"- **Writes**: {', '.join(set(writes))}")
                    if updates:
                        report.append(f"- **Updates**: {', '.join(set(updates))}")
                    report.append("")
        
        # Execution flows
        report.append("## 🔄 Execution Flows")
        report.append("")
        
        for i, flow in enumerate(self.results["execution_flows"], 1):
            report.append(f"### Flow {i}: {flow['type'].replace('_', ' ').title()}")
            report.append(f"**Phases**: {' → '.join(flow['phases'])}")
            report.append("")
        
        # Integration gaps
        report.append("## 🎯 Integration Gaps & Opportunities")
        report.append("")
        
        for gap in self.results["integration_gaps"]:
            report.append(f"### {gap['type']} [{gap['severity']}]")
            report.append(f"**Description**: {gap['description']}")
            if len(gap['phases']) <= 5:
                report.append(f"**Phases**: {', '.join(gap['phases'])}")
            else:
                report.append(f"**Phases**: {', '.join(gap['phases'][:5])} _(and {len(gap['phases']) - 5} more)_")
            report.append("")
        
        return "\n".join(report)
    
    def run_analysis(self):
        """Run complete architecture analysis"""
        print("=" * 80)
        print("🏗️ ARCHITECTURE FLOW ANALYSIS")
        print("=" * 80)
        print()
        
        self.analyze_phase_dependencies()
        self.analyze_tool_usage()
        self.analyze_ipc_patterns()
        self.analyze_execution_flows()
        self.identify_architectural_patterns()
        self.identify_integration_gaps()
        
        report = self.generate_report()
        
        # Save report
        report_path = self.project_root / "ARCHITECTURE_FLOW_ANALYSIS.md"
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"\n✅ Analysis complete! Report saved to: {report_path.name}")
        print()

if __name__ == "__main__":
    project_root = Path(".")
    analyzer = ArchitectureFlowAnalyzer(project_root)
    analyzer.run_analysis()