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
- [ ] Commit all changes to git
- [ ] Push to GitHub