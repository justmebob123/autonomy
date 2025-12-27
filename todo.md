# REAL INTEGRATION TODO - NO MORE DOCUMENTATION

## CRITICAL: INTEGRATE SPECIALISTS INTO PHASES

### 1. CodingPhase Integration ✅
- [x] Replace `self.chat()` call at line 93 in `pipeline/phases/coding.py`
- [x] Use `self.coding_specialist.execute_task()` instead
- [x] Create CodingTask from task context
- [x] Extract tool_calls from specialist result
- [x] Test coding phase works with specialist

### 2. QAPhase Integration ✅
- [x] Replace `self.chat()` call at line 136 in `pipeline/phases/qa.py`
- [x] Use `self.analysis_specialist.review_code()` instead
- [x] Pass file_path and code content
- [x] Extract tool_calls from specialist result
- [x] Test QA phase works with specialist

### 3. DebuggingPhase Integration ✅
- [x] Replace `self.chat()` call at line 430 in `pipeline/phases/debugging.py`
- [x] Replace `self.chat()` call at line 740
- [x] Replace `self.chat()` call at line 1052
- [x] Replace `self.chat()` call at line 1444
- [x] Use `self.reasoning_specialist.execute_task()` for all
- [x] Create ReasoningTask with error context
- [x] Test debugging phase works with specialist

### 4. Additional Phase Integrations ✅
- [x] PlanningPhase - uses reasoning_specialist
- [x] ProjectPlanningPhase - uses reasoning_specialist
- [x] InvestigationPhase - uses analysis_specialist
- [x] DocumentationPhase - uses analysis_specialist
- [x] PromptDesignPhase - uses reasoning_specialist
- [x] RoleDesignPhase - uses reasoning_specialist
- [x] ToolDesignPhase - uses reasoning_specialist
- [x] PromptImprovementPhase - uses reasoning_specialist
- [x] RoleImprovementPhase - uses reasoning_specialist

### 5. Remove Dead Code ✅
- [x] Delete `BasePhase.chat()` method (lines 410-442 in base.py)
- [x] Delete `BasePhase.get_model_for_task()` method
- [x] Delete `BasePhase._tools_cache` attribute
- [x] Delete temperature/timeout configuration logic
- [x] Clean up unused imports
- [x] Verify no references to deleted code

### 6. Final Verification ⏳
- [ ] Run full pipeline test
- [x] Verify NO direct client.chat() calls in phases
- [x] Verify ALL phases use specialists
- [ ] Verify tool execution still works
- [ ] Verify state management intact
- [ ] Check logs for specialist execution messages

### 7. Commit and Push ⏳
- [ ] Commit all changes
- [ ] Push to GitHub

## INTEGRATION COMPLETE
- ✅ ALL 12 phases now use specialists
- ✅ NO more direct client.chat() calls
- ✅ Dead code removed (~50 lines deleted)
- ✅ All files compile successfully
- ⏳ Ready for testing and commit