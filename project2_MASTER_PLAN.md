# PROJECT 2 MASTER PLAN: AI-Powered Debugging & Architecture Analysis System

> **Project Type**: REST API Web Application (WSGI + Apache)  
> **Purpose**: Deep debugging, architecture analysis, and code quality assessment  
> **Focus**: Bug detection, complexity analysis, refactoring recommendations  
> **Independence**: Completely separate from autonomy pipeline

---

## Vision

Build an intelligent web service that performs comprehensive code analysis to:
- **Detect** bugs before they reach production
- **Analyze** code architecture and identify design issues
- **Measure** code quality metrics and complexity
- **Identify** refactoring opportunities
- **Generate** call graphs and dependency diagrams
- **Recommend** architectural improvements
- **Track** code quality evolution over time

This system will serve as an **automated code reviewer and architect** for software projects, providing deep technical analysis through a REST API.

---

## Primary Objectives

### 1. Bug Detection Engine
**Goal**: Identify bugs through static analysis

**Bug Patterns to Detect** (from autonomy analysis):
1. **Variable Used Before Definition**
   - Track variable lifecycle
   - Detect use-before-assignment
   - Identify undefined variables

2. **Missing Tool Call Processing**
   - Detect function calls without result handling
   - Identify missing error handling
   - Find incomplete implementations

3. **Missing Return Values**
   - Detect functions that should return but don't
   - Identify inconsistent return paths
   - Find missing error returns

4. **State Mutation Without Save**
   - Track state changes
   - Detect unsaved modifications
   - Identify transaction boundaries

5. **Infinite Loop Risks**
   - Detect loops without exit conditions
   - Identify missing break/return statements
   - Find recursive calls without base cases

6. **Resource Leaks**
   - Track file handle lifecycle
   - Detect unclosed connections
   - Identify memory leaks

7. **Race Conditions**
   - Detect shared state access
   - Identify missing locks
   - Find thread-safety issues

8. **Type Mismatches**
   - Validate type hints
   - Detect incompatible operations
   - Identify implicit conversions

**Technical Approach**:
- AST-based static analysis
- Data flow analysis
- Control flow analysis
- Type inference
- Pattern matching
- Symbolic execution (limited)

### 2. Complexity Analysis Engine
**Goal**: Measure and track code complexity

**Metrics to Calculate**:
- **Cyclomatic Complexity** - Control flow complexity
- **Cognitive Complexity** - Human understanding difficulty
- **Halstead Metrics** - Program vocabulary and length
- **Maintainability Index** - Overall maintainability score
- **Nesting Depth** - Maximum nesting level
- **Function Length** - Lines of code per function
- **Parameter Count** - Number of function parameters
- **Class Coupling** - Dependencies between classes

**Thresholds**:
- Cyclomatic Complexity: < 15 (good), 15-30 (warning), > 30 (critical)
- Function Length: < 50 lines (good), 50-100 (warning), > 100 (critical)
- Nesting Depth: < 4 (good), 4-6 (warning), > 6 (critical)
- Parameters: < 5 (good), 5-7 (warning), > 7 (critical)

**Technical Approach**:
- Adapt `bin/analysis/complexity.py`
- AST traversal
- Graph-based analysis
- Statistical aggregation
- Trend tracking

### 3. Architecture Analysis Engine
**Goal**: Understand and evaluate system architecture

**Capabilities**:
- **Call Graph Generation**
  - Function-to-function calls
  - Class-to-class dependencies
  - Module-to-module relationships
  - Cross-file analysis

- **Dependency Analysis**
  - Import graph
  - Circular dependency detection
  - Unused dependency identification
  - Dependency depth analysis

- **Pattern Detection**
  - Design patterns (Factory, Singleton, Observer, etc.)
  - Anti-patterns (God Object, Spaghetti Code, etc.)
  - Architectural patterns (MVC, Layered, etc.)

- **Cohesion & Coupling**
  - Module cohesion scores
  - Class coupling metrics
  - Interface segregation analysis
  - Dependency inversion compliance

**Technical Approach**:
- Adapt `bin/analysis/call_graph.py`
- Graph database (NetworkX)
- Pattern matching algorithms
- Architectural metrics
- Visualization generation

### 4. Dead Code Detection Engine
**Goal**: Identify unused and unreachable code

**Detection Capabilities**:
- **Unused Functions** - Never called
- **Unused Classes** - Never instantiated
- **Unused Imports** - Never referenced
- **Unused Variables** - Assigned but never read
- **Unreachable Code** - After return/break/continue
- **Redundant Code** - Duplicate implementations

**Special Handling**:
- Template method patterns
- Dynamic calls (getattr, eval)
- Reflection usage
- Plugin systems
- Test code

**Technical Approach**:
- Adapt `bin/analysis/dead_code.py`
- Call graph analysis
- Reference tracking
- Control flow analysis
- Pattern-aware filtering

### 5. Integration Gap Finder
**Goal**: Identify incomplete integrations and orphaned code

**Detection Capabilities**:
- **Unused Mixins** - Inherited but methods never called
- **Incomplete Implementations** - Abstract methods not implemented
- **Orphaned Subsystems** - Components with no callers
- **Missing Wiring** - Components not connected
- **Inconsistent Interfaces** - Interface violations

**Technical Approach**:
- Adapt `bin/analysis/integration_gaps.py`
- Inheritance analysis
- Interface compliance checking
- Component connectivity analysis
- Architectural validation

### 6. Refactoring Recommendation Engine
**Goal**: Suggest code improvements

**Recommendation Types**:
1. **Extract Method** - Break down complex functions
2. **Extract Class** - Separate responsibilities
3. **Rename** - Improve naming clarity
4. **Remove Duplication** - Consolidate duplicate code
5. **Simplify Conditionals** - Reduce nesting
6. **Introduce Parameter Object** - Reduce parameter lists
7. **Replace Magic Numbers** - Use named constants
8. **Add Error Handling** - Improve robustness

**Prioritization**:
- Impact (high/medium/low)
- Effort (small/medium/large)
- Risk (low/medium/high)
- ROI score

**Technical Approach**:
- Rule-based recommendations
- Complexity-driven prioritization
- Pattern-based suggestions
- Effort estimation
- Risk assessment

### 7. Code Quality Tracking
**Goal**: Monitor quality evolution over time

**Metrics to Track**:
- Overall quality score (0-100)
- Bug density (bugs per 1000 LOC)
- Average complexity
- Test coverage
- Documentation coverage
- Technical debt ratio
- Maintainability index
- Code churn rate

**Visualizations**:
- Quality trend charts
- Complexity heatmaps
- Dependency graphs
- Architecture diagrams
- Hotspot identification

**Technical Approach**:
- Time-series database
- Historical comparison
- Trend analysis
- Anomaly detection
- Report generation

### 8. REST API Interface
**Goal**: Provide programmatic access to all features

**Endpoints**:
```
POST   /api/v1/projects                    # Register project
GET    /api/v1/projects/{id}               # Get project details
DELETE /api/v1/projects/{id}               # Delete project

POST   /api/v1/projects/{id}/analyze       # Trigger analysis
GET    /api/v1/projects/{id}/analysis      # Get latest analysis

GET    /api/v1/projects/{id}/bugs          # Get detected bugs
GET    /api/v1/projects/{id}/complexity    # Get complexity metrics
GET    /api/v1/projects/{id}/architecture  # Get architecture analysis
GET    /api/v1/projects/{id}/deadcode      # Get dead code report
GET    /api/v1/projects/{id}/gaps          # Get integration gaps
GET    /api/v1/projects/{id}/refactorings  # Get refactoring suggestions
GET    /api/v1/projects/{id}/quality       # Get quality metrics
GET    /api/v1/projects/{id}/history       # Get historical data

GET    /api/v1/projects/{id}/callgraph     # Get call graph (JSON)
GET    /api/v1/projects/{id}/dependencies  # Get dependency graph
GET    /api/v1/projects/{id}/hotspots      # Get complexity hotspots

POST   /api/v1/analyze/file                # Analyze single file (one-shot)
POST   /api/v1/analyze/directory           # Analyze directory (one-shot)
POST   /api/v1/compare                     # Compare two versions
```

---

## Architecture

```
code-analyzer/
├── app/
│   ├── __init__.py                 # Flask/FastAPI app factory
│   ├── config.py                   # Configuration management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── project.py              # Project model
│   │   ├── analysis.py             # Analysis result model
│   │   ├── bug.py                  # Bug report model
│   │   ├── complexity.py           # Complexity metrics model
│   │   ├── refactoring.py          # Refactoring suggestion model
│   │   └── snapshot.py             # Historical snapshot model
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── projects.py         # Project endpoints
│   │   │   ├── analysis.py         # Analysis endpoints
│   │   │   ├── bugs.py             # Bug endpoints
│   │   │   ├── complexity.py       # Complexity endpoints
│   │   │   ├── architecture.py     # Architecture endpoints
│   │   │   ├── refactorings.py     # Refactoring endpoints
│   │   │   └── quality.py          # Quality endpoints
│   │   └── middleware.py           # Auth, rate limiting, etc.
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── base.py                 # Base analyzer class
│   │   ├── bug_detector.py         # Bug detection engine
│   │   ├── complexity_analyzer.py  # Complexity analysis
│   │   ├── architecture_analyzer.py # Architecture analysis
│   │   ├── dead_code_detector.py   # Dead code detection
│   │   ├── integration_analyzer.py # Integration gap finder
│   │   ├── call_graph_builder.py   # Call graph generation
│   │   └── dependency_analyzer.py  # Dependency analysis
│   ├── detectors/
│   │   ├── __init__.py
│   │   ├── bug_patterns.py         # Bug pattern definitions
│   │   ├── use_before_def.py       # Use-before-definition detector
│   │   ├── missing_handling.py     # Missing error handling
│   │   ├── infinite_loop.py        # Infinite loop detector
│   │   ├── resource_leak.py        # Resource leak detector
│   │   ├── race_condition.py       # Race condition detector
│   │   └── type_mismatch.py        # Type mismatch detector
│   ├── engines/
│   │   ├── __init__.py
│   │   ├── refactoring.py          # Refactoring recommendation engine
│   │   ├── prioritization.py       # Priority scoring
│   │   ├── estimation.py           # Effort estimation
│   │   └── visualization.py        # Graph visualization
│   ├── metrics/
│   │   ├── __init__.py
│   │   ├── cyclomatic.py           # Cyclomatic complexity
│   │   ├── cognitive.py            # Cognitive complexity
│   │   ├── halstead.py             # Halstead metrics
│   │   ├── maintainability.py      # Maintainability index
│   │   └── quality_score.py        # Overall quality score
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── database.py             # Database connection
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── project_repo.py
│   │   │   ├── analysis_repo.py
│   │   │   ├── bug_repo.py
│   │   │   └── snapshot_repo.py
│   │   └── migrations/             # Database migrations
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── ast_utils.py            # AST utilities
│   │   ├── graph_utils.py          # Graph utilities
│   │   ├── file_utils.py           # File operations
│   │   └── validation.py           # Input validation
│   └── schemas/
│       ├── __init__.py
│       ├── project.py              # Pydantic schemas
│       ├── analysis.py
│       ├── bug.py
│       └── refactoring.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures
│   ├── test_api/
│   ├── test_analyzers/
│   ├── test_detectors/
│   ├── test_engines/
│   └── test_integration/
├── deployment/
│   ├── wsgi.py                     # WSGI entry point
│   ├── apache/
│   │   └── code-analyzer.conf      # Apache config
│   ├── nginx/
│   │   └── code-analyzer.conf      # Nginx config (alternative)
│   └── systemd/
│       └── code-analyzer.service   # Systemd service
├── docs/
│   ├── api.md                      # API documentation
│   ├── architecture.md             # Architecture overview
│   ├── bug_patterns.md             # Bug pattern catalog
│   ├── metrics.md                  # Metrics documentation
│   └── deployment.md               # Deployment guide
├── scripts/
│   ├── setup_db.py                 # Database setup
│   ├── migrate.py                  # Run migrations
│   └── benchmark.py                # Performance benchmarks
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── README.md
├── CHANGELOG.md
└── LICENSE
```

---

## Component Specifications

### 1. Bug Detector

```python
@dataclass
class Bug:
    id: str
    type: str  # "use_before_def", "missing_handling", etc.
    severity: str  # "critical", "high", "medium", "low"
    file: str
    line: int
    column: int
    message: str
    code_snippet: str
    suggestion: str
    confidence: float  # 0.0-1.0

class BugDetector:
    def detect(self, file_path: Path) -> List[Bug]:
        """Detect bugs in a file"""
        
    def detect_use_before_def(self, ast_tree) -> List[Bug]:
        """Detect use-before-definition bugs"""
        
    def detect_missing_handling(self, ast_tree) -> List[Bug]:
        """Detect missing error handling"""
        
    def detect_infinite_loops(self, ast_tree) -> List[Bug]:
        """Detect infinite loop risks"""
```

### 2. Complexity Analyzer

```python
@dataclass
class ComplexityMetrics:
    file: str
    function: str
    cyclomatic: int
    cognitive: int
    halstead_volume: float
    halstead_difficulty: float
    maintainability_index: float
    nesting_depth: int
    parameter_count: int
    line_count: int

class ComplexityAnalyzer:
    def analyze(self, file_path: Path) -> List[ComplexityMetrics]:
        """Analyze complexity of all functions in file"""
        
    def calculate_cyclomatic(self, ast_node) -> int:
        """Calculate cyclomatic complexity"""
        
    def calculate_cognitive(self, ast_node) -> int:
        """Calculate cognitive complexity"""
        
    def calculate_maintainability(self, metrics: ComplexityMetrics) -> float:
        """Calculate maintainability index"""
```

### 3. Architecture Analyzer

```python
@dataclass
class CallGraph:
    nodes: List[str]  # Function names
    edges: List[Tuple[str, str]]  # (caller, callee)
    metadata: Dict[str, Any]

@dataclass
class DependencyGraph:
    modules: List[str]
    dependencies: List[Tuple[str, str]]  # (from, to)
    circular: List[List[str]]  # Circular dependency chains

class ArchitectureAnalyzer:
    def build_call_graph(self, files: List[Path]) -> CallGraph:
        """Build function call graph"""
        
    def build_dependency_graph(self, files: List[Path]) -> DependencyGraph:
        """Build module dependency graph"""
        
    def detect_patterns(self, call_graph: CallGraph) -> List[str]:
        """Detect design patterns"""
        
    def calculate_coupling(self, files: List[Path]) -> Dict[str, float]:
        """Calculate coupling metrics"""
```

### 4. Refactoring Engine

```python
@dataclass
class Refactoring:
    id: str
    type: str  # "extract_method", "extract_class", etc.
    priority: int  # 1-100
    title: str
    description: str
    file: str
    line: int
    effort: str  # "small", "medium", "large"
    impact: str  # "low", "medium", "high"
    risk: str  # "low", "medium", "high"
    suggestion: str  # Detailed refactoring steps

class RefactoringEngine:
    def generate(self, bugs: List[Bug], 
                 complexity: List[ComplexityMetrics],
                 architecture: CallGraph) -> List[Refactoring]:
        """Generate refactoring recommendations"""
        
    def prioritize(self, refactorings: List[Refactoring]) -> List[Refactoring]:
        """Prioritize refactorings by ROI"""
        
    def estimate_effort(self, refactoring: Refactoring) -> str:
        """Estimate implementation effort"""
```

---

## Database Schema

### Projects Table
```sql
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    repository_url TEXT,
    local_path TEXT,
    language TEXT DEFAULT 'python',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_analyzed TIMESTAMP,
    status TEXT DEFAULT 'active'
);
```

### Analyses Table
```sql
CREATE TABLE analyses (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    analysis_type TEXT NOT NULL,  -- full, incremental, targeted
    status TEXT DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds REAL,
    files_analyzed INTEGER,
    lines_analyzed INTEGER,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

### Bugs Table
```sql
CREATE TABLE bugs (
    id TEXT PRIMARY KEY,
    analysis_id TEXT NOT NULL,
    type TEXT NOT NULL,
    severity TEXT NOT NULL,
    file TEXT NOT NULL,
    line INTEGER NOT NULL,
    column INTEGER,
    message TEXT,
    code_snippet TEXT,
    suggestion TEXT,
    confidence REAL,
    status TEXT DEFAULT 'open',  -- open, fixed, false_positive
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);
```

### Complexity Table
```sql
CREATE TABLE complexity_metrics (
    id TEXT PRIMARY KEY,
    analysis_id TEXT NOT NULL,
    file TEXT NOT NULL,
    function TEXT NOT NULL,
    cyclomatic INTEGER,
    cognitive INTEGER,
    halstead_volume REAL,
    halstead_difficulty REAL,
    maintainability_index REAL,
    nesting_depth INTEGER,
    parameter_count INTEGER,
    line_count INTEGER,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);
```

### Refactorings Table
```sql
CREATE TABLE refactorings (
    id TEXT PRIMARY KEY,
    analysis_id TEXT NOT NULL,
    type TEXT NOT NULL,
    priority INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    file TEXT NOT NULL,
    line INTEGER,
    effort TEXT,
    impact TEXT,
    risk TEXT,
    suggestion TEXT,
    status TEXT DEFAULT 'open',  -- open, accepted, rejected, completed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);
```

### Quality Snapshots Table
```sql
CREATE TABLE quality_snapshots (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    snapshot_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    quality_score REAL,
    bug_count INTEGER,
    critical_bug_count INTEGER,
    avg_complexity REAL,
    max_complexity INTEGER,
    dead_code_count INTEGER,
    technical_debt_ratio REAL,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

---

## API Examples

### Register Project
```bash
curl -X POST http://localhost:5000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Project",
    "local_path": "/path/to/project",
    "language": "python"
  }'
```

### Trigger Analysis
```bash
curl -X POST http://localhost:5000/api/v1/projects/proj_123/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "full",
    "include_bugs": true,
    "include_complexity": true,
    "include_architecture": true
  }'
```

### Get Bugs
```bash
curl http://localhost:5000/api/v1/projects/proj_123/bugs?severity=critical
```

### Get Complexity Hotspots
```bash
curl http://localhost:5000/api/v1/projects/proj_123/hotspots?limit=10
```

### Get Refactoring Suggestions
```bash
curl http://localhost:5000/api/v1/projects/proj_123/refactorings?priority_min=70
```

---

## Technology Stack

### Core Framework
- **Flask** or **FastAPI** (REST API)
- **SQLAlchemy** (ORM)
- **Alembic** (migrations)
- **Pydantic** (validation)

### Analysis Libraries
- **ast** (Python AST parsing)
- **radon** (complexity metrics)
- **networkx** (graph analysis)
- **graphviz** (visualization)
- **pylint** (linting integration)
- **mypy** (type checking integration)

### Deployment
- **mod_wsgi** (Apache integration)
- **gunicorn** (WSGI server alternative)
- **Apache 2.4+** (web server)
- **SQLite** (database)

### Development
- **pytest** (testing)
- **black** (formatting)
- **ruff** (linting)
- **mypy** (type checking)

---

## Development Phases

### Phase 1: Foundation (Weeks 1-2)
- [ ] Project structure setup
- [ ] Database schema and migrations
- [ ] Basic API skeleton
- [ ] Authentication and middleware
- [ ] Configuration management

### Phase 2: Bug Detection (Weeks 3-5)
- [ ] AST parsing infrastructure
- [ ] Use-before-definition detector
- [ ] Missing error handling detector
- [ ] Infinite loop detector
- [ ] Resource leak detector
- [ ] Bug reporting system

### Phase 3: Complexity Analysis (Weeks 6-7)
- [ ] Cyclomatic complexity calculator
- [ ] Cognitive complexity calculator
- [ ] Halstead metrics
- [ ] Maintainability index
- [ ] Complexity reporting

### Phase 4: Architecture Analysis (Weeks 8-10)
- [ ] Call graph builder
- [ ] Dependency graph builder
- [ ] Pattern detection
- [ ] Coupling metrics
- [ ] Graph visualization

### Phase 5: Dead Code & Gaps (Weeks 11-12)
- [ ] Dead code detector
- [ ] Integration gap finder
- [ ] Unused code identification
- [ ] Orphaned component detection

### Phase 6: Refactoring Engine (Weeks 13-14)
- [ ] Refactoring recommendation engine
- [ ] Priority scoring
- [ ] Effort estimation
- [ ] Risk assessment
- [ ] Suggestion generation

### Phase 7: Quality Tracking (Weeks 15-16)
- [ ] Quality score calculation
- [ ] Historical tracking
- [ ] Trend analysis
- [ ] Report generation
- [ ] Visualization

### Phase 8: Polish (Weeks 17-18)
- [ ] API documentation
- [ ] Error handling
- [ ] Performance optimization
- [ ] Security audit
- [ ] Deployment scripts

### Phase 9: Testing (Week 19-20)
- [ ] Unit tests (80%+ coverage)
- [ ] Integration tests
- [ ] API tests
- [ ] Performance tests
- [ ] Security tests

---

## Success Criteria

1. **Accuracy**: 95%+ accuracy in bug detection (< 5% false positives)
2. **Performance**: Analyze 10,000 LOC in < 60 seconds
3. **Coverage**: Detect all 8 bug patterns with high confidence
4. **API**: 99.9% uptime, < 300ms average response time
5. **Completeness**: Analyze 95%+ of Python language features
6. **Reliability**: Handle edge cases gracefully, no crashes

---

## Key Differentiators from Autonomy

1. **REST API** - Web service, not CLI tool
2. **External Analysis** - Analyzes other projects, not self
3. **Debugging Focus** - Bug detection, not execution
4. **Read-Only** - Analyzes but doesn't modify code
5. **Multi-Project** - Manages multiple projects
6. **Historical** - Tracks quality over time
7. **Visualization** - Generates graphs and diagrams

---

## Notes for Development

1. **Adapt Existing Tools** - Reuse bin/analysis/ scripts as foundation
2. **Start with Python** - Focus on Python first, add other languages later
3. **Test-Driven** - Write tests alongside code
4. **Incremental** - Build detectors incrementally
5. **Document** - API docs and bug pattern catalog from day one
6. **Performance** - Profile and optimize hot paths
7. **Accuracy** - Minimize false positives through testing

---

**Document Version**: 1.0.0  
**Created**: 2024-12-30  
**Status**: Ready for Implementation