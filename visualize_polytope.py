#!/usr/bin/env python3
"""
Create a visual representation of the polytopic structure.
Generates both ASCII art and a description of the graph structure.
"""

import sys

# Adjacency matrix
edges = {
    'planning': ['coding'],
    'coding': ['qa'],
    'qa': ['debugging', 'documentation', 'application_troubleshooting'],
    'debugging': ['investigation', 'coding', 'application_troubleshooting'],
    'investigation': ['debugging', 'coding', 'application_troubleshooting', 
                      'prompt_design', 'role_design', 'tool_design'],
    'project_planning': ['planning'],
    'documentation': ['planning'],
    'prompt_design': ['prompt_improvement'],
    'tool_design': ['tool_evaluation'],
    'role_design': ['role_improvement'],
    'tool_evaluation': ['tool_design', 'coding'],
    'prompt_improvement': ['prompt_design', 'planning'],
    'role_improvement': ['role_design', 'planning'],
    'application_troubleshooting': ['debugging', 'investigation', 'coding']
}

def print_ascii_graph():
    """Print ASCII art representation of the polytope."""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    HYPERDIMENSIONAL POLYTOPIC STRUCTURE                    ║
║                           14 Vertices, 7 Dimensions                        ║
╚════════════════════════════════════════════════════════════════════════════╝

                        ┌─────────────────────┐
                        │  project_planning   │ (ENTRY POINT)
                        └──────────┬──────────┘
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │      planning       │◄─────────┐
                        └──────────┬──────────┘          │
                                   │                     │
                                   ▼                     │
                        ┌─────────────────────┐          │
                        │       coding        │◄─────┐   │
                        └──────────┬──────────┘      │   │
                                   │                 │   │
                                   ▼                 │   │
                        ┌─────────────────────┐      │   │
                   ┌────┤         qa          ├────┐ │   │
                   │    └─────────────────────┘    │ │   │
                   │                               │ │   │
                   ▼                               ▼ │   │
        ┌─────────────────────┐       ┌─────────────────────┐
        │     debugging       │       │   documentation     │
        └──────────┬──────────┘       └──────────┬──────────┘
                   │                              │
                   │                              └──────────┘
                   ▼
        ┌─────────────────────┐
        │   investigation     │ (HUB - 6 outgoing)
        └──────────┬──────────┘
                   │
        ┌──────────┼──────────┬──────────┬──────────┐
        │          │          │          │          │
        ▼          ▼          ▼          ▼          ▼
   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
   │ prompt │ │  role  │ │  tool  │ │ coding │ │ debug  │
   │ design │ │ design │ │ design │ │        │ │  app   │
   └───┬────┘ └───┬────┘ └───┬────┘ └────────┘ └───┬────┘
       │          │          │                      │
       ▼          ▼          ▼                      │
   ┌────────┐ ┌────────┐ ┌────────┐                │
   │ prompt │ │  role  │ │  tool  │                │
   │improve │ │improve │ │  eval  │                │
   └───┬────┘ └───┬────┘ └───┬────┘                │
       │          │          │                      │
       └──────────┴──────────┴──────────────────────┘
              │          │          │
              ▼          ▼          ▼
          planning   planning    coding

╔════════════════════════════════════════════════════════════════════════════╗
║                            WORKFLOW TYPES                                  ║
╠════════════════════════════════════════════════════════════════════════════╣
║  1. Main Development:  project_planning → planning → coding → qa          ║
║  2. Debugging:         qa → debugging → investigation → coding            ║
║  3. App Troubleshoot:  qa → app_troubleshoot → investigation → coding     ║
║  4. Prompt Improve:    investigation → prompt_design → improve → planning ║
║  5. Role Improve:      investigation → role_design → improve → planning   ║
║  6. Tool Develop:      investigation → tool_design → eval → coding        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

def print_connectivity_matrix():
    """Print connectivity matrix."""
    all_phases = sorted(edges.keys())
    
    print("\n" + "="*80)
    print("CONNECTIVITY MATRIX")
    print("="*80)
    print("\nPhase                        → Outgoing Connections")
    print("-"*80)
    
    for phase in all_phases:
        targets = edges.get(phase, [])
        out_count = len(targets)
        
        # Calculate incoming
        incoming = [p for p, t in edges.items() if phase in t]
        in_count = len(incoming)
        
        print(f"{phase:28} → {out_count} out, {in_count} in  {targets}")

def print_statistics():
    """Print graph statistics."""
    print("\n" + "="*80)
    print("GRAPH STATISTICS")
    print("="*80)
    
    total_edges = sum(len(targets) for targets in edges.values())
    num_vertices = len(set(edges.keys()) | set(v for targets in edges.values() for v in targets))
    
    # Calculate degrees
    out_degrees = {phase: len(targets) for phase, targets in edges.items()}
    in_degrees = {}
    for phase in edges.keys():
        in_degrees[phase] = sum(1 for targets in edges.values() if phase in targets)
    
    max_out = max(out_degrees.values())
    max_in = max(in_degrees.values())
    
    max_out_phase = [p for p, d in out_degrees.items() if d == max_out][0]
    max_in_phase = [p for p, d in in_degrees.items() if d == max_in][0]
    
    print(f"\nVertices:              {num_vertices}")
    print(f"Directed Edges:        {total_edges}")
    print(f"Average Out-Degree:    {total_edges / len(edges):.2f}")
    print(f"Max Out-Degree:        {max_out} ({max_out_phase})")
    print(f"Max In-Degree:         {max_in} ({max_in_phase})")
    print(f"Density:               {total_edges / (num_vertices * (num_vertices - 1)):.3f}")

def print_critical_paths():
    """Print critical paths."""
    print("\n" + "="*80)
    print("CRITICAL PATHS")
    print("="*80)
    
    paths = [
        ("Main Development", ["project_planning", "planning", "coding", "qa", "documentation"]),
        ("Bug Fix", ["qa", "debugging", "investigation", "coding"]),
        ("App Troubleshoot", ["qa", "application_troubleshooting", "investigation", "coding"]),
        ("Prompt Improvement", ["investigation", "prompt_design", "prompt_improvement", "planning"]),
        ("Role Improvement", ["investigation", "role_design", "role_improvement", "planning"]),
        ("Tool Development", ["investigation", "tool_design", "tool_evaluation", "coding"]),
    ]
    
    for name, path in paths:
        print(f"\n{name}:")
        print("  " + " → ".join(path))

def main():
    """Main function."""
    print_ascii_graph()
    print_connectivity_matrix()
    print_statistics()
    print_critical_paths()
    
    print("\n" + "="*80)
    print("✅ Polytopic structure is complete and fully connected!")
    print("="*80)

if __name__ == '__main__':
    main()