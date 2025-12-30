# PROJECT 1 ARCHITECTURE: AI-Powered Project Management & Development Platform

> **Companion Document**: See `project1_MASTER_PLAN.md` for objectives and requirements  
> **Purpose**: Detailed technical architecture and implementation specifications  
> **Status**: Design Document - Ready for Implementation  
> **Implementation**: Custom code using Python standard library only

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Patterns](#architecture-patterns)
3. [Component Design](#component-design)
4. [Chat System Architecture](#chat-system-architecture)
5. [File Management Architecture](#file-management-architecture)
6. [Git Integration Architecture](#git-integration-architecture)
7. [Ollama Integration Architecture](#ollama-integration-architecture)
8. [Data Flow](#data-flow)
9. [API Design](#api-design)
10. [Database Design](#database-design)
11. [Frontend Architecture](#frontend-architecture)
12. [Security Architecture](#security-architecture)
13. [Performance Architecture](#performance-architecture)
14. [Deployment Architecture](#deployment-architecture)

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
---

## Chat System Architecture

### Real-Time Communication

**WebSocket/SSE Implementation**:
```python
class ChatService:
    """Manages real-time chat with Ollama models"""
    
    def __init__(self, ollama_service: OllamaService):
        self.ollama_service = ollama_service
        self.active_streams = {}
    
    def stream_response(self, thread_id: str, message: str, 
                       model: str, server: str) -> Generator:
        """Stream response from Ollama model"""
        # Store message
        self._save_message(thread_id, 'user', message)
        
        # Stream from Ollama
        response_text = ""
        for chunk in self.ollama_service.stream_chat(
            model=model,
            server=server,
            messages=self._get_thread_messages(thread_id)
        ):
            response_text += chunk
            yield chunk
        
        # Save complete response
        self._save_message(thread_id, 'assistant', response_text, model)
```

**Thread Management**:
```python
class ThreadRepository:
    """Manage conversation threads"""
    
    def create_thread(self, user_id: str, project_id: str = None,
                     title: str = "New Conversation") -> Thread:
        """Create new conversation thread"""
        
    def assign_to_project(self, thread_id: str, project_id: str):
        """Assign thread to project"""
        
    def get_project_threads(self, project_id: str) -> List[Thread]:
        """Get all threads for a project"""
        
    def search_threads(self, query: str, user_id: str) -> List[Thread]:
        """Search threads by content"""
```

---

## File Management Architecture

### File Browser Component

**Tree View Implementation**:
```python
class FileBrowserService:
    """Manage file operations"""
    
    def get_tree(self, project_id: str, path: str = "/") -> Dict:
        """Get directory tree structure"""
        project = self.project_repo.get_by_id(project_id)
        base_path = Path(project.local_path)
        
        tree = {
            'name': path,
            'type': 'directory',
            'children': []
        }
        
        for item in (base_path / path).iterdir():
            if item.is_dir():
                tree['children'].append({
                    'name': item.name,
                    'type': 'directory',
                    'path': str(item.relative_to(base_path))
                })
            else:
                tree['children'].append({
                    'name': item.name,
                    'type': 'file',
                    'path': str(item.relative_to(base_path)),
                    'size': item.stat().st_size,
                    'modified': item.stat().st_mtime
                })
        
        return tree
```

**File Upload/Download**:
```python
class FileService:
    """Handle file operations"""
    
    def upload_file(self, project_id: str, file_data: bytes,
                   filename: str, path: str = "/"):
        """Upload file to project"""
        project = self.project_repo.get_by_id(project_id)
        target_path = Path(project.local_path) / path / filename
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(file_data)
        
        # Store metadata
        self.file_repo.create(File(
            project_id=project_id,
            path=str(target_path.relative_to(project.local_path)),
            name=filename,
            size=len(file_data),
            hash=hashlib.sha256(file_data).hexdigest()
        ))
    
    def download_file(self, project_id: str, filepath: str) -> bytes:
        """Download file from project"""
        project = self.project_repo.get_by_id(project_id)
        file_path = Path(project.local_path) / filepath
        return file_path.read_bytes()
    
    def create_zip(self, project_id: str) -> bytes:
        """Create zip of entire project"""
        import zipfile
        from io import BytesIO
        
        project = self.project_repo.get_by_id(project_id)
        base_path = Path(project.local_path)
        
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in base_path.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(base_path)
                    zipf.write(file_path, arcname)
        
        return zip_buffer.getvalue()
```

---

## Git Integration Architecture

### Git Operations Service

**Git Status and Operations**:
```python
class GitService:
    """Handle git operations using subprocess"""
    
    def __init__(self):
        self.git_cmd = 'git'
    
    def get_status(self, project_id: str) -> Dict:
        """Get git status"""
        project = self.project_repo.get_by_id(project_id)
        repo_path = Path(project.local_path)
        
        # Get branch
        branch = self._run_git(repo_path, ['branch', '--show-current'])
        
        # Get status
        status_output = self._run_git(repo_path, ['status', '--porcelain'])
        
        # Parse status
        staged = []
        unstaged = []
        untracked = []
        
        for line in status_output.split('\n'):
            if not line:
                continue
            status = line[:2]
            filepath = line[3:]
            
            if status[0] in ['M', 'A', 'D']:
                staged.append({'file': filepath, 'status': status[0]})
            if status[1] in ['M', 'D']:
                unstaged.append({'file': filepath, 'status': status[1]})
            if status == '??':
                untracked.append(filepath)
        
        return {
            'branch': branch.strip(),
            'staged': staged,
            'unstaged': unstaged,
            'untracked': untracked
        }
    
    def stage_files(self, project_id: str, files: List[str]):
        """Stage files for commit"""
        project = self.project_repo.get_by_id(project_id)
        repo_path = Path(project.local_path)
        self._run_git(repo_path, ['add'] + files)
    
    def commit(self, project_id: str, message: str) -> str:
        """Commit staged changes"""
        project = self.project_repo.get_by_id(project_id)
        repo_path = Path(project.local_path)
        return self._run_git(repo_path, ['commit', '-m', message])
    
    def push(self, project_id: str, remote: str = 'origin',
            branch: str = None) -> str:
        """Push commits to remote"""
        project = self.project_repo.get_by_id(project_id)
        repo_path = Path(project.local_path)
        
        if not branch:
            branch = self._run_git(repo_path, ['branch', '--show-current']).strip()
        
        return self._run_git(repo_path, ['push', remote, branch])
    
    def pull(self, project_id: str, remote: str = 'origin',
            branch: str = None) -> str:
        """Pull changes from remote"""
        project = self.project_repo.get_by_id(project_id)
        repo_path = Path(project.local_path)
        
        if not branch:
            branch = self._run_git(repo_path, ['branch', '--show-current']).strip()
        
        return self._run_git(repo_path, ['pull', remote, branch])
    
    def get_diff(self, project_id: str, filepath: str = None) -> str:
        """Get diff for file or all changes"""
        project = self.project_repo.get_by_id(project_id)
        repo_path = Path(project.local_path)
        
        cmd = ['diff']
        if filepath:
            cmd.append(filepath)
        
        return self._run_git(repo_path, cmd)
    
    def get_log(self, project_id: str, limit: int = 10) -> List[Dict]:
        """Get commit history"""
        project = self.project_repo.get_by_id(project_id)
        repo_path = Path(project.local_path)
        
        log_output = self._run_git(repo_path, [
            'log',
            f'-{limit}',
            '--pretty=format:%H|%an|%ae|%at|%s'
        ])
        
        commits = []
        for line in log_output.split('\n'):
            if not line:
                continue
            hash, author, email, timestamp, message = line.split('|', 4)
            commits.append({
                'hash': hash,
                'author': author,
                'email': email,
                'timestamp': int(timestamp),
                'message': message
            })
        
        return commits
    
    def _run_git(self, repo_path: Path, args: List[str]) -> str:
        """Run git command"""
        import subprocess
        result = subprocess.run(
            [self.git_cmd, '-C', str(repo_path)] + args,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
```

**SSH Key Management**:
```python
class SSHKeyService:
    """Manage SSH keys per project"""
    
    def add_key(self, project_id: str, private_key: str,
               public_key: str = None):
        """Add SSH key for project"""
        project = self.project_repo.get_by_id(project_id)
        key_dir = Path(project.local_path) / '.ssh'
        key_dir.mkdir(exist_ok=True, mode=0o700)
        
        # Save private key
        private_key_path = key_dir / 'id_rsa'
        private_key_path.write_text(private_key)
        private_key_path.chmod(0o600)
        
        # Save public key if provided
        if public_key:
            public_key_path = key_dir / 'id_rsa.pub'
            public_key_path.write_text(public_key)
            public_key_path.chmod(0o644)
    
    def get_key(self, project_id: str) -> Dict:
        """Get SSH key for project"""
        project = self.project_repo.get_by_id(project_id)
        key_dir = Path(project.local_path) / '.ssh'
        
        private_key_path = key_dir / 'id_rsa'
        public_key_path = key_dir / 'id_rsa.pub'
        
        return {
            'private_key': private_key_path.read_text() if private_key_path.exists() else None,
            'public_key': public_key_path.read_text() if public_key_path.exists() else None
        }
```

---

## Ollama Integration Architecture

### Ollama Service

**Server Management**:
```python
class OllamaService:
    """Integrate with Ollama servers"""
    
    def __init__(self):
        self.servers = {}
    
    def add_server(self, name: str, host: str, port: int = 11434):
        """Add Ollama server"""
        self.servers[name] = {
            'host': host,
            'port': port,
            'base_url': f"http://{host}:{port}"
        }
    
    def test_connection(self, server_name: str) -> bool:
        """Test server connectivity"""
        import urllib.request
        server = self.servers[server_name]
        try:
            response = urllib.request.urlopen(
                f"{server['base_url']}/api/tags",
                timeout=5
            )
            return response.status == 200
        except:
            return False
    
    def list_models(self, server_name: str) -> List[Dict]:
        """List available models on server"""
        import urllib.request
        import json
        
        server = self.servers[server_name]
        response = urllib.request.urlopen(
            f"{server['base_url']}/api/tags"
        )
        data = json.loads(response.read())
        return data.get('models', [])
    
    def pull_model(self, server_name: str, model_name: str):
        """Pull model to server"""
        import urllib.request
        import json
        
        server = self.servers[server_name]
        data = json.dumps({'name': model_name}).encode('utf-8')
        
        req = urllib.request.Request(
            f"{server['base_url']}/api/pull",
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        response = urllib.request.urlopen(req)
        return response.read()
    
    def stream_chat(self, model: str, server: str,
                   messages: List[Dict]) -> Generator:
        """Stream chat response from Ollama"""
        import urllib.request
        import json
        
        server_config = self.servers[server]
        data = json.dumps({
            'model': model,
            'messages': messages,
            'stream': True
        }).encode('utf-8')
        
        req = urllib.request.Request(
            f"{server_config['base_url']}/api/chat",
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req) as response:
            for line in response:
                if line:
                    chunk = json.loads(line)
                    if 'message' in chunk:
                        yield chunk['message'].get('content', '')
```

**Model Configuration**:
```python
class ModelConfig:
    """Model configuration per project"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.config = self._load_config()
    
    def set_default_model(self, model: str, server: str):
        """Set default model for project"""
        self.config['default_model'] = model
        self.config['default_server'] = server
        self._save_config()
    
    def set_temperature(self, temperature: float):
        """Set default temperature"""
        self.config['temperature'] = temperature
        self._save_config()
    
    def get_config(self) -> Dict:
        """Get model configuration"""
        return self.config
```

---

## Frontend Architecture

### Component Structure

**Main Application**:
```javascript
class App {
    constructor() {
        this.api = new APIClient();
        this.router = new Router();
        this.state = new StateManager();
        
        this.components = {
            sidebar: new Sidebar(),
            dashboard: new Dashboard(),
            chat: new ChatInterface(),
            fileBrowser: new FileBrowser(),
            gitUI: new GitInterface(),
            editor: new CodeEditor()
        };
        
        this.init();
    }
    
    init() {
        this.router.init();
        this.loadUser();
        this.setupEventListeners();
    }
}
```

**Chat Interface Component**:
```javascript
class ChatInterface {
    constructor() {
        this.threads = [];
        this.currentThread = null;
        this.ws = null;
    }
    
    async sendMessage(message) {
        // Add user message to UI
        this.addMessage('user', message);
        
        // Stream response from server
        const response = await this.api.streamChat(
            this.currentThread.id,
            message,
            this.currentThread.model
        );
        
        let assistantMessage = '';
        for await (const chunk of response) {
            assistantMessage += chunk;
            this.updateStreamingMessage(assistantMessage);
        }
    }
    
    addMessage(role, content) {
        const messageEl = document.createElement('div');
        messageEl.className = `message message-${role}`;
        messageEl.innerHTML = this.renderMarkdown(content);
        document.getElementById('messages').appendChild(messageEl);
    }
    
    renderMarkdown(text) {
        // Custom markdown renderer
        return this.markdownRenderer.render(text);
    }
}
```

**File Browser Component**:
```javascript
class FileBrowser {
    constructor() {
        this.currentPath = '/';
        this.tree = null;
    }
    
    async loadTree(projectId) {
        this.tree = await this.api.getFileTree(projectId);
        this.render();
    }
    
    render() {
        const treeEl = document.getElementById('file-tree');
        treeEl.innerHTML = this.renderTree(this.tree);
    }
    
    renderTree(node, level = 0) {
        let html = '';
        const indent = '  '.repeat(level);
        
        if (node.type === 'directory') {
            html += `${indent}<div class="directory">📁 ${node.name}</div>`;
            for (const child of node.children) {
                html += this.renderTree(child, level + 1);
            }
        } else {
            html += `${indent}<div class="file" data-path="${node.path}">📄 ${node.name}</div>`;
        }
        
        return html;
    }
    
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('path', this.currentPath);
        
        await this.api.uploadFile(this.projectId, formData);
        await this.loadTree(this.projectId);
    }
}
```

**Git Interface Component**:
```javascript
class GitInterface {
    constructor() {
        this.status = null;
    }
    
    async loadStatus(projectId) {
        this.status = await this.api.getGitStatus(projectId);
        this.render();
    }
    
    render() {
        const statusEl = document.getElementById('git-status');
        statusEl.innerHTML = `
            <div class="git-branch">Branch: ${this.status.branch}</div>
            <div class="git-staged">Staged: ${this.status.staged.length}</div>
            <div class="git-unstaged">Unstaged: ${this.status.unstaged.length}</div>
            <div class="git-files">
                ${this.renderFiles()}
            </div>
        `;
    }
    
    async commit(message) {
        await this.api.gitCommit(this.projectId, message);
        await this.loadStatus(this.projectId);
    }
    
    async push() {
        await this.api.gitPush(this.projectId);
        this.showNotification('Pushed successfully');
    }
}
```

**Code Editor Component**:
```javascript
class CodeEditor {
    constructor() {
        this.content = '';
        this.language = 'python';
        this.highlighter = new SyntaxHighlighter();
    }
    
    load(filepath, content) {
        this.filepath = filepath;
        this.content = content;
        this.language = this.detectLanguage(filepath);
        this.render();
    }
    
    render() {
        const editorEl = document.getElementById('editor');
        editorEl.innerHTML = `
            <div class="editor-toolbar">
                <button onclick="editor.save()">Save</button>
                <button onclick="editor.download()">Download</button>
            </div>
            <div class="editor-content">
                <textarea id="code-input">${this.content}</textarea>
            </div>
        `;
        
        this.highlighter.highlight(document.getElementById('code-input'));
    }
    
    async save() {
        const content = document.getElementById('code-input').value;
        await this.api.saveFile(this.projectId, this.filepath, content);
        this.showNotification('Saved successfully');
    }
}
```

---

## API Design Extensions

### Chat Endpoints

```
POST   /api/v1/threads                      # Create new thread
GET    /api/v1/threads                      # List threads
GET    /api/v1/threads/{id}                 # Get thread details
PUT    /api/v1/threads/{id}                 # Update thread
DELETE /api/v1/threads/{id}                 # Delete thread
POST   /api/v1/threads/{id}/assign          # Assign to project

POST   /api/v1/threads/{id}/messages        # Send message
GET    /api/v1/threads/{id}/messages        # Get messages
GET    /api/v1/threads/{id}/stream          # Stream response (SSE)
```

### File Management Endpoints

```
GET    /api/v1/projects/{id}/files          # List files
GET    /api/v1/projects/{id}/files/tree     # Get file tree
POST   /api/v1/projects/{id}/files/upload   # Upload file
GET    /api/v1/projects/{id}/files/download # Download file
POST   /api/v1/projects/{id}/files/zip      # Create project zip
DELETE /api/v1/projects/{id}/files/{path}   # Delete file
PUT    /api/v1/projects/{id}/files/{path}   # Update file
```

### Git Endpoints

```
GET    /api/v1/projects/{id}/git/status     # Get git status
POST   /api/v1/projects/{id}/git/stage      # Stage files
POST   /api/v1/projects/{id}/git/commit     # Commit changes
POST   /api/v1/projects/{id}/git/push       # Push to remote
POST   /api/v1/projects/{id}/git/pull       # Pull from remote
GET    /api/v1/projects/{id}/git/log        # Get commit history
GET    /api/v1/projects/{id}/git/diff       # Get diff
POST   /api/v1/projects/{id}/git/keys       # Add SSH key
GET    /api/v1/projects/{id}/git/keys       # Get SSH key
```

### Server Management Endpoints

```
GET    /api/v1/servers                      # List servers
POST   /api/v1/servers                      # Add server
PUT    /api/v1/servers/{id}                 # Update server
DELETE /api/v1/servers/{id}                 # Delete server
GET    /api/v1/servers/{id}/test            # Test connection
GET    /api/v1/servers/{id}/models          # List models
POST   /api/v1/servers/{id}/models/pull     # Pull model
```

### Prompt Management Endpoints

```
GET    /api/v1/prompts                      # List prompts
POST   /api/v1/prompts                      # Create prompt
GET    /api/v1/prompts/{id}                 # Get prompt
PUT    /api/v1/prompts/{id}                 # Update prompt
DELETE /api/v1/prompts/{id}                 # Delete prompt
POST   /api/v1/prompts/{id}/test            # Test prompt
```

---

## Conclusion

This architecture provides a comprehensive project management platform with:
- ✅ **Real-time AI Chat** - Streaming responses with thread management
- ✅ **Complete File Management** - Upload, download, edit, browse
- ✅ **Full Git Integration** - Status, commit, push, pull, SSH keys
- ✅ **Ollama Management** - Server and model configuration
- ✅ **Prompt Engineering** - Custom prompt creation and testing
- ✅ **Project Analysis** - MASTER_PLAN parsing and gap analysis
- ✅ **Modern UI** - Responsive, tabbed interface
- ✅ **Custom Implementation** - No external framework dependencies

**Ready for implementation following project1_MASTER_PLAN.md objectives.**

---

**Document Version**: 3.0.0  
**Created**: 2024-12-30  
**Updated**: 2024-12-30  
**Status**: Design Complete - Ready for Development
