#!/usr/bin/env python3
"""
Deep Implementation Analysis
Analyzes actual implementation details by examining method calls,
attribute access, and inheritance patterns.
"""

import ast
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set

class DeepImplementationAnalyzer:
    """Analyzes actual implementation patterns in the codebase"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.phases_dir = project_root / "pipeline" / "phases"
        self.results = {
            "phases": {},
            "patterns": defaultdict(list),
            "statistics": {},
            "recommendations": []
        }
    
    def analyze_phase_implementation(self, file_path: Path) -> Dict:
        """Deeply analyze a phase implementation"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            analysis = {
                "file": file_path.name,
                "phase_name": file_path.stem,
                "line_count": len(content.split('\n')),
                "class_count": 0,
                "method_count": 0,
                "features": {
                    "adaptive_prompts": self._check_feature(content, [
                        "self.adaptive_prompts",
                        "adaptive_prompts.get_prompt",
                        "adaptive_prompts.record_result"
                    ]),
                    "pattern_recognition": self._check_feature(content, [
                        "self.pattern_recognition",
                        "pattern_recognition.record_pattern",
                        "pattern_recognition.analyze_patterns"
                    ]),
                    "correlation": self._check_feature(content, [
                        "self.correlation",
                        "correlation.record_correlation",
                        "correlation.get_correlations"
                    ]),
                    "analytics": self._check_feature(content, [
                        "self.analytics",
                        "track_phase_metric",
                        "analytics.track_metric"
                    ]),
                    "optimizer": self._check_feature(content, [
                        "self.optimizer",
                        "optimizer.optimize",
                        "pattern_optimizer"
                    ]),
                    "message_bus": self._check_feature(content, [
                        "self.message_bus",
                        "message_bus.publish",
                        "self.publish_event"
                    ]),
                    "subscriptions": self._check_feature(content, [
                        "message_bus.subscribe",
                        "self.subscribe",
                        "_setup_subscriptions"
                    ]),
                    "dimension_tracking": self._check_feature(content, [
                        "track_dimensions",
                        "self.dimensions",
                        "update_dimension"
                    ]),
                    "ipc_documents": self._check_feature(content, [
                        "read_document",
                        "write_document",
                        "update_document"
                    ])
                },
                "method_patterns": self._extract_method_patterns(content),
                "complexity_indicators": self._analyze_complexity(content)
            }
            
            # Parse AST for detailed analysis
            try:
                tree = ast.parse(content)
                analysis["class_count"] = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
                analysis["method_count"] = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
            except:
                pass
            
            # Calculate integration score
            score = sum(1 for feature, present in analysis["features"].items() 
                       if present and feature not in ["subscriptions", "dimension_tracking", "ipc_documents"])
            analysis["integration_score"] = score
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None
    
    def _check_feature(self, content: str, patterns: List[str]) -> bool:
        """Check if any of the patterns exist in content"""
        return any(pattern in content for pattern in patterns)
    
    def _extract_method_patterns(self, content: str) -> Dict:
        """Extract common method patterns"""
        patterns = {
            "execute_methods": len(re.findall(r'def execute\(', content)),
            "async_methods": len(re.findall(r'async def', content)),
            "property_methods": len(re.findall(r'@property', content)),
            "error_handling": len(re.findall(r'try:|except:', content)),
            "logging_calls": len(re.findall(r'logger\.|self\.logger\.', content))
        }
        return patterns
    
    def _analyze_complexity(self, content: str) -> Dict:
        """Analyze code complexity indicators"""
        return {
            "if_statements": len(re.findall(r'\bif\b', content)),
            "for_loops": len(re.findall(r'\bfor\b', content)),
            "while_loops": len(re.findall(r'\bwhile\b', content)),
            "function_calls": len(re.findall(r'\w+\([^)]*\)', content)),
            "class_definitions": len(re.findall(r'class \w+', content))
        }
    
    def analyze_all_phases(self):
        """Analyze all phase files"""
        print("🔍 Analyzing phase implementations...")
        
        phase_files = list(self.phases_dir.glob("*.py"))
        phase_files = [f for f in phase_files if not f.name.startswith("__")]
        
        for phase_file in sorted(phase_files):
            analysis = self.analyze_phase_implementation(phase_file)
            if analysis:
                self.results["phases"][analysis["phase_name"]] = analysis
                
                # Track patterns
                for feature, present in analysis["features"].items():
                    if present:
                        self.results["patterns"][feature].append(analysis["phase_name"])
        
        print(f"✅ Analyzed {len(phase_files)} phase files")
    
    def generate_statistics(self):
        """Generate comprehensive statistics"""
        print("\n📊 Generating statistics...")
        
        total_phases = len(self.results["phases"])
        execution_phases = [p for p in self.results["phases"].values() 
                           if not p["phase_name"].endswith("_mixin") 
                           and not p["phase_name"].endswith("_builder")
                           and p["phase_name"] not in ["base", "analysis_orchestrator", "phase_dependencies"]]
        
        self.results["statistics"] = {
            "total_phases": total_phases,
            "execution_phases": len(execution_phases),
            "average_integration_score": sum(p["integration_score"] for p in execution_phases) / len(execution_phases) if execution_phases else 0,
            "total_lines": sum(p["line_count"] for p in self.results["phases"].values()),
            "total_classes": sum(p["class_count"] for p in self.results["phases"].values()),
            "total_methods": sum(p["method_count"] for p in self.results["phases"].values()),
            "feature_coverage": {
                feature: len(phases) for feature, phases in self.results["patterns"].items()
            }
        }
        
        print("✅ Statistics generated")
    
    def identify_recommendations(self):
        """Identify improvement recommendations"""
        print("\n🎯 Identifying recommendations...")
        
        execution_phases = [p for p in self.results["phases"].values() 
                           if not p["phase_name"].endswith("_mixin") 
                           and not p["phase_name"].endswith("_builder")
                           and p["phase_name"] not in ["base", "analysis_orchestrator", "phase_dependencies"]]
        
        # 1. Phases with full integration but no dimension tracking
        full_integration_no_tracking = [
            p["phase_name"] for p in execution_phases
            if p["integration_score"] >= 5 and not p["features"]["dimension_tracking"]
        ]
        
        if full_integration_no_tracking:
            self.results["recommendations"].append({
                "priority": "HIGH",
                "category": "Dimension Tracking",
                "title": "Add dimension tracking to fully integrated phases",
                "description": f"{len(full_integration_no_tracking)} phases have full integration but lack dimension tracking",
                "phases": full_integration_no_tracking,
                "benefit": "Enable adaptive polytopic positioning for optimal phase coordination"
            })
        
        # 2. Phases with message bus but no subscriptions
        message_bus_no_subs = [
            p["phase_name"] for p in execution_phases
            if p["features"]["message_bus"] and not p["features"]["subscriptions"]
        ]
        
        if message_bus_no_subs:
            self.results["recommendations"].append({
                "priority": "MEDIUM",
                "category": "Event-Driven Architecture",
                "title": "Add message bus subscriptions for reactive coordination",
                "description": f"{len(message_bus_no_subs)} phases publish events but don't subscribe",
                "phases": message_bus_no_subs,
                "benefit": "Enable reactive event-driven coordination between phases"
            })
        
        # 3. Phases with low integration scores
        low_integration = [
            (p["phase_name"], p["integration_score"]) for p in execution_phases
            if p["integration_score"] < 4
        ]
        
        if low_integration:
            self.results["recommendations"].append({
                "priority": "MEDIUM",
                "category": "Integration Enhancement",
                "title": "Improve integration for phases with low scores",
                "description": f"{len(low_integration)} phases have integration scores below 4/6",
                "phases": [p[0] for p in low_integration],
                "scores": {p[0]: p[1] for p in low_integration},
                "benefit": "Increase overall system integration and learning capabilities"
            })
        
        # 4. Complex phases without adequate error handling
        complex_phases = [
            p["phase_name"] for p in execution_phases
            if p["complexity_indicators"]["if_statements"] > 20
            and p["method_patterns"]["error_handling"] < 5
        ]
        
        if complex_phases:
            self.results["recommendations"].append({
                "priority": "LOW",
                "category": "Code Quality",
                "title": "Enhance error handling in complex phases",
                "description": f"{len(complex_phases)} complex phases have minimal error handling",
                "phases": complex_phases,
                "benefit": "Improve system reliability and debugging capabilities"
            })
        
        print(f"✅ Identified {len(self.results['recommendations'])} recommendations")
    
    def generate_report(self) -> str:
        """Generate comprehensive analysis report"""
        report = []
        report.append("# 🔬 Deep Implementation Analysis Report")
        report.append("")
        report.append("## 📊 Overall Statistics")
        report.append("")
        
        stats = self.results["statistics"]
        report.append(f"- **Total Phases**: {stats['total_phases']}")
        report.append(f"- **Execution Phases**: {stats['execution_phases']}")
        report.append(f"- **Average Integration Score**: {stats['average_integration_score']:.2f}/6")
        report.append(f"- **Total Lines of Code**: {stats['total_lines']:,}")
        report.append(f"- **Total Classes**: {stats['total_classes']}")
        report.append(f"- **Total Methods**: {stats['total_methods']}")
        report.append("")
        
        # Feature coverage
        report.append("## 🎯 Feature Coverage")
        report.append("")
        for feature, count in sorted(stats['feature_coverage'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / stats['execution_phases'] * 100) if stats['execution_phases'] > 0 else 0
            report.append(f"- **{feature.replace('_', ' ').title()}**: {count}/{stats['execution_phases']} phases ({percentage:.0f}%)")
        report.append("")
        
        # Integration scores by phase
        report.append("## 📈 Integration Scores by Phase")
        report.append("")
        
        execution_phases = [p for p in self.results["phases"].values() 
                           if not p["phase_name"].endswith("_mixin") 
                           and not p["phase_name"].endswith("_builder")
                           and p["phase_name"] not in ["base", "analysis_orchestrator", "phase_dependencies"]]
        
        by_score = defaultdict(list)
        for phase in execution_phases:
            by_score[phase["integration_score"]].append(phase["phase_name"])
        
        for score in sorted(by_score.keys(), reverse=True):
            phases = by_score[score]
            report.append(f"### Score {score}/6: {len(phases)} phases")
            for phase in sorted(phases):
                phase_data = self.results["phases"][phase]
                features = [f for f, present in phase_data["features"].items() if present]
                report.append(f"- **{phase}**: {', '.join(features[:3])}")
                if len(features) > 3:
                    report.append(f"  _(and {len(features) - 3} more features)_")
            report.append("")
        
        # Recommendations
        report.append("## 🎯 Recommendations")
        report.append("")
        
        for i, rec in enumerate(self.results["recommendations"], 1):
            report.append(f"### {i}. {rec['title']} [{rec['priority']}]")
            report.append(f"**Category**: {rec['category']}")
            report.append(f"**Description**: {rec['description']}")
            report.append(f"**Benefit**: {rec['benefit']}")
            report.append(f"**Affected Phases**: {len(rec['phases'])}")
            if len(rec['phases']) <= 5:
                report.append(f"- {', '.join(rec['phases'])}")
            else:
                report.append(f"- {', '.join(rec['phases'][:5])} _(and {len(rec['phases']) - 5} more)_")
            report.append("")
        
        # Detailed phase analysis
        report.append("## 📋 Detailed Phase Analysis")
        report.append("")
        
        for phase_name in sorted(self.results["phases"].keys()):
            phase = self.results["phases"][phase_name]
            if phase_name.endswith("_mixin") or phase_name.endswith("_builder") or phase_name in ["base", "analysis_orchestrator", "phase_dependencies"]:
                continue
            
            report.append(f"### {phase_name}")
            report.append(f"- **Integration Score**: {phase['integration_score']}/6")
            report.append(f"- **Lines of Code**: {phase['line_count']}")
            report.append(f"- **Methods**: {phase['method_count']}")
            
            active_features = [f for f, present in phase["features"].items() if present]
            if active_features:
                report.append(f"- **Active Features**: {', '.join(active_features)}")
            
            report.append("")
        
        return "\n".join(report)
    
    def run_analysis(self):
        """Run complete deep analysis"""
        print("=" * 80)
        print("🔬 DEEP IMPLEMENTATION ANALYSIS")
        print("=" * 80)
        print()
        
        self.analyze_all_phases()
        self.generate_statistics()
        self.identify_recommendations()
        
        report = self.generate_report()
        
        # Save report
        report_path = self.project_root / "DEEP_IMPLEMENTATION_ANALYSIS.md"
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"\n✅ Analysis complete! Report saved to: {report_path.name}")
        print()
        
        # Print summary
        print("📊 SUMMARY")
        print("-" * 80)
        stats = self.results["statistics"]
        print(f"Execution Phases: {stats['execution_phases']}")
        print(f"Average Integration Score: {stats['average_integration_score']:.2f}/6")
        print(f"Total Lines of Code: {stats['total_lines']:,}")
        print(f"Recommendations: {len(self.results['recommendations'])}")
        print()

if __name__ == "__main__":
    project_root = Path(".")
    analyzer = DeepImplementationAnalyzer(project_root)
    analyzer.run_analysis()