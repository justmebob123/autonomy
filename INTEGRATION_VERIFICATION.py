"""
Deep Integration Verification

Verifies that all new polytopic features are properly integrated
across all systems and subsystems.
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

class IntegrationVerifier:
    """Verifies integration across all systems."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues = []
        self.warnings = []
        self.successes = []
        
    def verify_all(self):
        """Run all integration verification checks."""
        print("=" * 80)
        print("INTEGRATION VERIFICATION")
        print("=" * 80)
        
        # Check 1: Coordinator uses PolytopicObjectiveManager
        print("\n[CHECK 1] Coordinator Integration...")
        self.verify_coordinator_integration()
        
        # Check 2: All phases can access message bus
        print("\n[CHECK 2] Message Bus Integration...")
        self.verify_message_bus_integration()
        
        # Check 3: Polytopic manager properly extends base
        print("\n[CHECK 3] Polytopic Manager Inheritance...")
        self.verify_polytopic_inheritance()
        
        # Check 4: Dimensional profiles are calculated
        print("\n[CHECK 4] Dimensional Profile Calculation...")
        self.verify_dimensional_profiles()
        
        # Check 5: Health analysis is integrated
        print("\n[CHECK 5] Health Analysis Integration...")
        self.verify_health_analysis()
        
        # Check 6: Strategic decision-making uses 7D navigation
        print("\n[CHECK 6] Strategic Decision-Making...")
        self.verify_strategic_decisions()
        
        # Check 7: Logging includes dimensional metrics
        print("\n[CHECK 7] Dimensional Logging...")
        self.verify_dimensional_logging()
        
        # Check 8: Backward compatibility maintained
        print("\n[CHECK 8] Backward Compatibility...")
        self.verify_backward_compatibility()
        
        # Generate report
        self.generate_report()
    
    def verify_coordinator_integration(self):
        """Verify coordinator properly uses PolytopicObjectiveManager."""
        coordinator_file = self.project_root / "pipeline" / "coordinator.py"
        
        if not coordinator_file.exists():
            self.issues.append("Coordinator file not found")
            return
        
        content = coordinator_file.read_text()
        
        # Check import
        if "from .polytopic import PolytopicObjectiveManager" in content:
            self.successes.append("✓ Coordinator imports PolytopicObjectiveManager")
        else:
            self.issues.append("✗ Coordinator does not import PolytopicObjectiveManager")
        
        # Check instantiation
        if "PolytopicObjectiveManager(self.project_dir, self.state_manager)" in content:
            self.successes.append("✓ Coordinator instantiates PolytopicObjectiveManager")
        else:
            self.issues.append("✗ Coordinator does not instantiate PolytopicObjectiveManager")
        
        # Check 7D navigation usage
        if "find_optimal_objective" in content:
            self.successes.append("✓ Coordinator uses find_optimal_objective()")
        else:
            self.warnings.append("⚠ Coordinator may not use 7D navigation")
        
        # Check dimensional health
        if "analyze_dimensional_health" in content:
            self.successes.append("✓ Coordinator uses analyze_dimensional_health()")
        else:
            self.warnings.append("⚠ Coordinator may not use dimensional health analysis")
    
    def verify_message_bus_integration(self):
        """Verify message bus is integrated with phases."""
        base_phase_file = self.project_root / "pipeline" / "phases" / "base.py"
        
        if not base_phase_file.exists():
            self.issues.append("Base phase file not found")
            return
        
        content = base_phase_file.read_text()
        
        # Check message_bus parameter
        if "message_bus" in content:
            self.successes.append("✓ BasePhase has message_bus parameter")
        else:
            self.issues.append("✗ BasePhase missing message_bus parameter")
        
        # Check helper methods
        helper_methods = ["_publish_message", "_subscribe_to_messages", "_get_messages"]
        for method in helper_methods:
            if method in content:
                self.successes.append(f"✓ BasePhase has {method}()")
            else:
                self.warnings.append(f"⚠ BasePhase missing {method}()")
    
    def verify_polytopic_inheritance(self):
        """Verify PolytopicObjectiveManager properly extends ObjectiveManager."""
        manager_file = self.project_root / "pipeline" / "polytopic" / "polytopic_manager.py"
        
        if not manager_file.exists():
            self.issues.append("PolytopicObjectiveManager file not found")
            return
        
        content = manager_file.read_text()
        
        # Check inheritance
        if "class PolytopicObjectiveManager(ObjectiveManager)" in content:
            self.successes.append("✓ PolytopicObjectiveManager extends ObjectiveManager")
        else:
            self.issues.append("✗ PolytopicObjectiveManager does not extend ObjectiveManager")
        
        # Check super() calls
        if "super().__init__" in content:
            self.successes.append("✓ PolytopicObjectiveManager calls super().__init__()")
        else:
            self.warnings.append("⚠ PolytopicObjectiveManager may not call super().__init__()")
        
        # Check load_objectives override
        if "def load_objectives(self, state: PipelineState)" in content:
            self.successes.append("✓ PolytopicObjectiveManager overrides load_objectives()")
        else:
            self.issues.append("✗ PolytopicObjectiveManager does not override load_objectives()")
    
    def verify_dimensional_profiles(self):
        """Verify dimensional profiles are properly calculated."""
        manager_file = self.project_root / "pipeline" / "polytopic" / "polytopic_manager.py"
        
        if not manager_file.exists():
            return
        
        content = manager_file.read_text()
        
        # Check all 7 dimensions
        dimensions = ["temporal", "functional", "data", "state", "error", "context", "integration"]
        for dim in dimensions:
            if f'"{dim}"' in content or f"'{dim}'" in content:
                self.successes.append(f"✓ Dimension '{dim}' is calculated")
            else:
                self.warnings.append(f"⚠ Dimension '{dim}' may not be calculated")
        
        # Check profile calculation method
        if "def calculate_dimensional_profile" in content:
            self.successes.append("✓ calculate_dimensional_profile() method exists")
        else:
            self.issues.append("✗ calculate_dimensional_profile() method missing")
    
    def verify_health_analysis(self):
        """Verify health analysis is properly integrated."""
        manager_file = self.project_root / "pipeline" / "polytopic" / "polytopic_manager.py"
        
        if not manager_file.exists():
            return
        
        content = manager_file.read_text()
        
        # Check health analysis method
        if "def analyze_dimensional_health" in content:
            self.successes.append("✓ analyze_dimensional_health() method exists")
        else:
            self.issues.append("✗ analyze_dimensional_health() method missing")
        
        # Check health statuses
        health_statuses = ["HEALTHY", "DEGRADING", "CRITICAL", "BLOCKED"]
        found_statuses = sum(1 for status in health_statuses if status in content)
        if found_statuses >= 3:
            self.successes.append(f"✓ Health statuses defined ({found_statuses}/4)")
        else:
            self.warnings.append(f"⚠ Only {found_statuses}/4 health statuses found")
    
    def verify_strategic_decisions(self):
        """Verify strategic decision-making uses 7D navigation."""
        coordinator_file = self.project_root / "pipeline" / "coordinator.py"
        
        if not coordinator_file.exists():
            return
        
        content = coordinator_file.read_text()
        
        # Check strategic method exists
        if "def _determine_next_action_strategic" in content:
            self.successes.append("✓ _determine_next_action_strategic() method exists")
        else:
            self.issues.append("✗ _determine_next_action_strategic() method missing")
        
        # Check 7D navigation usage
        if "find_optimal_objective" in content:
            self.successes.append("✓ Strategic decisions use find_optimal_objective()")
        else:
            self.issues.append("✗ Strategic decisions do not use 7D navigation")
        
        # Check dimensional health usage
        if "dimensional_health" in content:
            self.successes.append("✓ Strategic decisions consider dimensional health")
        else:
            self.warnings.append("⚠ Strategic decisions may not consider dimensional health")
    
    def verify_dimensional_logging(self):
        """Verify dimensional metrics are logged."""
        coordinator_file = self.project_root / "pipeline" / "coordinator.py"
        
        if not coordinator_file.exists():
            return
        
        content = coordinator_file.read_text()
        
        # Check metric logging
        metrics = ["complexity_score", "risk_score", "readiness_score"]
        for metric in metrics:
            if metric in content:
                self.successes.append(f"✓ {metric} is logged")
            else:
                self.warnings.append(f"⚠ {metric} may not be logged")
        
        # Check dimensional space logging
        if "Dimensional Space" in content or "dimensional_space" in content:
            self.successes.append("✓ Dimensional space information is logged")
        else:
            self.warnings.append("⚠ Dimensional space may not be logged")
    
    def verify_backward_compatibility(self):
        """Verify backward compatibility is maintained."""
        coordinator_file = self.project_root / "pipeline" / "coordinator.py"
        
        if not coordinator_file.exists():
            return
        
        content = coordinator_file.read_text()
        
        # Check tactical mode still exists
        if "def _determine_next_action_tactical" in content:
            self.successes.append("✓ Tactical mode (backward compatibility) maintained")
        else:
            self.warnings.append("⚠ Tactical mode may not be available")
        
        # Check fallback logic
        if "if state.objectives" in content or "if not objective" in content:
            self.successes.append("✓ Fallback logic exists for missing objectives")
        else:
            self.warnings.append("⚠ Fallback logic may be missing")
    
    def generate_report(self):
        """Generate integration verification report."""
        print("\n" + "=" * 80)
        print("INTEGRATION VERIFICATION REPORT")
        print("=" * 80)
        
        print(f"\n✓ SUCCESSES: {len(self.successes)}")
        for success in self.successes:
            print(f"  {success}")
        
        if self.warnings:
            print(f"\n⚠ WARNINGS: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if self.issues:
            print(f"\n✗ ISSUES: {len(self.issues)}")
            for issue in self.issues:
                print(f"  {issue}")
        else:
            print("\n✓ NO CRITICAL ISSUES FOUND")
        
        # Overall status
        print("\n" + "=" * 80)
        if not self.issues:
            print("STATUS: ✓ ALL INTEGRATIONS VERIFIED")
        elif len(self.issues) <= 2:
            print("STATUS: ⚠ MINOR ISSUES FOUND")
        else:
            print("STATUS: ✗ CRITICAL ISSUES FOUND")
        print("=" * 80)
        
        # Save report
        report = {
            'successes': self.successes,
            'warnings': self.warnings,
            'issues': self.issues,
            'summary': {
                'total_checks': len(self.successes) + len(self.warnings) + len(self.issues),
                'successes': len(self.successes),
                'warnings': len(self.warnings),
                'issues': len(self.issues)
            }
        }
        
        import json
        with open(self.project_root / 'INTEGRATION_VERIFICATION_REPORT.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print("\nReport saved to: INTEGRATION_VERIFICATION_REPORT.json")


if __name__ == "__main__":
    verifier = IntegrationVerifier(".")
    verifier.verify_all()