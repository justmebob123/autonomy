# Intelligent Conflict Resolution - The Real Fix

## The Real Problem

The AI is being **LAZY**:
1. Sees two files with similar names
2. Compares them (0% similarity)
3. Creates a report saying "manual review needed"
4. **NEVER ACTUALLY READS THE FILES OR THINKS ABOUT THEM**

## What Should Happen

When the AI encounters files with similar names but 0% similarity:

### Step 1: READ BOTH FILES
```python
# Don't just compare - actually READ them
file1_content = read_file("tools/web_search_tool.py")
file2_content = read_file("search/web_search_tool.py")
```

### Step 2: UNDERSTAND THEIR PURPOSE
- What does each file do?
- Are they truly different implementations?
- Do they serve different purposes?
- Are they at different abstraction levels?

### Step 3: CHECK ARCHITECTURE
```python
# Read ARCHITECTURE.md to understand the design
architecture = read_file("ARCHITECTURE.md")
# Where should each file be according to the architecture?
# Is this a planned separation or an accidental duplicate?
```

### Step 4: MAKE AN INTELLIGENT DECISION

**Option A: They're Actually Different (Keep Both)**
- Different purposes (e.g., one is a tool wrapper, one is the core implementation)
- Different abstraction levels (e.g., one is high-level, one is low-level)
- **Action**: Update ARCHITECTURE.md to clarify why both exist

**Option B: They're Duplicates (Merge)**
- Same purpose, different locations
- One is better implemented
- **Action**: Merge into the better location, update imports

**Option C: One is Misplaced (Move)**
- One is in the wrong directory according to ARCHITECTURE.md
- **Action**: Move to correct location, update imports

**Option D: Architecture is Unclear (Update Architecture)**
- ARCHITECTURE.md doesn't explain this pattern
- **Action**: Update ARCHITECTURE.md to document the design decision

## Implementation

The AI should follow this workflow:

```python
# 1. Compare (quick check)
comparison = compare_file_implementations(file1, file2)

# 2. If 0% similarity, READ THE FILES
if comparison.similarity < 10:
    content1 = read_file(file1)
    content2 = read_file(file2)
    
    # 3. Check architecture
    architecture = read_file("ARCHITECTURE.md")
    
    # 4. Analyze purpose
    # - What does file1 do?
    # - What does file2 do?
    # - Are they different on purpose?
    # - Where should they be according to architecture?
    
    # 5. Make decision
    if files_serve_different_purposes:
        # Update ARCHITECTURE.md to clarify
        update_architecture(
            section="File Organization",
            content=f"{file1} handles X, {file2} handles Y"
        )
    elif one_is_misplaced:
        # Move to correct location
        move_file(source=misplaced_file, destination=correct_location)
    elif they_are_duplicates:
        # Merge into better location
        merge_file_implementations(...)
    else:
        # Only NOW create a report if truly unclear
        create_issue_report(...)
```

## The Key Insight

**0% similarity doesn't mean "manual review needed"**

It means:
- They might be intentionally different
- They might serve different purposes
- The architecture might explain why both exist
- OR the architecture needs to be updated to explain it

**The AI should THINK, not just REPORT.**

## Required Changes

### 1. Enhanced Prompt
Tell the AI:
- "0% similarity means READ THE FILES and UNDERSTAND them"
- "Check ARCHITECTURE.md to see if this is intentional"
- "Update ARCHITECTURE.md if the design isn't documented"
- "Only create reports if you truly can't decide"

### 2. Multi-Step Workflow
Force the AI to:
1. Compare (quick check)
2. Read files (understand purpose)
3. Check architecture (understand design)
4. Make decision (merge/move/keep/update)
5. Only report if genuinely unclear

### 3. Remove compare_file_implementations from First Step
Don't let AI start with comparison - make it start with READING and UNDERSTANDING.