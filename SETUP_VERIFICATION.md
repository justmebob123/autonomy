# Setup Verification Guide

## Quick Start

Since you're installing the models now, here's what you need to verify once they're ready:

### 1. Verify Models Are Installed

Run this on your system (where you can reach the Ollama servers):

```bash
cd ~/code/AI/test-automation
python autonomy/verify_models.py
```

This will show you:
- ✅ Which required models are installed
- ❌ Which models are missing
- 📊 Complete list of available models on each server

### 2. Required Models

**Critical (Must Have):**
- `qwen2.5-coder:32b` - Best coding/debugging model (32.8B params, ~20GB VRAM)
- `qwen2.5:14b` - Planning and QA (14B params, ~8GB VRAM)

**Recommended:**
- `functiongemma` - Fast routing and tool formatting
- `qwen2.5-coder:7b` - Quick fixes (optional)

### 3. Installation Commands

If any models are missing, install them:

```bash
# On ollama02 (your faster server with 96GB VRAM)
ollama pull qwen2.5-coder:32b  # ~20GB download, best coding model
ollama pull qwen2.5:14b         # ~8GB download
ollama pull functiongemma       # ~2GB download
ollama pull qwen2.5-coder:7b    # ~4GB download (optional)
```

### 4. Test the System

Once models are installed, test with the curses error:

```bash
cd ~/code/AI/test-automation
python run.py --debug --verbose 2
```

**What to look for:**
- ✅ AI makes tool calls (read_file, str_replace, etc.)
- ✅ No "empty response" errors
- ✅ Actual fix attempts on the curses error
- ✅ Detailed logging in `ai_activity.log`

### 5. Monitor Progress

Watch the activity log in real-time:

```bash
tail -f ai_activity.log
```

You should see:
- 🔧 Tool calls being made
- 📝 File operations
- 🔍 Code analysis
- ✏️ Fix attempts

## Configuration Summary

Your system is already configured optimally:

### Model Assignments
```
Planning:   qwen2.5:14b          (ollama02)
Coding:     qwen2.5-coder:32b    (ollama02) ⭐ BEST
QA:         qwen2.5:14b          (ollama02)
Debugging:  qwen2.5-coder:32b    (ollama02) ⭐ BEST
```

### Timeouts (Generous for CPU)
```
Planning:   300s (5 min)
Coding:     600s (10 min)
QA:         300s (5 min)
Debugging:  600s (10 min)
Request:    300s (5 min)
```

### Fallback Models
If primary models fail, system will try:
1. qwen2.5-coder:14b
2. deepseek-coder-v2
3. phi4
4. Other available models

## Why qwen2.5-coder:32b?

This is the **best open-source coding model** available:

- 📊 **73.7 score** on Aider code repair benchmark
- 🏆 **Competitive with GPT-4o** for code tasks
- 🎯 **Excellent at fixing bugs** (our primary use case)
- 🌍 **40+ programming languages** supported
- 💾 **~20GB VRAM** (perfect for your 96GB system)
- 🚀 **32.8B parameters** (sweet spot for quality/speed)

## Troubleshooting

### If AI still doesn't make tool calls:

1. **Check model is actually loaded:**
   ```bash
   curl http://ollama02.thiscluster.net:11434/api/tags
   ```

2. **Check logs for errors:**
   ```bash
   tail -100 ai_activity.log
   ```

3. **Try with investigation phase:**
   ```bash
   python run.py --debug --investigate --verbose 2
   ```

4. **Enable multi-agent consultation:**
   ```bash
   python run.py --debug --consult --verbose 2
   ```

### If timeouts occur:

The 600s (10 min) timeout should be plenty for CPU inference, but if needed:

```python
# In autonomy/pipeline/config.py
debug_timeout: Optional[int] = 900  # 15 minutes
coding_timeout: Optional[int] = 900  # 15 minutes
```

### If model selection fails:

Check the logs for model selection details:
```bash
grep "Model Selection" ai_activity.log
```

## Expected Behavior After Setup

1. **First Iteration:**
   - AI analyzes the curses error
   - Reads relevant files (pipeline_ui.py)
   - Identifies the issue (terminal not in cbreak mode)
   - Proposes a fix

2. **Fix Attempt:**
   - Uses `str_replace` to modify code
   - Adds proper error handling
   - Saves changes

3. **Verification:**
   - Re-runs the test
   - Checks if error is resolved
   - Moves to next issue or completes

## Success Criteria

✅ AI makes tool calls within first iteration
✅ Actual code changes are attempted
✅ Error handling is improved
✅ System doesn't give up after 1-2 tries
✅ Detailed logging shows decision-making process

## Next Steps After Verification

Once the system is working:

1. **Let it run** - The debug mode will continuously monitor and fix issues
2. **Review fixes** - Check the patches in `.pipeline/patches/`
3. **Adjust if needed** - Tweak timeouts or models based on performance
4. **Scale up** - Try with more complex errors

## Support

If you encounter issues:
1. Share the `ai_activity.log` file
2. Include the last 50 lines of terminal output
3. Mention which models are installed
4. Note any timeout or connection errors

---

**Current Status:** ✅ Configuration is optimal, waiting for model installation to complete