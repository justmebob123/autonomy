# PROJECT 2 ARCHITECTURE: AI-Powered Debugging & Development Platform

> **Companion Document**: See `project2_MASTER_PLAN.md` for objectives and requirements  
> **Purpose**: Detailed technical architecture and implementation specifications  
> **Technology**: Python standard library only (no external frameworks)  
> **Status**: Design Document - Ready for Implementation

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Patterns](#architecture-patterns)
3. [Component Design](#component-design)
4. [Frontend Architecture](#frontend-architecture)
5. [Backend Architecture](#backend-architecture)
6. [Analysis Algorithms](#analysis-algorithms)
7. [API Design](#api-design)
8. [Database Design](#database-design)
9. [Security Architecture](#security-architecture)
10. [Performance Architecture](#performance-architecture)
11. [Deployment Architecture](#deployment-architecture)

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│              (Web Browser - HTML/CSS/JavaScript)                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTPS/REST + WebSocket/SSE
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      API Gateway Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Auth/JWT     │  │ Rate Limiter │  │ Validator    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    Application Layer                             │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │         Custom WSGI Application (Python stdlib)              ││
│  │  /auth  /chat  /files  /git  /servers  /prompts  /analysis  ││
│  └──────────────────────┬───────────────────────────────────────┘│
└─────────────────────────┼────────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────────┐
│                   Service Layer                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │   Chat   │  │   File   │  │   Git    │  │  Ollama  │        │
│  │ Service  │  │ Service  │  │ Service  │  │ Service  │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  Prompt  │  │ Project  │  │   Bug    │  │Complexity│        │
│  │ Service  │  │ Service  │  │ Detector │  │ Analyzer │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────┬────────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────────┐
│                    Analysis Engine Layer                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐         │
│  │   Bug    │  │Complexity│  │Architecture│  │  Dead   │         │
│  │ Detector │  │ Analyzer │  │  Analyzer  │  │  Code   │         │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘         │
└─────────────────────────┬────────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────────┐
│                   Data Access Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Repositories │  │ DB Abstraction│  │ Graph Store  │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────┬────────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────────┐
│                   Persistence Layer                               │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │         SQLite Database (or MySQL) + NetworkX Graphs         ││
│  │  Users | Projects | Threads | Messages | Files | Servers    ││
│  │  Prompts | Analyses | Bugs | Complexity | Refactorings      ││
│  └──────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

### System Characteristics

- **Architecture Style**: Layered + Pipeline + Event-Driven
- **API Style**: RESTful + WebSocket/SSE for streaming
- **Frontend**: Custom HTML/CSS/JavaScript (no frameworks)
- **Backend**: Custom WSGI application (Python stdlib only)
- **Data Storage**: SQLite (or MySQL) + In-Memory Graphs
- **Deployment**: Apache + mod_wsgi
- **Analysis**: Static (AST-based)
- **Scalability**: Vertical (single instance)

---

## Architecture Patterns

### 1. Layered Architecture Pattern

**Purpose**: Separation of concerns across layers

**Layers**:
1. **Presentation Layer** - Frontend UI components
2. **API Layer** - REST endpoints and WebSocket handlers
3. **Service Layer** - Business logic and orchestration
4. **Analysis Layer** - Code analysis engines
5. **Data Access Layer** - Database operations
6. **Persistence Layer** - SQLite/MySQL storage

**Benefits**:
- Clear separation of concerns
- Easy to test each layer independently
- Can replace layers without affecting others
- Maintainable and scalable

### 2. Pipeline Pattern

**Purpose**: Sequential analysis stages

```python
class AnalysisPipeline:
    """Pipeline for code analysis"""
    
    def __init__(self):
        self.stages = [
            FileScanner(),
            ASTParser(),
            SymbolExtractor(),
            BugDetector(),
            ComplexityAnalyzer(),
            ArchitectureAnalyzer(),
            RefactoringEngine()
        ]
    
    def execute(self, project_path: Path) -> AnalysisResult:
        """Execute pipeline"""
        context = AnalysisContext(project_path)
        
        for stage in self.stages:
            context = stage.process(context)
            if context.has_errors():
                break
        
        return context.get_result()
```

### 3. Repository Pattern

**Purpose**: Abstract data access

```python
class BugRepository:
    """Repository for bug data"""
    
    def __init__(self, db):
        self.db = db
    
    def find_by_analysis(self, analysis_id: str) -> List[Bug]:
        """Find bugs by analysis ID"""
        pass
    
    def find_by_severity(self, severity: str) -> List[Bug]:
        """Find bugs by severity"""
        pass
    
    def save(self, bug: Bug) -> None:
        """Save bug"""
        pass
```

### 4. Service Pattern

**Purpose**: Business logic encapsulation

```python
class ChatService:
    """Service for chat operations"""
    
    def __init__(self, thread_repo, message_repo, ollama_client):
        self.thread_repo = thread_repo
        self.message_repo = message_repo
        self.ollama_client = ollama_client
    
    def send_message(self, thread_id: str, content: str, 
                     model: str) -> Generator[str, None, None]:
        """Send message and stream response"""
        # Save user message
        user_msg = Message(thread_id=thread_id, role='user', 
                          content=content)
        self.message_repo.save(user_msg)
        
        # Get thread history
        history = self.message_repo.find_by_thread(thread_id)
        
        # Stream response from Ollama
        response_content = ""
        for chunk in self.ollama_client.chat(model, history):
            response_content += chunk
            yield chunk
        
        # Save assistant message
        assistant_msg = Message(thread_id=thread_id, role='assistant',
                               content=response_content, model=model)
        self.message_repo.save(assistant_msg)
```

### 5. Visitor Pattern

**Purpose**: AST traversal for analysis

```python
class BugDetectorVisitor(ast.NodeVisitor):
    """Visitor for bug detection"""
    
    def __init__(self):
        self.bugs = []
        self.symbol_table = SymbolTable()
    
    def visit_FunctionDef(self, node):
        """Visit function definition"""
        self._check_missing_return(node)
        self._check_infinite_loop(node)
        self.generic_visit(node)
    
    def visit_Name(self, node):
        """Visit variable name"""
        if isinstance(node.ctx, ast.Load):
            self._check_use_before_def(node)
        self.generic_visit(node)
```

---

## Component Design

### 1. Frontend Components

#### 1.1 Chat Interface Component

**Purpose**: Real-time AI chat with streaming responses

**HTML Structure**:
```html
<div id="chat-container">
    <div id="chat-header">
        <h2 id="thread-title">Debugging Session</h2>
        <button id="new-thread-btn">New Thread</button>
    </div>
    <div id="chat-messages">
        <!-- Messages rendered here -->
    </div>
    <div id="chat-input-container">
        <textarea id="chat-input" placeholder="Ask a question..."></textarea>
        <button id="send-btn">Send</button>
    </div>
</div>
```

**JavaScript Implementation**:
```javascript
class ChatInterface {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.messages = [];
        this.currentThread = null;
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        document.getElementById('send-btn').addEventListener('click', () => {
            this.sendMessage();
        });
        
        document.getElementById('chat-input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                this.sendMessage();
            }
        });
    }
    
    async sendMessage() {
        const input = document.getElementById('chat-input');
        const content = input.value.trim();
        if (!content) return;
        
        // Add user message to UI
        this.addMessage('user', content);
        input.value = '';
        
        // Stream response from server
        const response = await fetch(`/api/v1/threads/${this.currentThread}/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.getToken()}`
            },
            body: JSON.stringify({
                content: content,
                model: this.getSelectedModel()
            })
        });
        
        // Handle streaming response
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let assistantMessage = '';
        
        // Create assistant message element
        const msgElement = this.createMessageElement('assistant', '');
        
        while (true) {
            const {done, value} = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            assistantMessage += chunk;
            msgElement.querySelector('.message-content').textContent = assistantMessage;
            this.scrollToBottom();
        }
    }
    
    addMessage(role, content) {
        const msgElement = this.createMessageElement(role, content);
        document.getElementById('chat-messages').appendChild(msgElement);
        this.scrollToBottom();
    }
    
    createMessageElement(role, content) {
        const div = document.createElement('div');
        div.className = `message message-${role}`;
        div.innerHTML = `
            <div class="message-header">${role === 'user' ? 'You' : 'AI'}</div>
            <div class="message-content">${this.renderMarkdown(content)}</div>
        `;
        return div;
    }
    
    renderMarkdown(text) {
        // Simple markdown rendering
        return text
            .replace(/```(\w+)?
([\s\S]*?)```/g, (match, lang, code) => {
                return `<pre><code class="language-${lang || 'text'}">${this.escapeHtml(code)}</code></pre>`;
            })
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            .replace(/\*([^*]+)\*/g, '<em>$1</em>');
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    scrollToBottom() {
        const messages = document.getElementById('chat-messages');
        messages.scrollTop = messages.scrollHeight;
    }
    
    getToken() {
        return localStorage.getItem('auth_token');
    }
    
    getSelectedModel() {
        return document.getElementById('model-select').value;
    }
}

// Initialize chat interface
const chat = new ChatInterface('chat-container');
```

**CSS Styling**:
```css
#chat-container {
    display: flex;
    flex-direction: column;
    height: 100vh;
    max-width: 1200px;
    margin: 0 auto;
}

#chat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid #ddd;
}

#chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
}

.message {
    margin-bottom: 1rem;
    padding: 1rem;
    border-radius: 8px;
}

.message-user {
    background-color: #e3f2fd;
    margin-left: 20%;
}

.message-assistant {
    background-color: #f5f5f5;
    margin-right: 20%;
}

.message-header {
    font-weight: bold;
    margin-bottom: 0.5rem;
}

.message-content {
    line-height: 1.6;
}

.message-content code {
    background-color: #f0f0f0;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
}

.message-content pre {
    background-color: #2d2d2d;
    color: #f8f8f2;
    padding: 1rem;
    border-radius: 5px;
    overflow-x: auto;
}

#chat-input-container {
    display: flex;
    padding: 1rem;
    border-top: 1px solid #ddd;
}

#chat-input {
    flex: 1;
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    resize: vertical;
    min-height: 60px;
}

#send-btn {
    margin-left: 1rem;
    padding: 0.5rem 2rem;
    background-color: #2196f3;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

#send-btn:hover {
    background-color: #1976d2;
}
```

#### 1.2 File Browser Component

**Purpose**: Navigate and manage project files

**JavaScript Implementation**:
```javascript
class FileBrowser {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.currentPath = '/';
        this.projectId = null;
        this.render();
    }
    
    async loadFiles(path = '/') {
        const response = await fetch(`/api/v1/projects/${this.projectId}/files?path=${path}`, {
            headers: {
                'Authorization': `Bearer ${this.getToken()}`
            }
        });
        const data = await response.json();
        return data.files;
    }
    
    async render() {
        const files = await this.loadFiles(this.currentPath);
        
        const html = `
            <div class="file-browser-header">
                <button onclick="fileBrowser.goUp()">↑ Up</button>
                <span class="current-path">${this.currentPath}</span>
                <button onclick="fileBrowser.refresh()">↻ Refresh</button>
            </div>
            <div class="file-tree">
                ${this.renderFileTree(files)}
            </div>
        `;
        
        this.container.innerHTML = html;
    }
    
    renderFileTree(files) {
        return files.map(file => {
            const icon = file.type === 'directory' ? '📁' : '📄';
            const onclick = file.type === 'directory' 
                ? `fileBrowser.openDirectory('${file.path}')`
                : `fileBrowser.openFile('${file.path}')`;
            
            return `
                <div class="file-item" onclick="${onclick}">
                    <span class="file-icon">${icon}</span>
                    <span class="file-name">${file.name}</span>
                    <span class="file-size">${this.formatSize(file.size)}</span>
                </div>
            `;
        }).join('');
    }
    
    async openFile(path) {
        const response = await fetch(`/api/v1/projects/${this.projectId}/files/${path}`, {
            headers: {
                'Authorization': `Bearer ${this.getToken()}`
            }
        });
        const data = await response.json();
        
        // Open file in editor
        editor.openFile(path, data.content);
    }
    
    async openDirectory(path) {
        this.currentPath = path;
        await this.render();
    }
    
    goUp() {
        const parts = this.currentPath.split('/').filter(p => p);
        parts.pop();
        this.currentPath = '/' + parts.join('/');
        this.render();
    }
    
    refresh() {
        this.render();
    }
    
    formatSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }
    
    getToken() {
        return localStorage.getItem('auth_token');
    }
}

const fileBrowser = new FileBrowser('file-browser-container');
```

#### 1.3 Code Editor Component

**Purpose**: Edit files with syntax highlighting

**JavaScript Implementation**:
```javascript
class CodeEditor {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.currentFile = null;
        this.content = '';
        this.render();
    }
    
    render() {
        const html = `
            <div class="editor-header">
                <span class="editor-filename">${this.currentFile || 'No file open'}</span>
                <button onclick="editor.save()">💾 Save</button>
                <button onclick="editor.close()">✖ Close</button>
            </div>
            <textarea id="editor-textarea" class="editor-content">${this.content}</textarea>
        `;
        
        this.container.innerHTML = html;
        this.setupEditor();
    }
    
    setupEditor() {
        const textarea = document.getElementById('editor-textarea');
        
        // Add syntax highlighting on input
        textarea.addEventListener('input', () => {
            this.content = textarea.value;
            this.highlightSyntax();
        });
        
        // Add tab key support
        textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                e.preventDefault();
                const start = textarea.selectionStart;
                const end = textarea.selectionEnd;
                textarea.value = textarea.value.substring(0, start) + '    ' + 
                               textarea.value.substring(end);
                textarea.selectionStart = textarea.selectionEnd = start + 4;
            }
        });
    }
    
    openFile(path, content) {
        this.currentFile = path;
        this.content = content;
        this.render();
    }
    
    async save() {
        if (!this.currentFile) return;
        
        const response = await fetch(`/api/v1/projects/${fileBrowser.projectId}/files/${this.currentFile}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.getToken()}`
            },
            body: JSON.stringify({
                content: this.content
            })
        });
        
        if (response.ok) {
            this.showNotification('File saved successfully');
        }
    }
    
    close() {
        this.currentFile = null;
        this.content = '';
        this.render();
    }
    
    highlightSyntax() {
        // Simple syntax highlighting (can be enhanced)
        // This is a placeholder - real implementation would use a proper highlighter
    }
    
    showNotification(message) {
        // Show notification to user
        alert(message);
    }
    
    getToken() {
        return localStorage.getItem('auth_token');
    }
}

const editor = new CodeEditor('editor-container');
```

#### 1.4 Git Interface Component

**Purpose**: Git operations within the platform

**JavaScript Implementation**:
```javascript
class GitInterface {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.projectId = null;
        this.render();
    }
    
    async render() {
        const status = await this.getStatus();
        
        const html = `
            <div class="git-header">
                <h3>Git Status</h3>
                <div class="git-actions">
                    <button onclick="gitInterface.pull()">⬇ Pull</button>
                    <button onclick="gitInterface.push()">⬆ Push</button>
                    <button onclick="gitInterface.refresh()">↻ Refresh</button>
                </div>
            </div>
            <div class="git-status">
                <div class="git-section">
                    <h4>Modified Files (${status.modified.length})</h4>
                    ${this.renderFileList(status.modified, 'modified')}
                </div>
                <div class="git-section">
                    <h4>Staged Files (${status.staged.length})</h4>
                    ${this.renderFileList(status.staged, 'staged')}
                </div>
                <div class="git-section">
                    <h4>Untracked Files (${status.untracked.length})</h4>
                    ${this.renderFileList(status.untracked, 'untracked')}
                </div>
            </div>
            <div class="git-commit">
                <textarea id="commit-message" placeholder="Commit message..."></textarea>
                <button onclick="gitInterface.commit()">Commit</button>
            </div>
        `;
        
        this.container.innerHTML = html;
    }
    
    renderFileList(files, type) {
        if (files.length === 0) {
            return '<p class="no-files">No files</p>';
        }
        
        return files.map(file => {
            const action = type === 'staged' ? 'unstage' : 'stage';
            return `
                <div class="git-file">
                    <span class="file-name">${file}</span>
                    <button onclick="gitInterface.${action}('${file}')">
                        ${action === 'stage' ? '+ Stage' : '- Unstage'}
                    </button>
                </div>
            `;
        }).join('');
    }
    
    async getStatus() {
        const response = await fetch(`/api/v1/projects/${this.projectId}/git/status`, {
            headers: {
                'Authorization': `Bearer ${this.getToken()}`
            }
        });
        return await response.json();
    }
    
    async stage(file) {
        await fetch(`/api/v1/projects/${this.projectId}/git/stage`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.getToken()}`
            },
            body: JSON.stringify({ files: [file] })
        });
        this.render();
    }
    
    async unstage(file) {
        await fetch(`/api/v1/projects/${this.projectId}/git/unstage`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.getToken()}`
            },
            body: JSON.stringify({ files: [file] })
        });
        this.render();
    }
    
    async commit() {
        const message = document.getElementById('commit-message').value;
        if (!message) {
            alert('Please enter a commit message');
            return;
        }
        
        await fetch(`/api/v1/projects/${this.projectId}/git/commit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.getToken()}`
            },
            body: JSON.stringify({ message })
        });
        
        document.getElementById('commit-message').value = '';
        this.render();
    }
    
    async pull() {
        await fetch(`/api/v1/projects/${this.projectId}/git/pull`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.getToken()}`
            }
        });
        this.render();
    }
    
    async push() {
        await fetch(`/api/v1/projects/${this.projectId}/git/push`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.getToken()}`
            }
        });
        this.render();
    }
    
    refresh() {
        this.render();
    }
    
    getToken() {
        return localStorage.getItem('auth_token');
    }
}

const gitInterface = new GitInterface('git-container');
```

### 2. Backend Components

#### 2.1 Custom WSGI Application

**Purpose**: Handle HTTP requests without external frameworks

```python
import json
import urllib.parse
from http.cookies import SimpleCookie
from typing import Dict, List, Callable, Tuple

class WSGIApplication:
    """Custom WSGI application"""
    
    def __init__(self):
        self.routes = {}
        self.middleware = []
        
    def route(self, path: str, methods: List[str] = None):
        """Decorator to register routes"""
        if methods is None:
            methods = ['GET']
            
        def decorator(func):
            for method in methods:
                key = f"{method}:{path}"
                self.routes[key] = func
            return func
        return decorator
    
    def use(self, middleware: Callable):
        """Add middleware"""
        self.middleware.append(middleware)
    
    def __call__(self, environ, start_response):
        """WSGI application entry point"""
        request = Request(environ)
        
        # Apply middleware
        for mw in self.middleware:
            result = mw(request)
            if result is not None:
                return self._send_response(result, start_response)
        
        # Route request
        key = f"{request.method}:{request.path}"
        handler = self.routes.get(key)
        
        if handler is None:
            response = Response(status=404, body={'error': 'Not found'})
        else:
            try:
                response = handler(request)
            except Exception as e:
                response = Response(status=500, body={'error': str(e)})
        
        return self._send_response(response, start_response)
    
    def _send_response(self, response, start_response):
        """Send HTTP response"""
        status = f"{response.status} {self._get_status_text(response.status)}"
        headers = list(response.headers.items())
        
        start_response(status, headers)
        
        if isinstance(response.body, dict):
            body = json.dumps(response.body).encode('utf-8')
        elif isinstance(response.body, str):
            body = response.body.encode('utf-8')
        else:
            body = response.body
        
        return [body]
    
    def _get_status_text(self, code: int) -> str:
        """Get HTTP status text"""
        status_texts = {
            200: 'OK',
            201: 'Created',
            204: 'No Content',
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not Found',
            500: 'Internal Server Error'
        }
        return status_texts.get(code, 'Unknown')

class Request:
    """HTTP request wrapper"""
    
    def __init__(self, environ):
        self.environ = environ
        self.method = environ['REQUEST_METHOD']
        self.path = environ['PATH_INFO']
        self.query_string = environ.get('QUERY_STRING', '')
        self.headers = self._parse_headers(environ)
        self.cookies = self._parse_cookies(environ)
        self._body = None
    
    @property
    def body(self):
        """Get request body"""
        if self._body is None:
            content_length = int(self.environ.get('CONTENT_LENGTH', 0))
            if content_length > 0:
                self._body = self.environ['wsgi.input'].read(content_length)
        return self._body
    
    @property
    def json(self):
        """Parse JSON body"""
        if self.body:
            return json.loads(self.body.decode('utf-8'))
        return None
    
    @property
    def query_params(self):
        """Parse query parameters"""
        return urllib.parse.parse_qs(self.query_string)
    
    def _parse_headers(self, environ):
        """Parse HTTP headers"""
        headers = {}
        for key, value in environ.items():
            if key.startswith('HTTP_'):
                header_name = key[5:].replace('_', '-').title()
                headers[header_name] = value
        return headers
    
    def _parse_cookies(self, environ):
        """Parse cookies"""
        cookie_header = environ.get('HTTP_COOKIE', '')
        cookies = SimpleCookie()
        cookies.load(cookie_header)
        return {key: morsel.value for key, morsel in cookies.items()}

class Response:
    """HTTP response wrapper"""
    
    def __init__(self, status=200, body=None, headers=None):
        self.status = status
        self.body = body or {}
        self.headers = headers or {}
        
        if 'Content-Type' not in self.headers:
            self.headers['Content-Type'] = 'application/json'
    
    def set_cookie(self, name, value, max_age=None):
        """Set cookie"""
        cookie = f"{name}={value}"
        if max_age:
            cookie += f"; Max-Age={max_age}"
        self.headers['Set-Cookie'] = cookie

# Create application instance
app = WSGIApplication()
```

#### 2.2 Authentication Middleware

**Purpose**: JWT-based authentication

```python
import hmac
import hashlib
import base64
import json
import time
from typing import Optional

class AuthMiddleware:
    """JWT authentication middleware"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode('utf-8')
        self.public_paths = ['/api/v1/auth/login', '/api/v1/auth/register']
    
    def __call__(self, request: Request) -> Optional[Response]:
        """Check authentication"""
        # Skip auth for public paths
        if request.path in self.public_paths:
            return None
        
        # Get token from header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return Response(status=401, body={'error': 'Missing token'})
        
        token = auth_header[7:]
        
        # Verify token
        payload = self.verify_token(token)
        if payload is None:
            return Response(status=401, body={'error': 'Invalid token'})
        
        # Add user info to request
        request.user = payload
        return None
    
    def create_token(self, payload: dict, expires_in: int = 3600) -> str:
        """Create JWT token"""
        # Add expiration
        payload['exp'] = int(time.time()) + expires_in
        
        # Encode payload
        header = {'alg': 'HS256', 'typ': 'JWT'}
        header_b64 = base64.urlsafe_b64encode(
            json.dumps(header).encode('utf-8')
        ).decode('utf-8').rstrip('=')
        
        payload_b64 = base64.urlsafe_b64encode(
            json.dumps(payload).encode('utf-8')
        ).decode('utf-8').rstrip('=')
        
        # Create signature
        message = f"{header_b64}.{payload_b64}".encode('utf-8')
        signature = hmac.new(self.secret_key, message, hashlib.sha256).digest()
        signature_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
        
        return f"{header_b64}.{payload_b64}.{signature_b64}"
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify JWT token"""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            header_b64, payload_b64, signature_b64 = parts
            
            # Verify signature
            message = f"{header_b64}.{payload_b64}".encode('utf-8')
            expected_signature = hmac.new(
                self.secret_key, message, hashlib.sha256
            ).digest()
            expected_signature_b64 = base64.urlsafe_b64encode(
                expected_signature
            ).decode('utf-8').rstrip('=')
            
            if signature_b64 != expected_signature_b64:
                return None
            
            # Decode payload
            payload_json = base64.urlsafe_b64decode(
                payload_b64 + '=' * (4 - len(payload_b64) % 4)
            )
            payload = json.loads(payload_json)
            
            # Check expiration
            if payload.get('exp', 0) < time.time():
                return None
            
            return payload
            
        except Exception:
            return None

# Add middleware to app
auth = AuthMiddleware(secret_key='your-secret-key-here')
app.use(auth)
```

#### 2.3 Chat Service with Streaming

**Purpose**: Handle chat with Ollama streaming

```python
import urllib.request
import urllib.parse
import json
from typing import Generator

class OllamaClient:
    """Client for Ollama API"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def chat(self, model: str, messages: List[dict]) -> Generator[str, None, None]:
        """Stream chat response"""
        url = f"{self.base_url}/api/chat"
        
        data = {
            'model': model,
            'messages': messages,
            'stream': True
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req) as response:
            for line in response:
                if line:
                    chunk = json.loads(line.decode('utf-8'))
                    if 'message' in chunk:
                        content = chunk['message'].get('content', '')
                        if content:
                            yield content

class ChatService:
    """Service for chat operations"""
    
    def __init__(self, thread_repo, message_repo, ollama_client):
        self.thread_repo = thread_repo
        self.message_repo = message_repo
        self.ollama_client = ollama_client
    
    def send_message(self, thread_id: str, content: str, 
                     model: str) -> Generator[str, None, None]:
        """Send message and stream response"""
        # Save user message
        user_msg = Message(
            id=self._generate_id(),
            thread_id=thread_id,
            role='user',
            content=content
        )
        self.message_repo.save(user_msg)
        
        # Get thread history
        history = self.message_repo.find_by_thread(thread_id)
        messages = [{'role': msg.role, 'content': msg.content} 
                   for msg in history]
        
        # Stream response from Ollama
        response_content = ""
        for chunk in self.ollama_client.chat(model, messages):
            response_content += chunk
            yield chunk
        
        # Save assistant message
        assistant_msg = Message(
            id=self._generate_id(),
            thread_id=thread_id,
            role='assistant',
            content=response_content,
            model=model
        )
        self.message_repo.save(assistant_msg)
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        import uuid
        return str(uuid.uuid4())

# Register chat endpoint with streaming
@app.route('/api/v1/threads/<thread_id>/messages', methods=['POST'])
def send_message(request):
    """Send message endpoint with streaming"""
    thread_id = request.path.split('/')[-2]
    data = request.json
    
    content = data.get('content')
    model = data.get('model', 'qwen2.5-coder:32b')
    
    # Create streaming response
    def generate():
        for chunk in chat_service.send_message(thread_id, content, model):
            yield chunk.encode('utf-8')
    
    return Response(
        status=200,
        body=generate(),
        headers={
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
    )
```

---

## Analysis Algorithms

### 1. Bug Detection Algorithms

#### 1.1 Use-Before-Definition Detection

```python
class UseBeforeDefDetector:
    """Detect variables used before definition"""
    
    def detect(self, ast_tree) -> List[Bug]:
        """Detect use-before-def bugs"""
        bugs = []
        symbol_table = SymbolTable()
        
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.FunctionDef):
                bugs.extend(self._check_function(node, symbol_table))
        
        return bugs
    
    def _check_function(self, func_node, symbol_table):
        """Check function for use-before-def"""
        bugs = []
        local_symbols = set()
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    # Variable definition
                    local_symbols.add(node.id)
                elif isinstance(node.ctx, ast.Load):
                    # Variable use
                    if node.id not in local_symbols and                        not symbol_table.is_global(node.id):
                        bugs.append(Bug(
                            type='use_before_def',
                            severity='high',
                            file=func_node.lineno,
                            line=node.lineno,
                            message=f"Variable '{node.id}' used before definition"
                        ))
        
        return bugs
```

#### 1.2 Infinite Loop Detection

```python
class InfiniteLoopDetector:
    """Detect potential infinite loops"""
    
    def detect(self, ast_tree) -> List[Bug]:
        """Detect infinite loop risks"""
        bugs = []
        
        for node in ast.walk(ast_tree):
            if isinstance(node, (ast.While, ast.For)):
                if self._is_infinite_loop(node):
                    bugs.append(Bug(
                        type='infinite_loop',
                        severity='critical',
                        line=node.lineno,
                        message='Potential infinite loop detected'
                    ))
        
        return bugs
    
    def _is_infinite_loop(self, loop_node):
        """Check if loop might be infinite"""
        # Check for break/return statements
        has_exit = False
        
        for node in ast.walk(loop_node):
            if isinstance(node, (ast.Break, ast.Return)):
                has_exit = True
                break
        
        if has_exit:
            return False
        
        # Check if loop condition can become false
        if isinstance(loop_node, ast.While):
            if isinstance(loop_node.test, ast.Constant):
                if loop_node.test.value is True:
                    return True
        
        return False
```

### 2. Complexity Analysis Algorithms

#### 2.1 Cyclomatic Complexity

```python
class CyclomaticComplexityCalculator:
    """Calculate cyclomatic complexity"""
    
    def calculate(self, func_node) -> int:
        """Calculate cyclomatic complexity for function"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(func_node):
            # Decision points
            if isinstance(node, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                # And/Or operators
                complexity += len(node.values) - 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
        
        return complexity
```

#### 2.2 Cognitive Complexity

```python
class CognitiveComplexityCalculator:
    """Calculate cognitive complexity"""
    
    def calculate(self, func_node) -> int:
        """Calculate cognitive complexity"""
        complexity = 0
        nesting_level = 0
        
        def visit(node, level):
            nonlocal complexity
            
            # Increment for control flow
            if isinstance(node, (ast.If, ast.While, ast.For)):
                complexity += 1 + level
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            
            # Increase nesting for certain nodes
            if isinstance(node, (ast.If, ast.While, ast.For, ast.With)):
                level += 1
            
            # Visit children
            for child in ast.iter_child_nodes(node):
                visit(child, level)
        
        visit(func_node, 0)
        return complexity
```

---

## API Design

### Complete API Specification

See project2_MASTER_PLAN.md for complete API endpoint list.

### API Response Format

```json
{
    "success": true,
    "data": {
        // Response data
    },
    "error": null,
    "timestamp": "2024-12-30T12:00:00Z"
}
```

### Error Response Format

```json
{
    "success": false,
    "data": null,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input",
        "details": {
            "field": "email",
            "reason": "Invalid email format"
        }
    },
    "timestamp": "2024-12-30T12:00:00Z"
}
```

---

## Database Design

See project2_MASTER_PLAN.md for complete database schema.

### Database Abstraction Layer

```python
class DatabaseAbstraction:
    """Abstract database operations"""
    
    def __init__(self, db_type='sqlite', **kwargs):
        self.db_type = db_type
        if db_type == 'sqlite':
            import sqlite3
            self.conn = sqlite3.connect(kwargs.get('database', 'app.db'))
        elif db_type == 'mysql':
            import mysql.connector
            self.conn = mysql.connector.connect(**kwargs)
    
    def execute(self, query, params=None):
        """Execute query"""
        cursor = self.conn.cursor()
        cursor.execute(query, params or ())
        return cursor
    
    def fetchall(self, query, params=None):
        """Fetch all results"""
        cursor = self.execute(query, params)
        return cursor.fetchall()
    
    def fetchone(self, query, params=None):
        """Fetch one result"""
        cursor = self.execute(query, params)
        return cursor.fetchone()
    
    def commit(self):
        """Commit transaction"""
        self.conn.commit()
    
    def rollback(self):
        """Rollback transaction"""
        self.conn.rollback()
```

---

## Security Architecture

### 1. Authentication

- JWT tokens with HMAC-SHA256 signatures
- Token expiration (default 1 hour)
- Secure password hashing (SHA-256 with salt)

### 2. Authorization

- Role-based access control (RBAC)
- User can only access their own projects
- Admin role for system management

### 3. Input Validation

- Validate all user inputs
- Sanitize file paths
- Prevent SQL injection
- Prevent XSS attacks

### 4. Rate Limiting

- Limit API requests per user
- Prevent brute force attacks
- Throttle expensive operations

---

## Performance Architecture

### 1. Caching

- Cache analysis results
- Cache file contents
- Cache git status

### 2. Async Processing

- Background analysis jobs
- Async file operations
- Streaming responses

### 3. Database Optimization

- Proper indexes on all foreign keys
- Query optimization
- Connection pooling

---

## Deployment Architecture

### Apache Configuration

```apache
<VirtualHost *:443>
    ServerName debugging-platform.example.com
    
    SSLEngine on
    SSLCertificateFile /path/to/cert.pem
    SSLCertificateKeyFile /path/to/key.pem
    
    WSGIDaemonProcess app user=www-data group=www-data threads=5
    WSGIScriptAlias / /var/www/app/wsgi.py
    
    <Directory /var/www/app>
        WSGIProcessGroup app
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
    </Directory>
    
    ErrorLog ${APACHE_LOG_DIR}/app-error.log
    CustomLog ${APACHE_LOG_DIR}/app-access.log combined
</VirtualHost>
```

### WSGI Entry Point

```python
# wsgi.py
import sys
sys.path.insert(0, '/var/www/app')

from app import app as application
```

---

**Document Version**: 2.0.0  
**Created**: 2024-12-30  
**Updated**: 2024-12-30  
**Status**: Ready for Implementation
