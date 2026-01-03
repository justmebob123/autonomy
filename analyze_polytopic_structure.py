#!/usr/bin/env python3
"""
Comprehensive Polytopic Structure Analysis
Examines self-similarity, integration patterns, and architectural consistency
"""

import ast
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

class PolytopicAnalyzer(ast.NodeVisitor):
    """Analyzes polytopic structure and self-similarity patterns"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.filename = Path(filepath).name
        
        # Phase structure
        self.class_name = None
        self.base_classes = []
        self.methods = []
        self.method_lines = {}
        
        # Integration patterns
        self.message_bus_calls = []
        self.adaptive_prompt_calls = []
        self.pattern_recognition_calls = []
        self.correlation_calls = []
        self.analytics_calls = []
        self.optimizer_calls = []
        
        # BasePhase integration methods
        self.basephase_methods_used = set()
        
        # Dimensional profile
        self.has_execute = False
        self.has_init = False
        self.has_error_handling = False
        self.has_state_management = False
        
    def visit_ClassDef(self, node):
        if 'Phase' in node.name:
            self.class_name = node.name
            self.base_classes = [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases]
        self.generic_visit(node)
        
    def visit_FunctionDef(self, node):
        if self.class_name:
            self.methods.append(node.name)
            self.method_lines[node.name] = node.end_lineno - node.lineno + 1
            
            if node.name == 'execute':
                self.has_execute = True
            elif node.name == '__init__':
                self.has_init = True
                
        # Check for integration calls
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    attr = child.func.attr
                    
                    # Message bus
                    if 'publish' in attr or 'subscribe' in attr or 'message_bus' in attr:
                        self.message_bus_calls.append(attr)
                    
                    # Adaptive prompts
                    if 'adaptive_prompt' in attr or 'update_system_prompt' in attr:
                        self.adaptive_prompt_calls.append(attr)
                        
                    # Pattern recognition
                    if 'pattern_recognition' in attr or 'record_pattern' in attr or 'record_execution_pattern' in attr:
                        self.pattern_recognition_calls.append(attr)
                        
                    # Correlation
                    if 'correlation' in attr or 'correlate' in attr or 'get_cross_phase_correlation' in attr:
                        self.correlation_calls.append(attr)
                        
                    # Analytics
                    if 'analytics' in attr or 'track_metric' in attr or 'track_phase_metric' in attr:
                        self.analytics_calls.append(attr)
                        
                    # Optimizer
                    if 'optimizer' in attr or 'optimize' in attr or 'get_optimization_suggestion' in attr:
                        self.optimizer_calls.append(attr)
                        
                    # BasePhase methods
                    if attr in ['send_message_to_phase', 'update_system_prompt_with_adaptation',
                               'record_execution_pattern', 'get_cross_phase_correlation',
                               'track_phase_metric', 'get_optimization_suggestion']:
                        self.basephase_methods_used.add(attr)
                        
            # Error handling
            if isinstance(child, (ast.Try, ast.ExceptHandler)):
                self.has_error_handling = True
                
            # State management
            if isinstance(child, ast.Attribute):
                if 'state' in child.attr or 'status' in child.attr:
                    self.has_state_management = True
                    
        self.generic_visit(node)

def analyze_phase_file(filepath: str) -> PolytopicAnalyzer:
    """Analyze a single phase file"""
    with open(filepath, 'r') as f:
        tree = ast.parse(f.read(), filename=filepath)
    
    analyzer = PolytopicAnalyzer(filepath)
    analyzer.visit(tree)
    return analyzer

def analyze_all_phases(phases_dir: str = "pipeline/phases") -> Dict[str, PolytopicAnalyzer]:
    """Analyze all phase files"""
    results = {}
    
    for filename in os.listdir(phases_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            filepath = os.path.join(phases_dir, filename)
            try:
                results[filename] = analyze_phase_file(filepath)
            except Exception as e:
                print(f"Error analyzing {filename}: {e}")
                
    return results

def compare_self_similarity(results: Dict[str, PolytopicAnalyzer]) -> Dict:
    """Compare self-similarity across phases"""
    
    comparison = {
        'base_classes': defaultdict(list),
        'method_counts': {},
        'execute_sizes': {},
        'integration_scores': {},
        'basephase_usage': {},
        'dimensional_profiles': {}
    }
    
    for filename, analyzer in results.items():
        # Base classes
        for base in analyzer.base_classes:
            comparison['base_classes'][base].append(filename)
            
        # Method counts
        comparison['method_counts'][filename] = len(analyzer.methods)
        
        # Execute method size
        if 'execute' in analyzer.method_lines:
            comparison['execute_sizes'][filename] = analyzer.method_lines['execute']
            
        # Integration score (0-6 for 6 engines)
        score = 0
        if analyzer.message_bus_calls: score += 1
        if analyzer.adaptive_prompt_calls: score += 1
        if analyzer.pattern_recognition_calls: score += 1
        if analyzer.correlation_calls: score += 1
        if analyzer.analytics_calls: score += 1
        if analyzer.optimizer_calls: score += 1
        comparison['integration_scores'][filename] = score
        
        # BasePhase method usage
        comparison['basephase_usage'][filename] = len(analyzer.basephase_methods_used)
        
        # Dimensional profile
        comparison['dimensional_profiles'][filename] = {
            'has_execute': analyzer.has_execute,
            'has_init': analyzer.has_init,
            'has_error_handling': analyzer.has_error_handling,
            'has_state_management': analyzer.has_state_management
        }
        
    return comparison

def generate_report(results: Dict[str, PolytopicAnalyzer], comparison: Dict) -> str:
    """Generate comprehensive analysis report"""
    
    report = []
    report.append("# 🔬 POLYTOPIC STRUCTURE ANALYSIS REPORT\n")
    report.append("## Executive Summary\n")
    report.append(f"**Total Phases Analyzed**: {len(results)}\n")
    
    # Self-similarity analysis
    report.append("\n## 🎯 Self-Similarity Analysis\n")
    
    report.append("\n### Base Class Inheritance\n")
    for base, files in comparison['base_classes'].items():
        report.append(f"- **{base}**: {len(files)} phases")
        for f in files:
            report.append(f"  - {f}")
    
    report.append("\n### Method Count Distribution\n")
    sorted_methods = sorted(comparison['method_counts'].items(), key=lambda x: x[1], reverse=True)
    for filename, count in sorted_methods:
        report.append(f"- **{filename}**: {count} methods")
        
    report.append("\n### Execute Method Sizes\n")
    sorted_execute = sorted(comparison['execute_sizes'].items(), key=lambda x: x[1], reverse=True)
    for filename, size in sorted_execute:
        status = "🔴 LARGE" if size > 200 else "🟡 MEDIUM" if size > 100 else "🟢 GOOD"
        report.append(f"- **{filename}**: {size} lines {status}")
        
    # Integration analysis
    report.append("\n## 🔌 Integration Pattern Analysis\n")
    
    report.append("\n### Engine Integration Scores (0-6)\n")
    sorted_scores = sorted(comparison['integration_scores'].items(), key=lambda x: x[1], reverse=True)
    for filename, score in sorted_scores:
        status = "✅ EXCELLENT" if score >= 4 else "🟡 PARTIAL" if score >= 2 else "🔴 MINIMAL"
        report.append(f"- **{filename}**: {score}/6 {status}")
        
    report.append("\n### BasePhase Method Usage\n")
    sorted_usage = sorted(comparison['basephase_usage'].items(), key=lambda x: x[1], reverse=True)
    for filename, count in sorted_usage:
        status = "✅ GOOD" if count >= 2 else "🟡 MINIMAL" if count >= 1 else "🔴 NONE"
        report.append(f"- **{filename}**: {count} methods {status}")
        
    # Detailed phase analysis
    report.append("\n## 📊 Detailed Phase Analysis\n")
    
    for filename, analyzer in sorted(results.items()):
        report.append(f"\n### {filename}\n")
        report.append(f"**Class**: {analyzer.class_name or 'N/A'}\n")
        report.append(f"**Base Classes**: {', '.join(analyzer.base_classes) or 'None'}\n")
        report.append(f"**Methods**: {len(analyzer.methods)}\n")
        
        if analyzer.message_bus_calls:
            report.append(f"**Message Bus**: ✅ {len(analyzer.message_bus_calls)} calls")
        else:
            report.append("**Message Bus**: ❌ Not used")
            
        if analyzer.adaptive_prompt_calls:
            report.append(f"**Adaptive Prompts**: ✅ {len(analyzer.adaptive_prompt_calls)} calls")
        else:
            report.append("**Adaptive Prompts**: ❌ Not used")
            
        if analyzer.pattern_recognition_calls:
            report.append(f"**Pattern Recognition**: ✅ {len(analyzer.pattern_recognition_calls)} calls")
        else:
            report.append("**Pattern Recognition**: ❌ Not used")
            
        if analyzer.basephase_methods_used:
            report.append(f"**BasePhase Methods**: {', '.join(sorted(analyzer.basephase_methods_used))}")
        else:
            report.append("**BasePhase Methods**: ❌ None used")
            
        report.append("")
        
    # Recommendations
    report.append("\n## 🎯 Recommendations\n")
    
    # Find phases with low integration
    low_integration = [f for f, s in comparison['integration_scores'].items() if s < 2]
    if low_integration:
        report.append("\n### Phases Needing Integration Improvements:\n")
        for filename in low_integration:
            report.append(f"- **{filename}**: Add message_bus and adaptive_prompts integration")
            
    # Find phases with large execute methods
    large_execute = [f for f, s in comparison['execute_sizes'].items() if s > 200]
    if large_execute:
        report.append("\n### Phases Needing Refactoring:\n")
        for filename in large_execute:
            size = comparison['execute_sizes'][filename]
            report.append(f"- **{filename}**: Break down execute() method ({size} lines)")
            
    # Find phases not using BasePhase methods
    no_basephase = [f for f, c in comparison['basephase_usage'].items() if c == 0]
    if no_basephase:
        report.append("\n### Phases Not Using BasePhase Integration:\n")
        for filename in no_basephase:
            report.append(f"- **{filename}**: Add BasePhase integration methods")
            
    return '\n'.join(report)

def main():
    print("🔬 Analyzing Polytopic Structure...")
    
    # Analyze all phases
    results = analyze_all_phases()
    
    print(f"✅ Analyzed {len(results)} phase files")
    
    # Compare self-similarity
    comparison = compare_self_similarity(results)
    
    # Generate report
    report = generate_report(results, comparison)
    
    # Save report
    with open('POLYTOPIC_STRUCTURE_ANALYSIS.md', 'w') as f:
        f.write(report)
        
    print("✅ Report saved to POLYTOPIC_STRUCTURE_ANALYSIS.md")
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    avg_integration = sum(comparison['integration_scores'].values()) / len(comparison['integration_scores'])
    print(f"Average Integration Score: {avg_integration:.1f}/6")
    
    avg_methods = sum(comparison['method_counts'].values()) / len(comparison['method_counts'])
    print(f"Average Methods per Phase: {avg_methods:.1f}")
    
    if comparison['execute_sizes']:
        avg_execute = sum(comparison['execute_sizes'].values()) / len(comparison['execute_sizes'])
        print(f"Average Execute Size: {avg_execute:.0f} lines")
    
    print("\n📄 Full report: POLYTOPIC_STRUCTURE_ANALYSIS.md")

if __name__ == '__main__':
    main()