"""
Advanced Polytopic Visualizations

Provides 3D visualizations, trajectory plots, health heatmaps,
and cluster visualizations for the 7D polytopic space.
"""

from typing import List, Dict, Any, Optional, Tuple
import math
from datetime import datetime


class PolytopicVisualizer:
    """Advanced visualizations for polytopic objectives."""
    
    def __init__(self, dimensional_space):
        """
        Initialize visualizer.
        
        Args:
            dimensional_space: DimensionalSpace instance
        """
        self.space = dimensional_space
    
    def visualize_3d_space(self, dimensions: Tuple[str, str, str] = ("temporal", "functional", "data")) -> str:
        """
        Create 3D ASCII visualization of objectives in selected dimensions.
        
        Args:
            dimensions: Tuple of 3 dimension names to visualize
            
        Returns:
            ASCII art 3D visualization
        """
        if not self.space.objectives:
            return "No objectives in space"
        
        # Get dimension indices
        dim_names = ["temporal", "functional", "data", "state", "error", "context", "integration"]
        try:
            idx_x = dim_names.index(dimensions[0])
            idx_y = dim_names.index(dimensions[1])
            idx_z = dim_names.index(dimensions[2])
        except ValueError:
            return "Invalid dimension names"
        
        # Extract 3D coordinates
        points = []
        for obj in self.space.objectives.values():
            vec = obj.get_dimensional_vector()
            x, y, z = vec[idx_x], vec[idx_y], vec[idx_z]
            points.append((x, y, z, obj.id[:8], obj.level.value if hasattr(obj.level, 'value') else str(obj.level)))
        
        # Create 3D grid (20x20x20)
        size = 20
        grid = [[[' ' for _ in range(size)] for _ in range(size)] for _ in range(size)]
        
        # Plot points
        for x, y, z, obj_id, level in points:
            gx = int(x * (size - 1))
            gy = int(y * (size - 1))
            gz = int(z * (size - 1))
            
            if 0 <= gx < size and 0 <= gy < size and 0 <= gz < size:
                # Use different symbols for different levels
                symbol = 'P' if 'primary' in level.lower() else 'S' if 'secondary' in level.lower() else 'T'
                grid[gz][gy][gx] = symbol
        
        # Render 3D view (isometric projection)
        lines = [f"3D Polytopic Space ({dimensions[0]} × {dimensions[1]} × {dimensions[2]})", ""]
        
        # Draw multiple z-slices
        for z in range(0, size, 5):
            lines.append(f"\nZ-slice {z}/{size-1}:")
            lines.append("  " + "─" * size)
            
            for y in range(size):
                row = "│ "
                for x in range(size):
                    row += grid[z][y][x]
                row += " │"
                lines.append(row)
            
            lines.append("  " + "─" * size)
        
        lines.append(f"\nLegend: P=PRIMARY, S=SECONDARY, T=TERTIARY")
        lines.append(f"Axes: X={dimensions[0]}, Y={dimensions[1]}, Z={dimensions[2]}")
        
        return "\n".join(lines)
    
    def visualize_trajectory(self, objective_id: str, time_steps: int = 5) -> str:
        """
        Visualize trajectory of an objective over time.
        
        Args:
            objective_id: Objective ID
            time_steps: Number of future time steps
            
        Returns:
            ASCII trajectory visualization
        """
        if objective_id not in self.space.objectives:
            return f"Objective {objective_id} not found"
        
        objective = self.space.objectives[objective_id]
        trajectory = self.space.calculate_trajectory(objective, time_steps)
        
        lines = [f"Trajectory for {objective.title}", ""]
        
        # Show current position
        lines.append("Current Position (7D):")
        current = trajectory[0]
        dim_names = ["temporal", "functional", "data", "state", "error", "context", "integration"]
        for i, dim in enumerate(dim_names):
            bar = "█" * int(current[i] * 20)
            lines.append(f"  {dim:12s} │{bar:<20s}│ {current[i]:.2f}")
        
        # Show predicted positions
        lines.append(f"\nPredicted Trajectory ({time_steps} steps):")
        for t in range(1, len(trajectory)):
            lines.append(f"\nStep {t}:")
            pos = trajectory[t]
            for i, dim in enumerate(dim_names):
                delta = pos[i] - trajectory[t-1][i]
                arrow = "↑" if delta > 0.01 else "↓" if delta < -0.01 else "→"
                bar = "█" * int(pos[i] * 20)
                lines.append(f"  {dim:12s} │{bar:<20s}│ {pos[i]:.2f} {arrow}")
        
        # Show velocity
        lines.append("\nDimensional Velocity:")
        for dim, vel in objective.dimensional_velocity.items():
            direction = "increasing" if vel > 0.05 else "decreasing" if vel < -0.05 else "stable"
            lines.append(f"  {dim:12s}: {vel:+.3f} ({direction})")
        
        return "\n".join(lines)
    
    def visualize_health_heatmap(self) -> str:
        """
        Create health heatmap for all objectives.
        
        Returns:
            ASCII heatmap visualization
        """
        if not self.space.objectives:
            return "No objectives in space"
        
        lines = ["Health Heatmap (All Objectives)", ""]
        
        # Header
        dim_names = ["Temp", "Func", "Data", "Stat", "Erro", "Cont", "Intg"]
        header = "Objective        │ " + " │ ".join(dim_names) + " │ Health"
        lines.append(header)
        lines.append("─" * len(header))
        
        # Sort by health (complexity + risk)
        objectives = sorted(
            self.space.objectives.values(),
            key=lambda o: (o.complexity_score + o.risk_score) / 2,
            reverse=True
        )
        
        for obj in objectives[:15]:  # Show top 15
            vec = obj.get_dimensional_vector()
            
            # Create heatmap cells
            cells = []
            for val in vec:
                if val > 0.7:
                    cells.append("██")  # High
                elif val > 0.4:
                    cells.append("▓▓")  # Medium
                else:
                    cells.append("░░")  # Low
            
            # Overall health indicator
            health_score = (obj.complexity_score + obj.risk_score) / 2
            if health_score > 0.7:
                health = "🔴"
            elif health_score > 0.5:
                health = "🟡"
            else:
                health = "🟢"
            
            row = f"{obj.id[:16]:16s} │ " + " │ ".join(cells) + f" │ {health}"
            lines.append(row)
        
        lines.append("\nLegend: ██=High(>0.7) ▓▓=Med(0.4-0.7) ░░=Low(<0.4)")
        lines.append("Health: 🔴=Critical 🟡=Warning 🟢=Good")
        
        return "\n".join(lines)
    
    def visualize_clusters(self, max_distance: float = 0.4) -> str:
        """
        Visualize objective clusters.
        
        Args:
            max_distance: Maximum distance for clustering
            
        Returns:
            ASCII cluster visualization
        """
        clusters = self.space.cluster_objectives(max_distance)
        
        if not clusters:
            return "No clusters found"
        
        lines = [f"Objective Clusters (max_distance={max_distance})", ""]
        
        for cluster_id, members in clusters.items():
            lines.append(f"\n{cluster_id.upper()} ({len(members)} objectives):")
            
            # Calculate cluster centroid
            centroid = self.space.calculate_centroid(members)
            
            # Show centroid
            lines.append("  Centroid:")
            dim_names = ["temporal", "functional", "data", "state", "error", "context", "integration"]
            for i, dim in enumerate(dim_names):
                bar = "█" * int(centroid[i] * 15)
                lines.append(f"    {dim:12s} │{bar:<15s}│ {centroid[i]:.2f}")
            
            # Show members
            lines.append("  Members:")
            for member_id in members[:5]:  # Show first 5
                if member_id in self.space.objectives:
                    obj = self.space.objectives[member_id]
                    level = obj.level.value if hasattr(obj.level, 'value') else str(obj.level)
                    lines.append(f"    • {obj.id[:20]:20s} ({level})")
            
            if len(members) > 5:
                lines.append(f"    ... and {len(members) - 5} more")
        
        return "\n".join(lines)
    
    def visualize_dimensional_distribution(self) -> str:
        """
        Visualize distribution of values across all dimensions.
        
        Returns:
            ASCII distribution visualization
        """
        if not self.space.objectives:
            return "No objectives in space"
        
        stats = self.space.calculate_dimensional_statistics()
        
        lines = ["Dimensional Distribution", ""]
        
        dim_names = ["temporal", "functional", "data", "state", "error", "context", "integration"]
        
        for dim in dim_names:
            if dim not in stats:
                continue
            
            dim_stats = stats[dim]
            mean = dim_stats['mean']
            std = dim_stats['std']
            min_val = dim_stats['min']
            max_val = dim_stats['max']
            
            lines.append(f"\n{dim.upper()}:")
            
            # Distribution bar
            bar_length = 40
            mean_pos = int(mean * bar_length)
            std_left = max(0, int((mean - std) * bar_length))
            std_right = min(bar_length, int((mean + std) * bar_length))
            
            bar = [' '] * bar_length
            bar[mean_pos] = '█'
            for i in range(std_left, std_right):
                if bar[i] == ' ':
                    bar[i] = '░'
            
            lines.append(f"  0.0 │{''.join(bar)}│ 1.0")
            lines.append(f"      │{' ' * mean_pos}↑ mean={mean:.2f}")
            lines.append(f"  Stats: min={min_val:.2f}, max={max_val:.2f}, std={std:.2f}")
        
        return "\n".join(lines)
    
    def visualize_adjacency_graph(self, max_objectives: int = 10) -> str:
        """
        Visualize adjacency relationships between objectives.
        
        Args:
            max_objectives: Maximum number of objectives to show
            
        Returns:
            ASCII adjacency graph
        """
        if not self.space.objectives:
            return "No objectives in space"
        
        lines = ["Adjacency Graph", ""]
        
        # Get objectives with most adjacencies
        obj_list = sorted(
            self.space.objectives.values(),
            key=lambda o: len(o.adjacent_objectives),
            reverse=True
        )[:max_objectives]
        
        for obj in obj_list:
            adj_count = len(obj.adjacent_objectives)
            lines.append(f"\n{obj.id[:20]:20s} ({adj_count} adjacent)")
            
            if adj_count > 0:
                for adj_id in obj.adjacent_objectives[:5]:  # Show first 5
                    if adj_id in self.space.objectives:
                        adj_obj = self.space.objectives[adj_id]
                        distance = obj.calculate_distance_to(adj_obj)
                        similarity = obj.calculate_similarity(adj_obj)
                        
                        # Visual connection
                        connection = "═══" if similarity > 0.8 else "───" if similarity > 0.6 else "···"
                        lines.append(f"  {connection}> {adj_obj.id[:20]:20s} (sim={similarity:.2f}, dist={distance:.2f})")
                
                if adj_count > 5:
                    lines.append(f"  ... and {adj_count - 5} more")
        
        return "\n".join(lines)
    
    def generate_comprehensive_report(self) -> str:
        """
        Generate comprehensive visualization report.
        
        Returns:
            Complete visualization report
        """
        lines = ["=" * 80, "COMPREHENSIVE POLYTOPIC VISUALIZATION REPORT", "=" * 80]
        
        # 1. Space summary
        summary = self.space.get_space_summary()
        lines.append(f"\n1. SPACE SUMMARY")
        lines.append(f"   Total Objectives: {summary['total_objectives']}")
        lines.append(f"   Dimensions: {summary['dimensions']}")
        lines.append(f"   Clusters: {summary.get('clusters', 0)}")
        
        # 2. 3D visualization
        lines.append(f"\n2. 3D SPACE VISUALIZATION")
        lines.append(self.visualize_3d_space())
        
        # 3. Health heatmap
        lines.append(f"\n3. HEALTH HEATMAP")
        lines.append(self.visualize_health_heatmap())
        
        # 4. Clusters
        lines.append(f"\n4. CLUSTERS")
        lines.append(self.visualize_clusters())
        
        # 5. Dimensional distribution
        lines.append(f"\n5. DIMENSIONAL DISTRIBUTION")
        lines.append(self.visualize_dimensional_distribution())
        
        # 6. Adjacency graph
        lines.append(f"\n6. ADJACENCY GRAPH")
        lines.append(self.visualize_adjacency_graph())
        
        lines.append("\n" + "=" * 80)
        
        return "\n".join(lines)


def create_visualizer(dimensional_space):
    """
    Factory function to create visualizer.
    
    Args:
        dimensional_space: DimensionalSpace instance
        
    Returns:
        PolytopicVisualizer instance
    """
    return PolytopicVisualizer(dimensional_space)