# System Analyzer - Practical Usage Examples

## Overview

This document provides practical, real-world examples of how to use the system analyzer tools in each phase of the Autonomy pipeline.

---

## Investigation Phase Examples

### Example 1: Root Cause Analysis

**Scenario**: A bug is occurring but the root cause is unclear.

```xml

<!-- Step 1: Analyze system connectivity to understand architecture -->
<analyze_connectivity>
</analyze_connectivity>

<!-- Step 2: Trace the critical variable through the system -->
<trace_variable_flow variable_name="state">
</trace_variable_flow>

<!-- Step 3: Check integration depth of the problematic phase -->
<analyze_integration_depth phase_name="debugging">
</analyze_integration_depth>
</function_calls>
```

**Expected Results**:
- Connectivity analysis shows which phases are connected
- Variable flow shows where 'state' is used (31 functions)
- Integration depth reveals debugging has 164 integration points

**Action**: Focus investigation on high-integration areas where state flows.

---

### Example 2: Performance Investigation

**Scenario**: System is running slowly, need to identify bottlenecks.

```xml

<!-- Find recursive patterns that might cause performance issues -->
<find_recursive_patterns>
</find_recursive_patterns>

<!-- Analyze integration depth of slow phase -->
<analyze_integration_depth phase_name="project_planning">
</analyze_integration_depth>

<!-- Get refactoring suggestions -->
<get_refactoring_suggestions phase_name="project_planning">
</get_refactoring_suggestions>
</function_calls>
```

**Expected Results**:
- Recursive patterns identified (7 functions)
- Integration depth shows complexity level
- Suggestions provide actionable improvements

**Action**: Refactor based on suggestions to improve performance.

---

## Debugging Phase Examples

### Example 1: Infinite Loop Detection

**Scenario**: Program hangs, suspect infinite loop.

```xml

<!-- Find all recursive patterns -->
<find_recursive_patterns>
</find_recursive_patterns>

<!-- Trace the recursion_depth variable -->
<trace_variable_flow variable_name="recursion_depth">
</trace_variable_flow>
</function_calls>
```

**Expected Results**:
- List of functions with direct recursion
- List of functions with circular calls
- Variable flow shows where recursion_depth is tracked

**Action**: Add recursion depth limits to identified functions.

---

### Example 2: Variable State Debugging

**Scenario**: Variable has unexpected value, need to trace its flow.

```xml

<!-- Trace the problematic variable -->
<trace_variable_flow variable_name="filepath">
</trace_variable_flow>

<!-- Check code quality of file where variable is used -->
<assess_code_quality filepath="pipeline/handlers.py">
</assess_code_quality>
</function_calls>
```

**Expected Results**:
- filepath flows through 39 functions (HIGH criticality)
- Code quality score and metrics for handlers.py

**Action**: Review the 39 functions to find where filepath is modified incorrectly.

---

## QA Phase Examples

### Example 1: Code Quality Validation

**Scenario**: New code submitted, need to validate quality.

```xml

<!-- Assess quality of new file -->
<assess_code_quality filepath="pipeline/phases/new_phase.py">
</assess_code_quality>

<!-- Check for recursive patterns -->
<find_recursive_patterns>
</find_recursive_patterns>

<!-- Get refactoring suggestions -->
<get_refactoring_suggestions phase_name="new_phase">
</get_refactoring_suggestions>
</function_calls>
```

**Expected Results**:
- Quality score (0-100)
- Comment ratio, function length metrics
- Recursive patterns detected
- Refactoring suggestions

**Action**: Approve if quality score > 70, otherwise request improvements.

---

### Example 2: Integration Validation

**Scenario**: Validate that new phase integrates properly.

```xml

<!-- Check integration depth -->
<analyze_integration_depth phase_name="new_phase">
</analyze_integration_depth>

<!-- Verify connectivity -->
<analyze_connectivity>
</analyze_connectivity>
</function_calls>
```

**Expected Results**:
- Integration points count
- Complexity level (LOW/MEDIUM/HIGH/VERY HIGH)
- Connectivity status

**Action**: If complexity is VERY HIGH, request refactoring before approval.

---

## Project Planning Phase Examples

### Example 1: Architecture Planning

**Scenario**: Planning system improvements, need current state analysis.

```xml

<!-- Get current connectivity status -->
<analyze_connectivity>
</analyze_connectivity>

<!-- Get refactoring suggestions for each phase -->
<get_refactoring_suggestions phase_name="debugging">
</get_refactoring_suggestions>

<get_refactoring_suggestions phase_name="coding">
</get_refactoring_suggestions>

<get_refactoring_suggestions phase_name="qa">
</get_refactoring_suggestions>
</function_calls>
```

**Expected Results**:
- Current connectivity metrics
- Isolated phases identified
- Refactoring suggestions for each phase

**Action**: Create tasks based on suggestions, prioritize by impact.

---

### Example 2: Refactoring Effort Estimation

**Scenario**: Need to estimate effort for refactoring a phase.

```xml

<!-- Analyze integration depth -->
<analyze_integration_depth phase_name="debugging">
</analyze_integration_depth>

<!-- Assess code quality -->
<assess_code_quality filepath="pipeline/phases/debugging.py">
</assess_code_quality>

<!-- Get suggestions -->
<get_refactoring_suggestions phase_name="debugging">
</get_refactoring_suggestions>
</function_calls>
```

**Expected Results**:
- Integration points: 164 (VERY HIGH)
- Lines: 1517, Functions: 12
- Quality score: 78.2
- Specific refactoring suggestions

**Action**: Estimate 2-3 days for refactoring based on complexity.

---

## Application Troubleshooting Phase Examples

### Example 1: System State Analysis

**Scenario**: Application behaving unexpectedly, need to understand current state.

```xml

<!-- Map system connectivity -->
<analyze_connectivity>
</analyze_connectivity>

<!-- Trace critical variables -->
<trace_variable_flow variable_name="state">
</trace_variable_flow>

<trace_variable_flow variable_name="content">
</trace_variable_flow>

<!-- Find recursive patterns -->
<find_recursive_patterns>
</find_recursive_patterns>
</function_calls>
```

**Expected Results**:
- System connectivity map
- Variable flow for state (31 functions)
- Variable flow for content (33 functions)
- Recursive patterns identified

**Action**: Focus troubleshooting on high-flow variables and recursive patterns.

---

### Example 2: Integration Bottleneck Identification

**Scenario**: System slow, suspect integration bottleneck.

```xml

<!-- Check integration depth of all phases -->
<analyze_integration_depth phase_name="debugging">
</analyze_integration_depth>

<analyze_integration_depth phase_name="project_planning">
</analyze_integration_depth>

<analyze_integration_depth phase_name="coding">
</analyze_integration_depth>
</function_calls>
```

**Expected Results**:
- debugging: 164 points (VERY HIGH)
- project_planning: 52 points (HIGH)
- coding: 15 points (LOW)

**Action**: Focus optimization on debugging phase (highest integration).

---

## Documentation Phase Examples

### Example 1: Documentation Coverage Analysis

**Scenario**: Need to ensure all code is properly documented.

```xml

<!-- Assess code quality (includes comment ratio) -->
<assess_code_quality filepath="pipeline/phases/debugging.py">
</assess_code_quality>

<assess_code_quality filepath="pipeline/handlers.py">
</assess_code_quality>

<assess_code_quality filepath="pipeline/coordinator.py">
</assess_code_quality>
</function_calls>
```

**Expected Results**:
- Comment ratio for each file
- Docstring count
- Quality scores

**Action**: Add documentation to files with comment ratio < 10%.

---

## Coding Phase Examples

### Example 1: Pre-Implementation Analysis

**Scenario**: Before implementing new feature, analyze current architecture.

```xml

<!-- Check connectivity to understand where to integrate -->
<analyze_connectivity>
</analyze_connectivity>

<!-- Check integration depth of target phase -->
<analyze_integration_depth phase_name="coding">
</analyze_integration_depth>

<!-- Get refactoring suggestions -->
<get_refactoring_suggestions phase_name="coding">
</get_refactoring_suggestions>
</function_calls>
```

**Expected Results**:
- Current connectivity status
- Integration complexity of coding phase
- Suggestions for improvement

**Action**: Implement feature following architectural guidelines.

---

## Combined Workflow Examples

### Example 1: Complete System Health Check

**Scenario**: Regular system health check.

```xml

<!-- 1. Check connectivity -->
<analyze_connectivity>
</analyze_connectivity>

<!-- 2. Find recursive patterns -->
<find_recursive_patterns>
</find_recursive_patterns>

<!-- 3. Check integration depth of critical phases -->
<analyze_integration_depth phase_name="debugging">
</analyze_integration_depth>

<analyze_integration_depth phase_name="coding">
</analyze_integration_depth>

<!-- 4. Assess code quality of critical files -->
<assess_code_quality filepath="pipeline/coordinator.py">
</assess_code_quality>

<!-- 5. Get refactoring suggestions -->
<get_refactoring_suggestions phase_name="debugging">
</get_refactoring_suggestions>
</function_calls>
```

**Expected Results**:
- Complete system health report
- Identified issues and bottlenecks
- Actionable improvement suggestions

**Action**: Create maintenance tasks based on findings.

---

### Example 2: Pre-Deployment Validation

**Scenario**: Before deploying changes, validate system integrity.

```xml

<!-- 1. Verify connectivity -->
<analyze_connectivity>
</analyze_connectivity>

<!-- 2. Check for new recursive patterns -->
<find_recursive_patterns>
</find_recursive_patterns>

<!-- 3. Assess quality of changed files -->
<assess_code_quality filepath="pipeline/phases/new_feature.py">
</assess_code_quality>

<!-- 4. Verify integration depth is acceptable -->
<analyze_integration_depth phase_name="new_feature">
</analyze_integration_depth>
</function_calls>
```

**Expected Results**:
- Connectivity maintained or improved
- No new problematic recursive patterns
- Quality score > 70
- Integration complexity acceptable

**Action**: Deploy if all checks pass, otherwise fix issues first.

---

## Best Practices

### When to Use Each Tool

1. **`analyze_connectivity`**
   - Start of investigation
   - Architecture planning
   - System health checks
   - After major changes

2. **`analyze_integration_depth`**
   - Before refactoring
   - Performance optimization
   - Complexity assessment
   - Integration validation

3. **`trace_variable_flow`**
   - Debugging variable issues
   - Understanding data flow
   - State management analysis
   - Impact analysis

4. **`find_recursive_patterns`**
   - Infinite loop debugging
   - Performance issues
   - Stack overflow investigation
   - Architecture validation

5. **`assess_code_quality`**
   - Code review
   - Pre-deployment validation
   - Quality assurance
   - Technical debt assessment

6. **`get_refactoring_suggestions`**
   - Planning improvements
   - Architecture optimization
   - Maintenance planning
   - Technical debt reduction

### Tool Combination Strategies

**For Investigation**:
1. Start with `analyze_connectivity`
2. Use `trace_variable_flow` for specific issues
3. Check `analyze_integration_depth` for complexity

**For Quality Assurance**:
1. Start with `assess_code_quality`
2. Check `find_recursive_patterns`
3. Get `get_refactoring_suggestions`

**For Planning**:
1. Start with `analyze_connectivity`
2. Get `get_refactoring_suggestions` for each phase
3. Use `analyze_integration_depth` to estimate effort

---

## Performance Tips

1. **Use Caching**: Results are cached, so repeated calls are fast
2. **Batch Analysis**: Analyze multiple phases in one session
3. **Targeted Analysis**: Only analyze what you need
4. **Regular Checks**: Run health checks regularly to catch issues early

---

## Troubleshooting

### Tool Returns Error

**Problem**: Tool call returns error message

**Solution**:
- Check parameter names are correct
- Verify phase/file exists
- Check file path is relative to project root

### Results Seem Outdated

**Problem**: Analysis results don't reflect recent changes

**Solution**:
- Restart the system to clear cache
- Make sure changes are saved to disk
- Verify you're analyzing the correct file/phase

### High Integration Depth

**Problem**: Phase has VERY HIGH integration depth

**Solution**:
- Use `get_refactoring_suggestions` for guidance
- Consider creating facade modules
- Break down into smaller components

---

**Repository**: https://github.com/justmebob123/autonomy  
**Branch**: main  
**Documentation**: Complete usage examples for all phases