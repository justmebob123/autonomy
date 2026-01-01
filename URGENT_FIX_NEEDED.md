# URGENT: Stop Removing Unused Code in Early-Stage Project

## The Problem

The refactoring phase is removing files/classes/methods that are detected as "unused":
- Removed `core/git/git_integration.py` (GitIntegration class)
- Removed `api/resources.py` (ResourceEstimator methods)
- About to remove more...

**This is WRONG for an early-stage project!**

## Why This Is Wrong

1. **Early-stage architecture** - Not everything is integrated yet
2. **Planned features** - Unused code may be for future functionality
3. **Architecture alignment** - Files may properly reflect the intended design
4. **Only remove redundant/duplicate** - Not unimplemented features

## What Should Be Removed

✅ **Duplicate files** - Same functionality in multiple places
✅ **Backup files** - `.autonomy/backups/*`
✅ **Truly redundant** - Obsolete code that's been replaced
✅ **Test artifacts** - Temporary test files

## What Should NOT Be Removed

❌ **Unused classes** - May be part of planned architecture
❌ **Unused methods** - May be for future features
❌ **Unintegrated modules** - Just need to be integrated, not removed
❌ **Placeholder implementations** - Part of the design

## The Fix Needed

1. **Update prompts** - Make it clear: only remove duplicates/redundant, not unused
2. **Update task creation** - Don't create "remove unused" tasks for early-stage projects
3. **Add project stage awareness** - Behave differently for early vs mature projects
4. **Require confirmation** - Ask before removing anything that's not clearly redundant

## Immediate Action

STOP the refactoring phase and fix the prompts/logic before more files are removed!