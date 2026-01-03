from pathlib import Path
import re

# Analyze prompt structure and similarities
prompts_file = Path("pipeline/prompts.py")

with open(prompts_file, 'r') as f:
    content = f.read()

# Extract all system prompts
system_prompts = re.findall(r"'([a-z_]+)':\s*f?'''(.*?)'''", content, re.DOTALL)

print("="*70)
print("📝 SYSTEM PROMPT ANALYSIS")
print("="*70)

prompt_features = {}
for phase, prompt in system_prompts:
    # Analyze prompt structure
    has_mission = bool(re.search(r'PRIMARY MISSION|YOUR MISSION|GOAL', prompt, re.IGNORECASE))
    has_workflow = bool(re.search(r'WORKFLOW|PROCESS|STEPS', prompt, re.IGNORECASE))
    has_tools = bool(re.search(r'TOOLS|AVAILABLE TOOLS', prompt, re.IGNORECASE))
    has_warnings = bool(re.search(r'WARNING|CRITICAL|IMPORTANT|DO NOT', prompt, re.IGNORECASE))
    has_examples = bool(re.search(r'EXAMPLE|FOR EXAMPLE', prompt, re.IGNORECASE))
    
    lines = len(prompt.split('\n'))
    
    prompt_features[phase] = {
        'lines': lines,
        'mission': has_mission,
        'workflow': has_workflow,
        'tools': has_tools,
        'warnings': has_warnings,
        'examples': has_examples
    }

print(f"\n{'Phase':<20} {'Lines':<7} {'Mission':<8} {'Workflow':<9} {'Tools':<6} {'Warnings':<9} {'Examples':<9}")
print("-"*70)

for phase, features in sorted(prompt_features.items()):
    mission = "✅" if features['mission'] else "❌"
    workflow = "✅" if features['workflow'] else "❌"
    tools = "✅" if features['tools'] else "❌"
    warnings = "✅" if features['warnings'] else "❌"
    examples = "✅" if features['examples'] else "❌"
    
    print(f"{phase:<20} {features['lines']:<7} {mission:<8} {workflow:<9} {tools:<6} {warnings:<9} {examples:<9}")

# Summary
total = len(prompt_features)
mission_count = sum(1 for p in prompt_features.values() if p['mission'])
workflow_count = sum(1 for p in prompt_features.values() if p['workflow'])
tools_count = sum(1 for p in prompt_features.values() if p['tools'])
warnings_count = sum(1 for p in prompt_features.values() if p['warnings'])
examples_count = sum(1 for p in prompt_features.values() if p['examples'])

print("\n" + "="*70)
print("📊 PROMPT QUALITY METRICS")
print("="*70)
print(f"Has Clear Mission: {mission_count}/{total} prompts ({mission_count*100//total}%)")
print(f"Has Workflow Guide: {workflow_count}/{total} prompts ({workflow_count*100//total}%)")
print(f"Has Tool Guidance: {tools_count}/{total} prompts ({tools_count*100//total}%)")
print(f"Has Warnings: {warnings_count}/{total} prompts ({warnings_count*100//total}%)")
print(f"Has Examples: {examples_count}/{total} prompts ({examples_count*100//total}%)")