# PROJECT 1 MASTER PLAN: AI-Powered Project Planning & Objective Management System

> **Project Type**: REST API Web Application (Custom WSGI + Apache)  
> **Purpose**: Deep analysis and improvement of project MASTER_PLAN.md files  
> **Focus**: Objective management, progress tracking, and intelligent recommendations  
> **Independence**: Completely separate from autonomy pipeline  
> **Implementation**: Custom code using Python standard library only

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
- Custom markdown parser using regex and string processing
- Custom grammar for objective extraction
- Pattern matching for common structures
- Hierarchical data model using dataclasses
- Validation and consistency checking

### 2. Source Code Analysis Engine
**Goal**: Understand actual project implementation state

**Capabilities**:
- Recursive directory traversal
- Multi-language file analysis (Python primary, JavaScript/HTML/CSS)
- AST parsing for Python files using standard library `ast` module
- Import/dependency graph generation
- Function/class inventory
- Complexity metrics calculation
- Test coverage estimation
- Documentation coverage analysis
- Architecture pattern detection

**Technical Approach**:
- Use `ast` module for Python analysis
- Custom parsers for JavaScript/HTML/CSS
- Build comprehensive project model
- Store in custom database abstraction layer

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
- Semantic matching algorithms using keyword extraction
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
- Time-series storage in database
- Snapshot comparison algorithms
- Trend analysis
- Statistical modeling
- Visualization data generation

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
- Custom WSGI application (no Flask/FastAPI)
- Apache deployment via mod_wsgi
- Custom JWT authentication using `hmac` module
- Custom rate limiting
- Request validation using custom validators
- Comprehensive error handling
- Pagination support
- Filtering and sorting

### 7. HTML5 Frontend Interface
**Goal**: Provide web-based user interface

**Capabilities**:
- Project dashboard
- Analysis results visualization
- Objective tracking
- Gap analysis display
- Recommendation management
- Progress charts and graphs
- Historical trend visualization
- Interactive reports

**Technical Approach**:
- Custom HTML5 markup
- Custom CSS styling (responsive design)
- Custom JavaScript for interactivity
- RESTful API client
- No frontend frameworks
- Progressive enhancement

---

## Architecture

```
project1/
├── app/
│   ├── __init__.py
│   ├── wsgi.py                     # WSGI application entry point
│   ├── core/
│   │   ├── application.py          # Main WSGI application
│   │   ├── router.py               # URL routing
│   │   ├── request.py              # Request parsing
│   │   ├── response.py             # Response formatting
│   │   └── middleware.py           # Middleware stack
│   ├── auth/
│   │   ├── jwt_handler.py          # Custom JWT implementation
│   │   ├── api_keys.py             # API key management
│   │   └── rbac.py                 # Role-based access control
│   ├── database/
│   │   ├── connection.py           # Database connection manager
│   │   ├── sqlite_adapter.py       # SQLite implementation
│   │   ├── mysql_adapter.py        # MySQL implementation (optional)
│   │   ├── query_builder.py        # SQL query builder
│   │   └── migrations.py           # Schema migrations
│   ├── models/
│   │   ├── base.py                 # Base model class
│   │   ├── project.py              # Project model
│   │   ├── objective.py            # Objective model
│   │   ├── analysis.py             # Analysis model
│   │   ├── recommendation.py       # Recommendation model
│   │   └── snapshot.py             # Snapshot model
│   ├── repositories/
│   │   ├── base.py                 # Base repository
│   │   ├── project_repo.py         # Project repository
│   │   ├── objective_repo.py       # Objective repository
│   │   ├── analysis_repo.py        # Analysis repository
│   │   └── recommendation_repo.py  # Recommendation repository
│   ├── analyzers/
│   │   ├── base.py                 # Base analyzer
│   │   ├── masterplan_parser.py    # Custom markdown parser
│   │   ├── source_analyzer.py      # Source code analyzer
│   │   ├── python_analyzer.py      # Python AST analyzer
│   │   ├── javascript_analyzer.py  # JavaScript analyzer
│   │   ├── gap_analyzer.py         # Gap analysis
│   │   └── complexity.py           # Complexity metrics
│   ├── engines/
│   │   ├── recommendation.py       # Recommendation engine
│   │   ├── matching.py             # Objective matching
│   │   ├── scoring.py              # Priority scoring
│   │   └── estimation.py           # Effort estimation
│   ├── services/
│   │   ├── analysis_service.py     # Analysis orchestration
│   │   ├── project_service.py      # Project management
│   │   └── snapshot_service.py     # Progress tracking
│   ├── api/
│   │   └── v1/
│   │       ├── projects.py         # Project endpoints
│   │       ├── analysis.py         # Analysis endpoints
│   │       ├── objectives.py       # Objective endpoints
│   │       ├── recommendations.py  # Recommendation endpoints
│   │       └── progress.py         # Progress endpoints
│   ├── utils/
│   │   ├── pagination.py           # Pagination helper
│   │   ├── filtering.py            # Query filtering
│   │   ├── sorting.py              # Result sorting
│   │   └── rate_limiter.py         # Rate limiting
│   └── config.py                   # Configuration management
├── frontend/
│   ├── index.html                  # Main HTML page
│   ├── css/
│   │   ├── main.css                # Main stylesheet
│   │   ├── components.css          # Component styles
│   │   └── responsive.css          # Responsive design
│   ├── js/
│   │   ├── app.js                  # Main application
│   │   ├── api.js                  # API client
│   │   ├── components.js           # UI components
│   │   └── utils.js                # Utility functions
│   └── assets/
│       └── images/                 # Images and icons
├── deployment/
│   ├── apache/
│   │   ├── http.conf               # HTTP vhost config
│   │   └── https.conf              # HTTPS vhost config
│   └── wsgi.py                     # WSGI entry point
├── tests/
│   ├── test_auth.py
│   ├── test_database.py
│   ├── test_analyzers.py
│   ├── test_api.py
│   └── test_integration.py
└── scripts/
    ├── setup_db.py                 # Database setup
    ├── create_admin.py             # Create admin user
    └── migrate.py                  # Run migrations
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
        """Analyze single Python file using ast module"""
        
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

### Core (Python Standard Library Only)
- **wsgiref** - WSGI reference implementation
- **sqlite3** - SQLite database (default)
- **ast** - Python AST parsing
- **re** - Regular expressions for markdown parsing
- **json** - JSON handling
- **hmac** - HMAC for JWT authentication
- **hashlib** - Hashing algorithms
- **pathlib** - Path operations
- **dataclasses** - Data structures
- **typing** - Type hints

### Optional External
- **mysql-connector-python** - MySQL support (only if MySQL is used instead of SQLite)

### Deployment
- **Apache 2.4+** - Web server with mod_wsgi
- **mod_wsgi** - WSGI interface for Apache

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
8. **Custom Implementation** - No external frameworks, all custom code

---

**Document Version**: 2.0.0  
**Created**: 2024-12-30  
**Updated**: 2024-12-30  
**Status**: Ready for Implementation