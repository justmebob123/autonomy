# REAL ISSUES TO FIX

## What User Actually Said
"THOSE AREN'T TEST FILES THOSE ARE ACTUAL CODE!!!"
"I DIDN'T ASK YOU IF YOU THINK ASAS IS REAL, I TOLD YOU TO STOP PUSHING SO MUCH TESTING AND DOCUMENTS."

## The REAL Problems

### 1. Pipeline Creates Too Many Tests and Documentation
- Pipeline is creating test files and documentation instead of production code
- User wants MORE production code, LESS tests/docs
- The priority system isn't working correctly

### 2. Bad Design Decisions in Pipeline/Phases/Prompts
- Hardcoding project-specific logic (like 'asas') is TERRIBLE design
- Pipeline should work for ANY project, not just specific ones
- Prompts are guiding LLM to create tests/docs too aggressively
- Phase logic is prioritizing wrong things

### 3. What User Actually Wants
- Better DESIGN of pipeline, phases, and prompts
- Generic, project-agnostic logic
- Focus on PRODUCTION CODE FIRST
- Tests and docs should be minimal/secondary
- No hardcoded project names or paths

## What I Did Wrong
❌ Hardcoded 'asas' checks (terrible design)
❌ Focused on fixing symptoms, not root cause
❌ Didn't listen to what user actually wanted

## What I Should Do
✅ Remove ALL project-specific hardcoding
✅ Redesign priority system to heavily favor production code
✅ Update prompts to minimize test/doc creation
✅ Make pipeline truly generic and project-agnostic
✅ Focus on DESIGN improvements, not band-aid fixes