# PROJECT 1 ARCHITECTURE: AI-Powered Project Planning & Objective Management System

> **Companion Document**: See `project1_MASTER_PLAN.md` for objectives and requirements  
> **Purpose**: Detailed technical architecture and implementation specifications  
> **Status**: Design Document - Ready for Implementation

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Patterns](#architecture-patterns)
3. [Component Design](#component-design)
4. [Data Flow](#data-flow)
5. [API Design](#api-design)
6. [Database Design](#database-design)
7. [Security Architecture](#security-architecture)
8. [Performance Architecture](#performance-architecture)
9. [Deployment Architecture](#deployment-architecture)
10. [Integration Points](#integration-points)

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  (REST API Clients, Web UI, CLI Tools, CI/CD Integrations)      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTPS/REST
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                      API Gateway Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Auth/JWT     │  │ Rate Limiter │  │ Validator    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    Application Layer                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              REST API Endpoints (Flask/FastAPI)          │   │
│  │  /projects  /analyze  /objectives  /recommendations      │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │                                          │
│  ┌────────────────────▼─────────────────────────────────────┐   │
│  │                 Business Logic Layer                      │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │   │
│  │  │ Analyzers   │  │ Engines     │  │ Processors  │      │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │   │
│  └────────────────────┬─────────────────────────────────────┘   │
└───────────────────────┼──────────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────────┐
│                    Data Access Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Repositories │  │ ORM Models   │  │ Migrations   │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└───────────────────────┬──────────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────────┐
│                   Persistence Layer                               │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │              SQLite Database                              │    │
│  │  Projects | Objectives | Analyses | Snapshots            │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

### System Characteristics

- **Architecture Style**: Layered + Service-Oriented
- **API Style**: RESTful
- **Data Storage**: SQLite (single-file database)
- **Deployment**: WSGI + Apache
- **Scalability**: Vertical (single instance)
- **Availability**: 99.9% target

---

## Architecture Patterns

### 1. Layered Architecture

**Layers** (from top to bottom):
1. **Presentation Layer** - REST API endpoints
2. **Application Layer** - Business logic orchestration
3. **Domain Layer** - Core business logic
4. **Infrastructure Layer** - Data access and external services

**Benefits**:
- Clear separation of concerns
- Easy to test each layer independently
- Maintainable and extensible

### 2. Repository Pattern

**Purpose**: Abstract data access logic

```python
class ProjectRepository:
    """Abstract data access for projects"""
    
    def get_by_id(self, project_id: str) -> Optional[Project]:
        """Retrieve project by ID"""
        
    def get_all(self, filters: Dict = None) -> List[Project]:
        """Retrieve all projects with optional filters"""
        
    def create(self, project: Project) -> Project:
        """Create new project"""
        
    def update(self, project: Project) -> Project:
        """Update existing project"""
        
    def delete(self, project_id: str) -> bool:
        """Delete project"""
```

**Benefits**:
- Decouples business logic from data access
- Easy to swap database implementations
- Simplifies testing with mock repositories

### 3. Service Layer Pattern

**Purpose**: Encapsulate business logic

```python
class AnalysisService:
    """Orchestrates analysis operations"""
    
    def __init__(self, 
                 project_repo: ProjectRepository,
                 masterplan_parser: MasterPlanParser,
                 source_analyzer: SourceAnalyzer,
                 gap_analyzer: GapAnalyzer):
        self.project_repo = project_repo
        self.masterplan_parser = masterplan_parser
        self.source_analyzer = source_analyzer
        self.gap_analyzer = gap_analyzer
    
    def analyze_project(self, project_id: str) -> AnalysisResult:
        """Perform complete project analysis"""
        # 1. Load project
        # 2. Parse MASTER_PLAN.md
        # 3. Analyze source code
        # 4. Perform gap analysis
        # 5. Generate recommendations
        # 6. Store results
        # 7. Return analysis
```

**Benefits**:
- Coordinates multiple components
- Implements complex workflows
- Handles transactions and error recovery

### 4. Strategy Pattern

**Purpose**: Pluggable analysis algorithms

```python
class AnalyzerStrategy(ABC):
    """Base class for analysis strategies"""
    
    @abstractmethod
    def analyze(self, project: Project) -> AnalysisResult:
        """Perform analysis"""
        pass

class PythonAnalyzer(AnalyzerStrategy):
    """Python-specific analysis"""
    
class JavaScriptAnalyzer(AnalyzerStrategy):
    """JavaScript-specific analysis"""

class AnalyzerFactory:
    """Factory for creating appropriate analyzer"""
    
    def create(self, language: str) -> AnalyzerStrategy:
        if language == "python":
            return PythonAnalyzer()
        elif language == "javascript":
            return JavaScriptAnalyzer()
        # ...
```

### 5. Factory Pattern

**Purpose**: Object creation abstraction

```python
class AnalysisFactory:
    """Creates analysis components"""
    
    @staticmethod
    def create_parser(format: str) -> Parser:
        """Create appropriate parser"""
        
    @staticmethod
    def create_analyzer(language: str) -> Analyzer:
        """Create appropriate analyzer"""
        
    @staticmethod
    def create_engine(type: str) -> Engine:
        """Create appropriate engine"""
```

---

## Component Design

### 1. MASTER_PLAN Parser Component

**Responsibility**: Parse and extract structured data from MASTER_PLAN.md files

**Architecture**:
```
MasterPlanParser
├── MarkdownTokenizer (lexical analysis)
├── ObjectiveExtractor (semantic analysis)
├── HierarchyBuilder (structure analysis)
└── Validator (consistency checking)
```

**Implementation**:
```python
class MasterPlanParser:
    """Parses MASTER_PLAN.md files"""
    
    def __init__(self):
        self.tokenizer = MarkdownTokenizer()
        self.extractor = ObjectiveExtractor()
        self.hierarchy_builder = HierarchyBuilder()
        self.validator = Validator()
    
    def parse(self, content: str) -> ParsedMasterPlan:
        """Parse MASTER_PLAN.md content"""
        # 1. Tokenize markdown
        tokens = self.tokenizer.tokenize(content)
        
        # 2. Extract objectives
        objectives = self.extractor.extract(tokens)
        
        # 3. Build hierarchy
        hierarchy = self.hierarchy_builder.build(objectives)
        
        # 4. Validate structure
        issues = self.validator.validate(hierarchy)
        
        return ParsedMasterPlan(
            objectives=objectives,
            hierarchy=hierarchy,
            validation_issues=issues
        )
```

**Key Algorithms**:

1. **Objective Extraction**:
```python
def extract_objectives(self, tokens: List[Token]) -> List[Objective]:
    """Extract objectives from markdown tokens"""
    objectives = []
    current_level = None
    current_objective = None
    
    for token in tokens:
        if token.type == "heading":
            # Determine objective level from heading
            level = self._determine_level(token)
            if level:
                if current_objective:
                    objectives.append(current_objective)
                current_objective = Objective(level=level)
                current_level = level
        
        elif token.type == "list_item" and current_objective:
            # Extract tasks, criteria, dependencies
            self._extract_list_item(token, current_objective)
    
    if current_objective:
        objectives.append(current_objective)
    
    return objectives
```

2. **Hierarchy Building**:
```python
def build_hierarchy(self, objectives: List[Objective]) -> ObjectiveTree:
    """Build hierarchical tree of objectives"""
    tree = ObjectiveTree()
    
    # Group by level
    primary = [o for o in objectives if o.level == "primary"]
    secondary = [o for o in objectives if o.level == "secondary"]
    tertiary = [o for o in objectives if o.level == "tertiary"]
    
    # Build parent-child relationships
    for obj in primary:
        tree.add_root(obj)
    
    for obj in secondary:
        parent = self._find_parent(obj, primary)
        if parent:
            tree.add_child(parent, obj)
    
    for obj in tertiary:
        parent = self._find_parent(obj, secondary)
        if parent:
            tree.add_child(parent, obj)
    
    return tree
```

### 2. Source Code Analyzer Component

**Responsibility**: Analyze project source code and build implementation model

**Architecture**:
```
SourceAnalyzer
├── FileScanner (directory traversal)
├── LanguageDetector (file type detection)
├── ASTParser (syntax tree generation)
├── SymbolExtractor (function/class extraction)
├── DependencyTracker (import analysis)
└── MetricsCalculator (complexity, coverage)
```

**Implementation**:
```python
class SourceAnalyzer:
    """Analyzes project source code"""
    
    def __init__(self):
        self.scanner = FileScanner()
        self.detector = LanguageDetector()
        self.parsers = {
            "python": PythonASTParser(),
            "javascript": JavaScriptASTParser(),
        }
        self.symbol_extractor = SymbolExtractor()
        self.dependency_tracker = DependencyTracker()
        self.metrics_calculator = MetricsCalculator()
    
    def analyze(self, project_path: Path) -> ProjectModel:
        """Analyze entire project"""
        # 1. Scan directory
        files = self.scanner.scan(project_path)
        
        # 2. Detect languages
        file_info = []
        for file in files:
            language = self.detector.detect(file)
            if language in self.parsers:
                # 3. Parse AST
                ast_tree = self.parsers[language].parse(file)
                
                # 4. Extract symbols
                symbols = self.symbol_extractor.extract(ast_tree)
                
                # 5. Track dependencies
                deps = self.dependency_tracker.track(ast_tree)
                
                # 6. Calculate metrics
                metrics = self.metrics_calculator.calculate(ast_tree)
                
                file_info.append(FileInfo(
                    path=file,
                    language=language,
                    symbols=symbols,
                    dependencies=deps,
                    metrics=metrics
                ))
        
        # 7. Build project model
        return ProjectModel(files=file_info)
```

**Key Algorithms**:

1. **Symbol Extraction**:
```python
def extract_symbols(self, ast_tree) -> List[Symbol]:
    """Extract functions, classes, variables from AST"""
    symbols = []
    
    for node in ast.walk(ast_tree):
        if isinstance(node, ast.FunctionDef):
            symbols.append(Symbol(
                type="function",
                name=node.name,
                line=node.lineno,
                parameters=[arg.arg for arg in node.args.args],
                docstring=ast.get_docstring(node)
            ))
        
        elif isinstance(node, ast.ClassDef):
            symbols.append(Symbol(
                type="class",
                name=node.name,
                line=node.lineno,
                methods=[m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                docstring=ast.get_docstring(node)
            ))
    
    return symbols
```

2. **Dependency Tracking**:
```python
def track_dependencies(self, ast_tree) -> DependencyGraph:
    """Build dependency graph from imports"""
    graph = DependencyGraph()
    
    for node in ast.walk(ast_tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                graph.add_dependency(alias.name)
        
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                graph.add_dependency(f"{module}.{alias.name}")
    
    return graph
```

### 3. Gap Analyzer Component

**Responsibility**: Compare objectives with implementation

**Architecture**:
```
GapAnalyzer
├── ObjectiveMatcher (semantic matching)
├── CompletionCalculator (progress calculation)
├── EvidenceCollector (proof gathering)
└── GapClassifier (gap categorization)
```

**Implementation**:
```python
class GapAnalyzer:
    """Analyzes gaps between plan and implementation"""
    
    def __init__(self):
        self.matcher = ObjectiveMatcher()
        self.calculator = CompletionCalculator()
        self.collector = EvidenceCollector()
        self.classifier = GapClassifier()
    
    def analyze(self, 
                objectives: List[Objective],
                project_model: ProjectModel) -> List[Gap]:
        """Identify gaps"""
        gaps = []
        
        for objective in objectives:
            # 1. Match objective to implementation
            matches = self.matcher.match(objective, project_model)
            
            # 2. Calculate completion
            completion = self.calculator.calculate(objective, matches)
            
            # 3. Collect evidence
            evidence = self.collector.collect(objective, matches)
            
            # 4. Classify gap
            if completion < 1.0:
                gap = self.classifier.classify(
                    objective, completion, evidence
                )
                gaps.append(gap)
        
        return gaps
```

**Key Algorithms**:

1. **Semantic Matching**:
```python
def match_objective(self, 
                   objective: Objective,
                   project_model: ProjectModel) -> List[Match]:
    """Match objective to implementation using semantic similarity"""
    matches = []
    
    # Extract keywords from objective
    obj_keywords = self._extract_keywords(objective.description)
    
    # Search for matching symbols
    for file in project_model.files:
        for symbol in file.symbols:
            # Calculate similarity score
            symbol_keywords = self._extract_keywords(
                symbol.name + " " + (symbol.docstring or "")
            )
            
            similarity = self._calculate_similarity(
                obj_keywords, symbol_keywords
            )
            
            if similarity > 0.6:  # Threshold
                matches.append(Match(
                    objective=objective,
                    symbol=symbol,
                    confidence=similarity
                ))
    
    return matches

def _calculate_similarity(self, keywords1: Set[str], 
                         keywords2: Set[str]) -> float:
    """Calculate Jaccard similarity"""
    intersection = keywords1 & keywords2
    union = keywords1 | keywords2
    return len(intersection) / len(union) if union else 0.0
```

2. **Completion Calculation**:
```python
def calculate_completion(self,
                        objective: Objective,
                        matches: List[Match]) -> float:
    """Calculate objective completion percentage"""
    if not objective.tasks:
        # No tasks defined, use match confidence
        if not matches:
            return 0.0
        return max(m.confidence for m in matches)
    
    # Calculate task completion
    completed_tasks = 0
    for task in objective.tasks:
        task_keywords = self._extract_keywords(task)
        for match in matches:
            match_keywords = self._extract_keywords(
                match.symbol.name + " " + (match.symbol.docstring or "")
            )
            similarity = self._calculate_similarity(
                task_keywords, match_keywords
            )
            if similarity > 0.7:
                completed_tasks += 1
                break
    
    return completed_tasks / len(objective.tasks)
```

### 4. Recommendation Engine Component

**Responsibility**: Generate actionable recommendations

**Architecture**:
```
RecommendationEngine
├── GapAnalyzer (input)
├── PriorityScorer (scoring)
├── EffortEstimator (estimation)
├── ImpactAnalyzer (impact assessment)
└── DependencyResolver (ordering)
```

**Implementation**:
```python
class RecommendationEngine:
    """Generates prioritized recommendations"""
    
    def __init__(self):
        self.scorer = PriorityScorer()
        self.estimator = EffortEstimator()
        self.impact_analyzer = ImpactAnalyzer()
        self.dependency_resolver = DependencyResolver()
    
    def generate(self,
                gaps: List[Gap],
                project_model: ProjectModel,
                objectives: List[Objective]) -> List[Recommendation]:
        """Generate recommendations"""
        recommendations = []
        
        for gap in gaps:
            # 1. Create recommendation
            rec = Recommendation(
                type=self._determine_type(gap),
                title=f"Implement {gap.objective.title}",
                description=gap.description,
                related_objective=gap.objective.id
            )
            
            # 2. Score priority
            rec.priority = self.scorer.score(gap, objectives)
            
            # 3. Estimate effort
            rec.effort = self.estimator.estimate(gap, project_model)
            
            # 4. Analyze impact
            rec.impact = self.impact_analyzer.analyze(gap, objectives)
            
            recommendations.append(rec)
        
        # 5. Resolve dependencies and order
        return self.dependency_resolver.resolve(recommendations)
```

**Key Algorithms**:

1. **Priority Scoring**:
```python
def score_priority(self, gap: Gap, objectives: List[Objective]) -> int:
    """Calculate priority score (1-100)"""
    score = 0
    
    # Factor 1: Objective level (40 points)
    if gap.objective.level == "primary":
        score += 40
    elif gap.objective.level == "secondary":
        score += 25
    else:  # tertiary
        score += 10
    
    # Factor 2: Gap severity (30 points)
    if gap.severity == "critical":
        score += 30
    elif gap.severity == "high":
        score += 20
    elif gap.severity == "medium":
        score += 10
    
    # Factor 3: Blocking other objectives (20 points)
    blocked_count = len([o for o in objectives 
                        if gap.objective.id in o.dependencies])
    score += min(blocked_count * 5, 20)
    
    # Factor 4: Completion percentage (10 points)
    # Lower completion = higher priority
    score += int((1.0 - gap.objective.completion) * 10)
    
    return min(score, 100)
```

2. **Effort Estimation**:
```python
def estimate_effort(self, gap: Gap, 
                   project_model: ProjectModel) -> str:
    """Estimate implementation effort"""
    # Calculate complexity factors
    factors = {
        "task_count": len(gap.objective.tasks),
        "dependency_count": len(gap.objective.dependencies),
        "avg_file_size": self._avg_file_size(project_model),
        "complexity": self._avg_complexity(project_model)
    }
    
    # Simple heuristic
    score = (
        factors["task_count"] * 2 +
        factors["dependency_count"] * 3 +
        (factors["complexity"] / 10)
    )
    
    if score < 10:
        return "small"  # < 1 day
    elif score < 30:
        return "medium"  # 1-3 days
    else:
        return "large"  # > 3 days
```

---

## Data Flow

### 1. Analysis Flow

```
User Request
    │
    ▼
POST /api/v1/projects/{id}/analyze
    │
    ▼
┌───────────────────────────────────┐
│   AnalysisService.analyze()      │
│                                   │
│   1. Load Project                 │
│   2. Parse MASTER_PLAN.md         │
│   3. Analyze Source Code          │
│   4. Perform Gap Analysis         │
│   5. Generate Recommendations     │
│   6. Store Results                │
│   7. Create Snapshot              │
└───────────────┬───────────────────┘
                │
                ▼
        AnalysisResult
                │
                ▼
        Return to User
```

### 2. Recommendation Flow

```
Gap Analysis Results
    │
    ▼
RecommendationEngine.generate()
    │
    ├─► PriorityScorer.score()
    │       │
    │       └─► Priority Score (1-100)
    │
    ├─► EffortEstimator.estimate()
    │       │
    │       └─► Effort (small/medium/large)
    │
    ├─► ImpactAnalyzer.analyze()
    │       │
    │       └─► Impact (low/medium/high)
    │
    └─► DependencyResolver.resolve()
            │
            └─► Ordered Recommendations
```

### 3. Progress Tracking Flow

```
Periodic Snapshot
    │
    ▼
SnapshotService.create()
    │
    ├─► Capture Current Metrics
    │       │
    │       ├─► Objective Completion %
    │       ├─► Gap Count
    │       ├─► Recommendation Count
    │       └─► Quality Metrics
    │
    ├─► Compare with Previous
    │       │
    │       └─► Calculate Trends
    │
    └─► Store Snapshot
            │
            └─► Database
```

---

## API Design

### REST API Principles

1. **Resource-Oriented**: URLs represent resources
2. **HTTP Methods**: GET (read), POST (create), PUT (update), DELETE (delete)
3. **Status Codes**: Proper HTTP status codes
4. **JSON**: Request/response format
5. **Versioning**: /api/v1/ prefix
6. **Pagination**: For list endpoints
7. **Filtering**: Query parameters
8. **HATEOAS**: Links to related resources

### Endpoint Design

#### 1. Project Management

```
POST /api/v1/projects
Request:
{
  "name": "My Project",
  "description": "Project description",
  "local_path": "/path/to/project",
  "repository_url": "https://github.com/user/repo"
}

Response: 201 Created
{
  "id": "proj_abc123",
  "name": "My Project",
  "description": "Project description",
  "local_path": "/path/to/project",
  "repository_url": "https://github.com/user/repo",
  "created_at": "2024-12-30T10:00:00Z",
  "updated_at": "2024-12-30T10:00:00Z",
  "status": "active",
  "_links": {
    "self": "/api/v1/projects/proj_abc123",
    "analyze": "/api/v1/projects/proj_abc123/analyze",
    "objectives": "/api/v1/projects/proj_abc123/objectives"
  }
}
```

#### 2. Analysis Trigger

```
POST /api/v1/projects/{id}/analyze
Request:
{
  "analysis_type": "full",  // full, incremental, targeted
  "include_history": true,
  "options": {
    "parse_masterplan": true,
    "analyze_source": true,
    "gap_analysis": true,
    "generate_recommendations": true
  }
}

Response: 202 Accepted
{
  "analysis_id": "ana_xyz789",
  "project_id": "proj_abc123",
  "status": "pending",
  "started_at": "2024-12-30T10:05:00Z",
  "_links": {
    "self": "/api/v1/analyses/ana_xyz789",
    "status": "/api/v1/analyses/ana_xyz789/status",
    "results": "/api/v1/analyses/ana_xyz789/results"
  }
}
```

#### 3. Get Recommendations

```
GET /api/v1/projects/{id}/recommendations?priority_min=70&limit=10

Response: 200 OK
{
  "project_id": "proj_abc123",
  "total": 25,
  "returned": 10,
  "recommendations": [
    {
      "id": "rec_001",
      "type": "implement",
      "priority": 95,
      "title": "Implement user authentication",
      "description": "Add JWT-based authentication system",
      "rationale": "Required for primary objective AUTH-001",
      "effort": "medium",
      "impact": "high",
      "related_objectives": ["primary_001"],
      "dependencies": [],
      "created_at": "2024-12-30T10:10:00Z"
    }
  ],
  "_links": {
    "self": "/api/v1/projects/proj_abc123/recommendations?priority_min=70&limit=10",
    "next": "/api/v1/projects/proj_abc123/recommendations?priority_min=70&limit=10&offset=10"
  }
}
```

### Error Handling

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid project path",
    "details": {
      "field": "local_path",
      "reason": "Path does not exist"
    },
    "timestamp": "2024-12-30T10:00:00Z",
    "request_id": "req_123456"
  }
}
```

**Error Codes**:
- 400: Bad Request (validation errors)
- 401: Unauthorized (authentication required)
- 403: Forbidden (insufficient permissions)
- 404: Not Found (resource doesn't exist)
- 409: Conflict (duplicate resource)
- 422: Unprocessable Entity (semantic errors)
- 429: Too Many Requests (rate limit exceeded)
- 500: Internal Server Error
- 503: Service Unavailable

---

## Database Design

### Schema Design Principles

1. **Normalization**: 3NF (Third Normal Form)
2. **Indexing**: On frequently queried columns
3. **Constraints**: Foreign keys, unique constraints
4. **Timestamps**: created_at, updated_at on all tables
5. **Soft Deletes**: status field instead of DELETE
6. **JSON Columns**: For flexible metadata

### Entity Relationship Diagram

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│  Projects   │1      *│  Objectives  │1      *│    Tasks    │
│─────────────│◄────────│──────────────│◄────────│─────────────│
│ id (PK)     │         │ id (PK)      │         │ id (PK)     │
│ name        │         │ project_id   │         │ objective_id│
│ description │         │ level        │         │ description │
│ local_path  │         │ title        │         │ status      │
│ status      │         │ description  │         │ completed_at│
│ created_at  │         │ status       │         └─────────────┘
│ updated_at  │         │ completion_%  │
└─────────────┘         │ created_at   │
       │                │ updated_at   │
       │                └──────────────┘
       │1                      │1
       │                       │
       │*                      │*
┌─────▼───────┐         ┌─────▼────────┐
│  Analyses   │         │     Gaps     │
│─────────────│         │──────────────│
│ id (PK)     │1      *│ id (PK)      │
│ project_id  │◄────────│ analysis_id  │
│ type        │         │ objective_id │
│ status      │         │ gap_type     │
│ started_at  │         │ severity     │
│ completed_at│         │ description  │
│ results     │         │ evidence     │
└─────────────┘         └──────────────┘
       │1
       │
       │*
┌─────▼──────────────┐
│  Recommendations   │
│────────────────────│
│ id (PK)            │
│ analysis_id        │
│ type               │
│ priority           │
│ title              │
│ description        │
│ effort             │
│ impact             │
│ status             │
└────────────────────┘
```

### Indexes

```sql
-- Projects
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_updated ON projects(updated_at);

-- Objectives
CREATE INDEX idx_objectives_project ON objectives(project_id);
CREATE INDEX idx_objectives_level ON objectives(level);
CREATE INDEX idx_objectives_status ON objectives(status);

-- Analyses
CREATE INDEX idx_analyses_project ON analyses(project_id);
CREATE INDEX idx_analyses_status ON analyses(status);
CREATE INDEX idx_analyses_completed ON analyses(completed_at);

-- Gaps
CREATE INDEX idx_gaps_analysis ON gaps(analysis_id);
CREATE INDEX idx_gaps_objective ON gaps(objective_id);
CREATE INDEX idx_gaps_severity ON gaps(severity);

-- Recommendations
CREATE INDEX idx_recommendations_analysis ON recommendations(analysis_id);
CREATE INDEX idx_recommendations_priority ON recommendations(priority);
CREATE INDEX idx_recommendations_status ON recommendations(status);
```

---

## Security Architecture

### 1. Authentication

**JWT (JSON Web Tokens)**:
```python
def generate_token(user_id: str) -> str:
    """Generate JWT token"""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> Optional[str]:
    """Verify JWT token and return user_id"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
```

### 2. Authorization

**Role-Based Access Control (RBAC)**:
```python
class Permission(Enum):
    READ_PROJECT = "read:project"
    WRITE_PROJECT = "write:project"
    DELETE_PROJECT = "delete:project"
    TRIGGER_ANALYSIS = "trigger:analysis"

class Role(Enum):
    VIEWER = [Permission.READ_PROJECT]
    DEVELOPER = [Permission.READ_PROJECT, Permission.TRIGGER_ANALYSIS]
    ADMIN = [Permission.READ_PROJECT, Permission.WRITE_PROJECT, 
             Permission.DELETE_PROJECT, Permission.TRIGGER_ANALYSIS]

def require_permission(permission: Permission):
    """Decorator to check permissions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user.has_permission(permission):
                raise PermissionDenied()
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

### 3. Input Validation

**Pydantic Schemas**:
```python
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    local_path: str = Field(..., min_length=1)
    repository_url: Optional[HttpUrl] = None
    
    @validator('local_path')
    def validate_path(cls, v):
        path = Path(v)
        if not path.exists():
            raise ValueError("Path does not exist")
        if not path.is_dir():
            raise ValueError("Path must be a directory")
        return str(path.absolute())
```

### 4. Rate Limiting

```python
from flask_limiter import Limiter

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

@app.route("/api/v1/projects/<id>/analyze", methods=["POST"])
@limiter.limit("10 per hour")  # Expensive operation
def trigger_analysis(id):
    # ...
```

### 5. SQL Injection Prevention

**Use ORM (SQLAlchemy)**:
```python
# SAFE - Using ORM
project = session.query(Project).filter(
    Project.id == project_id
).first()

# UNSAFE - Raw SQL (DON'T DO THIS)
# cursor.execute(f"SELECT * FROM projects WHERE id = '{project_id}'")
```

---

## Performance Architecture

### 1. Caching Strategy

**Multi-Level Caching**:
```python
from functools import lru_cache
from flask_caching import Cache

# Application-level cache
cache = Cache(config={'CACHE_TYPE': 'simple'})

@cache.memoize(timeout=300)  # 5 minutes
def get_project_analysis(project_id: str):
    """Cache analysis results"""
    return analysis_service.get_latest(project_id)

# Function-level cache
@lru_cache(maxsize=128)
def parse_masterplan(content: str):
    """Cache parsed MASTER_PLAN"""
    return parser.parse(content)
```

### 2. Async Processing

**Background Jobs**:
```python
from celery import Celery

celery = Celery('project_planner')

@celery.task
def analyze_project_async(project_id: str):
    """Async analysis task"""
    service = AnalysisService()
    result = service.analyze(project_id)
    return result.to_dict()

# Trigger async
@app.route("/api/v1/projects/<id>/analyze", methods=["POST"])
def trigger_analysis(id):
    task = analyze_project_async.delay(id)
    return {"task_id": task.id, "status": "pending"}
```

### 3. Database Optimization

**Query Optimization**:
```python
# Eager loading to avoid N+1 queries
projects = session.query(Project).options(
    joinedload(Project.objectives),
    joinedload(Project.analyses)
).all()

# Pagination
def get_projects_paginated(page: int, per_page: int):
    return session.query(Project).limit(per_page).offset(
        (page - 1) * per_page
    ).all()
```

### 4. Performance Monitoring

```python
import time
from functools import wraps

def monitor_performance(func):
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        
        logger.info(f"{func.__name__} took {duration:.2f}s")
        
        # Alert if slow
        if duration > 5.0:
            logger.warning(f"Slow operation: {func.__name__}")
        
        return result
    return wrapper
```

---

## Deployment Architecture

### Apache + mod_wsgi Configuration

**Apache VirtualHost**:
```apache
<VirtualHost *:80>
    ServerName project-planner.example.com
    
    WSGIDaemonProcess project_planner \
        user=www-data \
        group=www-data \
        processes=4 \
        threads=2 \
        python-home=/opt/project-planner/venv \
        python-path=/opt/project-planner
    
    WSGIProcessGroup project_planner
    WSGIScriptAlias / /opt/project-planner/deployment/wsgi.py
    
    <Directory /opt/project-planner>
        Require all granted
    </Directory>
    
    ErrorLog ${APACHE_LOG_DIR}/project-planner-error.log
    CustomLog ${APACHE_LOG_DIR}/project-planner-access.log combined
</VirtualHost>
```

**WSGI Entry Point**:
```python
# deployment/wsgi.py
import sys
import os

# Add project to path
sys.path.insert(0, '/opt/project-planner')

# Set environment
os.environ['FLASK_ENV'] = 'production'
os.environ['DATABASE_URL'] = 'sqlite:////var/lib/project-planner/db.sqlite'

from app import create_app

application = create_app()
```

### Directory Structure

```
/opt/project-planner/
├── app/                    # Application code
├── venv/                   # Virtual environment
├── deployment/
│   ├── wsgi.py            # WSGI entry point
│   └── config.py          # Production config
├── data/
│   └── db.sqlite          # Database
└── logs/
    ├── app.log            # Application logs
    └── error.log          # Error logs
```

---

## Integration Points

### 1. Git Integration

```python
import git

class GitIntegration:
    """Integrate with Git repositories"""
    
    def clone_repository(self, url: str, path: Path):
        """Clone repository"""
        git.Repo.clone_from(url, path)
    
    def pull_updates(self, path: Path):
        """Pull latest changes"""
        repo = git.Repo(path)
        repo.remotes.origin.pull()
    
    def get_commit_history(self, path: Path, limit: int = 10):
        """Get recent commits"""
        repo = git.Repo(path)
        return list(repo.iter_commits(max_count=limit))
```

### 2. CI/CD Integration

**GitHub Actions Example**:
```yaml
name: Project Analysis

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Trigger Analysis
        run: |
          curl -X POST \
            -H "Authorization: Bearer ${{ secrets.API_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d '{"analysis_type": "incremental"}' \
            https://project-planner.example.com/api/v1/projects/$PROJECT_ID/analyze
      
      - name: Get Recommendations
        run: |
          curl -H "Authorization: Bearer ${{ secrets.API_TOKEN }}" \
            https://project-planner.example.com/api/v1/projects/$PROJECT_ID/recommendations
```

### 3. Webhook Integration

```python
@app.route("/webhooks/github", methods=["POST"])
def github_webhook():
    """Handle GitHub webhook"""
    event = request.headers.get("X-GitHub-Event")
    payload = request.json
    
    if event == "push":
        # Trigger analysis on push
        project_id = get_project_by_repo(payload["repository"]["url"])
        if project_id:
            analyze_project_async.delay(project_id)
    
    return {"status": "ok"}
```

---

## Conclusion

This architecture provides:
- ✅ **Scalability** - Layered design allows independent scaling
- ✅ **Maintainability** - Clear separation of concerns
- ✅ **Testability** - Each component can be tested independently
- ✅ **Extensibility** - Easy to add new analyzers and engines
- ✅ **Performance** - Caching and async processing
- ✅ **Security** - Authentication, authorization, validation
- ✅ **Reliability** - Error handling and monitoring

**Ready for implementation following project1_MASTER_PLAN.md objectives.**

---

**Document Version**: 1.0.0  
**Created**: 2024-12-30  
**Status**: Design Complete - Ready for Development