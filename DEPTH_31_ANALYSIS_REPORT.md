# Depth-31 Recursive Analysis Report

## Summary

- **Python Files**: 154
- **Total Functions**: 1829
- **Total Classes**: 240
- **Tool Definitions**: 37
- **Tool Handlers**: 69
- **Phase Classes**: 1
- **State Classes**: 11

## Tool Definitions

- `analyze_complexity` (pipeline/tool_modules/tool_definitions.py)
- `detect_dead_code` (pipeline/tool_modules/tool_definitions.py)
- `find_integration_gaps` (pipeline/tool_modules/tool_definitions.py)
- `generate_call_graph` (pipeline/tool_modules/tool_definitions.py)
- `deep_analysis` (pipeline/tool_modules/tool_definitions.py)
- `advanced_analysis` (pipeline/tool_modules/tool_definitions.py)
- `unified_analysis` (pipeline/tool_modules/tool_definitions.py)
- `append_to_file` (pipeline/tool_modules/tool_definitions.py)
- `update_section` (pipeline/tool_modules/tool_definitions.py)
- `insert_after` (pipeline/tool_modules/tool_definitions.py)
- `insert_before` (pipeline/tool_modules/tool_definitions.py)
- `replace_between` (pipeline/tool_modules/tool_definitions.py)
- `find_bugs` (pipeline/tool_modules/tool_definitions.py)
- `detect_antipatterns` (pipeline/tool_modules/tool_definitions.py)
- `analyze_dataflow` (pipeline/tool_modules/tool_definitions.py)
- `create_refactoring_task` (pipeline/tool_modules/refactoring_tools.py)
- `update_refactoring_task` (pipeline/tool_modules/refactoring_tools.py)
- `list_refactoring_tasks` (pipeline/tool_modules/refactoring_tools.py)
- `get_refactoring_progress` (pipeline/tool_modules/refactoring_tools.py)
- `create_issue_report` (pipeline/tool_modules/refactoring_tools.py)
- `request_developer_review` (pipeline/tool_modules/refactoring_tools.py)
- `detect_duplicate_implementations` (pipeline/tool_modules/refactoring_tools.py)
- `compare_file_implementations` (pipeline/tool_modules/refactoring_tools.py)
- `extract_file_features` (pipeline/tool_modules/refactoring_tools.py)
- `analyze_architecture_consistency` (pipeline/tool_modules/refactoring_tools.py)
- `suggest_refactoring_plan` (pipeline/tool_modules/refactoring_tools.py)
- `merge_file_implementations` (pipeline/tool_modules/refactoring_tools.py)
- `validate_refactoring` (pipeline/tool_modules/refactoring_tools.py)
- `cleanup_redundant_files` (pipeline/tool_modules/refactoring_tools.py)
- `validate_attribute_access` (pipeline/tool_modules/validation_tools.py)
- `verify_import_class_match` (pipeline/tool_modules/validation_tools.py)
- `check_abstract_methods` (pipeline/tool_modules/validation_tools.py)
- `verify_tool_handlers` (pipeline/tool_modules/validation_tools.py)
- `validate_dict_access` (pipeline/tool_modules/validation_tools.py)
- `validate_syntax` (pipeline/tool_modules/validation_tools.py)
- `detect_circular_imports` (pipeline/tool_modules/validation_tools.py)
- `validate_all_imports` (pipeline/tool_modules/validation_tools.py)

## Tool Handlers

- `_handle_add_readme_section`
- `_handle_advanced_analysis`
- `_handle_analyze_architecture_consistency`
- `_handle_analyze_complexity`
- `_handle_analyze_connectivity`
- `_handle_analyze_dataflow`
- `_handle_analyze_documentation_needs`
- `_handle_analyze_integration_depth`
- `_handle_analyze_missing_import`
- `_handle_analyze_project_status`
- `_handle_append_to_file`
- `_handle_approve_code`
- `_handle_assess_code_quality`
- `_handle_check_abstract_methods`
- `_handle_check_config_structure`
- `_handle_check_import_scope`
- `_handle_cleanup_redundant_files`
- `_handle_compare_file_implementations`
- `_handle_confirm_documentation_current`
- `_handle_create_file`
- `_handle_create_issue_report`
- `_handle_create_plan`
- `_handle_create_refactoring_task`
- `_handle_deep_analysis`
- `_handle_detect_antipatterns`
- `_handle_detect_dead_code`
- `_handle_detect_duplicate_implementations`
- `_handle_execute_command`
- `_handle_extract_file_features`
- `_handle_find_bugs`
- `_handle_find_integration_gaps`
- `_handle_find_recursive_patterns`
- `_handle_generate_call_graph`
- `_handle_get_cpu_profile`
- `_handle_get_function_signature`
- `_handle_get_memory_profile`
- `_handle_get_refactoring_progress`
- `_handle_get_refactoring_suggestions`
- `_handle_get_system_resources`
- `_handle_insert_after`
- `_handle_insert_before`
- `_handle_inspect_process`
- `_handle_investigate_data_flow`
- `_handle_investigate_parameter_removal`
- `_handle_list_directory`
- `_handle_list_refactoring_tasks`
- `_handle_mark_task_complete`
- `_handle_merge_file_implementations`
- `_handle_modify_file`
- `_handle_propose_expansion_tasks`
- `_handle_read_file`
- `_handle_replace_between`
- `_handle_report_issue`
- `_handle_request_developer_review`
- `_handle_search_code`
- `_handle_show_process_tree`
- `_handle_suggest_refactoring_plan`
- `_handle_trace_variable_flow`
- `_handle_unified_analysis`
- `_handle_update_architecture`
- `_handle_update_readme_section`
- `_handle_update_refactoring_task`
- `_handle_update_section`
- `_handle_validate_attribute_access`
- `_handle_validate_dict_access`
- `_handle_validate_function_call`
- `_handle_validate_refactoring`
- `_handle_verify_import_class_match`
- `_handle_verify_tool_handlers`

## Phase Classes

- `InvestigationPhase` (investigation.py)

## State Classes

- `TaskError` (pipeline/state/manager.py)
- `TaskState` (pipeline/state/manager.py)
- `FileState` (pipeline/state/manager.py)
- `PhaseState` (pipeline/state/manager.py)
- `PipelineState` (pipeline/state/manager.py)
- `StateManager` (pipeline/state/manager.py)
- `FileTracker` (pipeline/state/file_tracker.py)
- `PriorityItem` (pipeline/state/priority.py)
- `PriorityQueue` (pipeline/state/priority.py)
- `RefactoringTask` (pipeline/state/refactoring_task.py)
- `RefactoringTaskManager` (pipeline/state/refactoring_task.py)
