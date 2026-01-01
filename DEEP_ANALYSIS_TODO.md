# Deep Analysis - Root Cause Investigation

## Current Symptoms

1. **Task refactor_0272**: "Merge duplicates: resource_estimator.py ↔ resource_estimator.py"
   - AI compares files (0% similar)
   - Task fails: "only analysis performed, no action taken"
   - Next iteration: AI does the SAME thing again
   - Eventually succeeds on 2nd try with merge

2. **Pattern**: AI keeps using analysis tools instead of resolving tools

## Questions to Answer

1. Why does the task title say "resource_estimator.py ↔ resource_estimator.py" (same file twice)?
2. Why does AI compare first instead of merging directly?
3. What's in the task's analysis_data that confuses the AI?
4. What does the prompt actually tell the AI to do?
5. Why does it work on the 2nd try but not the 1st?

## Investigation Plan

- [ ] Examine task creation for duplicates - what data is passed?
- [ ] Check the formatted analysis_data - what does AI actually see?
- [ ] Review the refactoring phase prompt - what instructions does AI get?
- [ ] Check the tool descriptions - are they clear about when to use each?
- [ ] Analyze the conversation history - what context does AI have?
- [ ] Look at the task completion logic - why does it fail after compare?

## Root Causes to Find

1. **Task data quality** - Is the task created with correct file pairs?
2. **Prompt clarity** - Does the prompt clearly say "merge immediately"?
3. **Tool descriptions** - Do tools clearly explain their purpose?
4. **Context building** - Does AI get enough info to make the right decision?
5. **Completion logic** - Is the failure detection too aggressive?