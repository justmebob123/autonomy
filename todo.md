# Critical Error Fix TODO

## Phase 1: Investigate Tool Schema and Handler ✅
- [x] Examine `create_issue_report` tool definition
- [x] Examine `create_issue_report` handler implementation
- [x] Identify schema mismatch

## Phase 2: Fix Tool Schema Mismatch ✅
- [x] Fix `create_issue_report` tool schema (made impact_analysis optional)
- [x] Fix `create_issue_report` handler (added backward compatibility)
- [x] Make `impact_analysis` optional or provide default
- [x] Add parameter mapping for old names (title, description, files_affected)
- [x] Add example to prompt with exact parameter names
- [ ] Test tool call works

## Phase 3: Fix Response Parsing ✅
- [x] Examined extraction system - comprehensive and working
- [x] Issue is model returning JSON in text instead of native tool calls
- [x] Extraction system successfully extracts from text
- [x] Real issue: AI using wrong parameter names
- [x] Fixed by adding backward compatibility in handler

## Phase 4: Fix Error Handling ✅
- [x] Investigate "unknown" tool error in fallback handler
- [x] Found bug: tool call missing "function" wrapper
- [x] Fixed tool call structure in fallback handler
- [ ] Test error handling paths

## Phase 5: Fix Task Retry Logic
- [ ] Add max retry limit enforcement
- [ ] Mark tasks as permanently failed after max retries
- [ ] Add alternative approach selection on retry
- [ ] Prevent infinite retry loops
- [ ] Test retry logic

## Phase 6: Examine All Related Tools
- [ ] Audit all tool schemas for missing parameters
- [ ] Audit all handlers for parameter mismatches
- [ ] Fix any other schema/handler mismatches found
- [ ] Test all refactoring tools

## Phase 7: Improve Prompts
- [x] Review tool calling instructions in prompts
- [x] Add clear examples of tool call format
- [ ] Add guidance on when to use each tool
- [ ] Test prompts with model

## Phase 8: Test Complete System
- [ ] Run full refactoring phase
- [ ] Verify no more KeyError exceptions
- [ ] Verify tasks complete or fail properly
- [ ] Verify no infinite loops
- [ ] Document all fixes