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
6. [Log Display System](#log-display-system)
7. [Comprehensive Chat Interface](#comprehensive-chat-interface)
8. [Custom Tool Framework](#custom-tool-framework)
9. [Session Management](#session-management)
10. [Debugging Components](#debugging-components)
11. [API Design](#api-design)
12. [Database Design](#database-design)

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│              (Web Browser - HTML/CSS/JavaScript)                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTPS/REST + WebSocket
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
│  │  /sessions  /logs  /tools  /variables  /breakpoints  /chat  ││
│  └──────────────────────┬───────────────────────────────────────┘│
└─────────────────────────┼────────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────────┐
│                   Service Layer                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Session  │  │   Log    │  │   Tool   │  │   Chat   │        │
│  │ Service  │  │ Service  │  │ Service  │  │ Service  │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │Variable  │  │Execution │  │Breakpoint│  │ Debugger │        │
│  │Inspector │  │  Tracer  │  │ Manager  │  │ Control  │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────┬────────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────────┐
│                   Analysis Engine Layer                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐         │
│  │   Bug    │  │Complexity│  │Architecture│  │  Dead   │         │
│  │ Detector │  │ Analyzer │  │  Analyzer  │  │  Code   │         │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘         │
└─────────────────────────┬────────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────────┐
│                   Tool Execution Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Sandbox    │  │   Parameter  │  │    Result    │           │
│  │  Environment │  │  Validator   │  │  Serializer  │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────┬────────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────────┐
│                   Data Access Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Repositories │  │ DB Abstraction│  │ Cache Layer  │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────┬────────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────────┐
│                   Persistence Layer                               │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │         SQLite Database (or MySQL)                           ││
│  │  Sessions | Logs | Tools | Variables | Breakpoints | Chat   ││
│  └──────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

### System Characteristics

- **Architecture Style**: Layered + Event-Driven
- **API Style**: RESTful + WebSocket for streaming
- **Frontend**: Custom HTML/CSS/JavaScript (no frameworks)
- **Backend**: Custom WSGI application (Python stdlib only)
- **Data Storage**: SQLite (or MySQL)
- **Deployment**: Apache + mod_wsgi
- **Focus**: Real-time debugging and execution monitoring

---

## Architecture Patterns

### 1. Event-Driven Pattern

**Purpose**: Real-time log streaming and updates

```python
class EventBus:
    """Event bus for real-time updates"""
    
    def __init__(self):
        self.subscribers = {}
    
    def subscribe(self, event_type: str, callback):
        """Subscribe to event"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
    
    def publish(self, event_type: str, data):
        """Publish event"""
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                callback(data)

# Global event bus
event_bus = EventBus()

# Subscribe to log events
event_bus.subscribe('log', lambda log: stream_to_clients(log))
```

### 2. Sandbox Pattern

**Purpose**: Safe tool execution

```python
class ToolSandbox:
    """Sandbox for safe tool execution"""
    
    def __init__(self):
        self.timeout = 30  # seconds
        self.max_memory = 512 * 1024 * 1024  # 512MB
    
    def execute(self, tool_code: str, parameters: Dict) -> Any:
        """Execute tool in sandbox"""
        # Create restricted globals
        restricted_globals = {
            '__builtins__': {
                'print': print,
                'len': len,
                'range': range,
                'str': str,
                'int': int,
                'float': float,
                'list': list,
                'dict': dict,
                # ... safe builtins only
            }
        }
        
        # Execute with timeout
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Tool execution timeout")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(self.timeout)
        
        try:
            result = exec(tool_code, restricted_globals, parameters)
            return result
        finally:
            signal.alarm(0)
```

---

## Component Design

### 1. Frontend Components

#### 1.1 Log Display Component (PRIMARY INTERFACE)

**Purpose**: Real-time log viewing with filtering

**HTML Structure**:
```html
<div id="log-display" class="primary-interface">
    <div class="log-controls">
        <div class="log-filters">
            <select id="level-filter">
                <option value="ALL">All Levels</option>
                <option value="DEBUG">DEBUG</option>
                <option value="INFO">INFO</option>
                <option value="WARN">WARN</option>
                <option value="ERROR">ERROR</option>
                <option value="CRITICAL">CRITICAL</option>
            </select>
            
            <select id="source-filter">
                <option value="ALL">All Sources</option>
                <!-- Dynamically populated -->
            </select>
            
            <select id="time-filter">
                <option value="1h">Last 1 hour</option>
                <option value="6h">Last 6 hours</option>
                <option value="24h">Last 24 hours</option>
                <option value="all">All time</option>
            </select>
            
            <input type="text" id="search-input" placeholder="Search logs...">
            <button id="search-btn">🔍</button>
        </div>
        
        <div class="log-actions">
            <button id="pause-btn">⏸️ Pause</button>
            <button id="clear-btn">🗑️ Clear</button>
            <button id="export-btn">💾 Export</button>
            <label>
                <input type="checkbox" id="auto-scroll"> Auto-scroll
            </label>
        </div>
    </div>
    
    <div class="log-viewer" id="log-viewer">
        <!-- Logs rendered here -->
    </div>
    
    <div class="log-stats">
        <span>Total: <span id="total-logs">0</span></span>
        <span>Errors: <span id="error-count">0</span></span>
        <span>Warnings: <span id="warning-count">0</span></span>
    </div>
</div>
```

**JavaScript Implementation**:
```javascript
class LogDisplay {
    constructor(sessionId) {
        this.sessionId = sessionId;
        this.logs = [];
        this.filteredLogs = [];
        this.paused = false;
        this.autoScroll = true;
        this.filters = {
            level: 'ALL',
            source: 'ALL',
            time: '1h',
            search: ''
        };
        this.ws = null;
        
        this.init();
    }
    
    init() {
        this.connectWebSocket();
        this.attachEventListeners();
        this.loadHistoricalLogs();
    }
    
    connectWebSocket() {
        const wsUrl = `wss://${window.location.host}/api/v1/sessions/${this.sessionId}/logs/stream`;
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onmessage = (event) => {
            const log = JSON.parse(event.data);
            this.addLog(log);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.reconnect();
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket closed, reconnecting...');
            this.reconnect();
        };
    }
    
    reconnect() {
        setTimeout(() => {
            this.connectWebSocket();
        }, 5000);
    }
    
    async loadHistoricalLogs() {
        const response = await fetch(
            `/api/v1/sessions/${this.sessionId}/logs?limit=1000`,
            {headers: {'Authorization': `Bearer ${this.getToken()}`}}
        );
        const data = await response.json();
        
        this.logs = data.logs;
        this.applyFilters();
        this.render();
    }
    
    addLog(log) {
        if (this.paused) return;
        
        this.logs.push(log);
        
        // Update stats
        this.updateStats();
        
        // Apply filters
        if (this.matchesFilters(log)) {
            this.filteredLogs.push(log);
            this.renderLog(log);
            
            if (this.autoScroll) {
                this.scrollToBottom();
            }
        }
    }
    
    matchesFilters(log) {
        // Level filter
        if (this.filters.level !== 'ALL' && log.level !== this.filters.level) {
            return false;
        }
        
        // Source filter
        if (this.filters.source !== 'ALL' && log.source_file !== this.filters.source) {
            return false;
        }
        
        // Time filter
        const logTime = new Date(log.timestamp);
        const now = new Date();
        const hoursDiff = (now - logTime) / (1000 * 60 * 60);
        
        if (this.filters.time !== 'all') {
            const hours = parseInt(this.filters.time);
            if (hoursDiff > hours) {
                return false;
            }
        }
        
        // Search filter
        if (this.filters.search && !log.message.toLowerCase().includes(this.filters.search.toLowerCase())) {
            return false;
        }
        
        return true;
    }
    
    applyFilters() {
        this.filteredLogs = this.logs.filter(log => this.matchesFilters(log));
    }
    
    render() {
        const viewer = document.getElementById('log-viewer');
        viewer.innerHTML = '';
        
        this.filteredLogs.forEach(log => {
            this.renderLog(log);
        });
    }
    
    renderLog(log) {
        const viewer = document.getElementById('log-viewer');
        const logElement = document.createElement('div');
        logElement.className = `log-entry log-${log.level.toLowerCase()}`;
        
        const timestamp = new Date(log.timestamp).toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            fractionalSecondDigits: 3
        });
        
        logElement.innerHTML = `
            <span class="log-timestamp">${timestamp}</span>
            <span class="log-level">[${log.level}]</span>
            <span class="log-source">${log.source_file}:${log.line_number}</span>
            <span class="log-message">${this.escapeHtml(log.message)}</span>
            ${log.thread_id ? `<span class="log-thread">(${log.thread_id})</span>` : ''}
        `;
        
        viewer.appendChild(logElement);
    }
    
    attachEventListeners() {
        // Level filter
        document.getElementById('level-filter').addEventListener('change', (e) => {
            this.filters.level = e.target.value;
            this.applyFilters();
            this.render();
        });
        
        // Source filter
        document.getElementById('source-filter').addEventListener('change', (e) => {
            this.filters.source = e.target.value;
            this.applyFilters();
            this.render();
        });
        
        // Time filter
        document.getElementById('time-filter').addEventListener('change', (e) => {
            this.filters.time = e.target.value;
            this.applyFilters();
            this.render();
        });
        
        // Search
        document.getElementById('search-btn').addEventListener('click', () => {
            this.filters.search = document.getElementById('search-input').value;
            this.applyFilters();
            this.render();
        });
        
        // Pause
        document.getElementById('pause-btn').addEventListener('click', () => {
            this.paused = !this.paused;
            document.getElementById('pause-btn').textContent = 
                this.paused ? '▶️ Resume' : '⏸️ Pause';
        });
        
        // Clear
        document.getElementById('clear-btn').addEventListener('click', () => {
            this.logs = [];
            this.filteredLogs = [];
            this.render();
        });
        
        // Export
        document.getElementById('export-btn').addEventListener('click', () => {
            this.exportLogs();
        });
        
        // Auto-scroll
        document.getElementById('auto-scroll').addEventListener('change', (e) => {
            this.autoScroll = e.target.checked;
        });
    }
    
    updateStats() {
        document.getElementById('total-logs').textContent = this.logs.length;
        document.getElementById('error-count').textContent = 
            this.logs.filter(l => l.level === 'ERROR' || l.level === 'CRITICAL').length;
        document.getElementById('warning-count').textContent = 
            this.logs.filter(l => l.level === 'WARN').length;
    }
    
    scrollToBottom() {
        const viewer = document.getElementById('log-viewer');
        viewer.scrollTop = viewer.scrollHeight;
    }
    
    exportLogs() {
        const content = this.filteredLogs.map(log => 
            `${log.timestamp} [${log.level}] ${log.source_file}:${log.line_number} - ${log.message}`
        ).join('
');
        
        const blob = new Blob([content], {type: 'text/plain'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `logs_${this.sessionId}_${Date.now()}.txt`;
        a.click();
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    getToken() {
        return localStorage.getItem('auth_token');
    }
}

// Initialize log display
const logDisplay = new LogDisplay(sessionId);
```

**CSS Styling**:
```css
#log-display {
    display: flex;
    flex-direction: column;
    height: 100vh;
    width: 100%;
}

.log-controls {
    display: flex;
    justify-content: space-between;
    padding: 1rem;
    background-color: #f5f5f5;
    border-bottom: 1px solid #ddd;
}

.log-filters {
    display: flex;
    gap: 0.5rem;
}

.log-filters select,
.log-filters input {
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
}

.log-actions {
    display: flex;
    gap: 0.5rem;
    align-items: center;
}

.log-actions button {
    padding: 0.5rem 1rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    background-color: white;
    cursor: pointer;
}

.log-actions button:hover {
    background-color: #e0e0e0;
}

.log-viewer {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    background-color: #1e1e1e;
    color: #d4d4d4;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.5;
}

.log-entry {
    padding: 0.25rem 0;
    border-bottom: 1px solid #333;
}

.log-entry:hover {
    background-color: #2d2d2d;
}

.log-timestamp {
    color: #858585;
    margin-right: 0.5rem;
}

.log-level {
    font-weight: bold;
    margin-right: 0.5rem;
}

.log-debug .log-level { color: #858585; }
.log-info .log-level { color: #4ec9b0; }
.log-warn .log-level { color: #dcdcaa; }
.log-error .log-level { color: #f48771; }
.log-critical .log-level { color: #f14c4c; }

.log-source {
    color: #569cd6;
    margin-right: 0.5rem;
}

.log-message {
    color: #d4d4d4;
}

.log-thread {
    color: #858585;
    margin-left: 0.5rem;
    font-size: 11px;
}

.log-stats {
    padding: 0.5rem 1rem;
    background-color: #f5f5f5;
    border-top: 1px solid #ddd;
    display: flex;
    gap: 2rem;
    font-size: 14px;
}
```

#### 1.2 Comprehensive Chat Interface

**Purpose**: Show ALL conversations including auto-generated prompts

**HTML Structure**:
```html
<div id="chat-interface">
    <div class="chat-header">
        <h3>Debugging Chat</h3>
        <div class="chat-controls">
            <label>
                <input type="checkbox" id="show-system-prompts" checked>
                Show system prompts
            </label>
            <label>
                <input type="checkbox" id="show-tool-logs" checked>
                Show tool logs
            </label>
            <button id="export-chat-btn">Export</button>
        </div>
    </div>
    
    <div class="chat-messages" id="chat-messages">
        <!-- Messages rendered here -->
    </div>
    
    <div class="chat-input-container">
        <textarea id="chat-input" placeholder="Ask about the code..."></textarea>
        <button id="send-btn">Send</button>
        <button id="tools-btn">Tools ▼</button>
    </div>
</div>
```

**JavaScript Implementation**:
```javascript
class ComprehensiveChat {
    constructor(sessionId) {
        this.sessionId = sessionId;
        this.messages = [];
        this.showSystemPrompts = true;
        this.showToolLogs = true;
        this.ws = null;
        
        this.init();
    }
    
    init() {
        this.connectWebSocket();
        this.attachEventListeners();
        this.loadHistory();
    }
    
    connectWebSocket() {
        const wsUrl = `wss://${window.location.host}/api/v1/sessions/${this.sessionId}/chat/stream`;
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.addMessage(message);
        };
    }
    
    async loadHistory() {
        const response = await fetch(
            `/api/v1/sessions/${this.sessionId}/chat/history`,
            {headers: {'Authorization': `Bearer ${this.getToken()}`}}
        );
        const data = await response.json();
        
        this.messages = data.messages;
        this.render();
    }
    
    addMessage(message) {
        this.messages.push(message);
        this.renderMessage(message);
        this.scrollToBottom();
    }
    
    render() {
        const container = document.getElementById('chat-messages');
        container.innerHTML = '';
        
        this.messages.forEach(message => {
            if (this.shouldShowMessage(message)) {
                this.renderMessage(message);
            }
        });
    }
    
    shouldShowMessage(message) {
        if (message.type === 'system' && !this.showSystemPrompts) {
            return false;
        }
        if (message.type === 'tool' && !this.showToolLogs) {
            return false;
        }
        return true;
    }
    
    renderMessage(message) {
        const container = document.getElementById('chat-messages');
        const messageElement = document.createElement('div');
        messageElement.className = `chat-message chat-${message.type}`;
        
        let icon = '';
        let label = '';
        
        switch (message.type) {
            case 'user':
                icon = '👤';
                label = 'You';
                break;
            case 'assistant':
                icon = '🤖';
                label = 'AI';
                break;
            case 'system':
                icon = '🔧';
                label = 'SYSTEM';
                break;
            case 'tool':
                icon = '🛠️';
                label = 'TOOL';
                break;
        }
        
        messageElement.innerHTML = `
            <div class="message-header">
                <span class="message-icon">${icon}</span>
                <span class="message-label">${label}</span>
                <span class="message-timestamp">${this.formatTime(message.timestamp)}</span>
            </div>
            <div class="message-content">
                ${this.renderContent(message)}
            </div>
        `;
        
        container.appendChild(messageElement);
    }
    
    renderContent(message) {
        if (message.type === 'system') {
            return `
                <div class="system-prompt">
                    <strong>Auto-generated prompt:</strong>
                    <pre>${this.escapeHtml(message.content)}</pre>
                    ${message.context ? `
                        <details>
                            <summary>Context injected</summary>
                            <pre>${this.escapeHtml(JSON.stringify(message.context, null, 2))}</pre>
                        </details>
                    ` : ''}
                </div>
            `;
        }
        
        if (message.type === 'tool') {
            return `
                <div class="tool-execution">
                    <strong>Executed tool:</strong> ${message.tool_name}
                    <pre>Parameters: ${this.escapeHtml(JSON.stringify(message.parameters, null, 2))}</pre>
                    <pre>Result: ${this.escapeHtml(JSON.stringify(message.result, null, 2))}</pre>
                    <span class="tool-duration">${message.duration_ms}ms</span>
                </div>
            `;
        }
        
        // Regular message (user or assistant)
        return this.renderMarkdown(message.content);
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
            .replace(/\*([^*]+)\*/g, '<em>$1</em>')
            .replace(/
/g, '<br>');
    }
    
    async sendMessage() {
        const input = document.getElementById('chat-input');
        const content = input.value.trim();
        if (!content) return;
        
        // Add user message
        this.addMessage({
            type: 'user',
            content: content,
            timestamp: new Date().toISOString()
        });
        
        input.value = '';
        
        // Send to server
        const response = await fetch(
            `/api/v1/sessions/${this.sessionId}/chat/send`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getToken()}`
                },
                body: JSON.stringify({content: content})
            }
        );
        
        // Response will come via WebSocket
    }
    
    attachEventListeners() {
        document.getElementById('send-btn').addEventListener('click', () => {
            this.sendMessage();
        });
        
        document.getElementById('chat-input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                this.sendMessage();
            }
        });
        
        document.getElementById('show-system-prompts').addEventListener('change', (e) => {
            this.showSystemPrompts = e.target.checked;
            this.render();
        });
        
        document.getElementById('show-tool-logs').addEventListener('change', (e) => {
            this.showToolLogs = e.target.checked;
            this.render();
        });
        
        document.getElementById('export-chat-btn').addEventListener('click', () => {
            this.exportChat();
        });
    }
    
    exportChat() {
        const content = this.messages.map(m => 
            `[${m.type.toUpperCase()}] ${m.timestamp}
${m.content}
`
        ).join('
---

');
        
        const blob = new Blob([content], {type: 'text/plain'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat_${this.sessionId}_${Date.now()}.txt`;
        a.click();
    }
    
    formatTime(timestamp) {
        return new Date(timestamp).toLocaleTimeString();
    }
    
    scrollToBottom() {
        const container = document.getElementById('chat-messages');
        container.scrollTop = container.scrollHeight;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    getToken() {
        return localStorage.getItem('auth_token');
    }
}

const chat = new ComprehensiveChat(sessionId);
```

#### 1.3 Custom Tool Palette

**Purpose**: Create and execute custom debugging tools

**JavaScript Implementation**:
```javascript
class ToolPalette {
    constructor(sessionId) {
        this.sessionId = sessionId;
        this.tools = [];
        this.categories = {};
        
        this.init();
    }
    
    async init() {
        await this.loadTools();
        this.render();
        this.attachEventListeners();
    }
    
    async loadTools() {
        const response = await fetch('/api/v1/tools', {
            headers: {'Authorization': `Bearer ${this.getToken()}`}
        });
        const data = await response.json();
        
        this.tools = data.tools;
        this.categorizeTools();
    }
    
    categorizeTools() {
        this.categories = {};
        
        this.tools.forEach(tool => {
            const category = tool.category || 'Uncategorized';
            if (!this.categories[category]) {
                this.categories[category] = [];
            }
            this.categories[category].push(tool);
        });
    }
    
    render() {
        const container = document.getElementById('tool-palette');
        
        let html = '<div class="tool-palette-header">';
        html += '<input type="text" id="tool-search" placeholder="Search tools...">';
        html += '<button id="create-tool-btn">+ Create Tool</button>';
        html += '</div>';
        
        html += '<div class="tool-categories">';
        
        for (const [category, tools] of Object.entries(this.categories)) {
            html += `
                <div class="tool-category">
                    <h4 class="category-header">${category}</h4>
                    <div class="category-tools">
                        ${tools.map(tool => this.renderTool(tool)).join('')}
                    </div>
                </div>
            `;
        }
        
        html += '</div>';
        
        container.innerHTML = html;
    }
    
    renderTool(tool) {
        return `
            <div class="tool-item" data-tool-id="${tool.id}">
                <div class="tool-icon">🔧</div>
                <div class="tool-info">
                    <div class="tool-name">${tool.name}</div>
                    <div class="tool-description">${tool.description}</div>
                </div>
                <button class="tool-execute-btn" data-tool-id="${tool.id}">
                    Execute
                </button>
            </div>
        `;
    }
    
    async executeTool(toolId) {
        const tool = this.tools.find(t => t.id === toolId);
        if (!tool) return;
        
        // Show parameter dialog
        const parameters = await this.showParameterDialog(tool);
        if (!parameters) return;
        
        // Execute tool
        const response = await fetch(`/api/v1/tools/${toolId}/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.getToken()}`
            },
            body: JSON.stringify({
                session_id: this.sessionId,
                parameters: parameters
            })
        });
        
        const result = await response.json();
        
        // Show result
        this.showResult(tool.name, result);
    }
    
    async showParameterDialog(tool) {
        // Create modal dialog for parameters
        const modal = document.createElement('div');
        modal.className = 'modal';
        
        let html = `
            <div class="modal-content">
                <h3>Execute ${tool.name}</h3>
                <form id="tool-params-form">
        `;
        
        const params = JSON.parse(tool.parameters || '{}');
        for (const [name, param] of Object.entries(params)) {
            html += `
                <div class="form-group">
                    <label>${name}${param.required ? '*' : ''}</label>
                    <input type="text" name="${name}" 
                           placeholder="${param.description}"
                           ${param.required ? 'required' : ''}>
                </div>
            `;
        }
        
        html += `
                    <div class="form-actions">
                        <button type="submit">Execute</button>
                        <button type="button" id="cancel-btn">Cancel</button>
                    </div>
                </form>
            </div>
        `;
        
        modal.innerHTML = html;
        document.body.appendChild(modal);
        
        return new Promise((resolve) => {
            const form = document.getElementById('tool-params-form');
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                const formData = new FormData(form);
                const parameters = Object.fromEntries(formData);
                document.body.removeChild(modal);
                resolve(parameters);
            });
            
            document.getElementById('cancel-btn').addEventListener('click', () => {
                document.body.removeChild(modal);
                resolve(null);
            });
        });
    }
    
    showResult(toolName, result) {
        // Show result in modal or panel
        alert(`Tool ${toolName} executed:
${JSON.stringify(result, null, 2)}`);
    }
    
    attachEventListeners() {
        // Tool execution
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('tool-execute-btn')) {
                const toolId = e.target.dataset.toolId;
                this.executeTool(toolId);
            }
        });
        
        // Create tool
        document.getElementById('create-tool-btn')?.addEventListener('click', () => {
            this.showCreateToolDialog();
        });
        
        // Search
        document.getElementById('tool-search')?.addEventListener('input', (e) => {
            this.filterTools(e.target.value);
        });
    }
    
    showCreateToolDialog() {
        // Show tool creation dialog
        window.location.href = '/tools/create';
    }
    
    filterTools(query) {
        const lowerQuery = query.toLowerCase();
        const filtered = this.tools.filter(tool => 
            tool.name.toLowerCase().includes(lowerQuery) ||
            tool.description.toLowerCase().includes(lowerQuery)
        );
        
        // Re-render with filtered tools
        // ... filtering logic
    }
    
    getToken() {
        return localStorage.getItem('auth_token');
    }
}

const toolPalette = new ToolPalette(sessionId);
```

### 2. Backend Components

#### 2.1 Log Streaming Service

**Purpose**: Stream logs in real-time via WebSocket

```python
import json
import threading
import queue
from typing import Dict, Set

class LogStreamingService:
    """Service for streaming logs to clients"""
    
    def __init__(self):
        self.clients: Dict[str, Set] = {}  # session_id -> set of websockets
        self.log_queues: Dict[str, queue.Queue] = {}
        self.lock = threading.Lock()
    
    def register_client(self, session_id: str, websocket):
        """Register client for log streaming"""
        with self.lock:
            if session_id not in self.clients:
                self.clients[session_id] = set()
                self.log_queues[session_id] = queue.Queue()
            
            self.clients[session_id].add(websocket)
    
    def unregister_client(self, session_id: str, websocket):
        """Unregister client"""
        with self.lock:
            if session_id in self.clients:
                self.clients[session_id].discard(websocket)
                
                if not self.clients[session_id]:
                    del self.clients[session_id]
                    del self.log_queues[session_id]
    
    def add_log(self, session_id: str, log: Dict):
        """Add log entry"""
        # Store in database
        self._store_log(session_id, log)
        
        # Stream to connected clients
        if session_id in self.clients:
            message = json.dumps(log)
            for websocket in self.clients[session_id]:
                try:
                    websocket.send(message)
                except Exception as e:
                    print(f"Error sending log: {e}")
    
    def _store_log(self, session_id: str, log: Dict):
        """Store log in database"""
        # ... database storage logic
        pass

# Global log streaming service
log_streaming = LogStreamingService()
```

#### 2.2 Custom Tool Execution Engine

**Purpose**: Execute custom tools safely

```python
import ast
import json
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class ToolDefinition:
    id: str
    name: str
    description: str
    code: str
    parameters: Dict
    version: int

class ToolExecutionEngine:
    """Engine for executing custom tools"""
    
    def __init__(self):
        self.sandbox = ToolSandbox()
        self.tool_registry = {}
    
    def register_tool(self, tool: ToolDefinition):
        """Register a tool"""
        # Validate tool code
        self._validate_tool_code(tool.code)
        
        # Store in registry
        self.tool_registry[tool.id] = tool
    
    def execute_tool(self, tool_id: str, parameters: Dict) -> Any:
        """Execute a tool"""
        tool = self.tool_registry.get(tool_id)
        if not tool:
            raise ValueError(f"Tool {tool_id} not found")
        
        # Validate parameters
        self._validate_parameters(tool, parameters)
        
        # Execute in sandbox
        try:
            result = self.sandbox.execute(tool.code, parameters)
            return {
                'success': True,
                'result': result,
                'tool_id': tool_id,
                'tool_name': tool.name
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tool_id': tool_id,
                'tool_name': tool.name
            }
    
    def _validate_tool_code(self, code: str):
        """Validate tool code"""
        try:
            ast.parse(code)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python code: {e}")
        
        # Check for dangerous operations
        dangerous_keywords = ['exec', 'eval', 'compile', '__import__', 'open']
        for keyword in dangerous_keywords:
            if keyword in code:
                raise ValueError(f"Dangerous operation '{keyword}' not allowed")
    
    def _validate_parameters(self, tool: ToolDefinition, parameters: Dict):
        """Validate parameters"""
        params_def = tool.parameters
        
        for name, param_def in params_def.items():
            if param_def.get('required', False) and name not in parameters:
                raise ValueError(f"Required parameter '{name}' missing")
            
            if name in parameters:
                # Type validation
                expected_type = param_def.get('type', 'str')
                actual_value = parameters[name]
                
                if expected_type == 'int' and not isinstance(actual_value, int):
                    try:
                        parameters[name] = int(actual_value)
                    except ValueError:
                        raise ValueError(f"Parameter '{name}' must be an integer")
                
                elif expected_type == 'float' and not isinstance(actual_value, float):
                    try:
                        parameters[name] = float(actual_value)
                    except ValueError:
                        raise ValueError(f"Parameter '{name}' must be a float")

# Global tool execution engine
tool_engine = ToolExecutionEngine()
```

#### 2.3 Session Manager

**Purpose**: Manage long-running debugging sessions

```python
import json
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass, asdict

@dataclass
class SessionState:
    session_id: str
    project_id: str
    user_id: str
    status: str  # active, paused, stopped
    created_at: datetime
    updated_at: datetime
    state_data: Dict

class SessionManager:
    """Manager for debugging sessions"""
    
    def __init__(self, db):
        self.db = db
        self.active_sessions: Dict[str, SessionState] = {}
    
    def create_session(self, project_id: str, user_id: str, name: str) -> SessionState:
        """Create new session"""
        session_id = self._generate_id()
        
        session = SessionState(
            session_id=session_id,
            project_id=project_id,
            user_id=user_id,
            status='active',
            created_at=datetime.now(),
            updated_at=datetime.now(),
            state_data={}
        )
        
        # Save to database
        self._save_session(session)
        
        # Add to active sessions
        self.active_sessions[session_id] = session
        
        return session
    
    def pause_session(self, session_id: str):
        """Pause session"""
        session = self.active_sessions.get(session_id)
        if session:
            session.status = 'paused'
            session.updated_at = datetime.now()
            self._save_session(session)
    
    def resume_session(self, session_id: str):
        """Resume session"""
        session = self.active_sessions.get(session_id)
        if session:
            session.status = 'active'
            session.updated_at = datetime.now()
            self._save_session(session)
    
    def stop_session(self, session_id: str):
        """Stop session"""
        session = self.active_sessions.get(session_id)
        if session:
            session.status = 'stopped'
            session.updated_at = datetime.now()
            self._save_session(session)
            
            # Remove from active sessions
            del self.active_sessions[session_id]
    
    def save_state(self, session_id: str, state_data: Dict):
        """Save session state"""
        session = self.active_sessions.get(session_id)
        if session:
            session.state_data = state_data
            session.updated_at = datetime.now()
            self._save_session(session)
    
    def create_snapshot(self, session_id: str, name: str, description: str):
        """Create session snapshot"""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        snapshot_id = self._generate_id()
        
        query = """
            INSERT INTO session_snapshots 
            (id, session_id, name, description, state_data, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        
        self.db.execute(query, (
            snapshot_id,
            session_id,
            name,
            description,
            json.dumps(session.state_data),
            datetime.now()
        ))
        self.db.commit()
        
        return snapshot_id
    
    def rollback_to_snapshot(self, session_id: str, snapshot_id: str):
        """Rollback session to snapshot"""
        query = "SELECT state_data FROM session_snapshots WHERE id = ?"
        row = self.db.fetchone(query, (snapshot_id,))
        
        if not row:
            raise ValueError(f"Snapshot {snapshot_id} not found")
        
        state_data = json.loads(row[0])
        self.save_state(session_id, state_data)
    
    def _save_session(self, session: SessionState):
        """Save session to database"""
        query = """
            INSERT OR REPLACE INTO sessions 
            (id, project_id, user_id, status, created_at, updated_at, state_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        self.db.execute(query, (
            session.session_id,
            session.project_id,
            session.user_id,
            session.status,
            session.created_at,
            session.updated_at,
            json.dumps(session.state_data)
        ))
        self.db.commit()
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        import uuid
        return str(uuid.uuid4())

# Global session manager
session_manager = SessionManager(db)
```

---

## API Design

### Complete API Specification

#### Sessions
- `GET /api/v1/sessions` - List sessions
- `POST /api/v1/sessions` - Create session
- `GET /api/v1/sessions/{id}` - Get session
- `PUT /api/v1/sessions/{id}` - Update session
- `DELETE /api/v1/sessions/{id}` - Delete session
- `POST /api/v1/sessions/{id}/pause` - Pause session
- `POST /api/v1/sessions/{id}/resume` - Resume session
- `POST /api/v1/sessions/{id}/snapshot` - Create snapshot
- `GET /api/v1/sessions/{id}/snapshots` - List snapshots
- `POST /api/v1/sessions/{id}/rollback` - Rollback to snapshot

#### Logs
- `GET /api/v1/sessions/{id}/logs` - Get logs (with pagination)
- `WS /api/v1/sessions/{id}/logs/stream` - Stream logs (WebSocket)
- `GET /api/v1/sessions/{id}/logs/export` - Export logs
- `POST /api/v1/sessions/{id}/logs/filter` - Filter logs
- `GET /api/v1/sessions/{id}/logs/analyze` - Analyze logs

#### Custom Tools
- `GET /api/v1/tools` - List tools
- `POST /api/v1/tools` - Create tool
- `GET /api/v1/tools/{id}` - Get tool
- `PUT /api/v1/tools/{id}` - Update tool
- `DELETE /api/v1/tools/{id}` - Delete tool
- `POST /api/v1/tools/{id}/execute` - Execute tool
- `GET /api/v1/tools/{id}/executions` - Get execution history
- `POST /api/v1/tools/import` - Import tool
- `GET /api/v1/tools/{id}/export` - Export tool

#### Variables
- `GET /api/v1/sessions/{id}/variables` - Get variables
- `GET /api/v1/sessions/{id}/variables/{name}/history` - Get variable history
- `POST /api/v1/sessions/{id}/watch` - Add watch expression
- `DELETE /api/v1/sessions/{id}/watch/{id}` - Remove watch

#### Breakpoints
- `GET /api/v1/sessions/{id}/breakpoints` - List breakpoints
- `POST /api/v1/sessions/{id}/breakpoints` - Add breakpoint
- `PUT /api/v1/breakpoints/{id}` - Update breakpoint
- `DELETE /api/v1/breakpoints/{id}` - Remove breakpoint
- `POST /api/v1/breakpoints/{id}/toggle` - Enable/disable

#### Execution Control
- `POST /api/v1/sessions/{id}/step-over` - Step over
- `POST /api/v1/sessions/{id}/step-into` - Step into
- `POST /api/v1/sessions/{id}/step-out` - Step out
- `POST /api/v1/sessions/{id}/continue` - Continue execution
- `POST /api/v1/sessions/{id}/pause` - Pause execution

#### Chat
- `GET /api/v1/sessions/{id}/chat/history` - Get chat history
- `POST /api/v1/sessions/{id}/chat/send` - Send message
- `WS /api/v1/sessions/{id}/chat/stream` - Stream chat (WebSocket)

---

## Database Design

See project2_MASTER_PLAN.md for complete database schema.

---

**Document Version**: 3.0.0  
**Created**: 2024-12-30  
**Updated**: 2024-12-30  
**Status**: Ready for Implementation
