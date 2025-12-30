# PROJECT 1 MASTER PLAN: AI-Powered Project Management & Development Platform

> **Project Type**: Web Application (Custom WSGI + Apache)  
> **Purpose**: Comprehensive project management platform with AI-powered analysis and chat interface  
> **Focus**: Project planning, code analysis, AI chat, file management, git integration, and intelligent recommendations  
> **Independence**: Completely separate from autonomy pipeline  
> **Implementation**: Custom code using Python standard library only

---

## Vision

Build a comprehensive web-based project management platform that combines:
- **AI Chat Interface** - Real-time conversations with Ollama models
- **Project Management** - Complete project lifecycle management
- **Code Analysis** - Deep analysis of MASTER_PLAN.md and source code
- **File Management** - Upload, download, navigate, and edit project files
- **Git Integration** - Full git operations (status, commit, push, pull)
- **Model Management** - Configure Ollama servers and models per project
- **Prompt Engineering** - Create and manage custom prompts
- **Thread Management** - Organize conversations by project and topic

This system serves as a **complete development environment** with AI assistance, providing strategic planning, code analysis, and interactive development support through a modern web interface.

---

## Primary Objectives

### 1. AI Chat Interface
**Goal**: Real-time conversational interface with Ollama models

**Capabilities**:
- Live streaming responses from Ollama models
- Multiple conversation threads per project
- Thread assignment to specific projects
- Conversation history and search
- Model selection per conversation
- Temperature and parameter controls
- Tool calling support in chat
- Code highlighting in responses
- Markdown rendering
- File attachments in chat
- Export conversations

**Technical Approach**:
- WebSocket or Server-Sent Events (SSE) for streaming
- Custom chat UI with HTML5/CSS/JavaScript
- Real-time token streaming from Ollama
- Thread management with database storage
- Message persistence and retrieval

### 2. Project Management System
**Goal**: Complete project lifecycle management

**Capabilities**:
- Create new projects
- Project dashboard with status overview
- Project settings and configuration
- Objective tracking (primary/secondary/tertiary)
- Task management and assignment
- Progress visualization
- Project templates
- Multi-project support
- Project archiving and deletion
- Project search and filtering

**Technical Approach**:
- Project model with full metadata
- Dashboard with real-time updates
- Objective hierarchy management
- Progress calculation algorithms
- Template system for common project types

### 3. File Management System
**Goal**: Complete file operations within projects

**Capabilities**:
- File browser with tree view
- Create new files and directories
- Upload files (individual or zip)
- Download files (individual or project zip)
- File editing with syntax highlighting
- File preview (code, markdown, images)
- File search within project
- File history and versions
- Drag-and-drop upload
- Bulk operations
- File permissions

**Technical Approach**:
- Custom file browser UI
- File upload/download handlers
- Zip file creation and extraction
- Syntax highlighting with custom JavaScript
- File watcher for changes
- Temporary file storage

### 4. Git Integration
**Goal**: Full git operations within the platform

**Capabilities**:
- View git status
- Stage and unstage files
- Commit with messages
- Push to remote
- Pull from remote
- Branch management
- View commit history
- Diff viewer
- Merge conflict resolution
- Add remote repositories
- SSH key management per project
- Private git server support
- Clone repositories

**Technical Approach**:
- Git operations using subprocess
- Custom git UI components
- SSH key storage and management
- Remote repository configuration
- Diff visualization
- Conflict resolution interface

### 5. Ollama Server & Model Management
**Goal**: Configure and manage Ollama servers and models

**Capabilities**:
- Add/edit/remove Ollama servers
- Test server connectivity
- List available models per server
- Pull new models
- Delete models
- Set default models per project
- Model performance monitoring
- Server load balancing
- Fallback model configuration
- Model capabilities tagging
- Temperature settings per model

**Technical Approach**:
- Server configuration storage
- Ollama API integration
- Model discovery and listing
- Health check system
- Load balancing algorithms
- Configuration per project

### 6. Prompt Management System
**Goal**: Create, edit, and manage custom prompts

**Capabilities**:
- Browse existing prompts
- Create new prompts
- Edit prompt templates
- Test prompts with models
- Prompt versioning
- Prompt categories
- Import/export prompts
- Prompt variables and templates
- Prompt effectiveness tracking
- Share prompts between projects

**Technical Approach**:
- Prompt storage in database
- Template variable system
- Version control for prompts
- Testing interface
- Analytics on prompt usage

### 7. MASTER_PLAN Analysis Engine
**Goal**: Deep understanding of project planning documents

**Capabilities**:
- Parse MASTER_PLAN.md files
- Extract objective hierarchies
- Identify acceptance criteria
- Extract dependencies and blockers
- Parse task lists and checklists
- Understand project phases
- Extract success criteria
- Validate structure
- Generate objective reports

**Technical Approach**:
- Custom markdown parser using regex
- Objective extraction algorithms
- Hierarchical data model
- Validation rules
- Report generation

### 8. Source Code Analysis Engine
**Goal**: Understand actual project implementation

**Capabilities**:
- Recursive directory traversal
- Multi-language file analysis (Python, JavaScript, HTML, CSS)
- AST parsing for Python using `ast` module
- Import/dependency graph generation
- Function/class inventory
- Complexity metrics
- Test coverage estimation
- Documentation coverage
- Architecture pattern detection
- Code quality metrics

**Technical Approach**:
- Use `ast` module for Python
- Custom parsers for other languages
- Build comprehensive project model
- Store analysis results in database

### 9. Gap Analysis Engine
**Goal**: Compare planned vs. actual implementation

**Capabilities**:
- Match objectives to implemented features
- Identify missing implementations
- Detect partially completed objectives
- Find over-implemented features
- Calculate completion percentages
- Estimate remaining work
- Identify technical debt
- Detect architectural mismatches
- Generate gap reports

**Technical Approach**:
- Semantic matching algorithms
- Keyword extraction and matching
- File path pattern matching
- Function/class name analysis
- Confidence scoring

### 10. Recommendation Engine
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
- Generate implementation plans

**Technical Approach**:
- Rule-based recommendation system
- Priority scoring algorithms
- Dependency-aware scheduling
- Risk assessment
- Effort estimation
- Impact analysis

### 11. Analysis Dashboard
**Goal**: Visualize project status and metrics

**Capabilities**:
- Project overview dashboard
- Objective completion charts
- Code quality metrics
- Complexity trends
- Gap analysis visualization
- Recommendation priority matrix
- Progress over time graphs
- Team velocity metrics
- Risk indicators

**Technical Approach**:
- Custom charting with JavaScript
- Real-time data updates
- Interactive visualizations
- Export to PDF/PNG

### 12. User Interface Components
**Goal**: Modern, responsive web interface

**Capabilities**:
- Responsive design (desktop, tablet, mobile)
- Dark/light theme toggle
- Tabbed interface for different views
- Split-pane layouts
- Drag-and-drop support
- Keyboard shortcuts
- Context menus
- Modal dialogs
- Toast notifications
- Loading indicators
- Progress bars

**Technical Approach**:
- Custom HTML5/CSS3
- Vanilla JavaScript (no frameworks)
- CSS Grid and Flexbox
- Local storage for preferences
- Service workers for offline support

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
│   │   ├── websocket.py            # WebSocket support for chat
│   │   └── middleware.py           # Middleware stack
│   ├── auth/
│   │   ├── jwt_handler.py          # Custom JWT implementation
│   │   ├── api_keys.py             # API key management
│   │   ├── session.py              # Session management
│   │   └── rbac.py                 # Role-based access control
│   ├── database/
│   │   ├── connection.py           # Database connection manager
│   │   ├── sqlite_adapter.py       # SQLite implementation
│   │   ├── mysql_adapter.py        # MySQL implementation (optional)
│   │   ├── query_builder.py        # SQL query builder
│   │   └── migrations.py           # Schema migrations
│   ├── models/
│   │   ├── base.py                 # Base model class
│   │   ├── user.py                 # User model
│   │   ├── project.py              # Project model
│   │   ├── objective.py            # Objective model
│   │   ├── thread.py               # Conversation thread model
│   │   ├── message.py              # Chat message model
│   │   ├── file.py                 # File metadata model
│   │   ├── server.py               # Ollama server model
│   │   ├── prompt.py               # Prompt template model
│   │   ├── analysis.py             # Analysis result model
│   │   ├── recommendation.py       # Recommendation model
│   │   └── snapshot.py             # Snapshot model
│   ├── repositories/
│   │   ├── base.py                 # Base repository
│   │   ├── user_repo.py            # User repository
│   │   ├── project_repo.py         # Project repository
│   │   ├── thread_repo.py          # Thread repository
│   │   ├── message_repo.py         # Message repository
│   │   ├── file_repo.py            # File repository
│   │   ├── server_repo.py          # Server repository
│   │   ├── prompt_repo.py          # Prompt repository
│   │   └── analysis_repo.py        # Analysis repository
│   ├── services/
│   │   ├── chat_service.py         # Chat orchestration
│   │   ├── ollama_service.py       # Ollama API integration
│   │   ├── project_service.py      # Project management
│   │   ├── file_service.py         # File operations
│   │   ├── git_service.py          # Git operations
│   │   ├── analysis_service.py     # Analysis orchestration
│   │   └── prompt_service.py       # Prompt management
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
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py             # Authentication endpoints
│   │       ├── projects.py         # Project endpoints
│   │       ├── files.py            # File management endpoints
│   │       ├── chat.py             # Chat endpoints
│   │       ├── threads.py          # Thread management endpoints
│   │       ├── git.py              # Git operation endpoints
│   │       ├── servers.py          # Server management endpoints
│   │       ├── models.py           # Model management endpoints
│   │       ├── prompts.py          # Prompt management endpoints
│   │       ├── analysis.py         # Analysis endpoints
│   │       ├── objectives.py       # Objective endpoints
│   │       └── recommendations.py  # Recommendation endpoints
│   ├── utils/
│   │   ├── pagination.py           # Pagination helper
│   │   ├── filtering.py            # Query filtering
│   │   ├── sorting.py              # Result sorting
│   │   ├── rate_limiter.py         # Rate limiting
│   │   ├── file_utils.py           # File utilities
│   │   └── git_utils.py            # Git utilities
│   └── config.py                   # Configuration management
├── frontend/
│   ├── index.html                  # Main application page
│   ├── css/
│   │   ├── main.css                # Main stylesheet
│   │   ├── components.css          # Component styles
│   │   ├── chat.css                # Chat interface styles
│   │   ├── editor.css              # Code editor styles
│   │   ├── dashboard.css           # Dashboard styles
│   │   └── responsive.css          # Responsive design
│   ├── js/
│   │   ├── app.js                  # Main application
│   │   ├── api.js                  # API client
│   │   ├── chat.js                 # Chat interface
│   │   ├── editor.js               # Code editor
│   │   ├── file-browser.js         # File browser
│   │   ├── git-ui.js               # Git interface
│   │   ├── dashboard.js            # Dashboard
│   │   ├── components.js           # UI components
│   │   ├── markdown.js             # Markdown renderer
│   │   ├── syntax-highlighter.js   # Syntax highlighting
│   │   └── utils.js                # Utility functions
│   └── assets/
│       ├── images/                 # Images and icons
│       └── fonts/                  # Custom fonts
├── deployment/
│   ├── apache/
│   │   ├── http.conf               # HTTP vhost config
│   │   └── https.conf              # HTTPS vhost config
│   ├── wsgi.py                     # WSGI entry point
│   └── requirements.txt            # Minimal dependencies
├── tests/
│   ├── test_auth.py
│   ├── test_chat.py
│   ├── test_file_management.py
│   ├── test_git.py
│   ├── test_analyzers.py
│   └── test_api.py
└── scripts/
    ├── setup_db.py                 # Database setup
    ├── create_admin.py             # Create admin user
    └── migrate.py                  # Run migrations
```

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

### Projects Table
```sql
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    local_path TEXT,
    git_url TEXT,
    git_branch TEXT DEFAULT 'main',
    default_model TEXT,
    default_server TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_analyzed TIMESTAMP,
    status TEXT DEFAULT 'active',
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Threads Table
```sql
CREATE TABLE threads (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    model TEXT,
    server TEXT,
    temperature REAL DEFAULT 0.7,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Messages Table
```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL,
    role TEXT NOT NULL,  -- user, assistant, system
    content TEXT NOT NULL,
    model TEXT,
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (thread_id) REFERENCES threads(id)
);
```

### Files Table
```sql
CREATE TABLE files (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    path TEXT NOT NULL,
    name TEXT NOT NULL,
    size INTEGER,
    mime_type TEXT,
    hash TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

### Servers Table
```sql
CREATE TABLE servers (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    host TEXT NOT NULL,
    port INTEGER DEFAULT 11434,
    capabilities TEXT,  -- JSON array
    online BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Prompts Table
```sql
CREATE TABLE prompts (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    category TEXT,
    template TEXT NOT NULL,
    variables TEXT,  -- JSON array
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
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
    analysis_type TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    results JSON,
    FOREIGN KEY (project_id) REFERENCES projects(id)
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
    effort TEXT,
    impact TEXT,
    status TEXT DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);
```

---

## User Interface Layout

### Main Application Layout
```
┌─────────────────────────────────────────────────────────────┐
│  Header: Logo | Project Selector | User Menu               │
├─────────────────────────────────────────────────────────────┤
│ Sidebar          │  Main Content Area                       │
│                  │                                           │
│ • Dashboard      │  ┌─────────────────────────────────────┐ │
│ • Chat           │  │  Tab Bar: Dashboard | Chat | Files  │ │
│ • Files          │  ├─────────────────────────────────────┤ │
│ • Analysis       │  │                                     │ │
│ • Objectives     │  │  Content based on selected tab      │ │
│ • Git            │  │                                     │ │
│ • Servers        │  │                                     │ │
│ • Prompts        │  │                                     │ │
│ • Settings       │  │                                     │ │
│                  │  └─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Chat Interface
```
┌─────────────────────────────────────────────────────────────┐
│  Thread List     │  Chat Area                               │
│                  │                                           │
│  ┌────────────┐  │  ┌─────────────────────────────────────┐ │
│  │ Thread 1   │  │  │ User: How do I implement auth?      │ │
│  │ Thread 2   │  │  │ Assistant: Here's how...            │ │
│  │ + New      │  │  │ [Code block with syntax highlight]  │ │
│  └────────────┘  │  └─────────────────────────────────────┘ │
│                  │  ┌─────────────────────────────────────┐ │
│                  │  │ [Type message...]        [Send]     │ │
│                  │  │ Model: qwen2.5-coder:32b  Temp: 0.7 │ │
│                  │  └─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### File Browser
```
┌─────────────────────────────────────────────────────────────┐
│  Tree View       │  File Content / Editor                   │
│                  │                                           │
│  📁 project/     │  ┌─────────────────────────────────────┐ │
│    📁 src/       │  │ Line numbers | Code with syntax     │ │
│      📄 main.py  │  │ highlighting                        │ │
│      📄 utils.py │  │                                     │ │
│    📁 tests/     │  │ [Edit] [Save] [Download]            │ │
│    📄 README.md  │  └─────────────────────────────────────┘ │
│                  │                                           │
│  [Upload] [New]  │  [Search files...]                       │
└─────────────────────────────────────────────────────────────┘
```

### Git Interface
```
┌─────────────────────────────────────────────────────────────┐
│  Status          │  Diff Viewer                             │
│                  │                                           │
│  Branch: main    │  ┌─────────────────────────────────────┐ │
│  ✓ 3 staged      │  │ - old line                          │ │
│  ✗ 2 unstaged    │  │ + new line                          │ │
│                  │  │                                     │ │
│  Modified:       │  └─────────────────────────────────────┘ │
│  □ file1.py      │                                           │
│  ☑ file2.py      │  Commit Message:                         │
│                  │  [Implement feature X]                   │
│  [Commit] [Push] │  [Commit] [Push] [Pull]                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Features

### Real-Time Chat
- Streaming responses from Ollama
- Code syntax highlighting
- Markdown rendering
- File attachments
- Thread organization
- Search history

### Project Management
- Multi-project support
- Project templates
- Objective tracking
- Progress visualization
- Team collaboration

### File Operations
- Upload/download
- Zip import/export
- Syntax highlighting
- Code editing
- File search

### Git Integration
- Status viewing
- Commit/push/pull
- Branch management
- Diff viewer
- SSH key management

### Analysis Tools
- MASTER_PLAN parsing
- Source code analysis
- Gap detection
- Recommendations
- Progress tracking

### Model Management
- Server configuration
- Model selection
- Performance monitoring
- Load balancing

### Prompt Engineering
- Custom prompts
- Template variables
- Version control
- Testing interface

---

## Success Criteria

1. **Chat Performance**: < 100ms response start time
2. **File Operations**: Handle 10,000+ files per project
3. **Analysis Speed**: Analyze 10,000 LOC in < 30 seconds
4. **UI Responsiveness**: < 50ms interaction response
5. **Concurrent Users**: Support 100+ simultaneous users
6. **Uptime**: 99.9% availability
7. **Data Integrity**: Zero data loss
8. **Security**: Pass security audit

---

## Technology Stack

### Core (Python Standard Library Only)
- **wsgiref** - WSGI reference implementation
- **sqlite3** - SQLite database (default)
- **ast** - Python AST parsing
- **re** - Regular expressions
- **json** - JSON handling
- **hmac** - HMAC for JWT
- **hashlib** - Hashing
- **pathlib** - Path operations
- **subprocess** - Git operations
- **threading** - Concurrent operations
- **queue** - Message queuing

### Optional External
- **mysql-connector-python** - MySQL support (optional)

### Deployment
- **Apache 2.4+** - Web server with mod_wsgi
- **mod_wsgi** - WSGI interface for Apache

---

**Document Version**: 3.0.0  
**Created**: 2024-12-30  
**Updated**: 2024-12-30  
**Status**: Ready for Implementation