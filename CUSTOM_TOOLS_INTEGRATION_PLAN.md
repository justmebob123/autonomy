# Custom Tools Integration Plan

## Overview
Integrate the new custom tools design (scripts/custom_tools/) with the existing pipeline system to enable:
1. Dynamic tool loading from scripts directory
2. Seamless integration with existing tool calling system
3. Live reload capability for tool development
4. Proper tool discovery and registration
5. Security and isolation for custom tools

---

## Current State Analysis

### Existing Custom Tools Infrastructure
**Location**: `autonomy/scripts/custom_tools/`

**Components**:
1. **core/base.py** - BaseTool abstract class ✅
2. **core/executor.py** - ToolExecutor for subprocess execution ✅
3. **core/validator.py** - Tool validation ✅
4. **core/template.py** - Tool templates ✅
5. **tools/** - Directory for custom tool implementations ✅

**Features**:
- Process isolation (tools run in subprocess)
- Timeout enforcement
- Resource limits
- Live reload (no module caching)
- Security sandboxing
- Standard ToolResult format

### Existing Pipeline Integration Points
**Locations**:
1. `pipeline/tools.py` - Tool definitions for LLM
2. `pipeline/handlers.py` - Tool execution handlers
3. `pipeline/tool_analyzer.py` - Tool analysis system
4. `pipeline/coordinator.py` - Pipeline coordination
5. `pipeline/phases/tool_design.py` - Tool design phase

**Current Custom Tool Support**:
- Limited to `pipeline/tools/custom/` directory
- Uses JSON spec files (*_spec.json)
- No subprocess isolation
- No live reload
- Manual registration required

---

## Integration Architecture

### 1. Tool Discovery System
**Purpose**: Automatically discover and register custom tools

**Components**:
```
ToolRegistry (NEW)
├── discover_tools() - Scan scripts/custom_tools/tools/
├── register_tool() - Register tool with metadata
├── get_tool_definition() - Get OpenAI-compatible definition
├── list_tools() - List all available tools
└── reload_tool() - Reload tool for live updates
```

**Integration Points**:
- Called by coordinator on startup
- Called by tool_design phase when new tools created
- Called by handlers when executing custom tools

### 2. Tool Execution System
**Purpose**: Execute custom tools with isolation and safety

**Components**:
```
CustomToolHandler (NEW)
├── execute_custom_tool() - Execute via ToolExecutor
├── validate_tool_call() - Validate parameters
├── handle_tool_result() - Process ToolResult
└── get_tool_timeout() - Get tool-specific timeout
```

**Integration Points**:
- Called by handlers._handle_tool_call()
- Integrated with existing error handling
- Integrated with action tracking

### 3. Tool Definition System
**Purpose**: Generate OpenAI-compatible tool definitions

**Components**:
```
ToolDefinitionGenerator (NEW)
├── generate_definition() - Create tool definition
├── extract_parameters() - Parse tool signature
├── extract_description() - Parse docstrings
└── validate_definition() - Ensure valid format
```

**Integration Points**:
- Called by tools.py to add custom tools
- Called by phases to get available tools
- Called by coordinator for tool selection

### 4. Tool Development System
**Purpose**: Support tool creation and testing

**Components**:
```
ToolDeveloper (NEW)
├── create_from_template() - Create new tool
├── validate_tool() - Check tool validity
├── test_tool() - Run tool tests
└── generate_docs() - Create tool documentation
```

**Integration Points**:
- Called by tool_design phase
- Called by tool_evaluation phase
- Integrated with existing tool analyzer

---

## Implementation Steps

### Phase 1: Core Integration (High Priority)
**Goal**: Basic custom tool execution working

1. **Create ToolRegistry** (2-3 hours)
   - Implement tool discovery
   - Implement tool registration
   - Implement tool definition generation
   - Add caching for performance

2. **Create CustomToolHandler** (2-3 hours)
   - Implement tool execution via ToolExecutor
   - Implement result processing
   - Integrate with existing handlers
   - Add error handling

3. **Integrate with handlers.py** (1-2 hours)
   - Add custom tool detection
   - Route custom tool calls to CustomToolHandler
   - Maintain backward compatibility
   - Add logging

4. **Integrate with tools.py** (1-2 hours)
   - Add custom tool definitions
   - Implement dynamic tool loading
   - Update get_tools_for_phase()
   - Add tool categories

**Estimated Time**: 6-10 hours

### Phase 2: Tool Development Support (Medium Priority)
**Goal**: Enable easy tool creation and testing

1. **Create ToolDeveloper** (2-3 hours)
   - Implement template-based creation
   - Implement validation
   - Implement testing framework
   - Add documentation generation

2. **Integrate with tool_design phase** (1-2 hours)
   - Use ToolDeveloper for tool creation
   - Add custom tool support
   - Update prompts
   - Add validation

3. **Integrate with tool_evaluation phase** (1-2 hours)
   - Add custom tool evaluation
   - Add testing support
   - Update prompts
   - Add metrics

**Estimated Time**: 4-7 hours

### Phase 3: Advanced Features (Low Priority)
**Goal**: Enhanced functionality and developer experience

1. **Tool Hot Reload** (1-2 hours)
   - Implement file watching
   - Implement automatic reload
   - Add reload notifications
   - Add reload testing

2. **Tool Marketplace** (2-3 hours)
   - Implement tool sharing
   - Implement tool discovery
   - Add tool ratings
   - Add tool documentation

3. **Tool Analytics** (1-2 hours)
   - Track tool usage
   - Track tool performance
   - Track tool errors
   - Generate reports

**Estimated Time**: 4-7 hours

---

## File Changes Required

### New Files
1. `pipeline/custom_tools/registry.py` - ToolRegistry
2. `pipeline/custom_tools/handler.py` - CustomToolHandler
3. `pipeline/custom_tools/definition.py` - ToolDefinitionGenerator
4. `pipeline/custom_tools/developer.py` - ToolDeveloper
5. `pipeline/custom_tools/__init__.py` - Package init

### Modified Files
1. `pipeline/handlers.py` - Add custom tool routing
2. `pipeline/tools.py` - Add custom tool definitions
3. `pipeline/coordinator.py` - Add tool registry initialization
4. `pipeline/phases/tool_design.py` - Use ToolDeveloper
5. `pipeline/phases/tool_evaluation.py` - Add custom tool evaluation
6. `pipeline/tool_analyzer.py` - Update for new tool location

---

## Migration Strategy

### Backward Compatibility
**Goal**: Maintain existing functionality while adding new features

1. **Keep existing custom tool support** (pipeline/tools/custom/)
2. **Add new custom tool support** (scripts/custom_tools/)
3. **Gradually migrate** existing custom tools
4. **Deprecate old system** after migration complete

### Migration Steps
1. Implement new system alongside old system
2. Add migration tool to convert old tools to new format
3. Update documentation
4. Migrate existing tools
5. Deprecate old system (after 1-2 releases)

---

## Testing Strategy

### Unit Tests
1. Test ToolRegistry discovery and registration
2. Test CustomToolHandler execution
3. Test ToolDefinitionGenerator
4. Test ToolDeveloper creation and validation

### Integration Tests
1. Test end-to-end tool execution
2. Test tool creation and evaluation phases
3. Test error handling and timeouts
4. Test live reload

### Performance Tests
1. Test tool discovery performance
2. Test tool execution overhead
3. Test subprocess isolation overhead
4. Test caching effectiveness

---

## Security Considerations

### Isolation
- ✅ Tools run in subprocess (already implemented)
- ✅ Timeout enforcement (already implemented)
- ✅ Resource limits (already implemented)

### Validation
- ✅ Tool signature validation (already implemented)
- ✅ Parameter validation (already implemented)
- ⚠️ Add code scanning for malicious patterns
- ⚠️ Add sandboxing for filesystem access

### Permissions
- ⚠️ Add permission system for tools
- ⚠️ Add user confirmation for dangerous operations
- ⚠️ Add audit logging for tool execution

---

## Documentation Requirements

### Developer Documentation
1. **Tool Development Guide**
   - How to create custom tools
   - BaseTool API reference
   - Best practices
   - Examples

2. **Tool Integration Guide**
   - How to integrate tools with pipeline
   - Tool definition format
   - Error handling
   - Testing

3. **Tool Security Guide**
   - Security best practices
   - Permission system
   - Sandboxing
   - Audit logging

### User Documentation
1. **Custom Tools Overview**
   - What are custom tools
   - When to use them
   - How to install them
   - How to use them

2. **Tool Marketplace Guide**
   - How to find tools
   - How to install tools
   - How to rate tools
   - How to share tools

---

## Success Metrics

### Functionality
- ✅ Custom tools can be created and executed
- ✅ Tools are automatically discovered and registered
- ✅ Tools run in isolated subprocess
- ✅ Tools have proper timeout enforcement
- ✅ Tool results are properly formatted

### Performance
- ✅ Tool discovery < 100ms
- ✅ Tool execution overhead < 50ms
- ✅ Tool reload < 10ms
- ✅ Subprocess startup < 100ms

### Developer Experience
- ✅ Tool creation < 5 minutes
- ✅ Tool testing < 1 minute
- ✅ Tool documentation auto-generated
- ✅ Clear error messages

### Security
- ✅ Tools cannot crash pipeline
- ✅ Tools cannot access unauthorized resources
- ✅ Tools have proper timeout enforcement
- ✅ Tool execution is audited

---

## Timeline

### Week 1: Core Integration
- Day 1-2: ToolRegistry implementation
- Day 3-4: CustomToolHandler implementation
- Day 5: Integration with handlers.py and tools.py

### Week 2: Tool Development Support
- Day 1-2: ToolDeveloper implementation
- Day 3-4: Integration with tool phases
- Day 5: Testing and documentation

### Week 3: Advanced Features (Optional)
- Day 1-2: Hot reload implementation
- Day 3-4: Tool marketplace
- Day 5: Analytics and reporting

**Total Estimated Time**: 2-3 weeks

---

## Next Steps

1. ✅ Review and approve integration plan
2. Create feature branch for integration
3. Implement Phase 1 (Core Integration)
4. Test and validate Phase 1
5. Implement Phase 2 (Tool Development Support)
6. Test and validate Phase 2
7. Create pull request
8. Review and merge
9. Update documentation
10. Announce new feature

---

**Plan Created**: December 28, 2024
**Status**: Ready for Implementation
**Priority**: HIGH