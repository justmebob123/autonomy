# Deep Validation Tool Reexamination & Full Integration

## CRITICAL FINDING
The validators are NOT YET using the SymbolTable! They still collect symbols independently.
We created the infrastructure but didn't integrate it. This must be fixed.

## Phase 1: Fix SymbolCollector (CRITICAL - DO FIRST)
- [x] Enhance to collect method definitions (now collecting 2,257 methods)
- [x] Enhance to collect enum definitions (now collecting 19 enums)
- [x] Track method return types properly
- [x] Track class hierarchy (parent -> child)
- [x] Test that all symbols are collected correctly
- [x] Fix statistics calculation to count methods correctly

## Phase 2: Integrate SymbolTable into ALL Validators (CRITICAL)
- [ ] Update TypeUsageValidator to use SymbolTable instead of own collection
- [ ] Update MethodExistenceValidator to use SymbolTable instead of own collection
- [ ] Update FunctionCallValidator to use SymbolTable instead of own collection
- [ ] Update EnumAttributeValidator to use SymbolTable instead of own collection
- [ ] Update MethodSignatureValidator to use SymbolTable instead of own collection
- [ ] Remove duplicate symbol collection code from each validator
- [ ] Test each validator with SymbolTable

## Phase 3: Integrate Call Graph (HIGH PRIORITY)
- [ ] Add call graph integration to MethodExistenceValidator
- [ ] Add call graph integration to TypeUsageValidator
- [ ] Use call graph for type inference
- [ ] Use call graph for dead code detection

## Phase 4: Advanced Type Inference (HIGH PRIORITY)
- [ ] Track types through assignments (y = x)
- [ ] Track types through function returns (z = func(x))
- [ ] Track types through conditionals
- [ ] Implement cross-file type propagation

## Phase 5: Final Validation (CRITICAL)
- [ ] Run enhanced validators on entire codebase
- [ ] Compare results with original validators
- [ ] Fix any errors found
- [ ] Document all improvements
- [ ] Create performance comparison report

## Expected Improvements After Full Integration
- Type inference accuracy: 40% → 85%
- Method validation accuracy: 60% → 90%
- False positives: -70%
- False negatives: -80%
- Validation speed: +50% (single-pass collection)