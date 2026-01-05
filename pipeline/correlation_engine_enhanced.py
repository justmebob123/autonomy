"""
Enhanced Correlation Engine for Cross-Phase Analysis

WEEK 2 PHASE 2 ENHANCEMENT:
This enhanced version adds:
1. Phase dependency analysis
2. Phase success prediction
3. Optimal phase sequence recommendation
4. Cross-phase pattern learning
5. Correlation-based decision support

Builds on existing correlation engine with pipeline-specific features.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from pathlib import Path
import json
import re


class PhaseCorrelation:
    """Represents a correlation between two phases"""
    
    def __init__(self, phase_a: str, phase_b: str, correlation_type: str, 
                 strength: float, evidence: List[Dict]):
        self.phase_a = phase_a
        self.phase_b = phase_b
        self.correlation_type = correlation_type
        self.strength = strength  # 0.0-1.0
        self.evidence = evidence
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "phase_a": self.phase_a,
            "phase_b": self.phase_b,
            "correlation_type": self.correlation_type,
            "strength": self.strength,
            "evidence_count": len(self.evidence),
            "timestamp": self.timestamp.isoformat()
        }


class PhaseDependency:
    """Represents a dependency between phases"""
    
    def __init__(self, source_phase: str, target_phase: str, 
                 dependency_type: str, strength: float):
        self.source_phase = source_phase
        self.target_phase = target_phase
        self.dependency_type = dependency_type
        self.strength = strength
        self.observations = 0
        self.success_rate = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "source": self.source_phase,
            "target": self.target_phase,
            "type": self.dependency_type,
            "strength": self.strength,
            "observations": self.observations,
            "success_rate": self.success_rate
        }


class EnhancedCorrelationEngine:
    """
    Enhanced correlation engine for pipeline phase analysis.
    
    WEEK 2 ENHANCEMENTS:
    - Phase dependency tracking
    - Success prediction based on correlations
    - Optimal phase sequence recommendation
    - Cross-phase pattern learning
    """
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        
        # Phase execution history
        self.phase_history: List[Dict] = []
        
        # Phase correlations
        self.correlations: Dict[Tuple[str, str], PhaseCorrelation] = {}
        
        # Phase dependencies
        self.dependencies: Dict[Tuple[str, str], PhaseDependency] = {}
        
        # Success patterns
        self.success_patterns: Dict[str, List[str]] = defaultdict(list)
        self.failure_patterns: Dict[str, List[str]] = defaultdict(list)
        
        # Phase transition matrix (phase_a -> phase_b -> success_rate)
        self.transition_matrix: Dict[Tuple[str, str], Dict] = {}
        
        # Load existing data
        self._load_data()
    
    def record_phase_execution(self, phase: str, success: bool, 
                              context: Optional[Dict] = None) -> None:
        """
        Record a phase execution for correlation analysis.
        
        Args:
            phase: Phase name
            success: Whether phase succeeded
            context: Additional context (tasks completed, errors, etc.)
        """
        record = {
            "phase": phase,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }
        
        self.phase_history.append(record)
        
        # Update success/failure patterns
        if success:
            # Record what happened before this success
            recent_phases = [r["phase"] for r in self.phase_history[-5:-1]]
            self.success_patterns[phase].append(tuple(recent_phases))
        else:
            # Record what happened before this failure
            recent_phases = [r["phase"] for r in self.phase_history[-5:-1]]
            self.failure_patterns[phase].append(tuple(recent_phases))
        
        # Update transition matrix
        if len(self.phase_history) >= 2:
            prev_phase = self.phase_history[-2]["phase"]
            transition_key = (prev_phase, phase)
            
            if transition_key not in self.transition_matrix:
                self.transition_matrix[transition_key] = {
                    "total": 0,
                    "successes": 0,
                    "failures": 0
                }
            
            self.transition_matrix[transition_key]["total"] += 1
            if success:
                self.transition_matrix[transition_key]["successes"] += 1
            else:
                self.transition_matrix[transition_key]["failures"] += 1
        
        # Analyze correlations periodically
        if len(self.phase_history) % 10 == 0:
            self._analyze_correlations()
        
        # Save data
        self._save_data()
    
    def analyze_phase_dependencies(self) -> Dict[str, List[Dict]]:
        """
        Analyze dependencies between phases.
        
        Returns:
            Dictionary mapping each phase to its dependencies
        """
        dependencies = defaultdict(list)
        
        # Analyze transition patterns
        for (source, target), stats in self.transition_matrix.items():
            if stats["total"] < 3:
                continue  # Need more data
            
            success_rate = stats["successes"] / stats["total"]
            
            # Strong dependency if high success rate
            if success_rate > 0.7:
                dep = PhaseDependency(
                    source_phase=source,
                    target_phase=target,
                    dependency_type="sequential",
                    strength=success_rate
                )
                dep.observations = stats["total"]
                dep.success_rate = success_rate
                
                dependencies[target].append(dep.to_dict())
                
                # Store for later use
                self.dependencies[(source, target)] = dep
        
        # Analyze success patterns
        for phase, patterns in self.success_patterns.items():
            if len(patterns) < 3:
                continue
            
            # Find most common preceding phases
            all_preceding = []
            for pattern in patterns:
                all_preceding.extend(pattern)
            
            if not all_preceding:
                continue
            
            common_preceding = Counter(all_preceding).most_common(3)
            
            for preceding_phase, count in common_preceding:
                if count / len(patterns) > 0.5:  # Appears in >50% of successes
                    dep = PhaseDependency(
                        source_phase=preceding_phase,
                        target_phase=phase,
                        dependency_type="prerequisite",
                        strength=count / len(patterns)
                    )
                    dep.observations = count
                    
                    dependencies[phase].append(dep.to_dict())
        
        return dict(dependencies)
    
    def predict_phase_success(self, phase: str, context: Optional[Dict] = None) -> Dict:
        """
        Predict success probability for a phase based on current context.
        
        Args:
            phase: Phase to predict success for
            context: Current context (recent phases, state, etc.)
            
        Returns:
            Dictionary with prediction details
        """
        # Get recent phase history
        recent_phases = [r["phase"] for r in self.phase_history[-5:]]
        recent_pattern = tuple(recent_phases)
        
        # Check success patterns
        success_matches = sum(
            1 for pattern in self.success_patterns[phase]
            if self._pattern_similarity(recent_pattern, pattern) > 0.6
        )
        
        # Check failure patterns
        failure_matches = sum(
            1 for pattern in self.failure_patterns[phase]
            if self._pattern_similarity(recent_pattern, pattern) > 0.6
        )
        
        total_matches = success_matches + failure_matches
        
        if total_matches == 0:
            # No historical data - use transition matrix
            if len(self.phase_history) > 0:
                prev_phase = self.phase_history[-1]["phase"]
                transition_key = (prev_phase, phase)
                
                if transition_key in self.transition_matrix:
                    stats = self.transition_matrix[transition_key]
                    success_prob = stats["successes"] / stats["total"]
                    confidence = min(1.0, stats["total"] / 10)
                    
                    return {
                        "phase": phase,
                        "success_probability": success_prob,
                        "confidence": confidence,
                        "basis": "transition_history",
                        "observations": stats["total"]
                    }
            
            # No data at all
            return {
                "phase": phase,
                "success_probability": 0.5,
                "confidence": 0.0,
                "basis": "no_data",
                "observations": 0
            }
        
        # Calculate probability based on pattern matches
        success_prob = success_matches / total_matches
        confidence = min(1.0, total_matches / 10)
        
        # Adjust based on dependencies
        dependencies = self.analyze_phase_dependencies().get(phase, [])
        if dependencies:
            # Check if prerequisites are met
            met_prerequisites = 0
            total_prerequisites = 0
            
            for dep in dependencies:
                if dep["type"] == "prerequisite":
                    total_prerequisites += 1
                    if dep["source"] in recent_phases:
                        met_prerequisites += 1
            
            if total_prerequisites > 0:
                prerequisite_factor = met_prerequisites / total_prerequisites
                success_prob = success_prob * 0.7 + prerequisite_factor * 0.3
        
        return {
            "phase": phase,
            "success_probability": success_prob,
            "confidence": confidence,
            "basis": "pattern_matching",
            "observations": total_matches,
            "success_matches": success_matches,
            "failure_matches": failure_matches
        }
    
    def recommend_phase_sequence(self, objectives: List[str], 
                                current_phase: Optional[str] = None) -> List[Dict]:
        """
        Recommend optimal phase sequence based on objectives and correlations.
        
        Args:
            objectives: List of objectives to achieve
            current_phase: Current phase (if any)
            
        Returns:
            List of recommended phases with rationale
        """
        recommendations = []
        
        # Map objectives to phases
        objective_phase_map = {
            "implement_features": ["planning", "coding"],
            "fix_bugs": ["debugging", "qa"],
            "improve_quality": ["qa", "refactoring"],
            "optimize_performance": ["investigation", "refactoring"],
            "update_docs": ["documentation"],
            "analyze_architecture": ["investigation", "planning"]
        }
        
        # Collect candidate phases
        candidate_phases = set()
        for objective in objectives:
            phases = objective_phase_map.get(objective, [])
            candidate_phases.update(phases)
        
        if not candidate_phases:
            # Default sequence
            candidate_phases = {"planning", "coding", "qa"}
        
        # Score each phase
        phase_scores = {}
        for phase in candidate_phases:
            prediction = self.predict_phase_success(phase)
            
            # Base score on success probability
            score = prediction["success_probability"] * prediction["confidence"]
            
            # Boost score if dependencies are met
            dependencies = self.analyze_phase_dependencies().get(phase, [])
            if dependencies:
                recent_phases = [r["phase"] for r in self.phase_history[-5:]]
                met_deps = sum(
                    1 for dep in dependencies
                    if dep["source"] in recent_phases
                )
                if met_deps > 0:
                    score *= (1.0 + 0.1 * met_deps)
            
            # Penalize if recently executed
            if len(self.phase_history) > 0:
                recent_phases = [r["phase"] for r in self.phase_history[-3:]]
                if phase in recent_phases:
                    score *= 0.7
            
            phase_scores[phase] = score
        
        # Sort by score
        sorted_phases = sorted(phase_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Build recommendations
        for phase, score in sorted_phases:
            prediction = self.predict_phase_success(phase)
            dependencies = self.analyze_phase_dependencies().get(phase, [])
            
            recommendations.append({
                "phase": phase,
                "score": score,
                "success_probability": prediction["success_probability"],
                "confidence": prediction["confidence"],
                "dependencies": dependencies,
                "rationale": self._generate_rationale(phase, score, prediction, dependencies)
            })
        
        return recommendations
    
    def get_cross_phase_correlations(self, phase_a: str, phase_b: str) -> Optional[Dict]:
        """
        Get correlation between two phases.
        
        Args:
            phase_a: First phase
            phase_b: Second phase
            
        Returns:
            Correlation dictionary or None
        """
        key = tuple(sorted([phase_a, phase_b]))
        correlation = self.correlations.get(key)
        
        if correlation:
            return correlation.to_dict()
        
        return None
    
    def get_phase_statistics(self, phase: str) -> Dict:
        """
        Get statistics for a specific phase.
        
        Args:
            phase: Phase name
            
        Returns:
            Dictionary with phase statistics
        """
        phase_records = [r for r in self.phase_history if r["phase"] == phase]
        
        if not phase_records:
            return {
                "phase": phase,
                "total_executions": 0,
                "success_rate": 0.0,
                "avg_success_probability": 0.0
            }
        
        successes = sum(1 for r in phase_records if r["success"])
        
        return {
            "phase": phase,
            "total_executions": len(phase_records),
            "successes": successes,
            "failures": len(phase_records) - successes,
            "success_rate": successes / len(phase_records),
            "recent_success_rate": self._calculate_recent_success_rate(phase),
            "common_predecessors": self._get_common_predecessors(phase),
            "common_successors": self._get_common_successors(phase)
        }
    
    def _analyze_correlations(self) -> None:
        """Analyze correlations between phases"""
        if len(self.phase_history) < 10:
            return
        
        # Get unique phases
        phases = list(set(r["phase"] for r in self.phase_history))
        
        # Analyze pairwise correlations
        for i, phase_a in enumerate(phases):
            for phase_b in phases[i+1:]:
                self._analyze_phase_pair(phase_a, phase_b)
    
    def _analyze_phase_pair(self, phase_a: str, phase_b: str) -> None:
        """Analyze correlation between two specific phases"""
        # Find sequences where both phases appear
        sequences = []
        
        for i in range(len(self.phase_history) - 1):
            window = self.phase_history[i:i+5]
            phases_in_window = [r["phase"] for r in window]
            
            if phase_a in phases_in_window and phase_b in phases_in_window:
                sequences.append(window)
        
        if len(sequences) < 3:
            return  # Not enough data
        
        # Analyze success patterns
        both_success = sum(
            1 for seq in sequences
            if all(r["success"] for r in seq if r["phase"] in [phase_a, phase_b])
        )
        
        correlation_strength = both_success / len(sequences)
        
        if correlation_strength > 0.6:
            key = tuple(sorted([phase_a, phase_b]))
            
            correlation = PhaseCorrelation(
                phase_a=phase_a,
                phase_b=phase_b,
                correlation_type="success_correlation",
                strength=correlation_strength,
                evidence=sequences
            )
            
            self.correlations[key] = correlation
    
    def _pattern_similarity(self, pattern1: Tuple, pattern2: Tuple) -> float:
        """Calculate similarity between two phase patterns"""
        if not pattern1 or not pattern2:
            return 0.0
        
        # Convert to sets for comparison
        set1 = set(pattern1)
        set2 = set(pattern2)
        
        if not set1 or not set2:
            return 0.0
        
        intersection = set1 & set2
        union = set1 | set2
        
        return len(intersection) / len(union)
    
    def _calculate_recent_success_rate(self, phase: str, window: int = 10) -> float:
        """Calculate success rate for recent executions"""
        recent_records = [
            r for r in self.phase_history[-window:]
            if r["phase"] == phase
        ]
        
        if not recent_records:
            return 0.0
        
        successes = sum(1 for r in recent_records if r["success"])
        return successes / len(recent_records)
    
    def _get_common_predecessors(self, phase: str) -> List[Dict]:
        """Get phases that commonly precede this phase"""
        predecessors = []
        
        for i, record in enumerate(self.phase_history):
            if record["phase"] == phase and i > 0:
                prev_phase = self.phase_history[i-1]["phase"]
                predecessors.append(prev_phase)
        
        if not predecessors:
            return []
        
        common = Counter(predecessors).most_common(3)
        return [{"phase": p, "count": c} for p, c in common]
    
    def _get_common_successors(self, phase: str) -> List[Dict]:
        """Get phases that commonly follow this phase"""
        successors = []
        
        for i, record in enumerate(self.phase_history):
            if record["phase"] == phase and i < len(self.phase_history) - 1:
                next_phase = self.phase_history[i+1]["phase"]
                successors.append(next_phase)
        
        if not successors:
            return []
        
        common = Counter(successors).most_common(3)
        return [{"phase": p, "count": c} for p, c in common]
    
    def _generate_rationale(self, phase: str, score: float, 
                          prediction: Dict, dependencies: List[Dict]) -> str:
        """Generate human-readable rationale for phase recommendation"""
        rationale_parts = []
        
        # Success probability
        prob = prediction["success_probability"]
        if prob > 0.8:
            rationale_parts.append(f"High success probability ({prob:.1%})")
        elif prob > 0.6:
            rationale_parts.append(f"Good success probability ({prob:.1%})")
        else:
            rationale_parts.append(f"Moderate success probability ({prob:.1%})")
        
        # Dependencies
        if dependencies:
            met_deps = sum(
                1 for dep in dependencies
                if dep["source"] in [r["phase"] for r in self.phase_history[-5:]]
            )
            if met_deps == len(dependencies):
                rationale_parts.append("all prerequisites met")
            elif met_deps > 0:
                rationale_parts.append(f"{met_deps}/{len(dependencies)} prerequisites met")
        
        # Recent execution
        recent_phases = [r["phase"] for r in self.phase_history[-3:]]
        if phase not in recent_phases:
            rationale_parts.append("not recently executed")
        
        return ", ".join(rationale_parts)
    
    def _load_data(self) -> None:
        """Load correlation data from file"""
        data_file = self.project_dir / ".autonomy" / "correlation_data.json"
        if not data_file.exists():
            return
        
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            # Load phase history
            self.phase_history = data.get("phase_history", [])
            
            # Load transition matrix
            self.transition_matrix = {
                tuple(k.split(":")):  v
                for k, v in data.get("transition_matrix", {}).items()
            }
            
            # Load success/failure patterns
            self.success_patterns = defaultdict(list, {
                k: [tuple(p) for p in v]
                for k, v in data.get("success_patterns", {}).items()
            })
            self.failure_patterns = defaultdict(list, {
                k: [tuple(p) for p in v]
                for k, v in data.get("failure_patterns", {}).items()
            })
            
        except Exception as e:
            print(f"Warning: Could not load correlation data: {e}")
    
    def _save_data(self) -> None:
        """Save correlation data to file"""
        data_dir = self.project_dir / ".autonomy"
        data_dir.mkdir(exist_ok=True)
        data_file = data_dir / "correlation_data.json"
        
        try:
            # Keep only recent history (last 1000 records)
            recent_history = self.phase_history[-1000:]
            
            data = {
                "phase_history": recent_history,
                "transition_matrix": {
                    f"{k[0]}:{k[1]}": v
                    for k, v in self.transition_matrix.items()
                },
                "success_patterns": {
                    k: [list(p) for p in v[-100:]]  # Keep last 100 patterns
                    for k, v in self.success_patterns.items()
                },
                "failure_patterns": {
                    k: [list(p) for p in v[-100:]]  # Keep last 100 patterns
                    for k, v in self.failure_patterns.items()
                }
            }
            
            with open(data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save correlation data: {e}")