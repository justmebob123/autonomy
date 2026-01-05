# HTML Entity Encoding Fix - Implementation Plan

## Critical Fixes (Must Do Now)

### 1. Add Proactive HTML Entity Decoding to File Handlers
- [x] Fixed HTMLEntityDecoder to handle backslash-quote sequences
- [x] Added _aggressive_decode() method for syntax error cases
- [x] Decoder already integrated in syntax_validator (runs before file write)
- [x] Test with actual broken files - ✅ WORKS!

### 2. Fix fix_html_entities Tool Regex Patterns
- [x] Updated _aggressive_decode to handle `&quot;` sequences
- [x] Uses chr(92) + chr(34) for literal backslash-quote matching
- [x] Test pattern matching - ✅ WORKS!

### 3. Add validate_code_entities Tool
- [ ] Create handler method (optional - decoder already works proactively)
- [ ] Add to tool registry (optional)
- [ ] Add to coding/debugging/refactoring phases (optional)

### 4. Testing and Validation
- [x] Created test cases for backslash-quote patterns
- [x] Tested with actual broken file - ✅ COMPILES!
- [x] Verified decoder fixes syntax errors
- [x] Confirmed modified flag works correctly

### 5. Documentation
- [x] Created HTML_ENTITY_COMPREHENSIVE_ANALYSIS.md
- [x] Created HTML_ENTITY_FIX_IMPLEMENTATION.md
- [x] Updated todo.md with completion status
- [x] Commit all changes to git
- [x] Push to GitHub

## ✅ ALL TASKS COMPLETE!

## Additional Work: Context-Aware Decoding

### Issue Raised by User
User correctly pointed out that the aggressive decoder was TOO aggressive and would break:
- Valid escape sequences in strings (e.g., `"He said &quot;Hello&quot;"`)
- HTML entities in string content (e.g., `'<div>&quot;text&quot;</div>'`)
- Raw strings and f-strings with escapes

### Solution: Context-Aware Decoder v2
- [x] Created `html_entity_decoder_v2.py` with conservative approach
- [x] Only fixes patterns that are DEFINITELY syntax errors
- [x] Preserves valid escape sequences in string literals
- [x] Preserves HTML entities in string content
- [x] Decodes entities only in safe contexts (docstrings, comments)
- [x] Created comprehensive test suite (8 tests, all passing)
- [x] Verified integration with SyntaxValidator
- [x] Replaced old decoder with new version

### Test Results
✅ All 8 context-aware tests pass:
1. Syntax error fix (lines starting with &quot;)
2. Preserve string escapes
3. Preserve HTML in strings
4. Decode in comments
5. Decode in docstrings
6. Complex mixed contexts
7. Preserve raw strings
8. Preserve f-strings

### Documentation
- [x] HTML_ENTITY_CONTEXT_AWARE_FIX.md - Analysis of the issue
- [x] test_html_entity_context_aware.py - Comprehensive test suite
- [x] test_context_integration.py - Integration tests

### Ready to Commit
- [ ] Commit context-aware decoder changes
- [ ] Push to GitHub