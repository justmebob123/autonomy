# PROJECT 1 MASTER PLAN: AI-Powered Project Planning & Objective Management System

> **Project Type**: REST API Web Application (WSGI + Apache)  
> **Purpose**: Deep analysis and improvement of project MASTER_PLAN.md files  
> **Focus**: Objective management, progress tracking, and intelligent recommendations  
> **Independence**: Completely separate from autonomy pipeline

---

## Vision

Build an intelligent web service that deeply examines project source files and documentation to:
- **Understand** the current state of any software project
- **Analyze** MASTER_PLAN.md files to extract objectives and requirements
- **Compare** actual implementation vs. planned objectives
- **Recommend** next steps, priorities, and improvements
- **Track** progress over time with metrics and visualizations
- **Identify** blockers, dependencies, and risks

This system will serve as an **external strategic advisor** for software projects, providing objective analysis and actionable recommendations through a REST API.

---

## Primary Objectives

### 1. MASTER_PLAN Analysis Engine
**Goal**: Deep understanding of project planning documents

**Capabilities**:
- Parse MASTER_PLAN.md files (any markdown format)
- Extract objective hierarchies (primary/secondary/tertiary)
- Identify acceptance criteria
- Extract dependencies and blockers
- Parse task lists and checklists
- Understand project phases and milestones
- Extract success criteria
- Identify technology stack requirements

**Technical Approach**:
- Markdown AST parsing (using `markdown-it-py` or `mistune`)
- Custom grammar for objective extraction
- Regex patterns for common structures
- Hierarchical data model
- Validation and consistency checking

### 2. Source Code Analysis Engine
**Goal**: Understand actual project implementation state

**Capabilities**:
- Recursive directory traversal
- Multi-language file analysis (Python, JavaScript, Java, Go, etc.)
- AST parsing for Python files
- Import/dependency graph generation
- Function/class inventory
- Complexity metrics
- Test coverage estimation
- Documentation coverage
- Architecture pattern detection

**Technical Approach**:
- Adapt `bin/deep_analyze.py` methodology
- Use `ast` module for Python
- Use language-specific parsers for others
- Build comprehensive project model
- Store in structured database

### 3. Gap Analysis Engine
**Goal**: Compare planned vs. actual implementation

**Capabilities**:
- Match objectives to implemented features
- Identify missing implementations
- Detect partially completed objectives
- Find over-implemented features (scope creep)
- Calculate completion percentages
- Estimate remaining work
- Identify technical debt
- Detect architectural mismatches

**Technical Approach**:
- Semantic matching algorithms
- Keyword extraction and matching
- File path pattern matching
- Function/class name analysis
- Documentation string analysis
- Confidence scoring

### 4. Recommendation Engine
**Goal**: Provide actionable next steps

**Capabilities**:
- Prioritize next objectives
- Suggest task breakdown
- Identify quick wins
- Recommend refactoring targets
- Suggest documentation improvements
- Identify testing gaps
- Recommend dependency updates
- Suggest architecture improvements

**Technical Approach**:
- Rule-based recommendation system
- Priority scoring algorithms
- Dependency-aware scheduling
- Risk assessment
- Effort estimation
- Impact analysis

### 5. Progress Tracking System
**Goal**: Monitor project evolution over time

**Capabilities**:
- Store historical snapshots
- Track objective completion rates
- Monitor code quality trends
- Track complexity evolution
- Measure velocity
- Identify bottlenecks
- Generate progress reports
- Predict completion dates

**Technical Approach**:
- Time-series database (SQLite with temporal tables)
- Snapshot comparison algorithms
- Trend analysis
- Statistical modeling
- Visualization generation

### 6. REST API Interface
**Goal**: Provide programmatic access to all features

**Endpoints**:
```
POST   /api/v1/projects                    # Register new project
GET    /api/v1/projects/{id}               # Get project details
PUT    /api/v1/projects/{id}               # Update project
DELETE /api/v1/projects/{id}               # Delete project

POST   /api/v1/projects/{id}/analyze       # Trigger full analysis
GET    /api/v1/projects/{id}/analysis      # Get latest analysis
GET    /api/v1/projects/{id}/objectives    # Get objectives
GET    /api/v1/projects/{id}/gaps          # Get gap analysis
GET    /api/v1/projects/{id}/recommendations # Get recommendations
GET    /api/v1/projects/{id}/progress      # Get progress metrics
GET    /api/v1/projects/{id}/history       # Get historical data

POST   /api/v1/analyze/masterplan          # Analyze MASTER_PLAN.md (one-shot)
POST   /api/v1/analyze/directory           # Analyze directory (one-shot)
POST   /api/v1/compare                     # Compare plan vs. implementation
```

**Technical Approach**:
- Flask or FastAPI framework
- WSGI deployment (mod_wsgi for Apache)
- JWT authentication
- Rate limiting
- Request validation
- Comprehensive error handling
- OpenAPI/Swagger documentation

---

## Architecture

```
project-planner/
├── app/
│   ├── __init__.py                 # Flask/FastAPI app factory
│   ├── config.py                   # Configuration management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── project.py              # Project model
│   │   ├── objective.py            # Objective model
│   │   ├── analysis.py             # Analysis result model
│   │   ├── recommendation.py       # Recommendation model
│   │   └── snapshot.py             # Historical snapshot model
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── projects.py         # Project endpoints
│   │   │   ├── analysis.py         # Analysis endpoints
│   │   │   ├── objectives.py       # Objective endpoints
│   │   │   ├── recommendations.py  # Recommendation endpoints
│   │   │   └── progress.py         # Progress endpoints
│   │   └── middleware.py           # Auth, rate limiting, etc.
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── base.py                 # Base analyzer class
│   │   ├── masterplan_parser.py    # MASTER_PLAN.md parser
│   │   ├── source_analyzer.py      # Source code analyzer
│   │   ├── python_analyzer.py      # Python-specific analyzer
│   │   ├── javascript_analyzer.py  # JavaScript analyzer
│   │   ├── gap_analyzer.py         # Gap analysis engine
│   │   └── complexity_analyzer.py  # Complexity metrics
│   ├── engines/
│   │   ├── __init__.py
│   │   ├── recommendation.py       # Recommendation engine
│   │   ├── matching.py             # Objective matching
│   │   ├── scoring.py              # Priority scoring
│   │   └── estimation.py           # Effort estimation
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── database.py             # Database connection
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── project_repo.py
│   │   │   ├── objective_repo.py
│   │   │   ├── analysis_repo.py
│   │   │   └── snapshot_repo.py
│   │   └── migrations/             # Database migrations
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── markdown_parser.py      # Markdown utilities
│   │   ├── ast_utils.py            # AST utilities
│   │   ├── file_utils.py           # File operations
│   │   └── validation.py           # Input validation
│   └── schemas/
│       ├── __init__.py
│       ├── project.py              # Pydantic schemas
│       ├── objective.py
│       ├── analysis.py
│       └── recommendation.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures
│   ├── test_api/
│   ├── test_analyzers/
│   ├── test_engines/
│   └── test_integration/
├── deployment/
│   ├── wsgi.py                     # WSGI entry point
│   ├── apache/
│   │   └── project-planner.conf    # Apache config
│   ├── nginx/
│   │   └── project-planner.conf    # Nginx config (alternative)
│   └── systemd/
│       └── project-planner.service # Systemd service
├── docs/
│   ├── api.md                      # API documentation
│   ├── architecture.md             # Architecture overview
│   ├── deployment.md               # Deployment guide
│   └── examples.md                 # Usage examples
├── scripts/
│   ├── setup_db.py                 # Database setup
│   ├── migrate.py                  # Run migrations
│   └── seed_data.py                # Seed test data
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── README.md
├── CHANGELOG.md
└── LICENSE
```

---

## Component Specifications

### 1. MASTER_PLAN Parser

**Input**: MASTER_PLAN.md file content  
**Output**: Structured objective hierarchy

```python
@dataclass
class ParsedObjective:
    id: str
    level: str  # "primary", "secondary", "tertiary"
    title: str
    description: str
    acceptance_criteria: List[str]
    dependencies: List[str]
    tasks: List[str]
    status: str  # "proposed", "in_progress", "completed"
    metadata: Dict[str, Any]

class MasterPlanParser:
    def parse(self, content: str) -> List[ParsedObjective]:
        """Parse MASTER_PLAN.md and extract objectives"""
        
    def extract_hierarchy(self, content: str) -> Dict[str, List[str]]:
        """Extract objective hierarchy"""
        
    def extract_dependencies(self, content: str) -> Dict[str, List[str]]:
        """Extract objective dependencies"""
        
    def validate_structure(self, content: str) -> List[str]:
        """Validate MASTER_PLAN.md structure"""
```

### 2. Source Code Analyzer

**Input**: Project directory path  
**Output**: Project implementation model

```python
@dataclass
class ProjectModel:
    files: List[FileInfo]
    modules: List[ModuleInfo]
    classes: List[ClassInfo]
    functions: List[FunctionInfo]
    imports: Dict[str, List[str]]
    call_graph: Dict[str, List[str]]
    complexity_metrics: Dict[str, float]
    test_coverage: float
    documentation_coverage: float

class SourceAnalyzer:
    def analyze_directory(self, path: Path) -> ProjectModel:
        """Analyze entire project directory"""
        
    def analyze_python_file(self, path: Path) -> FileInfo:
        """Analyze single Python file"""
        
    def build_call_graph(self, files: List[FileInfo]) -> Dict[str, List[str]]:
        """Build function call graph"""
        
    def calculate_complexity(self, files: List[FileInfo]) -> Dict[str, float]:
        """Calculate complexity metrics"""
```

### 3. Gap Analyzer

**Input**: Objectives + Project Model  
**Output**: Gap analysis report

```python
@dataclass
class Gap:
    objective_id: str
    gap_type: str  # "missing", "partial", "mismatch"
    severity: str  # "critical", "high", "medium", "low"
    description: str
    evidence: List[str]
    recommendations: List[str]

class GapAnalyzer:
    def analyze(self, objectives: List[ParsedObjective], 
                model: ProjectModel) -> List[Gap]:
        """Identify gaps between plan and implementation"""
        
    def match_objectives(self, objectives: List[ParsedObjective],
                        model: ProjectModel) -> Dict[str, float]:
        """Match objectives to implementation (confidence scores)"""
        
    def calculate_completion(self, objectives: List[ParsedObjective],
                            model: ProjectModel) -> Dict[str, float]:
        """Calculate completion percentage per objective"""
```

### 4. Recommendation Engine

**Input**: Gaps + Project Model + Objectives  
**Output**: Prioritized recommendations

```python
@dataclass
class Recommendation:
    id: str
    type: str  # "implement", "refactor", "document", "test"
    priority: int  # 1-100
    title: str
    description: str
    rationale: str
    effort_estimate: str  # "small", "medium", "large"
    impact: str  # "low", "medium", "high"
    dependencies: List[str]
    related_objectives: List[str]

class RecommendationEngine:
    def generate(self, gaps: List[Gap], model: ProjectModel,
                 objectives: List[ParsedObjective]) -> List[Recommendation]:
        """Generate prioritized recommendations"""
        
    def score_priority(self, rec: Recommendation) -> int:
        """Calculate priority score"""
        
    def estimate_effort(self, rec: Recommendation) -> str:
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_analyzed TIMESTAMP,
    status TEXT DEFAULT 'active'
);
```

### Objectives Table
```sql
CREATE TABLE objectives (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    level TEXT NOT NULL,  -- primary, secondary, tertiary
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'proposed',
    completion_percentage REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
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
    results JSON,  -- Full analysis results
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

### Gaps Table
```sql
CREATE TABLE gaps (
    id TEXT PRIMARY KEY,
    analysis_id TEXT NOT NULL,
    objective_id TEXT,
    gap_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    description TEXT,
    evidence JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id),
    FOREIGN KEY (objective_id) REFERENCES objectives(id)
);
```

### Recommendations Table
```sql
CREATE TABLE recommendations (
    id TEXT PRIMARY KEY,
    analysis_id TEXT NOT NULL,
    type TEXT NOT NULL,
    priority INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    rationale TEXT,
    effort_estimate TEXT,
    impact TEXT,
    status TEXT DEFAULT 'open',  -- open, accepted, rejected, completed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);
```

### Snapshots Table
```sql
CREATE TABLE snapshots (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    snapshot_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metrics JSON,  -- All metrics at this point in time
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
    "description": "A sample project",
    "local_path": "/path/to/project"
  }'
```

### Trigger Analysis
```bash
curl -X POST http://localhost:5000/api/v1/projects/proj_123/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "full",
    "include_history": true
  }'
```

### Get Recommendations
```bash
curl http://localhost:5000/api/v1/projects/proj_123/recommendations?priority_min=70
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
- **markdown-it-py** (Markdown parsing)
- **radon** (complexity metrics)
- **networkx** (graph analysis)
- **scikit-learn** (matching algorithms)

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

### Phase 2: Parsing (Weeks 3-4)
- [ ] MASTER_PLAN.md parser
- [ ] Objective extraction
- [ ] Hierarchy detection
- [ ] Dependency parsing
- [ ] Validation logic

### Phase 3: Analysis (Weeks 5-7)
- [ ] Source code analyzer
- [ ] Python AST analysis
- [ ] Call graph generation
- [ ] Complexity metrics
- [ ] Project model building

### Phase 4: Gap Analysis (Weeks 8-9)
- [ ] Objective matching
- [ ] Gap detection
- [ ] Completion calculation
- [ ] Evidence collection
- [ ] Confidence scoring

### Phase 5: Recommendations (Weeks 10-11)
- [ ] Recommendation engine
- [ ] Priority scoring
- [ ] Effort estimation
- [ ] Impact analysis
- [ ] Dependency resolution

### Phase 6: Progress Tracking (Weeks 12-13)
- [ ] Snapshot system
- [ ] Historical comparison
- [ ] Trend analysis
- [ ] Metrics calculation
- [ ] Visualization data

### Phase 7: Polish (Weeks 14-15)
- [ ] API documentation
- [ ] Error handling
- [ ] Performance optimization
- [ ] Security audit
- [ ] Deployment scripts

### Phase 8: Testing (Week 16)
- [ ] Unit tests (80%+ coverage)
- [ ] Integration tests
- [ ] API tests
- [ ] Performance tests
- [ ] Security tests

---

## Success Criteria

1. **Accuracy**: 90%+ accuracy in objective extraction
2. **Completeness**: Analyze 95%+ of common project structures
3. **Performance**: Analyze 10,000 LOC project in < 30 seconds
4. **API**: 99.9% uptime, < 200ms average response time
5. **Usability**: Clear API documentation, easy integration
6. **Reliability**: Handle edge cases gracefully, no crashes

---

## Key Differentiators from Autonomy

1. **REST API** - Web service, not CLI tool
2. **External Analysis** - Analyzes other projects, not self
3. **Planning Focus** - Strategic planning, not execution
4. **Read-Only** - Analyzes but doesn't modify code
5. **Multi-Project** - Manages multiple projects
6. **Historical** - Tracks changes over time

---

## Notes for Development

1. **Start with Python** - Focus on Python projects first, add other languages later
2. **Simple First** - Basic parsing before advanced matching
3. **Test-Driven** - Write tests alongside code
4. **Incremental** - Build features incrementally
5. **Document** - API docs from day one
6. **Performance** - Profile and optimize hot paths
7. **Security** - Validate all inputs, sanitize outputs

---

**Document Version**: 1.0.0  
**Created**: 2024-12-30  
**Status**: Ready for Implementation