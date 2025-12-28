================================================================================
HYPERDIMENSIONAL POLYTOPIC CODE ANALYSIS REPORT
Depth-61 Recursive Bidirectional Examination
================================================================================

## SUMMARY STATISTICS
--------------------------------------------------------------------------------
Total Files Analyzed: 176
Total Functions: 1712
Total Classes: 209
Total Vertices: 1921
Call Graph Edges: 8058
Module Dependencies: 1681

## 7D POLYTOPIC STRUCTURE
--------------------------------------------------------------------------------
Vertices in 7D space: 1921
Dimensions:
  1. Temporal (execution order)
  2. Functional (call relationships)
  3. Data (variable flow)
  4. State (state transitions)
  5. Error (exception paths)
  6. Context (scope relationships)
  7. Integration (module dependencies)

## MOST COMPLEX FUNCTIONS (Top 20)
--------------------------------------------------------------------------------
 1. run.py::run_debug_qa_mode                                    Complexity: 192
 2. pipeline/phases/debugging.py::execute_with_conversation_thread Complexity: 85
 3. pipeline/handlers.py::_handle_modify_file                    Complexity: 54
 4. pipeline/phases/qa.py::execute                               Complexity: 50
 5. pipeline/phases/debugging.py::execute                        Complexity: 45
 6. pipeline/coordinator.py::_run_loop                           Complexity: 38
 7. pipeline/orchestration/arbiter.py::_parse_decision           Complexity: 33
 8. pipeline/phases/planning.py::execute                         Complexity: 30
 9. pipeline/objective_manager.py::_parse_objective_file         Complexity: 28
10. pipeline/handlers.py::_log_tool_activity                     Complexity: 25
11. pipeline/runtime_tester.py::_run                             Complexity: 25
12. pipeline/phases/project_planning.py::execute                 Complexity: 22
13. pipeline/coordinator.py::_determine_next_action_tactical     Complexity: 20
14. pipeline/line_fixer.py::apply_fix                            Complexity: 20
15. pipeline/orchestration/arbiter.py::_parse_text_decision      Complexity: 20
16. pipeline/prompts.py::_get_runtime_debug_prompt               Complexity: 20
17. pipeline/client.py::_extract_all_json_blocks                 Complexity: 19
18. pipeline/prompt_registry.py::generate_adaptive_prompt        Complexity: 19
19. pipeline/signature_extractor.py::extract_function_signature  Complexity: 19
20. pipeline/debugging_utils.py::analyze_no_tool_call_response   Complexity: 18

## MOST CONNECTED FUNCTIONS (Top 20)
--------------------------------------------------------------------------------
 1. len                                                          Connections: 437
 2. get                                                          Connections: 377
 3. append                                                       Connections: 359
 4. info                                                         Connections: 204
 5. now                                                          Connections: 152
 6. join                                                         Connections: 148
 7. print                                                        Connections: 147
 8. items                                                        Connections: 141
 9. str                                                          Connections: 127
10. exists                                                       Connections: 116
11. values                                                       Connections: 101
12. error                                                        Connections: 100
13. run.py::run_debug_qa_mode                                    Connections: 99
14. isoformat                                                    Connections: 98
15. Path                                                         Connections: 95
16. assertEqual                                                  Connections: 94
17. range                                                        Connections: 82
18. warning                                                      Connections: 82
19. sum                                                          Connections: 80
20. open                                                         Connections: 78

## MODULE DEPENDENCY ANALYSIS
--------------------------------------------------------------------------------
  DEPTH_59_POLYTOPIC_ANALYSIS.py                     In:   0 Out:  11
  DEPTH_61_DEFAULTDICT_ANALYSIS.py                   In:   0 Out:   9
  DEPTH_61_MODEL_SELECTION_ANALYSIS.py               In:   0 Out:   4
  HYPERDIMENSIONAL_ANALYSIS_FRAMEWORK.py             In:   0 Out:  17
  INTEGRATION_VERIFICATION.py                        In:   0 Out:   8
  __future__.annotations                             In:   1 Out:   0
  abc.ABC                                            In:   1 Out:   0
  abc.abstractmethod                                 In:   1 Out:   0
  action_tracker.Action                              In:   1 Out:   0
  action_tracker.ActionTracker                       In:   3 Out:   0
  analysis_specialist.AnalysisSpecialist             In:   1 Out:   0
  analysis_specialist.AnalysisTask                   In:   1 Out:   0
  analysis_specialist.AnalysisType                   In:   1 Out:   0
  analysis_specialist.create_analysis_specialist     In:   1 Out:   0
  analytics.AnomalyDetector                          In:   1 Out:   0
  analytics.MessageAnalytics                         In:   2 Out:   0
  analytics.OptimizationEngine                       In:   1 Out:   0
  analytics.PredictiveAnalyticsEngine                In:   1 Out:   0
  anomaly_detector.Anomaly                           In:   2 Out:   0
  anomaly_detector.AnomalyDetector                   In:   2 Out:   0

================================================================================
END OF REPORT
================================================================================