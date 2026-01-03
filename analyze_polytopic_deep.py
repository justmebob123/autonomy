#!/usr/bin/env python3
"""
Deep Polytopic Structure Analysis Tool

Performs comprehensive analysis of:
1. Integration gaps and opportunities
2. Polytopic dimension coverage
3. Learning system utilization
4. Cross-phase communication patterns
5. Architecture consistency
6. Potential improvements
"""

import sys
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple
import ast

sys.path.insert(0, str(Path(__file__).parent))

from pipeline.analysis.symbol_table import SymbolTable
from pipeline.analysis.symbol_collector import SymbolCollector


class DeepPolytopicAnalyzer:
    """Performs deep analysis of polytopic structure and integration."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.symbol_table = SymbolTable(str(project_root))
        self.collector = SymbolCollector(self.symbol_table)
        
        # Analysis results
        self.phase_files = []
        self.phase_analysis = {}
        self.integration_patterns = defaultdict(list)
        self.learning_usage = defaultdict(list)
        self.dimension_coverage = {}
        self.improvement_opportunities = []
        
    def analyze(self):
        """Run comprehensive analysis."""
        print("🔍 Starting Deep Polytopic Analysis...")
        print("=" * 80)
        
        # Collect symbols
        print("\n📊 Collecting symbols...")
        self.collector.collect_from_project(self.project_root)
        
        # Find all phase files
        self._find_phase_files()
        
        # Analyze each phase
        print(f"\n🔬 Analyzing {len(self.phase_files)} phase files...")
        for phase_file in self.phase_files:
            self._analyze_phase_file(phase_file)
        
        # Analyze integration patterns
        print("\n🔗 Analyzing integration patterns...")
        self._analyze_integration_patterns()
        
        # Analyze learning system usage
        print("\n🧠 Analyzing learning system usage...")
        self._analyze_learning_usage()
        
        # Analyze dimension coverage
        print("\n📐 Analyzing polytopic dimension coverage...")
        self._analyze_dimension_coverage()
        
        # Identify improvement opportunities
        print("\n💡 Identifying improvement opportunities...")
        self._identify_improvements()
        
        # Generate report
        print("\n📝 Generating comprehensive report...")
        self._generate_report()
        
    def _find_phase_files(self):
        """Find all phase implementation files."""
        phases_dir = self.project_root / "pipeline" / "phases"
        if phases_dir.exists():
            for file in phases_dir.glob("*.py"):
                if file.name not in ["__init__.py", "base.py"]:
                    self.phase_files.append(file)
                    
    def _analyze_phase_file(self, filepath: Path):
        """Analyze a single phase file for polytopic integration."""
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                tree = ast.parse(content)
            
            phase_name = filepath.stem
            analysis = {
                'file': str(filepath),
                'name': phase_name,
                'message_bus_usage': [],
                'adaptive_prompts_usage': [],
                'pattern_recognition_usage': [],
                'correlation_usage': [],
                'analytics_usage': [],
                'optimizer_usage': [],
                'cross_phase_calls': [],
                'dimension_awareness': [],
                'methods': [],
                'integration_score': 0
            }
            
            # Walk AST to find integration patterns
            for node in ast.walk(tree):
                # Find method definitions
                if isinstance(node, ast.FunctionDef):
                    analysis['methods'].append(node.name)
                
                # Find message_bus usage
                if isinstance(node, ast.Attribute):
                    if node.attr in ['publish_event', 'subscribe_to']:
                        analysis['message_bus_usage'].append(node.attr)
                    elif node.attr in ['update_system_prompt_with_adaptation', 'get_adapted_prompt']:
                        analysis['adaptive_prompts_usage'].append(node.attr)
                    elif node.attr in ['record_execution_pattern', 'get_pattern']:
                        analysis['pattern_recognition_usage'].append(node.attr)
                    elif node.attr in ['get_cross_phase_correlation', 'correlate']:
                        analysis['correlation_usage'].append(node.attr)
                    elif node.attr in ['track_phase_metric', 'get_metrics']:
                        analysis['analytics_usage'].append(node.attr)
                    elif node.attr in ['get_optimization_suggestion', 'optimize']:
                        analysis['optimizer_usage'].append(node.attr)
                    elif node.attr == 'send_message_to_phase':
                        analysis['cross_phase_calls'].append('send_message_to_phase')
                
                # Find dimension awareness
                if isinstance(node, ast.Name):
                    if 'dimension' in node.id.lower() or 'polytopic' in node.id.lower():
                        analysis['dimension_awareness'].append(node.id)
            
            # Calculate integration score (0-6)
            score = 0
            if analysis['message_bus_usage']: score += 1
            if analysis['adaptive_prompts_usage']: score += 1
            if analysis['pattern_recognition_usage']: score += 1
            if analysis['correlation_usage']: score += 1
            if analysis['analytics_usage']: score += 1
            if analysis['optimizer_usage']: score += 1
            analysis['integration_score'] = score
            
            self.phase_analysis[phase_name] = analysis
            
        except Exception as e:
            print(f"  ⚠️  Error analyzing {filepath}: {e}")
    
    def _analyze_integration_patterns(self):
        """Analyze cross-phase integration patterns."""
        for phase_name, analysis in self.phase_analysis.items():
            # Message bus patterns
            if analysis['message_bus_usage']:
                self.integration_patterns['message_bus'].append({
                    'phase': phase_name,
                    'usage_count': len(analysis['message_bus_usage']),
                    'methods': set(analysis['message_bus_usage'])
                })
            
            # Cross-phase communication
            if analysis['cross_phase_calls']:
                self.integration_patterns['cross_phase'].append({
                    'phase': phase_name,
                    'call_count': len(analysis['cross_phase_calls'])
                })
    
    def _analyze_learning_usage(self):
        """Analyze learning system usage across phases."""
        for phase_name, analysis in self.phase_analysis.items():
            # Adaptive prompts
            if analysis['adaptive_prompts_usage']:
                self.learning_usage['adaptive_prompts'].append({
                    'phase': phase_name,
                    'usage_count': len(analysis['adaptive_prompts_usage'])
                })
            
            # Pattern recognition
            if analysis['pattern_recognition_usage']:
                self.learning_usage['pattern_recognition'].append({
                    'phase': phase_name,
                    'usage_count': len(analysis['pattern_recognition_usage'])
                })
            
            # Correlation engine
            if analysis['correlation_usage']:
                self.learning_usage['correlation'].append({
                    'phase': phase_name,
                    'usage_count': len(analysis['correlation_usage'])
                })
    
    def _analyze_dimension_coverage(self):
        """Analyze polytopic dimension coverage."""
        dimensions = [
            'temporal', 'functional', 'data', 'state', 
            'error', 'context', 'integration', 'architecture'
        ]
        
        for dim in dimensions:
            self.dimension_coverage[dim] = {
                'phases_aware': [],
                'total_references': 0
            }
        
        for phase_name, analysis in self.phase_analysis.items():
            for ref in analysis['dimension_awareness']:
                for dim in dimensions:
                    if dim in ref.lower():
                        self.dimension_coverage[dim]['phases_aware'].append(phase_name)
                        self.dimension_coverage[dim]['total_references'] += 1
    
    def _identify_improvements(self):
        """Identify potential improvements."""
        # 1. Phases with low integration scores
        for phase_name, analysis in self.phase_analysis.items():
            if analysis['integration_score'] < 4:
                self.improvement_opportunities.append({
                    'type': 'LOW_INTEGRATION',
                    'phase': phase_name,
                    'current_score': analysis['integration_score'],
                    'missing': self._get_missing_integrations(analysis),
                    'priority': 'HIGH' if analysis['integration_score'] < 2 else 'MEDIUM'
                })
        
        # 2. Phases without adaptive prompts
        for phase_name, analysis in self.phase_analysis.items():
            if not analysis['adaptive_prompts_usage']:
                self.improvement_opportunities.append({
                    'type': 'NO_ADAPTIVE_PROMPTS',
                    'phase': phase_name,
                    'priority': 'HIGH',
                    'suggestion': 'Add update_system_prompt_with_adaptation() call'
                })
        
        # 3. Phases without message bus
        for phase_name, analysis in self.phase_analysis.items():
            if not analysis['message_bus_usage']:
                self.improvement_opportunities.append({
                    'type': 'NO_MESSAGE_BUS',
                    'phase': phase_name,
                    'priority': 'HIGH',
                    'suggestion': 'Add publish_event() calls for key events'
                })
        
        # 4. Phases without pattern recognition
        for phase_name, analysis in self.phase_analysis.items():
            if not analysis['pattern_recognition_usage']:
                self.improvement_opportunities.append({
                    'type': 'NO_PATTERN_RECOGNITION',
                    'phase': phase_name,
                    'priority': 'MEDIUM',
                    'suggestion': 'Add record_execution_pattern() calls'
                })
        
        # 5. Dimensions with low coverage
        for dim, data in self.dimension_coverage.items():
            if len(data['phases_aware']) < 3:
                self.improvement_opportunities.append({
                    'type': 'LOW_DIMENSION_COVERAGE',
                    'dimension': dim,
                    'phases_aware': len(data['phases_aware']),
                    'priority': 'LOW',
                    'suggestion': f'Increase {dim} dimension awareness across phases'
                })
    
    def _get_missing_integrations(self, analysis: Dict) -> List[str]:
        """Get list of missing integrations for a phase."""
        missing = []
        if not analysis['message_bus_usage']:
            missing.append('message_bus')
        if not analysis['adaptive_prompts_usage']:
            missing.append('adaptive_prompts')
        if not analysis['pattern_recognition_usage']:
            missing.append('pattern_recognition')
        if not analysis['correlation_usage']:
            missing.append('correlation_engine')
        if not analysis['analytics_usage']:
            missing.append('analytics')
        if not analysis['optimizer_usage']:
            missing.append('pattern_optimizer')
        return missing
    
    def _generate_report(self):
        """Generate comprehensive analysis report."""
        report_path = self.project_root / "DEEP_POLYTOPIC_ANALYSIS.md"
        
        with open(report_path, 'w') as f:
            f.write("# 🔬 Deep Polytopic Structure Analysis Report\n\n")
            f.write(f"**Generated**: {Path.cwd()}\n\n")
            f.write("---\n\n")
            
            # Executive Summary
            f.write("## 📊 Executive Summary\n\n")
            total_phases = len(self.phase_analysis)
            avg_score = sum(a['integration_score'] for a in self.phase_analysis.values()) / total_phases if total_phases > 0 else 0
            f.write(f"- **Total Phases Analyzed**: {total_phases}\n")
            f.write(f"- **Average Integration Score**: {avg_score:.2f}/6\n")
            f.write(f"- **Improvement Opportunities**: {len(self.improvement_opportunities)}\n")
            f.write(f"- **Symbol Table Size**: {len(self.symbol_table.call_graph)} components\n\n")
            
            # Phase Integration Scores
            f.write("## 🎯 Phase Integration Scores\n\n")
            f.write("| Phase | Score | Message Bus | Adaptive | Pattern | Correlation | Analytics | Optimizer |\n")
            f.write("|-------|-------|-------------|----------|---------|-------------|-----------|----------|\n")
            
            for phase_name in sorted(self.phase_analysis.keys()):
                analysis = self.phase_analysis[phase_name]
                f.write(f"| {phase_name} | {analysis['integration_score']}/6 | ")
                f.write(f"{'✅' if analysis['message_bus_usage'] else '❌'} | ")
                f.write(f"{'✅' if analysis['adaptive_prompts_usage'] else '❌'} | ")
                f.write(f"{'✅' if analysis['pattern_recognition_usage'] else '❌'} | ")
                f.write(f"{'✅' if analysis['correlation_usage'] else '❌'} | ")
                f.write(f"{'✅' if analysis['analytics_usage'] else '❌'} | ")
                f.write(f"{'✅' if analysis['optimizer_usage'] else '❌'} |\n")
            
            f.write("\n")
            
            # Integration Patterns
            f.write("## 🔗 Integration Patterns\n\n")
            f.write("### Message Bus Usage\n\n")
            if self.integration_patterns['message_bus']:
                for item in self.integration_patterns['message_bus']:
                    f.write(f"- **{item['phase']}**: {item['usage_count']} calls\n")
                    f.write(f"  - Methods: {', '.join(item['methods'])}\n")
            else:
                f.write("*No message bus usage detected*\n")
            f.write("\n")
            
            f.write("### Cross-Phase Communication\n\n")
            if self.integration_patterns['cross_phase']:
                for item in self.integration_patterns['cross_phase']:
                    f.write(f"- **{item['phase']}**: {item['call_count']} cross-phase calls\n")
            else:
                f.write("*No cross-phase communication detected*\n")
            f.write("\n")
            
            # Learning System Usage
            f.write("## 🧠 Learning System Usage\n\n")
            for system, usage in self.learning_usage.items():
                f.write(f"### {system.replace('_', ' ').title()}\n\n")
                if usage:
                    for item in usage:
                        f.write(f"- **{item['phase']}**: {item['usage_count']} calls\n")
                else:
                    f.write("*Not used by any phase*\n")
                f.write("\n")
            
            # Dimension Coverage
            f.write("## 📐 Polytopic Dimension Coverage\n\n")
            f.write("| Dimension | Phases Aware | Total References |\n")
            f.write("|-----------|--------------|------------------|\n")
            for dim in sorted(self.dimension_coverage.keys()):
                data = self.dimension_coverage[dim]
                f.write(f"| {dim.title()} | {len(data['phases_aware'])} | {data['total_references']} |\n")
            f.write("\n")
            
            # Improvement Opportunities
            f.write("## 💡 Improvement Opportunities\n\n")
            
            # Group by priority
            high_priority = [o for o in self.improvement_opportunities if o.get('priority') == 'HIGH']
            medium_priority = [o for o in self.improvement_opportunities if o.get('priority') == 'MEDIUM']
            low_priority = [o for o in self.improvement_opportunities if o.get('priority') == 'LOW']
            
            f.write(f"### 🔴 High Priority ({len(high_priority)})\n\n")
            for opp in high_priority:
                f.write(f"#### {opp['type'].replace('_', ' ').title()}\n")
                if 'phase' in opp:
                    f.write(f"- **Phase**: {opp['phase']}\n")
                if 'current_score' in opp:
                    f.write(f"- **Current Score**: {opp['current_score']}/6\n")
                if 'missing' in opp:
                    f.write(f"- **Missing**: {', '.join(opp['missing'])}\n")
                if 'suggestion' in opp:
                    f.write(f"- **Suggestion**: {opp['suggestion']}\n")
                f.write("\n")
            
            f.write(f"### 🟡 Medium Priority ({len(medium_priority)})\n\n")
            for opp in medium_priority:
                f.write(f"#### {opp['type'].replace('_', ' ').title()}\n")
                if 'phase' in opp:
                    f.write(f"- **Phase**: {opp['phase']}\n")
                if 'suggestion' in opp:
                    f.write(f"- **Suggestion**: {opp['suggestion']}\n")
                f.write("\n")
            
            f.write(f"### 🟢 Low Priority ({len(low_priority)})\n\n")
            for opp in low_priority:
                f.write(f"#### {opp['type'].replace('_', ' ').title()}\n")
                if 'dimension' in opp:
                    f.write(f"- **Dimension**: {opp['dimension']}\n")
                    f.write(f"- **Phases Aware**: {opp['phases_aware']}\n")
                if 'suggestion' in opp:
                    f.write(f"- **Suggestion**: {opp['suggestion']}\n")
                f.write("\n")
            
            # Detailed Phase Analysis
            f.write("## 📋 Detailed Phase Analysis\n\n")
            for phase_name in sorted(self.phase_analysis.keys()):
                analysis = self.phase_analysis[phase_name]
                f.write(f"### {phase_name}\n\n")
                f.write(f"- **Integration Score**: {analysis['integration_score']}/6\n")
                f.write(f"- **Methods**: {len(analysis['methods'])}\n")
                f.write(f"- **Message Bus Calls**: {len(analysis['message_bus_usage'])}\n")
                f.write(f"- **Adaptive Prompts Calls**: {len(analysis['adaptive_prompts_usage'])}\n")
                f.write(f"- **Pattern Recognition Calls**: {len(analysis['pattern_recognition_usage'])}\n")
                f.write(f"- **Correlation Calls**: {len(analysis['correlation_usage'])}\n")
                f.write(f"- **Analytics Calls**: {len(analysis['analytics_usage'])}\n")
                f.write(f"- **Optimizer Calls**: {len(analysis['optimizer_usage'])}\n")
                f.write(f"- **Cross-Phase Calls**: {len(analysis['cross_phase_calls'])}\n")
                f.write(f"- **Dimension Awareness**: {len(analysis['dimension_awareness'])}\n")
                f.write("\n")
        
        print(f"\n✅ Report generated: {report_path}")


def main():
    """Main entry point."""
    project_root = Path.cwd()
    
    analyzer = DeepPolytopicAnalyzer(project_root)
    analyzer.analyze()
    
    print("\n" + "=" * 80)
    print("✅ Deep Polytopic Analysis Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()