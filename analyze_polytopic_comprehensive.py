#!/usr/bin/env python3
"""
Comprehensive Polytopic Structure Analysis
Analyzes the entire codebase for polytopic integration, dimension tracking,
learning systems, and cross-phase communication patterns.
"""

import ast
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

class ComprehensivePolytopicAnalyzer:
    """Analyzes polytopic structure across the entire codebase"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.phases_dir = project_root / "pipeline" / "phases"
        self.results = {
            "integration_scores": {},
            "dimension_tracking": {},
            "learning_systems": {},
            "message_bus": {},
            "ipc_usage": {},
            "tool_usage": {},
            "cross_phase_patterns": {},
            "improvement_opportunities": []
        }
    
    def analyze_phase_file(self, file_path: Path) -> Dict:
        """Analyze a single phase file for polytopic features"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                tree = ast.parse(content)
            
            analysis = {
                "file": file_path.name,
                "has_adaptive_prompts": False,
                "has_pattern_recognition": False,
                "has_correlation": False,
                "has_analytics": False,
                "has_optimizer": False,
                "has_message_bus": False,
                "has_subscriptions": False,
                "has_dimension_tracking": False,
                "message_bus_events": [],
                "subscribed_events": [],
                "dimensions_tracked": [],
                "metrics_tracked": [],
                "ipc_documents": [],
                "tools_used": [],
                "imports": []
            }
            
            # Analyze imports
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module:
                        analysis["imports"].append(node.module)
                        
                        # Check for polytopic components
                        if "adaptive_prompts" in node.module:
                            analysis["has_adaptive_prompts"] = True
                        if "pattern_recognition" in node.module:
                            analysis["has_pattern_recognition"] = True
                        if "correlation" in node.module:
                            analysis["has_correlation"] = True
                        if "analytics" in node.module:
                            analysis["has_analytics"] = True
                        if "optimizer" in node.module:
                            analysis["has_optimizer"] = True
                        if "message_bus" in node.module:
                            analysis["has_message_bus"] = True
            
            # Analyze method calls
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        method_name = node.func.attr
                        
                        # Message bus publishing
                        if method_name == "publish":
                            if node.args and isinstance(node.args[0], ast.Constant):
                                analysis["message_bus_events"].append(node.args[0].value)
                        
                        # Message bus subscriptions
                        if method_name == "subscribe":
                            if node.args and isinstance(node.args[0], ast.Constant):
                                analysis["subscribed_events"].append(node.args[0].value)
                                analysis["has_subscriptions"] = True
                        
                        # Dimension tracking
                        if method_name == "track_dimensions":
                            analysis["has_dimension_tracking"] = True
                        
                        # Analytics
                        if method_name == "track_phase_metric":
                            if node.args and isinstance(node.args[0], ast.Constant):
                                analysis["metrics_tracked"].append(node.args[0].value)
                        
                        # IPC documents
                        if method_name in ["read_document", "write_document", "update_document"]:
                            if node.args and isinstance(node.args[0], ast.Constant):
                                analysis["ipc_documents"].append(node.args[0].value)
            
            # Calculate integration score
            score = 0
            if analysis["has_adaptive_prompts"]: score += 1
            if analysis["has_pattern_recognition"]: score += 1
            if analysis["has_correlation"]: score += 1
            if analysis["has_analytics"]: score += 1
            if analysis["has_optimizer"]: score += 1
            if analysis["has_message_bus"]: score += 1
            
            analysis["integration_score"] = score
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None
    
    def analyze_all_phases(self):
        """Analyze all phase files"""
        print("🔍 Analyzing all phase files...")
        
        phase_files = list(self.phases_dir.glob("*.py"))
        phase_files = [f for f in phase_files if not f.name.startswith("__")]
        
        for phase_file in sorted(phase_files):
            analysis = self.analyze_phase_file(phase_file)
            if analysis:
                phase_name = phase_file.stem
                self.results["integration_scores"][phase_name] = analysis["integration_score"]
                
                if analysis["has_dimension_tracking"]:
                    self.results["dimension_tracking"][phase_name] = True
                
                if analysis["has_subscriptions"]:
                    self.results["message_bus"][phase_name] = {
                        "publishes": analysis["message_bus_events"],
                        "subscribes": analysis["subscribed_events"]
                    }
                
                self.results["learning_systems"][phase_name] = {
                    "adaptive_prompts": analysis["has_adaptive_prompts"],
                    "pattern_recognition": analysis["has_pattern_recognition"],
                    "correlation": analysis["has_correlation"]
                }
                
                if analysis["metrics_tracked"]:
                    self.results["ipc_usage"][phase_name] = {
                        "metrics": analysis["metrics_tracked"],
                        "documents": analysis["ipc_documents"]
                    }
        
        print(f"✅ Analyzed {len(phase_files)} phase files")
    
    def identify_improvement_opportunities(self):
        """Identify areas for improvement"""
        print("\n🎯 Identifying improvement opportunities...")
        
        opportunities = []
        
        # 1. Phases without dimension tracking
        phases_without_tracking = []
        for phase, score in self.results["integration_scores"].items():
            if score == 6 and phase not in self.results["dimension_tracking"]:
                phases_without_tracking.append(phase)
        
        if phases_without_tracking:
            opportunities.append({
                "priority": "HIGH",
                "category": "Dimension Tracking",
                "description": f"Add dimension tracking to {len(phases_without_tracking)} phases",
                "phases": phases_without_tracking,
                "impact": "Enable adaptive polytopic positioning"
            })
        
        # 2. Phases without subscriptions
        phases_without_subs = []
        for phase, score in self.results["integration_scores"].items():
            if score == 6 and phase not in self.results["message_bus"]:
                phases_without_subs.append(phase)
        
        if phases_without_subs:
            opportunities.append({
                "priority": "MEDIUM",
                "category": "Message Bus",
                "description": f"Add subscriptions to {len(phases_without_subs)} phases",
                "phases": phases_without_subs,
                "impact": "Enable reactive event-driven coordination"
            })
        
        # 3. Phases with low integration scores
        low_integration = []
        for phase, score in self.results["integration_scores"].items():
            if score < 6 and not phase.endswith("_mixin") and not phase.endswith("_builder"):
                low_integration.append((phase, score))
        
        if low_integration:
            opportunities.append({
                "priority": "MEDIUM",
                "category": "Integration",
                "description": f"Improve integration for {len(low_integration)} phases",
                "phases": [p[0] for p in low_integration],
                "scores": {p[0]: p[1] for p in low_integration},
                "impact": "Increase overall system integration"
            })
        
        # 4. Learning system utilization
        phases_with_learning = sum(1 for ls in self.results["learning_systems"].values() 
                                   if ls["adaptive_prompts"] and ls["pattern_recognition"])
        total_phases = len([p for p in self.results["integration_scores"].keys() 
                           if not p.endswith("_mixin") and not p.endswith("_builder")])
        
        if phases_with_learning < total_phases:
            opportunities.append({
                "priority": "LOW",
                "category": "Learning Systems",
                "description": f"Learning systems active in {phases_with_learning}/{total_phases} phases",
                "impact": "Maximize learning and adaptation capabilities"
            })
        
        self.results["improvement_opportunities"] = opportunities
        print(f"✅ Identified {len(opportunities)} improvement opportunities")
    
    def generate_report(self) -> str:
        """Generate comprehensive analysis report"""
        report = []
        report.append("# 🔬 Comprehensive Polytopic Structure Analysis")
        report.append("")
        report.append("## 📊 Integration Score Summary")
        report.append("")
        
        # Group by score
        by_score = defaultdict(list)
        for phase, score in sorted(self.results["integration_scores"].items()):
            by_score[score].append(phase)
        
        for score in sorted(by_score.keys(), reverse=True):
            phases = by_score[score]
            report.append(f"### Score {score}/6: {len(phases)} phases")
            for phase in sorted(phases):
                report.append(f"- {phase}")
            report.append("")
        
        # Average score
        scores = list(self.results["integration_scores"].values())
        avg_score = sum(scores) / len(scores) if scores else 0
        report.append(f"**Average Integration Score**: {avg_score:.2f}/6")
        report.append("")
        
        # Dimension tracking
        report.append("## 🎯 Dimension Tracking Status")
        report.append("")
        tracked = len(self.results["dimension_tracking"])
        total = len([p for p in self.results["integration_scores"].keys() 
                    if not p.endswith("_mixin") and not p.endswith("_builder")])
        report.append(f"**Phases with Dimension Tracking**: {tracked}/{total} ({tracked*100//total}%)")
        report.append("")
        
        if self.results["dimension_tracking"]:
            report.append("### Phases with Tracking:")
            for phase in sorted(self.results["dimension_tracking"].keys()):
                report.append(f"- {phase}")
            report.append("")
        
        # Message bus
        report.append("## 📡 Message Bus Integration")
        report.append("")
        with_subs = len(self.results["message_bus"])
        report.append(f"**Phases with Subscriptions**: {with_subs}/{total} ({with_subs*100//total}%)")
        report.append("")
        
        if self.results["message_bus"]:
            report.append("### Event Patterns:")
            for phase, events in sorted(self.results["message_bus"].items()):
                report.append(f"#### {phase}")
                if events["publishes"]:
                    report.append(f"- **Publishes**: {', '.join(set(events['publishes']))}")
                if events["subscribes"]:
                    report.append(f"- **Subscribes**: {', '.join(set(events['subscribes']))}")
                report.append("")
        
        # Learning systems
        report.append("## 🧠 Learning Systems Status")
        report.append("")
        
        adaptive = sum(1 for ls in self.results["learning_systems"].values() if ls["adaptive_prompts"])
        pattern = sum(1 for ls in self.results["learning_systems"].values() if ls["pattern_recognition"])
        correlation = sum(1 for ls in self.results["learning_systems"].values() if ls["correlation"])
        
        report.append(f"- **Adaptive Prompts**: {adaptive}/{total} phases ({adaptive*100//total}%)")
        report.append(f"- **Pattern Recognition**: {pattern}/{total} phases ({pattern*100//total}%)")
        report.append(f"- **Correlation Engine**: {correlation}/{total} phases ({correlation*100//total}%)")
        report.append("")
        
        # Improvement opportunities
        report.append("## 🎯 Improvement Opportunities")
        report.append("")
        
        for i, opp in enumerate(self.results["improvement_opportunities"], 1):
            report.append(f"### {i}. {opp['category']} [{opp['priority']}]")
            report.append(f"**Description**: {opp['description']}")
            report.append(f"**Impact**: {opp['impact']}")
            if "phases" in opp:
                report.append(f"**Phases**: {', '.join(opp['phases'][:5])}")
                if len(opp['phases']) > 5:
                    report.append(f"  _(and {len(opp['phases']) - 5} more)_")
            report.append("")
        
        return "\n".join(report)
    
    def run_analysis(self):
        """Run complete analysis"""
        print("=" * 80)
        print("🔬 COMPREHENSIVE POLYTOPIC STRUCTURE ANALYSIS")
        print("=" * 80)
        print()
        
        self.analyze_all_phases()
        self.identify_improvement_opportunities()
        
        report = self.generate_report()
        
        # Save report
        report_path = self.project_root / "COMPREHENSIVE_POLYTOPIC_ANALYSIS.md"
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"\n✅ Analysis complete! Report saved to: {report_path.name}")
        print()
        
        # Print summary
        print("📊 SUMMARY")
        print("-" * 80)
        scores = list(self.results["integration_scores"].values())
        avg_score = sum(scores) / len(scores) if scores else 0
        print(f"Average Integration Score: {avg_score:.2f}/6")
        print(f"Phases Analyzed: {len(scores)}")
        print(f"Dimension Tracking: {len(self.results['dimension_tracking'])} phases")
        print(f"Message Bus Subscriptions: {len(self.results['message_bus'])} phases")
        print(f"Improvement Opportunities: {len(self.results['improvement_opportunities'])}")
        print()

if __name__ == "__main__":
    project_root = Path(".")
    analyzer = ComprehensivePolytopicAnalyzer(project_root)
    analyzer.run_analysis()