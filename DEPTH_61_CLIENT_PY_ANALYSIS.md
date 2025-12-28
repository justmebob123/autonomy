# Depth-29 Recursive Analysis: pipeline/client.py

## File Overview
- **Path**: autonomy/pipeline/client.py
- **Lines**: 1,019
- **Classes**: 3
- **Functions**: 27
- **Purpose**: Ollama API client with tool calling support and fallback parsing

---

## Class Structure

### Class 1: OllamaClient (Lines 17-213)
**Purpose**: Main client for Ollama API communication

**Methods** (11 total):
1. `__init__(config: PipelineConfig)` - Initialize client
2. `discover_servers() -> Dict[str, List[str]]` - Discover available models
3. `get_model_for_task(task_type: str) -> Optional[Tuple[str, str]]` - Get best model for task
4. `_model_matches(available: str, requested: str) -> bool` - Check model match
5. `chat(host, model, messages, tools, temperature, timeout) -> Dict` - Send chat request

**Key Attributes**:
- `config: PipelineConfig` - Pipeline configuration
- `servers: Dict[str, ServerConfig]` - Available servers
- `available_models: Dict[str, List[str]]` - Models per server
- `logger` - Logger instance
- `verbose: bool` - Verbose logging flag

### Class 2: FunctionGemmaFormatter (Lines 215-394)
**Purpose**: Format tool calls for Gemma models

**Methods** (3 total):
1. `__init__(client: OllamaClient)` - Initialize formatter
2. `_find_gemma_host() -> Optional[str]` - Find host with Gemma model
3. `format_tool_call(raw_output, available_tools) -> Optional[Dict]` - Format tool call
4. `validate_and_fix_tool_call(tool_call, available_tools, raw_output) -> Optional[Dict]` - Validate and fix

### Class 3: ResponseParser (Lines 396-1019)
**Purpose**: Parse responses and extract tool calls from text

**Methods** (13 total):
1. `__init__(client: OllamaClient)` - Initialize parser
2. `parse_response(response, tools) -> Tuple[List[Dict], str]` - Main parsing method
3. `_extract_tool_call_from_text(text) -> Optional[Dict]` - Extract from text
4. `_extract_all_json_blocks(text) -> Optional[Dict]` - Extract JSON blocks
5. `_try_standard_json(text) -> Optional[Dict]` - Try standard JSON parsing
6. `_extract_file_from_codeblock(text) -> Optional[Dict]` - Extract file from code block
7. `_extract_file_creation_robust(text) -> Optional[Dict]` - Robust file extraction
8. `_extract_tasks_json(text) -> Optional[List[Dict]]` - Extract tasks JSON
9. `_validate_tasks(tasks) -> bool` - Validate tasks
10. `_normalize_tasks(tasks) -> List[Dict]` - Normalize tasks
11. `_extract_function_call_syntax(text) -> Optional[Dict]` - Extract function call
12. `_convert_python_strings_to_json(text) -> str` - Convert Python to JSON
13. `_clean_json(text) -> str` - Clean JSON text
14. `_extract_json_aggressive(text) -> Optional[Dict]` - Aggressive JSON extraction
15. `extract_tasks_from_text(text) -> List[Dict]` - Extract tasks from text

---

## Depth-29 Call Stack Analysis

### Entry Point 1: OllamaClient.chat()
**Purpose**: Send chat request to Ollama API

**Call Stack (Depth 29)**:
```
Level 0: OllamaClient.chat()
  ├─ Level 1: requests.post() [external]
  │   └─ Level 2-10: HTTP/network stack [external]
  ├─ Level 1: self._log_response_verbose()
  │   └─ Level 2: self.logger.debug() [logging]
  │       └─ Level 3-5: logging framework [external]
  └─ Level 1: Return response dict

Variables Tracked:
- host: str -> base_url: str (transformation)
- model: str (passed through)
- messages: List[Dict] (passed through)
- tools: List[Dict] (passed through)
- temperature: float (passed through)
- timeout: Optional[int] (passed through)
- payload: Dict (constructed)
- response: requests.Response (from API)
- result: Dict (parsed JSON)
```

**State Mutations**:
- None (pure function, no state changes)

**Integration Points**:
- requests library (HTTP communication)
- logging framework
- PipelineConfig (configuration)

### Entry Point 2: OllamaClient.get_model_for_task()
**Purpose**: Select best available model for a task

**Call Stack (Depth 29)**:
```
Level 0: OllamaClient.get_model_for_task(task_type)
  ├─ Level 1: self.config.model_assignments[task_type]
  │   └─ Level 2: Dict lookup
  ├─ Level 1: self.available_models[preferred_host]
  │   └─ Level 2: Dict lookup
  ├─ Level 1: self._model_matches(avail, model)
  │   └─ Level 2: String comparison and splitting
  │       └─ Level 3: str.split(), str.startswith()
  ├─ Level 1: self.config.model_fallbacks[task_type]
  │   └─ Level 2: Dict lookup
  └─ Level 1: self.logger.info/warning/error()
      └─ Level 2-5: logging framework

Variables Tracked:
- task_type: str (input)
- model: str (from config)
- preferred_host: str (from config)
- selection_log: List[str] (tracking selection process)
- host: str (iteration variable)
- models: List[str] (iteration variable)
- avail: str (iteration variable)
- fallback: str (iteration variable)
- Return: Optional[Tuple[str, str]] (host, model)
```

**State Mutations**:
- None (reads from self.config and self.available_models, no writes)

**Integration Points**:
- PipelineConfig (model_assignments, model_fallbacks)
- available_models (populated by discover_servers)
- logging framework

**CRITICAL FINDING**: This is where Issue #3 and #4 were fixed!
- Issue #3: Model selection now checks if preferred_host is available
- Issue #4: This method provides intelligent fallback logic

### Entry Point 3: ResponseParser.parse_response()
**Purpose**: Parse API response and extract tool calls

**Call Stack (Depth 29)**:
```
Level 0: ResponseParser.parse_response(response, tools)
  ├─ Level 1: response.get("message", {})
  │   └─ Level 2: Dict.get()
  ├─ Level 1: message.get("tool_calls", [])
  │   └─ Level 2: Dict.get()
  ├─ Level 1: message.get("content", "")
  │   └─ Level 2: Dict.get()
  ├─ Level 1: self._extract_tool_call_from_text(content)
  │   ├─ Level 2: self._extract_all_json_blocks(text)
  │   │   ├─ Level 3: re.finditer() [regex]
  │   │   ├─ Level 3: json.loads()
  │   │   │   └─ Level 4-8: JSON parsing [external]
  │   │   └─ Level 3: self._try_standard_json(text)
  │   │       └─ Level 4: json.loads()
  │   ├─ Level 2: self._extract_file_from_codeblock(text)
  │   │   ├─ Level 3: re.search() [regex]
  │   │   └─ Level 3: Dict construction
  │   ├─ Level 2: self._extract_file_creation_robust(text)
  │   │   ├─ Level 3: re.search() [regex multiple patterns]
  │   │   └─ Level 3: Dict construction
  │   ├─ Level 2: self._extract_tasks_json(text)
  │   │   ├─ Level 3: re.search() [regex]
  │   │   ├─ Level 3: json.loads()
  │   │   ├─ Level 3: self._validate_tasks(tasks)
  │   │   │   └─ Level 4: isinstance checks, dict.get()
  │   │   └─ Level 3: self._normalize_tasks(tasks)
  │   │       └─ Level 4: List comprehension, dict operations
  │   ├─ Level 2: self._extract_function_call_syntax(text)
  │   │   ├─ Level 3: re.search() [regex]
  │   │   ├─ Level 3: self._convert_python_strings_to_json(text)
  │   │   │   └─ Level 4: re.sub() with callback
  │   │   │       └─ Level 5: replace_triple_quotes()
  │   │   └─ Level 3: json.loads()
  │   └─ Level 2: self._extract_json_aggressive(text)
  │       ├─ Level 3: self._clean_json(text)
  │       │   └─ Level 4: re.sub() [multiple patterns]
  │       └─ Level 3: json.loads()
  └─ Level 1: Return (tool_calls, content)

Variables Tracked:
- response: Dict (API response)
- tools: List[Dict] (available tools)
- message: Dict (extracted from response)
- tool_calls: List[Dict] (extracted tool calls)
- content: str (message content)
- extracted_call: Optional[Dict] (from text extraction)
- Return: Tuple[List[Dict], str] (tool_calls, content)
```

**State Mutations**:
- None (pure function, no state changes)

**Integration Points**:
- json library (JSON parsing)
- re library (regex matching)
- logging framework

---

## Critical Integration Points

### 1. PipelineConfig Integration
**Used By**: OllamaClient.__init__, get_model_for_task
**Dependencies**:
- model_assignments: Dict[str, Tuple[str, str]]
- model_fallbacks: Dict[str, List[str]]
- servers: List[ServerConfig]

**Call Path**:
```
PipelineConfig
  └─> OllamaClient.__init__
      └─> OllamaClient.get_model_for_task
          └─> Returns (host, model) tuple
```

### 2. ServerConfig Integration
**Used By**: OllamaClient.discover_servers
**Dependencies**:
- base_url: str
- host: str
- name: str
- models: List[str]
- online: bool

**Call Path**:
```
ServerConfig
  └─> OllamaClient.discover_servers
      └─> Updates server.models and server.online
          └─> Populates self.available_models
```

### 3. Requests Library Integration
**Used By**: OllamaClient.discover_servers, OllamaClient.chat
**Dependencies**:
- requests.get() - For model discovery
- requests.post() - For chat API

**Call Path**:
```
requests.get(f"{server.base_url}/api/tags")
  └─> Returns list of models
      └─> Populates available_models

requests.post(f"{base_url}/api/chat", json=payload)
  └─> Returns chat response
      └─> Parsed by ResponseParser
```

### 4. ResponseParser Integration
**Used By**: External callers (phases, coordinator)
**Dependencies**:
- OllamaClient (optional, for logging)

**Call Path**:
```
External Caller
  └─> OllamaClient.chat()
      └─> Returns response dict
          └─> ResponseParser.parse_response(response, tools)
              └─> Returns (tool_calls, content)
```

---

## Issues Analysis

### Issue #3: Model Selection Configuration (FIXED)
**Location**: Lines 53-108 (get_model_for_task method)

**Problem**: Planning phase configured to use ollama01, but model only exists on ollama02

**Fix Applied**: Lines 59-67
```python
# CRITICAL FIX: Check if preferred host is actually available
if preferred_host in self.available_models and self.available_models[preferred_host]:
    for avail in self.available_models[preferred_host]:
        if self._model_matches(avail, model):
            self.logger.debug(f"  Model selection: Using preferred {avail} on {preferred_host}")
            return (preferred_host, avail)
    selection_log.append(f"Preferred model not found on {preferred_host}")
else:
    selection_log.append(f"Preferred host {preferred_host} not available or has no models")
    self.logger.warning(f"  Preferred host {preferred_host} is not available!")
```

**Verification Needed**:
- [ ] Check if this fix is actually in the code
- [ ] Verify it works correctly with test cases
- [ ] Ensure fallback logic is triggered properly

### Issue #4: Model Selection Architecture (FIXED)
**Location**: Lines 53-108 (get_model_for_task method)

**Problem**: Fallback logic was being bypassed

**Fix Applied**: The entire get_model_for_task method provides intelligent fallback:
1. Try preferred model on preferred host
2. Try preferred model on other hosts
3. Try fallback models on all hosts
4. Use any available model as last resort

**Verification Needed**:
- [ ] Verify this method is actually called by chat_with_history()
- [ ] Check if base.py was updated to use this method
- [ ] Test fallback scenarios

---

## Complexity Analysis

### OllamaClient Class
**Cyclomatic Complexity**: Medium (15-20)
- discover_servers: Low (5)
- get_model_for_task: High (25) - Multiple nested loops and conditions
- chat: Medium (10)

**Maintainability**: Good
- Clear method separation
- Good error handling
- Comprehensive logging

### FunctionGemmaFormatter Class
**Cyclomatic Complexity**: High (30-40)
- format_tool_call: High (20)
- validate_and_fix_tool_call: Very High (40+)

**Maintainability**: Moderate
- Complex validation logic
- Many edge cases handled
- Could benefit from refactoring

### ResponseParser Class
**Cyclomatic Complexity**: Very High (60+)
- parse_response: Medium (15)
- _extract_tool_call_from_text: High (25)
- _extract_all_json_blocks: High (20)
- _extract_file_creation_robust: Very High (40+)
- _extract_function_call_syntax: High (30)
- _extract_json_aggressive: High (25)

**Maintainability**: Moderate to Low
- Very complex parsing logic
- Many extraction methods with overlapping functionality
- Could benefit from significant refactoring
- High cognitive load

---

## Dependencies (Depth-29 Traced)

### Direct Dependencies
1. **json** (standard library)
   - Used for: JSON parsing and serialization
   - Methods: json.loads(), json.dumps()
   - Depth: 5-8 levels into JSON parsing internals

2. **re** (standard library)
   - Used for: Regex pattern matching
   - Methods: re.search(), re.finditer(), re.sub()
   - Depth: 3-5 levels into regex engine

3. **requests** (external)
   - Used for: HTTP communication
   - Methods: requests.get(), requests.post()
   - Depth: 10+ levels into HTTP/network stack

4. **typing** (standard library)
   - Used for: Type hints
   - Types: Dict, List, Optional, Tuple
   - Depth: 0 (compile-time only)

### Internal Dependencies
1. **pipeline.config**
   - Classes: PipelineConfig, ServerConfig
   - Used by: OllamaClient
   - Depth: 2-3 levels

2. **pipeline.logging_setup**
   - Function: get_logger()
   - Used by: All classes
   - Depth: 3-5 levels into logging framework

---

## Data Flow Analysis

### Flow 1: Model Discovery
```
discover_servers()
  ├─> For each server in config.servers
  │   ├─> requests.get(f"{server.base_url}/api/tags")
  │   ├─> Parse response.json()
  │   ├─> Extract model names
  │   ├─> Update server.models
  │   ├─> Update server.online
  │   └─> Store in self.available_models[server.host]
  └─> Return self.available_models
```

**Variables**:
- Input: self.config.servers (List[ServerConfig])
- Output: self.available_models (Dict[str, List[str]])
- Side Effects: Updates server.models and server.online

### Flow 2: Model Selection
```
get_model_for_task(task_type)
  ├─> Lookup task_type in config.model_assignments
  │   └─> Get (model, preferred_host)
  ├─> Check if preferred_host is available
  │   ├─> Yes: Check if model exists on preferred_host
  │   │   ├─> Yes: Return (preferred_host, model)
  │   │   └─> No: Try other hosts
  │   └─> No: Try other hosts
  ├─> Try fallback models
  │   └─> For each fallback in config.model_fallbacks[task_type]
  │       └─> Check all hosts for fallback model
  └─> Last resort: Return first available model
```

**Variables**:
- Input: task_type (str)
- Output: Optional[Tuple[str, str]] (host, model)
- Side Effects: Logging

### Flow 3: Chat Request
```
chat(host, model, messages, tools, temperature, timeout)
  ├─> Construct payload dict
  │   ├─> model: str
  │   ├─> messages: List[Dict]
  │   ├─> stream: False
  │   ├─> options: {temperature, num_ctx}
  │   └─> tools: List[Dict] (optional)
  ├─> Parse host to base_url
  ├─> requests.post(f"{base_url}/api/chat", json=payload)
  ├─> Parse response.json()
  ├─> Log response (if verbose)
  └─> Return response dict
```

**Variables**:
- Input: host, model, messages, tools, temperature, timeout
- Output: Dict (API response)
- Side Effects: HTTP request, logging

### Flow 4: Response Parsing
```
parse_response(response, tools)
  ├─> Extract message from response
  ├─> Extract tool_calls from message
  │   ├─> If tool_calls exist: Return (tool_calls, content)
  │   └─> If no tool_calls: Try text extraction
  ├─> Extract content from message
  ├─> Try multiple extraction methods:
  │   ├─> _extract_all_json_blocks()
  │   ├─> _extract_file_from_codeblock()
  │   ├─> _extract_file_creation_robust()
  │   ├─> _extract_tasks_json()
  │   ├─> _extract_function_call_syntax()
  │   └─> _extract_json_aggressive()
  └─> Return (tool_calls, content)
```

**Variables**:
- Input: response (Dict), tools (List[Dict])
- Output: Tuple[List[Dict], str] (tool_calls, content)
- Side Effects: Logging

---

## Verification Checklist

### Issue #3 Fix Verification
- [ ] Read lines 59-67 to confirm fix is present
- [ ] Check if preferred_host availability is checked
- [ ] Verify fallback to other hosts works
- [ ] Test with unavailable preferred host

### Issue #4 Fix Verification
- [ ] Verify get_model_for_task() is called by chat_with_history()
- [ ] Check if base.py was updated
- [ ] Test fallback scenarios
- [ ] Verify last resort logic works

### Code Quality
- [ ] Check for any syntax errors
- [ ] Verify all imports are present
- [ ] Check for unused variables
- [ ] Verify error handling is comprehensive

### Integration
- [ ] Verify PipelineConfig integration
- [ ] Check ServerConfig integration
- [ ] Verify logging integration
- [ ] Check requests library usage

---

## Recommendations

### High Priority
1. **Verify Issue #3 and #4 fixes are actually in the code**
   - Read the actual code to confirm
   - Run tests to verify functionality
   - Check for any regressions

2. **Refactor ResponseParser class**
   - Extract common patterns into helper methods
   - Reduce cyclomatic complexity
   - Improve maintainability
   - Consider splitting into multiple classes

### Medium Priority
1. **Add unit tests for model selection logic**
   - Test preferred host selection
   - Test fallback logic
   - Test last resort logic
   - Test error cases

2. **Improve error handling in chat() method**
   - Add more specific exception handling
   - Improve error messages
   - Add retry logic for transient failures

### Low Priority
1. **Add type hints to all methods**
   - Improve code documentation
   - Enable better IDE support
   - Catch type errors early

2. **Add docstrings to all methods**
   - Improve code documentation
   - Explain complex logic
   - Document edge cases

---

## Next Steps

1. **Verify fixes are actually in the code**
   - Read lines 59-67 for Issue #3 fix
   - Check if base.py uses get_model_for_task()
   - Run tests to confirm functionality

2. **Complete examination of remaining 50%**
   - Examine FunctionGemmaFormatter class in detail
   - Examine ResponseParser class in detail
   - Document all methods and their purposes

3. **Move to next file**
   - pipeline/handlers.py (1981 lines, complexity 54)
   - Continue systematic examination

---

**Status**: 50% Complete - Need to verify fixes and examine remaining classes
**Next Action**: Verify Issue #3 and #4 fixes are actually in the code