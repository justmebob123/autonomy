# PROJECT 2 MASTER PLAN: AI-Powered Debugging & Development Platform

> **Project Type**: Web Application (Custom WSGI + Apache)  
> **Purpose**: Comprehensive debugging, architecture analysis, and AI-assisted development  
> **Focus**: Bug detection, code quality, real-time AI assistance, and development workflow  
> **Independence**: Completely separate from autonomy pipeline  
> **Technology**: Python standard library only (no external frameworks)

---

## Vision

Build an intelligent web platform that combines **deep code analysis** with **AI-powered development assistance** to:
- **Detect** bugs before they reach production through advanced static analysis
- **Analyze** code architecture and identify design issues
- **Assist** developers with real-time AI chat for debugging and problem-solving
- **Manage** complete development workflow (files, git, models, prompts)
- **Measure** code quality metrics and complexity
- **Identify** refactoring opportunities and technical debt
- **Generate** call graphs, dependency diagrams, and visualizations
- **Recommend** architectural improvements with AI insights
- **Track** code quality evolution over time

This system serves as an **AI-powered debugging companion and code architect** that combines automated analysis with conversational AI assistance.

---

## Primary Objectives

### 1. AI Chat Interface for Debugging
**Goal**: Provide real-time AI assistance for debugging and development

**Capabilities**:
- **Real-time Chat** with Ollama models specialized in debugging
- **Code Context Awareness** - Chat understands current project and files
- **Bug Discussion** - Discuss detected bugs and get AI suggestions
- **Architecture Advice** - Get AI recommendations on design decisions
- **Thread Management** - Organize conversations by topic/feature
- **Thread-to-Project Assignment** - Link conversations to specific projects
- **Streaming Responses** - Real-time token streaming for better UX
- **Code Highlighting** - Syntax-highlighted code in chat messages
- **Markdown Rendering** - Rich formatting for explanations

**Technical Implementation**:
- WebSocket or Server-Sent Events (SSE) for streaming
- Custom message queue for async processing
- Thread persistence in database
- Integration with Ollama API
- Markdown parser for rendering
- Code syntax highlighter

**Use Cases**:
- "Why is this function causing a memory leak?"
- "How should I refactor this complex method?"
- "Explain this bug detection result"
- "What's the best way to implement this feature?"

### 2. File Management System
**Goal**: Complete file operations within the platform

**Capabilities**:
- **File Browser** with tree view navigation
- **File Upload** - Single files or entire project zips
- **File Download** - Individual files or project archives
- **File Editing** - In-browser code editor with syntax highlighting
- **File Creation** - Create new files and directories
- **File Deletion** - Remove files and directories
- **Drag-and-Drop** - Upload files via drag-and-drop
- **Bulk Operations** - Multi-file operations
- **Search** - Find files by name or content
- **File Preview** - View files without editing

**Technical Implementation**:
- Custom file tree builder
- File upload handler with chunking
- ZIP archive creation/extraction
- In-browser code editor (custom or CodeMirror-like)
- File system operations via Python `os` and `pathlib`
- Search using `grep` or custom indexing

### 3. Git Integration
**Goal**: Complete git workflow within the platform

**Capabilities**:
- **Git Status** - View modified, staged, untracked files
- **Stage Files** - Add files to staging area
- **Commit** - Create commits with messages
- **Push** - Push to remote repositories
- **Pull** - Pull latest changes
- **Branch Management** - Create, switch, delete branches
- **Diff Viewer** - View file differences
- **Commit History** - Browse commit log
- **SSH Key Management** - Configure SSH keys per project
- **Private Git Server Support** - Connect to any git server

**Technical Implementation**:
- Git operations via `subprocess` module
- SSH key storage and management
- Diff parsing and rendering
- Git log parsing
- Branch visualization
- Conflict detection and display

### 4. Ollama Server & Model Management
**Goal**: Configure and manage AI models for analysis and chat

**Capabilities**:
- **Add Ollama Servers** - Configure multiple Ollama instances
- **Edit Server Settings** - Update server URLs and credentials
- **Remove Servers** - Delete server configurations
- **List Models** - View available models on each server
- **Pull Models** - Download new models
- **Set Default Models** - Configure default model per project
- **Server Health Monitoring** - Check server availability
- **Load Balancing** - Distribute requests across servers
- **Model Testing** - Test models with sample prompts

**Technical Implementation**:
- Ollama API integration via `urllib` or `http.client`
- Server health checks with timeouts
- Model metadata storage
- Load balancing algorithm
- Connection pooling

### 5. Prompt Management
**Goal**: Create and manage custom prompts for debugging and analysis

**Capabilities**:
- **Create Prompts** - Design custom prompts for specific tasks
- **Edit Prompts** - Modify existing prompts
- **Prompt Templates** - Use variables in prompts
- **Test Prompts** - Try prompts with different models
- **Prompt Library** - Pre-built prompts for common tasks
- **Version Control** - Track prompt changes over time
- **Prompt Sharing** - Export/import prompts
- **Context Injection** - Automatically inject code context

**Technical Implementation**:
- Prompt storage in database
- Template variable substitution
- Prompt versioning system
- Context extraction from code
- Prompt testing interface

**Example Prompts**:
- "Analyze this function for potential bugs"
- "Suggest refactorings for this class"
- "Explain this architecture pattern"
- "Review this code for security issues"

### 6. Project Management
**Goal**: Manage multiple projects with comprehensive dashboards

**Capabilities**:
- **Multi-Project Support** - Work with multiple codebases
- **Project Dashboard** - Overview of project health
- **Objective Tracking** - Track primary/secondary/tertiary objectives
- **Progress Visualization** - Charts and graphs of progress
- **Task Management** - Create and track development tasks
- **Quality Metrics** - Real-time quality scores
- **Bug Tracking** - Monitor detected bugs
- **Complexity Trends** - Track complexity over time

**Technical Implementation**:
- Project metadata storage
- Objective hierarchy management
- Progress calculation algorithms
- Chart generation (custom or Chart.js-like)
- Dashboard aggregation queries

### 7. Bug Detection Engine
**Goal**: Identify bugs through advanced static analysis

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

**AI Integration**:
- Discuss bugs with AI in chat
- Get AI explanations of bug causes
- Receive AI suggestions for fixes
- Ask follow-up questions about bugs

### 8. Complexity Analysis Engine
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

**AI Integration**:
- Ask AI about complexity hotspots
- Get refactoring suggestions from AI
- Discuss complexity reduction strategies

### 9. Architecture Analysis Engine
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

**AI Integration**:
- Discuss architecture with AI
- Get AI recommendations on design
- Ask about architectural patterns
- Receive refactoring suggestions

### 10. Dead Code Detection Engine
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

### 11. Integration Gap Finder
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

### 12. Refactoring Recommendation Engine
**Goal**: Suggest code improvements with AI assistance

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
- Pattern-based detection
- Complexity-driven recommendations
- AI-powered suggestion generation
- Priority scoring algorithm

**AI Integration**:
- Discuss refactorings with AI
- Get detailed implementation steps
- Ask about trade-offs and risks
- Receive code examples

---

## Core Data Models

### 1. Bug Detection

```python
@dataclass
class Bug:
    id: str
    type: str  # use_before_def, missing_handling, etc.
    severity: str  # critical, high, medium, low
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

### Users Table
```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
```

### Projects Table
```sql
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    repository_url TEXT,
    local_path TEXT,
    language TEXT DEFAULT 'python',
    default_model TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_analyzed TIMESTAMP,
    status TEXT DEFAULT 'active',
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_projects_user ON projects(user_id);
CREATE INDEX idx_projects_status ON projects(status);
```

### Threads Table (Chat)
```sql
CREATE TABLE threads (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_threads_project ON threads(project_id);
CREATE INDEX idx_threads_user ON threads(user_id);
```

### Messages Table (Chat)
```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    model TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tokens INTEGER,
    FOREIGN KEY (thread_id) REFERENCES threads(id)
);

CREATE INDEX idx_messages_thread ON messages(thread_id);
CREATE INDEX idx_messages_created ON messages(created_at);
```

### Files Table
```sql
CREATE TABLE files (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    path TEXT NOT NULL,
    size INTEGER,
    modified_at TIMESTAMP,
    content_hash TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE INDEX idx_files_project ON files(project_id);
CREATE INDEX idx_files_path ON files(path);
```

### Servers Table (Ollama)
```sql
CREATE TABLE servers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    api_key TEXT,
    is_active BOOLEAN DEFAULT 1,
    last_health_check TIMESTAMP,
    health_status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_servers_active ON servers(is_active);
```

### Prompts Table
```sql
CREATE TABLE prompts (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    variables TEXT,  -- JSON array of variable names
    category TEXT,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_prompts_user ON prompts(user_id);
CREATE INDEX idx_prompts_category ON prompts(category);
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

CREATE INDEX idx_analyses_project ON analyses(project_id);
CREATE INDEX idx_analyses_status ON analyses(status);
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

CREATE INDEX idx_bugs_analysis ON bugs(analysis_id);
CREATE INDEX idx_bugs_severity ON bugs(severity);
CREATE INDEX idx_bugs_status ON bugs(status);
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

CREATE INDEX idx_complexity_analysis ON complexity_metrics(analysis_id);
CREATE INDEX idx_complexity_file ON complexity_metrics(file);
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

CREATE INDEX idx_refactorings_analysis ON refactorings(analysis_id);
CREATE INDEX idx_refactorings_priority ON refactorings(priority);
CREATE INDEX idx_refactorings_status ON refactorings(status);
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

CREATE INDEX idx_snapshots_project ON quality_snapshots(project_id);
CREATE INDEX idx_snapshots_date ON quality_snapshots(snapshot_date);
```

---

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/me` - Get current user info

### Chat
- `GET /api/v1/threads` - List all threads
- `POST /api/v1/threads` - Create new thread
- `GET /api/v1/threads/{id}` - Get thread details
- `PUT /api/v1/threads/{id}` - Update thread
- `DELETE /api/v1/threads/{id}` - Delete thread
- `GET /api/v1/threads/{id}/messages` - Get thread messages
- `POST /api/v1/threads/{id}/messages` - Send message (streaming response)
- `GET /api/v1/threads/{id}/stream` - SSE endpoint for streaming

### Projects
- `GET /api/v1/projects` - List all projects
- `POST /api/v1/projects` - Create new project
- `GET /api/v1/projects/{id}` - Get project details
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project
- `GET /api/v1/projects/{id}/dashboard` - Get project dashboard

### Files
- `GET /api/v1/projects/{id}/files` - List project files (tree)
- `GET /api/v1/projects/{id}/files/{path}` - Get file content
- `POST /api/v1/projects/{id}/files` - Create new file
- `PUT /api/v1/projects/{id}/files/{path}` - Update file content
- `DELETE /api/v1/projects/{id}/files/{path}` - Delete file
- `POST /api/v1/projects/{id}/upload` - Upload files
- `GET /api/v1/projects/{id}/download` - Download project as ZIP
- `POST /api/v1/projects/{id}/search` - Search files

### Git
- `GET /api/v1/projects/{id}/git/status` - Get git status
- `POST /api/v1/projects/{id}/git/stage` - Stage files
- `POST /api/v1/projects/{id}/git/commit` - Create commit
- `POST /api/v1/projects/{id}/git/push` - Push to remote
- `POST /api/v1/projects/{id}/git/pull` - Pull from remote
- `GET /api/v1/projects/{id}/git/branches` - List branches
- `POST /api/v1/projects/{id}/git/branches` - Create branch
- `PUT /api/v1/projects/{id}/git/branches/{name}` - Switch branch
- `DELETE /api/v1/projects/{id}/git/branches/{name}` - Delete branch
- `GET /api/v1/projects/{id}/git/log` - Get commit history
- `GET /api/v1/projects/{id}/git/diff` - Get file diff

### Servers (Ollama)
- `GET /api/v1/servers` - List all servers
- `POST /api/v1/servers` - Add new server
- `GET /api/v1/servers/{id}` - Get server details
- `PUT /api/v1/servers/{id}` - Update server
- `DELETE /api/v1/servers/{id}` - Delete server
- `GET /api/v1/servers/{id}/models` - List available models
- `POST /api/v1/servers/{id}/models/pull` - Pull new model
- `GET /api/v1/servers/{id}/health` - Check server health

### Prompts
- `GET /api/v1/prompts` - List all prompts
- `POST /api/v1/prompts` - Create new prompt
- `GET /api/v1/prompts/{id}` - Get prompt details
- `PUT /api/v1/prompts/{id}` - Update prompt
- `DELETE /api/v1/prompts/{id}` - Delete prompt
- `POST /api/v1/prompts/{id}/test` - Test prompt with model

### Analysis
- `POST /api/v1/projects/{id}/analyze` - Trigger analysis
- `GET /api/v1/projects/{id}/analyses` - List analyses
- `GET /api/v1/projects/{id}/analyses/{aid}` - Get analysis details
- `GET /api/v1/projects/{id}/bugs` - Get detected bugs
- `GET /api/v1/projects/{id}/bugs/{bid}` - Get bug details
- `PUT /api/v1/projects/{id}/bugs/{bid}` - Update bug status
- `GET /api/v1/projects/{id}/complexity` - Get complexity metrics
- `GET /api/v1/projects/{id}/hotspots` - Get complexity hotspots
- `GET /api/v1/projects/{id}/architecture` - Get architecture analysis
- `GET /api/v1/projects/{id}/callgraph` - Get call graph
- `GET /api/v1/projects/{id}/dependencies` - Get dependency graph
- `GET /api/v1/projects/{id}/deadcode` - Get dead code report
- `GET /api/v1/projects/{id}/refactorings` - Get refactoring suggestions
- `PUT /api/v1/projects/{id}/refactorings/{rid}` - Update refactoring status
- `GET /api/v1/projects/{id}/quality` - Get quality metrics
- `GET /api/v1/projects/{id}/trends` - Get quality trends

---

## Technology Stack

### Core (Python Standard Library Only)
- **wsgiref** - WSGI server implementation
- **http.server** - HTTP request handling
- **urllib** - HTTP client for Ollama API
- **json** - JSON parsing and generation
- **sqlite3** - Database operations
- **hmac** - JWT token generation
- **hashlib** - Password hashing
- **pathlib** - File path operations
- **subprocess** - Git operations
- **ast** - Python AST parsing
- **threading** - Async operations
- **queue** - Message queuing

### Optional (Only if Needed)
- **mysql.connector** - MySQL support (if not using SQLite)

### Analysis Libraries (Adapt from autonomy)
- Custom implementations based on `bin/analysis/` scripts
- No external dependencies

### Deployment
- **Apache 2.4+** with mod_wsgi
- **HTTPS** with SSL certificates
- **systemd** for service management

---

## API Examples

### Register and Login
```bash
# Register
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "developer",
    "password": "secure_password",
    "email": "dev@example.com"
  }'

# Login
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "developer",
    "password": "secure_password"
  }'
# Returns: {"token": "eyJ0eXAiOiJKV1QiLCJhbGc..."}
```

### Create Project and Start Chat
```bash
# Create project
curl -X POST http://localhost:5000/api/v1/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Project",
    "local_path": "/path/to/project",
    "language": "python"
  }'

# Create chat thread
curl -X POST http://localhost:5000/api/v1/threads \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "proj_123",
    "title": "Debugging Session"
  }'

# Send message (streaming)
curl -X POST http://localhost:5000/api/v1/threads/thread_456/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Why is this function causing a memory leak?",
    "model": "qwen2.5-coder:32b"
  }'
```

### File Operations
```bash
# List files
curl http://localhost:5000/api/v1/projects/proj_123/files \
  -H "Authorization: Bearer $TOKEN"

# Get file content
curl http://localhost:5000/api/v1/projects/proj_123/files/src/main.py \
  -H "Authorization: Bearer $TOKEN"

# Update file
curl -X PUT http://localhost:5000/api/v1/projects/proj_123/files/src/main.py \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "def main():\n    print("Hello")"
  }'

# Upload files
curl -X POST http://localhost:5000/api/v1/projects/proj_123/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/file.py"
```

### Git Operations
```bash
# Get status
curl http://localhost:5000/api/v1/projects/proj_123/git/status \
  -H "Authorization: Bearer $TOKEN"

# Stage and commit
curl -X POST http://localhost:5000/api/v1/projects/proj_123/git/stage \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"files": ["src/main.py"]}'

curl -X POST http://localhost:5000/api/v1/projects/proj_123/git/commit \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Fix memory leak"}'

# Push
curl -X POST http://localhost:5000/api/v1/projects/proj_123/git/push \
  -H "Authorization: Bearer $TOKEN"
```

### Analysis Operations
```bash
# Trigger analysis
curl -X POST http://localhost:5000/api/v1/projects/proj_123/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "full",
    "include_bugs": true,
    "include_complexity": true,
    "include_architecture": true
  }'

# Get bugs
curl http://localhost:5000/api/v1/projects/proj_123/bugs?severity=critical \
  -H "Authorization: Bearer $TOKEN"

# Get complexity hotspots
curl http://localhost:5000/api/v1/projects/proj_123/hotspots?limit=10 \
  -H "Authorization: Bearer $TOKEN"

# Get refactoring suggestions
curl http://localhost:5000/api/v1/projects/proj_123/refactorings?priority_min=70 \
  -H "Authorization: Bearer $TOKEN"
```

---

## Success Criteria

1. **Accuracy**: 95%+ accuracy in bug detection (< 5% false positives)
2. **Performance**: Analyze 10,000 LOC in < 60 seconds
3. **Coverage**: Detect all 8 bug patterns with high confidence
4. **API**: 99.9% uptime, < 300ms average response time
5. **Chat**: < 2s first token latency, smooth streaming
6. **Completeness**: Analyze 95%+ of Python language features
7. **Reliability**: Handle edge cases gracefully, no crashes
8. **Usability**: Intuitive UI, < 5 minute learning curve

---

## Key Differentiators

### From Autonomy Pipeline
1. **Web Platform** - Full web application, not CLI tool
2. **External Analysis** - Analyzes other projects, not self
3. **Debugging Focus** - Bug detection and analysis, not execution
4. **Read-Only** - Analyzes but doesn't modify code (except via file editor)
5. **Multi-Project** - Manages multiple projects simultaneously
6. **Historical** - Tracks quality over time
7. **Visualization** - Generates graphs and diagrams
8. **AI Chat** - Real-time conversational debugging assistance

### From Project 1
1. **Debugging Focus** - Advanced bug detection and analysis engines
2. **Code Quality** - Complexity metrics and quality tracking
3. **Architecture Analysis** - Call graphs, dependency analysis, pattern detection
4. **Refactoring** - Automated refactoring recommendations
5. **Technical Debt** - Track and visualize technical debt

---

## Notes for Development

1. **Custom Implementation** - Use only Python standard library (no Flask, FastAPI, SQLAlchemy)
2. **Adapt Existing Tools** - Reuse bin/analysis/ scripts as foundation
3. **Start with Python** - Focus on Python first, add other languages later
4. **Test-Driven** - Write tests alongside code
5. **Incremental** - Build detectors incrementally
6. **Document** - API docs and bug pattern catalog from day one
7. **Performance** - Profile and optimize hot paths
8. **Accuracy** - Minimize false positives through testing
9. **Security** - Implement proper authentication and authorization
10. **Streaming** - Use SSE or WebSocket for real-time chat

---

**Document Version**: 2.0.0  
**Created**: 2024-12-30  
**Updated**: 2024-12-30  
**Status**: Ready for Implementation
