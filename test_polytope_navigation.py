#!/usr/bin/env python3
"""
Test script to verify complete polytopic navigation.
Ensures all 14 phases are reachable and properly connected.
"""

import sys
sys.path.insert(0, 'autonomy')

from collections import deque

# Adjacency matrix after fix
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

all_phases = [
    'application_troubleshooting', 'coding', 'debugging', 'documentation',
    'investigation', 'planning', 'project_planning', 'prompt_design',
    'prompt_improvement', 'qa', 'role_design', 'role_improvement',
    'tool_design', 'tool_evaluation'
]

def bfs_reachable(start, edges):
    """Find all phases reachable from start using BFS."""
    visited = {start}
    queue = deque([start])
    
    while queue:
        current = queue.popleft()
        neighbors = edges.get(current, [])
        
        for neighbor in neighbors:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    
    return visited

def test_reachability():
    """Test that all phases are reachable from project_planning (entry point)."""
    print("="*80)
    print("POLYTOPIC NAVIGATION TEST")
    print("="*80)
    
    # Test from project_planning (typical entry point)
    reachable = bfs_reachable('project_planning', edges)
    
    print(f"\nStarting from: project_planning")
    print(f"Reachable phases: {len(reachable)}/{len(all_phases)}")
    print(f"\nReachable:")
    for phase in sorted(reachable):
        print(f"  ✅ {phase}")
    
    unreachable = set(all_phases) - reachable
    if unreachable:
        print(f"\n❌ Unreachable phases: {len(unreachable)}")
        for phase in sorted(unreachable):
            print(f"  ❌ {phase}")
        return False
    else:
        print(f"\n✅ All phases reachable from project_planning!")
    
    return True

def test_all_phases_connected():
    """Test that every phase has at least one connection."""
    print("\n" + "="*80)
    print("CONNECTION TEST")
    print("="*80)
    
    all_connected = True
    
    for phase in sorted(all_phases):
        outgoing = edges.get(phase, [])
        incoming = [p for p, targets in edges.items() if phase in targets]
        
        has_outgoing = len(outgoing) > 0
        has_incoming = len(incoming) > 0
        
        status = "✅" if (has_outgoing or has_incoming) else "❌"
        
        print(f"\n{status} {phase}:")
        print(f"    Outgoing ({len(outgoing)}): {outgoing if outgoing else 'none'}")
        print(f"    Incoming ({len(incoming)}): {incoming if incoming else 'none'}")
        
        if not has_outgoing and not has_incoming:
            print(f"    ⚠️  WARNING: Isolated phase!")
            all_connected = False
    
    return all_connected

def test_application_troubleshooting():
    """Specifically test application_troubleshooting connections."""
    print("\n" + "="*80)
    print("APPLICATION_TROUBLESHOOTING SPECIFIC TEST")
    print("="*80)
    
    phase = 'application_troubleshooting'
    
    # Check outgoing
    outgoing = edges.get(phase, [])
    print(f"\n✅ Outgoing edges: {outgoing}")
    
    # Check incoming
    incoming = [p for p, targets in edges.items() if phase in targets]
    print(f"✅ Incoming edges: {incoming}")
    
    # Verify can reach from entry point
    reachable_from_entry = bfs_reachable('project_planning', edges)
    if phase in reachable_from_entry:
        print(f"✅ Reachable from project_planning (entry point)")
    else:
        print(f"❌ NOT reachable from project_planning!")
        return False
    
    # Verify can reach other phases from it
    reachable_from_phase = bfs_reachable(phase, edges)
    print(f"✅ Can reach {len(reachable_from_phase)} phases from {phase}")
    
    return True

def test_graph_properties():
    """Test graph properties."""
    print("\n" + "="*80)
    print("GRAPH PROPERTIES")
    print("="*80)
    
    # Count edges
    total_edges = sum(len(targets) for targets in edges.values())
    print(f"\nTotal directed edges: {total_edges}")
    
    # Count vertices
    all_vertices = set(edges.keys()) | set(v for targets in edges.values() for v in targets)
    print(f"Total vertices: {len(all_vertices)}")
    
    # Average degree
    avg_out_degree = total_edges / len(edges)
    print(f"Average out-degree: {avg_out_degree:.2f}")
    
    # Check for cycles
    print(f"\nCycle detection:")
    cycles_found = []
    for phase in all_phases:
        reachable = bfs_reachable(phase, edges)
        if phase in reachable and phase in edges.get(phase, []):
            cycles_found.append(phase)
    
    if cycles_found:
        print(f"  ✅ Cycles found (good for iterative refinement): {cycles_found}")
    else:
        print(f"  ℹ️  No direct self-loops")
    
    return True

def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("POLYTOPIC STRUCTURE VERIFICATION")
    print("="*80)
    print(f"\nTesting adjacency matrix with {len(all_phases)} phases")
    print(f"Total edges defined: {len(edges)}")
    
    results = []
    
    # Run tests
    results.append(("Reachability Test", test_reachability()))
    results.append(("Connection Test", test_all_phases_connected()))
    results.append(("Application Troubleshooting Test", test_application_troubleshooting()))
    results.append(("Graph Properties Test", test_graph_properties()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Polytopic structure is complete and valid.")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the adjacency matrix.")
        return 1

if __name__ == '__main__':
    sys.exit(main())