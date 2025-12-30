# PROJECT 1 ARCHITECTURE: AI-Powered Project Planning & Objective Management System

> **Companion Document**: See `project1_MASTER_PLAN.md` for objectives and requirements  
> **Purpose**: Detailed technical architecture and implementation specifications  
> **Status**: Design Document - Ready for Implementation  
> **Implementation**: Custom code using Python standard library only

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
│  │              REST API Endpoints (Custom WSGI)            │   │
│  │  /projects  /analyze  /objectives  /recommendations      │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │                                          │
│  ┌────────────────────▼─────────────────────────────────────┐   │
│  │                 Business Logic Layer                      │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │   │
│  │  │ Analyzers   │  │ Engines     │  │ Processors  │      │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │   │
│  └────────────────────┬─────────────────────────────────────┘   │
└───────────────────────┼─────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│                    Data Access Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Repositories │  │ Models       │  │ Migrations   │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└───────────────────────┬─────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│                   Persistence Layer                               │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │              SQLite/MySQL Database                       │    │
│  │  Projects | Objectives | Analyses | Snapshots            │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

### System Characteristics

- **Architecture Style**: Layered + Service-Oriented
- **API Style**: RESTful
- **Data Storage**: SQLite (default) or MySQL
- **Deployment**: Custom WSGI + Apache
- **Scalability**: Vertical (single instance)
- **Availability**: 99.9% target
- **Implementation**: Python standard library only

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
    """Python-specific analysis using ast module"""
    
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

### 1. Custom WSGI Application

**Responsibility**: Handle HTTP requests and route to appropriate handlers

**Architecture**:
```
WSGIApplication
├── Router (URL routing)
├── Request (request parsing)
├── Response (response formatting)
└── Middleware Stack
    ├── AuthenticationMiddleware
    ├── RateLimitMiddleware
    └── ValidationMiddleware
```

**Implementation**:
```python
class WSGIApplication:
    """Custom WSGI application using only standard library"""
    
    def __init__(self):
        self.router = Router()
        self.middleware_stack = []
    
    def __call__(self, environ: Dict, start_response: Callable) -> List[bytes]:
        """WSGI application interface"""
        # Build request object
        request = Request(environ)
        
        # Apply middleware
        for middleware in self.middleware_stack:
            request = middleware.process_request(request)
            if request.response:
                return self._send_response(request.response, start_response)
        
        # Route request
        try:
            handler = self.router.match(request.method, request.path)
            response = handler(request)
        except RouteNotFound:
            response = Response(status=404, body={'error': 'Not found'})
        except Exception as e:
            response = Response(status=500, body={'error': str(e)})
        
        return self._send_response(response, start_response)
```

### 2. Custom JWT Authentication

**Responsibility**: Authenticate and authorize API requests

**Architecture**:
```
JWTHandler
├── encode() - Create JWT tokens
├── decode() - Verify JWT tokens
├── _sign() - HMAC signature
└── _base64url_encode/decode() - Base64 encoding
```

**Implementation**:
```python
class JWTHandler:
    """Custom JWT implementation using hmac and hashlib"""
    
    def __init__(self, secret_key: str, algorithm: str = 'HS256'):
        self.secret_key = secret_key.encode('utf-8')
        self.algorithm = algorithm
    
    def encode(self, payload: Dict, expires_in: int = 86400) -> str:
        """Encode JWT token"""
        # Add standard claims
        now = datetime.utcnow()
        payload['iat'] = int(now.timestamp())
        payload['exp'] = int((now + timedelta(seconds=expires_in)).timestamp())
        
        # Create header
        header = {'typ': 'JWT', 'alg': self.algorithm}
        
        # Encode and sign
        header_encoded = self._base64url_encode(json.dumps(header))
        payload_encoded = self._base64url_encode(json.dumps(payload))
        message = f"{header_encoded}.{payload_encoded}"
        signature = self._sign(message)
        
        return f"{message}.{signature}"
    
    def _sign(self, message: str) -> str:
        """Create HMAC signature"""
        signature = hmac.new(
            self.secret_key,
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return self._base64url_encode(signature)
```

### 3. Database Abstraction Layer

**Responsibility**: Provide unified interface for SQLite and MySQL

**Architecture**:
```
DatabaseConnection
├── SQLiteAdapter
│   ├── connect()
│   ├── execute()
│   ├── fetchone()
│   └── fetchall()
└── MySQLAdapter
    ├── connect()
    ├── execute()
    ├── fetchone()
    └── fetchall()
```

**Implementation**:
```python
class DatabaseConnection:
    """Database connection manager supporting SQLite and MySQL"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.db_type = config.get('type', 'sqlite')
        
        if self.db_type == 'sqlite':
            self.adapter = SQLiteAdapter(config)
        elif self.db_type == 'mysql':
            self.adapter = MySQLAdapter(config)
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
    
    def connect(self):
        """Establish database connection"""
        self.connection = self.adapter.connect()
    
    def execute(self, query: str, params: tuple = None) -> Any:
        """Execute SQL query"""
        return self.adapter.execute(self.connection, query, params)
```

### 4. MASTER_PLAN Parser Component

**Responsibility**: Parse and extract structured data from MASTER_PLAN.md files

**Architecture**:
```
MasterPlanParser
├── MarkdownTokenizer (lexical analysis using re module)
├── ObjectiveExtractor (semantic analysis)
├── HierarchyBuilder (structure analysis)
└── Validator (consistency checking)
```

**Implementation**:
```python
class MasterPlanParser:
    """Parses MASTER_PLAN.md files using regex and string processing"""
    
    def __init__(self):
        self.tokenizer = MarkdownTokenizer()
        self.extractor = ObjectiveExtractor()
        self.hierarchy_builder = HierarchyBuilder()
        self.validator = Validator()
    
    def parse(self, content: str) -> ParsedMasterPlan:
        """Parse MASTER_PLAN.md content"""
        # 1. Tokenize markdown using regex
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

### 5. Source Code Analyzer Component

**Responsibility**: Analyze project source code and build implementation model

**Architecture**:
```
SourceAnalyzer
├── FileScanner (directory traversal)
├── LanguageDetector (file type detection)
├── ASTParser (syntax tree generation using ast module)
├── SymbolExtractor (function/class extraction)
├── DependencyTracker (import analysis)
└── MetricsCalculator (complexity, coverage)
```

**Implementation**:
```python
class SourceAnalyzer:
    """Analyzes project source code using ast module"""
    
    def __init__(self):
        self.scanner = FileScanner()
        self.detector = LanguageDetector()
        self.parsers = {
            "python": PythonASTParser(),
            "javascript": JavaScriptParser(),
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

### 6. Gap Analyzer Component

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

### 7. Recommendation Engine Component

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
└────────────────┬──────────────────┘
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
┌──────▼──────────┐         ┌──────▼──────────┐
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
┌──────▼──────────────┐
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

**Custom JWT Implementation**:
```python
def generate_token(user_id: str) -> str:
    """Generate JWT token using hmac"""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow()
    }
    return jwt_handler.encode(payload)

def verify_token(token: str) -> Optional[str]:
    """Verify JWT token and return user_id"""
    payload = jwt_handler.decode(token)
    return payload.get("user_id") if payload else None
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

**Custom Validators**:
```python
class ProjectValidator:
    """Validate project data"""
    
    @staticmethod
    def validate_create(data: Dict) -> Tuple[bool, List[str]]:
        """Validate project creation data"""
        errors = []
        
        # Required fields
        if not data.get('name'):
            errors.append("name is required")
        elif len(data['name']) > 255:
            errors.append("name must be <= 255 characters")
        
        # Path validation
        if 'local_path' in data:
            path = Path(data['local_path'])
            if not path.exists():
                errors.append("local_path does not exist")
            elif not path.is_dir():
                errors.append("local_path must be a directory")
        
        return len(errors) == 0, errors
```

### 4. Rate Limiting

```python
class RateLimiter:
    """Custom rate limiter using in-memory storage"""
    
    def __init__(self, max_requests: int = 100, window: int = 3600):
        self.max_requests = max_requests
        self.window = window
        self.requests = {}
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed"""
        now = time.time()
        
        # Clean old entries
        self.requests = {
            k: v for k, v in self.requests.items()
            if now - v['timestamp'] < self.window
        }
        
        # Check limit
        if client_id not in self.requests:
            self.requests[client_id] = {'count': 1, 'timestamp': now}
            return True
        
        if self.requests[client_id]['count'] >= self.max_requests:
            return False
        
        self.requests[client_id]['count'] += 1
        return True
```

### 5. SQL Injection Prevention

**Use Parameterized Queries**:
```python
# SAFE - Using parameterized queries
cursor.execute(
    "SELECT * FROM projects WHERE id = ?",
    (project_id,)
)

# UNSAFE - String interpolation (DON'T DO THIS)
# cursor.execute(f"SELECT * FROM projects WHERE id = '{project_id}'")
```

---

## Performance Architecture

### 1. Caching Strategy

**Multi-Level Caching**:
```python
from functools import lru_cache

# Function-level cache
@lru_cache(maxsize=128)
def parse_masterplan(content: str):
    """Cache parsed MASTER_PLAN"""
    return parser.parse(content)

# Application-level cache
class CacheManager:
    """Simple in-memory cache"""
    
    def __init__(self, ttl: int = 300):
        self.cache = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Set cached value"""
        self.cache[key] = (value, time.time())
```

### 2. Database Optimization

**Query Optimization**:
```python
# Use indexes
cursor.execute("""
    SELECT * FROM projects 
    WHERE status = ? 
    ORDER BY updated_at DESC
""", ('active',))

# Pagination
def get_projects_paginated(page: int, per_page: int):
    offset = (page - 1) * per_page
    cursor.execute("""
        SELECT * FROM projects 
        LIMIT ? OFFSET ?
    """, (per_page, offset))
    return cursor.fetchall()
```

### 3. Performance Monitoring

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

**Apache VirtualHost (HTTP)**:
```apache
<VirtualHost *:80>
    ServerName project1.example.com
    ServerAdmin admin@example.com
    
    # Redirect to HTTPS
    Redirect permanent / https://project1.example.com/
    
    ErrorLog ${APACHE_LOG_DIR}/project1-error.log
    CustomLog ${APACHE_LOG_DIR}/project1-access.log combined
</VirtualHost>
```

**Apache VirtualHost (HTTPS)**:
```apache
<VirtualHost *:443>
    ServerName project1.example.com
    ServerAdmin admin@example.com
    
    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/project1.crt
    SSLCertificateKeyFile /etc/ssl/private/project1.key
    SSLCertificateChainFile /etc/ssl/certs/project1-chain.crt
    
    # Security headers
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-XSS-Protection "1; mode=block"
    
    # WSGI Configuration
    WSGIDaemonProcess project1 \
        user=www-data \
        group=www-data \
        processes=4 \
        threads=2 \
        python-home=/opt/project1/venv \
        python-path=/opt/project1
    
    WSGIProcessGroup project1
    WSGIScriptAlias / /opt/project1/deployment/wsgi.py
    
    # Static files
    Alias /static /opt/project1/frontend
    <Directory /opt/project1/frontend>
        Require all granted
        Options -Indexes
    </Directory>
    
    # Application directory
    <Directory /opt/project1>
        Require all granted
    </Directory>
    
    # Logging
    ErrorLog ${APACHE_LOG_DIR}/project1-ssl-error.log
    CustomLog ${APACHE_LOG_DIR}/project1-ssl-access.log combined
    
    # Compression
    <IfModule mod_deflate.c>
        AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css text/javascript application/javascript application/json
    </IfModule>
</VirtualHost>
```

**WSGI Entry Point**:
```python
# deployment/wsgi.py
import sys
import os

# Add project to path
sys.path.insert(0, '/opt/project1')

# Set environment
os.environ['APP_ENV'] = 'production'
os.environ['DATABASE_TYPE'] = 'sqlite'
os.environ['DATABASE_PATH'] = '/var/lib/project1/db.sqlite'

from app.wsgi import application
```

### Directory Structure

```
/opt/project1/
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
import subprocess

class GitIntegration:
    """Integrate with Git repositories using subprocess"""
    
    def clone_repository(self, url: str, path: Path):
        """Clone repository"""
        subprocess.run(['git', 'clone', url, str(path)], check=True)
    
    def pull_updates(self, path: Path):
        """Pull latest changes"""
        subprocess.run(['git', '-C', str(path), 'pull'], check=True)
    
    def get_commit_history(self, path: Path, limit: int = 10):
        """Get recent commits"""
        result = subprocess.run(
            ['git', '-C', str(path), 'log', f'-{limit}', '--oneline'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split('\n')
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
            https://project1.example.com/api/v1/projects/$PROJECT_ID/analyze
      
      - name: Get Recommendations
        run: |
          curl -H "Authorization: Bearer ${{ secrets.API_TOKEN }}" \
            https://project1.example.com/api/v1/projects/$PROJECT_ID/recommendations
```

### 3. Webhook Integration

```python
def handle_github_webhook(request: Request) -> Response:
    """Handle GitHub webhook"""
    event = request.headers.get("X-GitHub-Event")
    payload = request.body
    
    if event == "push":
        # Trigger analysis on push
        project_id = get_project_by_repo(payload["repository"]["url"])
        if project_id:
            trigger_analysis(project_id)
    
    return Response(status=200, body={"status": "ok"})
```

---

## Conclusion

This architecture provides:
- ✅ **Scalability** - Layered design allows independent scaling
- ✅ **Maintainability** - Clear separation of concerns
- ✅ **Testability** - Each component can be tested independently
- ✅ **Extensibility** - Easy to add new analyzers and engines
- ✅ **Performance** - Caching and optimization strategies
- ✅ **Security** - Authentication, authorization, validation
- ✅ **Reliability** - Error handling and monitoring
- ✅ **Custom Implementation** - No external framework dependencies

**Ready for implementation following project1_MASTER_PLAN.md objectives.**

---

**Document Version**: 2.0.0  
**Created**: 2024-12-30  
**Updated**: 2024-12-30  
**Status**: Design Complete - Ready for Development