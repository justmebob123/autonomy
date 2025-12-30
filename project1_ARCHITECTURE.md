# PROJECT 1 ARCHITECTURE: AI-Powered Project Planning & Management Platform

> **Companion Document**: See `project1_MASTER_PLAN.md` for objectives and requirements  
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
6. [Web Search Tool](#web-search-tool)
7. [Planning Tools](#planning-tools)
8. [Collaboration Features](#collaboration-features)
9. [API Design](#api-design)
10. [Database Design](#database-design)
11. [Security Architecture](#security-architecture)
12. [Deployment Architecture](#deployment-architecture)

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
│  │  /projects  /objectives  /tasks  /search  /chat  /timeline  ││
│  └──────────────────────┬───────────────────────────────────────┘│
└─────────────────────────┼────────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────────┐
│                   Service Layer                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Project  │  │Objective │  │   Task   │  │   Chat   │        │
│  │ Service  │  │ Service  │  │ Service  │  │ Service  │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │   Web    │  │ Timeline │  │ Resource │  │   Risk   │        │
│  │  Search  │  │Generator │  │Estimator │  │Assessment│        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────┬────────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────────┐
│                   Analysis Engine Layer                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐         │
│  │MASTER_   │  │   Gap    │  │Progress  │  │  Risk   │         │
│  │PLAN      │  │ Detector │  │Calculator│  │ Analyzer│         │
│  │ Parser   │  └──────────┘  └──────────┘  └─────────┘         │
│  └──────────┘                                                    │
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
│  │  Projects | Objectives | Tasks | Risks | Comments | Users   ││
│  └──────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

### System Characteristics

- **Architecture Style**: Layered + Service-Oriented
- **API Style**: RESTful + WebSocket for real-time
- **Frontend**: Custom HTML/CSS/JavaScript (no frameworks)
- **Backend**: Custom WSGI application (Python stdlib only)
- **Data Storage**: SQLite (or MySQL)
- **Deployment**: Apache + mod_wsgi
- **Focus**: Document analysis and project planning

---

## Architecture Patterns

### 1. Layered Architecture Pattern

**Purpose**: Separation of concerns across layers

**Layers**:
1. **Presentation Layer** - Frontend UI components
2. **API Layer** - REST endpoints and WebSocket handlers
3. **Service Layer** - Business logic and orchestration
4. **Analysis Layer** - Document parsing and analysis
5. **Data Access Layer** - Database operations
6. **Persistence Layer** - SQLite/MySQL storage

### 2. Service Pattern

**Purpose**: Encapsulate business logic

```python
class ProjectService:
    """Service for project operations"""
    
    def __init__(self, project_repo, objective_repo, master_plan_parser):
        self.project_repo = project_repo
        self.objective_repo = objective_repo
        self.parser = master_plan_parser
    
    def analyze_master_plan(self, project_id: str) -> Analysis:
        """Analyze MASTER_PLAN.md"""
        project = self.project_repo.find_by_id(project_id)
        content = self._read_master_plan(project.master_plan_path)
        
        # Parse objectives
        objectives = self.parser.extract_objectives(content)
        
        # Save to database
        for obj in objectives:
            self.objective_repo.save(obj)
        
        # Detect gaps
        gaps = self._detect_gaps(project_id, objectives)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(objectives, gaps)
        
        return Analysis(
            objectives=objectives,
            gaps=gaps,
            recommendations=recommendations
        )
```

### 3. Repository Pattern

**Purpose**: Abstract data access

```python
class ObjectiveRepository:
    """Repository for objective data"""
    
    def __init__(self, db):
        self.db = db
    
    def find_by_project(self, project_id: str) -> List[Objective]:
        """Find objectives by project"""
        query = """
            SELECT * FROM objectives 
            WHERE project_id = ? 
            ORDER BY priority DESC
        """
        rows = self.db.fetchall(query, (project_id,))
        return [self._row_to_objective(row) for row in rows]
    
    def save(self, objective: Objective) -> None:
        """Save objective"""
        query = """
            INSERT OR REPLACE INTO objectives 
            (id, project_id, type, title, description, status, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute(query, (
            objective.id,
            objective.project_id,
            objective.type,
            objective.title,
            objective.description,
            objective.status,
            objective.priority
        ))
        self.db.commit()
```

---

## Component Design

### 1. Frontend Components

#### 1.1 Planning Dashboard Component

**Purpose**: Project overview and key metrics

**HTML Structure**:
```html
<div id="planning-dashboard">
    <div class="dashboard-header">
        <h1 id="project-name">Project Name</h1>
        <div class="dashboard-actions">
            <button id="analyze-btn">Analyze MASTER_PLAN</button>
            <button id="generate-timeline-btn">Generate Timeline</button>
        </div>
    </div>
    
    <div class="dashboard-metrics">
        <div class="metric-card">
            <h3>Completion</h3>
            <div class="metric-value">65%</div>
            <div class="metric-trend">↑ 5% this week</div>
        </div>
        <div class="metric-card">
            <h3>Objectives</h3>
            <div class="metric-value">12 / 20</div>
            <div class="metric-trend">8 remaining</div>
        </div>
        <div class="metric-card">
            <h3>Risks</h3>
            <div class="metric-value">3 High</div>
            <div class="metric-trend">2 new this week</div>
        </div>
        <div class="metric-card">
            <h3>Velocity</h3>
            <div class="metric-value">2.5 obj/week</div>
            <div class="metric-trend">On track</div>
        </div>
    </div>
    
    <div class="dashboard-charts">
        <div class="chart-container">
            <h3>Progress Over Time</h3>
            <canvas id="progress-chart"></canvas>
        </div>
        <div class="chart-container">
            <h3>Burndown Chart</h3>
            <canvas id="burndown-chart"></canvas>
        </div>
    </div>
    
    <div class="dashboard-sections">
        <div class="section">
            <h3>Recent Activity</h3>
            <div id="activity-feed"></div>
        </div>
        <div class="section">
            <h3>Upcoming Milestones</h3>
            <div id="milestones-list"></div>
        </div>
    </div>
</div>
```

**JavaScript Implementation**:
```javascript
class PlanningDashboard {
    constructor(projectId) {
        this.projectId = projectId;
        this.metrics = null;
        this.charts = {};
    }
    
    async load() {
        // Load dashboard data
        const response = await fetch(`/api/v1/projects/${this.projectId}/dashboard`, {
            headers: {'Authorization': `Bearer ${this.getToken()}`}
        });
        const data = await response.json();
        
        this.metrics = data.metrics;
        this.renderMetrics();
        this.renderCharts(data.charts);
        this.renderActivity(data.activity);
        this.renderMilestones(data.milestones);
    }
    
    renderMetrics() {
        // Update metric cards
        document.querySelector('.metric-card:nth-child(1) .metric-value')
            .textContent = `${this.metrics.completion}%`;
        document.querySelector('.metric-card:nth-child(2) .metric-value')
            .textContent = `${this.metrics.completed} / ${this.metrics.total}`;
        // ... more metrics
    }
    
    renderCharts(chartData) {
        // Render progress chart
        this.charts.progress = this.createLineChart(
            'progress-chart',
            chartData.progress
        );
        
        // Render burndown chart
        this.charts.burndown = this.createLineChart(
            'burndown-chart',
            chartData.burndown
        );
    }
    
    createLineChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        const ctx = canvas.getContext('2d');
        
        // Simple line chart implementation
        // (In production, could use Chart.js or custom implementation)
        const width = canvas.width;
        const height = canvas.height;
        const padding = 40;
        
        // Draw axes
        ctx.beginPath();
        ctx.moveTo(padding, padding);
        ctx.lineTo(padding, height - padding);
        ctx.lineTo(width - padding, height - padding);
        ctx.stroke();
        
        // Draw data points
        const xScale = (width - 2 * padding) / (data.length - 1);
        const yScale = (height - 2 * padding) / 100;
        
        ctx.beginPath();
        data.forEach((value, index) => {
            const x = padding + index * xScale;
            const y = height - padding - value * yScale;
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        ctx.strokeStyle = '#2196f3';
        ctx.lineWidth = 2;
        ctx.stroke();
        
        return canvas;
    }
    
    getToken() {
        return localStorage.getItem('auth_token');
    }
}

// Initialize dashboard
const dashboard = new PlanningDashboard(projectId);
dashboard.load();
```

#### 1.2 Gantt Chart Component

**Purpose**: Visualize project timeline

**JavaScript Implementation**:
```javascript
class GanttChart {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.tasks = [];
        this.startDate = null;
        this.endDate = null;
    }
    
    async load(projectId) {
        const response = await fetch(`/api/v1/projects/${projectId}/timeline`, {
            headers: {'Authorization': `Bearer ${this.getToken()}`}
        });
        const data = await response.json();
        
        this.tasks = data.tasks;
        this.startDate = new Date(data.start_date);
        this.endDate = new Date(data.end_date);
        
        this.render();
    }
    
    render() {
        const html = `
            <div class="gantt-chart">
                <div class="gantt-header">
                    <div class="gantt-timeline">
                        ${this.renderTimeline()}
                    </div>
                </div>
                <div class="gantt-body">
                    ${this.renderTasks()}
                </div>
            </div>
        `;
        
        this.container.innerHTML = html;
        this.attachEventListeners();
    }
    
    renderTimeline() {
        const days = this.getDaysBetween(this.startDate, this.endDate);
        const months = this.getMonthsBetween(this.startDate, this.endDate);
        
        let html = '<div class="gantt-months">';
        months.forEach(month => {
            html += `<div class="gantt-month" style="width: ${month.days * 30}px">
                ${month.name}
            </div>`;
        });
        html += '</div>';
        
        html += '<div class="gantt-days">';
        days.forEach(day => {
            html += `<div class="gantt-day">${day}</div>`;
        });
        html += '</div>';
        
        return html;
    }
    
    renderTasks() {
        return this.tasks.map(task => {
            const startOffset = this.getDaysBetween(this.startDate, new Date(task.start_date));
            const duration = this.getDaysBetween(new Date(task.start_date), new Date(task.end_date));
            
            return `
                <div class="gantt-task-row">
                    <div class="gantt-task-label">${task.title}</div>
                    <div class="gantt-task-bar-container">
                        <div class="gantt-task-bar ${task.status}" 
                             style="left: ${startOffset * 30}px; width: ${duration * 30}px"
                             data-task-id="${task.id}">
                            <span class="gantt-task-progress" style="width: ${task.completion}%"></span>
                        </div>
                        ${this.renderDependencies(task)}
                    </div>
                </div>
            `;
        }).join('');
    }
    
    renderDependencies(task) {
        if (!task.dependencies || task.dependencies.length === 0) {
            return '';
        }
        
        // Draw dependency lines
        return task.dependencies.map(depId => {
            const depTask = this.tasks.find(t => t.id === depId);
            if (!depTask) return '';
            
            return `<svg class="gantt-dependency-line">
                <line x1="0" y1="0" x2="100" y2="0" stroke="#999" />
            </svg>`;
        }).join('');
    }
    
    getDaysBetween(start, end) {
        const days = [];
        const current = new Date(start);
        while (current <= end) {
            days.push(current.getDate());
            current.setDate(current.getDate() + 1);
        }
        return days;
    }
    
    getMonthsBetween(start, end) {
        const months = [];
        const current = new Date(start);
        while (current <= end) {
            const monthStart = new Date(current);
            const monthEnd = new Date(current.getFullYear(), current.getMonth() + 1, 0);
            const days = this.getDaysBetween(monthStart, monthEnd).length;
            
            months.push({
                name: current.toLocaleString('default', { month: 'short' }),
                days: days
            });
            
            current.setMonth(current.getMonth() + 1);
        }
        return months;
    }
    
    attachEventListeners() {
        // Add drag-and-drop for task bars
        const taskBars = this.container.querySelectorAll('.gantt-task-bar');
        taskBars.forEach(bar => {
            bar.addEventListener('mousedown', (e) => this.startDrag(e, bar));
        });
    }
    
    startDrag(e, bar) {
        // Implement drag-and-drop for rescheduling
        // ... drag logic
    }
    
    getToken() {
        return localStorage.getItem('auth_token');
    }
}

const gantt = new GanttChart('gantt-container');
gantt.load(projectId);
```

#### 1.3 Objective Hierarchy Tree Component

**Purpose**: Visualize objective relationships

**JavaScript Implementation**:
```javascript
class ObjectiveTree {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.objectives = [];
    }
    
    async load(projectId) {
        const response = await fetch(`/api/v1/projects/${projectId}/objectives`, {
            headers: {'Authorization': `Bearer ${this.getToken()}`}
        });
        const data = await response.json();
        
        this.objectives = data.objectives;
        this.render();
    }
    
    render() {
        const tree = this.buildTree(this.objectives);
        const html = this.renderNode(tree);
        this.container.innerHTML = html;
        this.attachEventListeners();
    }
    
    buildTree(objectives) {
        // Group by type
        const primary = objectives.filter(o => o.type === 'primary');
        const secondary = objectives.filter(o => o.type === 'secondary');
        const tertiary = objectives.filter(o => o.type === 'tertiary');
        
        // Build hierarchy
        return {
            type: 'root',
            children: primary.map(p => ({
                ...p,
                children: secondary.filter(s => 
                    s.dependencies && s.dependencies.includes(p.id)
                ).map(s => ({
                    ...s,
                    children: tertiary.filter(t =>
                        t.dependencies && t.dependencies.includes(s.id)
                    )
                }))
            }))
        };
    }
    
    renderNode(node, level = 0) {
        if (node.type === 'root') {
            return `<div class="objective-tree">
                ${node.children.map(child => this.renderNode(child, 0)).join('')}
            </div>`;
        }
        
        const statusClass = node.status || 'not_started';
        const completionPercent = node.completion_percentage || 0;
        
        return `
            <div class="objective-node level-${level}" data-id="${node.id}">
                <div class="objective-header ${statusClass}">
                    <span class="objective-toggle">
                        ${node.children && node.children.length > 0 ? '▼' : ''}
                    </span>
                    <span class="objective-type">${node.type}</span>
                    <span class="objective-title">${node.title}</span>
                    <span class="objective-completion">${completionPercent}%</span>
                    <div class="objective-progress-bar">
                        <div class="objective-progress-fill" 
                             style="width: ${completionPercent}%"></div>
                    </div>
                </div>
                ${node.children && node.children.length > 0 ? `
                    <div class="objective-children">
                        ${node.children.map(child => this.renderNode(child, level + 1)).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    attachEventListeners() {
        // Toggle expand/collapse
        const toggles = this.container.querySelectorAll('.objective-toggle');
        toggles.forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                const node = e.target.closest('.objective-node');
                const children = node.querySelector('.objective-children');
                if (children) {
                    children.style.display = 
                        children.style.display === 'none' ? 'block' : 'none';
                    e.target.textContent = 
                        children.style.display === 'none' ? '▶' : '▼';
                }
            });
        });
        
        // Click to view details
        const headers = this.container.querySelectorAll('.objective-header');
        headers.forEach(header => {
            header.addEventListener('click', (e) => {
                if (e.target.classList.contains('objective-toggle')) return;
                const node = e.target.closest('.objective-node');
                const objectiveId = node.dataset.id;
                this.showObjectiveDetails(objectiveId);
            });
        });
    }
    
    showObjectiveDetails(objectiveId) {
        // Show objective details in modal or side panel
        window.location.href = `/objectives/${objectiveId}`;
    }
    
    getToken() {
        return localStorage.getItem('auth_token');
    }
}

const objectiveTree = new ObjectiveTree('objective-tree-container');
objectiveTree.load(projectId);
```

### 2. Backend Components

#### 2.1 MASTER_PLAN.md Parser

**Purpose**: Extract objectives from MASTER_PLAN.md

```python
import re
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class Objective:
    type: str  # primary, secondary, tertiary
    title: str
    description: str
    dependencies: List[str]
    success_criteria: List[str]

class MasterPlanParser:
    """Parse MASTER_PLAN.md files"""
    
    def __init__(self):
        self.objective_pattern = re.compile(
            r'^#{1,3}\s+(\d+\.?\d*\.?\d*)\s+(.+)$',
            re.MULTILINE
        )
    
    def parse(self, content: str) -> Dict:
        """Parse MASTER_PLAN.md content"""
        objectives = self.extract_objectives(content)
        dependencies = self.extract_dependencies(content)
        success_criteria = self.extract_success_criteria(content)
        
        return {
            'objectives': objectives,
            'dependencies': dependencies,
            'success_criteria': success_criteria
        }
    
    def extract_objectives(self, content: str) -> List[Objective]:
        """Extract objectives from content"""
        objectives = []
        lines = content.split('
')
        
        current_objective = None
        current_description = []
        
        for line in lines:
            # Check for objective header
            match = self.objective_pattern.match(line)
            if match:
                # Save previous objective
                if current_objective:
                    current_objective.description = '
'.join(current_description)
                    objectives.append(current_objective)
                
                # Start new objective
                number = match.group(1)
                title = match.group(2)
                obj_type = self._determine_type(number)
                
                current_objective = Objective(
                    type=obj_type,
                    title=title,
                    description='',
                    dependencies=[],
                    success_criteria=[]
                )
                current_description = []
            
            elif current_objective:
                # Add to description
                current_description.append(line)
        
        # Save last objective
        if current_objective:
            current_objective.description = '
'.join(current_description)
            objectives.append(current_objective)
        
        return objectives
    
    def _determine_type(self, number: str) -> str:
        """Determine objective type from number"""
        parts = number.split('.')
        if len(parts) == 1:
            return 'primary'
        elif len(parts) == 2:
            return 'secondary'
        else:
            return 'tertiary'
    
    def extract_dependencies(self, content: str) -> Dict[str, List[str]]:
        """Extract dependencies between objectives"""
        dependencies = {}
        
        # Look for dependency keywords
        dep_pattern = re.compile(
            r'depends on|requires|needs|after|following',
            re.IGNORECASE
        )
        
        # ... dependency extraction logic
        
        return dependencies
    
    def extract_success_criteria(self, content: str) -> Dict[str, List[str]]:
        """Extract success criteria"""
        criteria = {}
        
        # Look for success criteria sections
        criteria_pattern = re.compile(
            r'success criteria:(.+?)(?=
#|\Z)',
            re.IGNORECASE | re.DOTALL
        )
        
        # ... criteria extraction logic
        
        return criteria
```

#### 2.2 Web Search Tool

**Purpose**: Search the web for project research

```python
import urllib.request
import urllib.parse
import json
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    published_date: str
    score: float

class WebSearchTool:
    """Custom web search tool"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.cache = {}
    
    def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Search the web"""
        # Check cache
        cache_key = f"{query}:{num_results}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Perform search
        results = self._search_google(query, num_results)
        
        # Cache results
        self.cache[cache_key] = results
        
        return results
    
    def _search_google(self, query: str, num_results: int) -> List[SearchResult]:
        """Search using Google Custom Search API"""
        base_url = "https://www.googleapis.com/customsearch/v1"
        
        params = {
            'key': self.api_key,
            'cx': 'your-search-engine-id',
            'q': query,
            'num': num_results
        }
        
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                results = []
                for item in data.get('items', []):
                    results.append(SearchResult(
                        title=item.get('title', ''),
                        url=item.get('link', ''),
                        snippet=item.get('snippet', ''),
                        published_date=item.get('pagemap', {}).get('metatags', [{}])[0].get('article:published_time', ''),
                        score=1.0
                    ))
                
                return results
        
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def research_technology(self, tech_name: str) -> Dict:
        """Research a specific technology"""
        queries = [
            f"{tech_name} documentation",
            f"{tech_name} tutorial",
            f"{tech_name} pros and cons",
            f"{tech_name} best practices",
            f"{tech_name} vs alternatives"
        ]
        
        results = {}
        for query in queries:
            results[query] = self.search(query, num_results=5)
        
        return results
    
    def find_similar_projects(self, description: str) -> List[SearchResult]:
        """Find similar projects"""
        query = f"open source project {description}"
        return self.search(query, num_results=20)
    
    def competitive_analysis(self, project_name: str) -> Dict:
        """Analyze competitors"""
        queries = [
            f"{project_name} competitors",
            f"{project_name} alternatives",
            f"{project_name} comparison",
            f"best {project_name} alternatives"
        ]
        
        results = {}
        for query in queries:
            results[query] = self.search(query, num_results=10)
        
        return results
```

#### 2.3 Timeline Generator

**Purpose**: Generate project timelines

```python
from datetime import datetime, timedelta
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class Task:
    id: str
    title: str
    duration_days: int
    dependencies: List[str]
    assigned_to: str
    start_date: datetime
    end_date: datetime

class TimelineGenerator:
    """Generate project timelines"""
    
    def __init__(self):
        self.tasks = []
    
    def generate(self, objectives: List[Objective]) -> Dict:
        """Generate timeline from objectives"""
        # Convert objectives to tasks
        tasks = self._objectives_to_tasks(objectives)
        
        # Calculate dependencies
        dep_graph = self._build_dependency_graph(tasks)
        
        # Calculate critical path
        critical_path = self._calculate_critical_path(dep_graph)
        
        # Schedule tasks
        scheduled_tasks = self._schedule_tasks(tasks, dep_graph)
        
        # Calculate project duration
        start_date = min(t.start_date for t in scheduled_tasks)
        end_date = max(t.end_date for t in scheduled_tasks)
        
        return {
            'tasks': scheduled_tasks,
            'critical_path': critical_path,
            'start_date': start_date,
            'end_date': end_date,
            'duration_days': (end_date - start_date).days
        }
    
    def _objectives_to_tasks(self, objectives: List[Objective]) -> List[Task]:
        """Convert objectives to tasks"""
        tasks = []
        
        for obj in objectives:
            # Estimate duration based on objective type
            if obj.type == 'primary':
                duration = 30  # 30 days
            elif obj.type == 'secondary':
                duration = 14  # 14 days
            else:
                duration = 7  # 7 days
            
            task = Task(
                id=f"task_{len(tasks)}",
                title=obj.title,
                duration_days=duration,
                dependencies=obj.dependencies,
                assigned_to='',
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=duration)
            )
            tasks.append(task)
        
        return tasks
    
    def _build_dependency_graph(self, tasks: List[Task]) -> Dict:
        """Build dependency graph"""
        graph = {task.id: [] for task in tasks}
        
        for task in tasks:
            for dep_id in task.dependencies:
                if dep_id in graph:
                    graph[dep_id].append(task.id)
        
        return graph
    
    def _calculate_critical_path(self, graph: Dict) -> List[str]:
        """Calculate critical path using CPM"""
        # Topological sort
        sorted_tasks = self._topological_sort(graph)
        
        # Calculate earliest start times
        earliest_start = {}
        for task_id in sorted_tasks:
            if not graph[task_id]:
                earliest_start[task_id] = 0
            else:
                earliest_start[task_id] = max(
                    earliest_start[dep] + self._get_task_duration(dep)
                    for dep in graph[task_id]
                )
        
        # Calculate latest start times
        latest_start = {}
        for task_id in reversed(sorted_tasks):
            if not any(task_id in deps for deps in graph.values()):
                latest_start[task_id] = earliest_start[task_id]
            else:
                latest_start[task_id] = min(
                    latest_start[successor] - self._get_task_duration(task_id)
                    for successor, deps in graph.items()
                    if task_id in deps
                )
        
        # Find critical path (tasks with zero slack)
        critical_path = [
            task_id for task_id in sorted_tasks
            if earliest_start[task_id] == latest_start[task_id]
        ]
        
        return critical_path
    
    def _topological_sort(self, graph: Dict) -> List[str]:
        """Topological sort of dependency graph"""
        visited = set()
        stack = []
        
        def dfs(node):
            visited.add(node)
            for neighbor in graph[node]:
                if neighbor not in visited:
                    dfs(neighbor)
            stack.append(node)
        
        for node in graph:
            if node not in visited:
                dfs(node)
        
        return list(reversed(stack))
    
    def _schedule_tasks(self, tasks: List[Task], graph: Dict) -> List[Task]:
        """Schedule tasks based on dependencies"""
        scheduled = {}
        start_date = datetime.now()
        
        # Sort tasks by dependencies
        sorted_tasks = self._topological_sort(graph)
        
        for task_id in sorted_tasks:
            task = next(t for t in tasks if t.id == task_id)
            
            # Find latest end date of dependencies
            if task.dependencies:
                dep_end_dates = [
                    scheduled[dep_id].end_date
                    for dep_id in task.dependencies
                    if dep_id in scheduled
                ]
                if dep_end_dates:
                    task.start_date = max(dep_end_dates)
                else:
                    task.start_date = start_date
            else:
                task.start_date = start_date
            
            task.end_date = task.start_date + timedelta(days=task.duration_days)
            scheduled[task_id] = task
        
        return list(scheduled.values())
    
    def _get_task_duration(self, task_id: str) -> int:
        """Get task duration"""
        task = next((t for t in self.tasks if t.id == task_id), None)
        return task.duration_days if task else 0
```

#### 2.4 Resource Estimator

**Purpose**: Estimate project resources

```python
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class ResourceEstimate:
    total_hours: float
    total_days: float
    team_size: int
    cost: float
    skills_required: List[str]

class ResourceEstimator:
    """Estimate project resources"""
    
    def __init__(self):
        self.hourly_rate = 100  # Default hourly rate
        self.hours_per_day = 8
    
    def estimate(self, objectives: List[Objective]) -> ResourceEstimate:
        """Estimate resources for objectives"""
        # Calculate total effort
        total_hours = self._calculate_effort(objectives)
        
        # Identify required skills
        skills = self._identify_skills(objectives)
        
        # Recommend team size
        team_size = self._recommend_team_size(total_hours, skills)
        
        # Calculate cost
        cost = total_hours * self.hourly_rate
        
        # Calculate duration
        total_days = total_hours / (self.hours_per_day * team_size)
        
        return ResourceEstimate(
            total_hours=total_hours,
            total_days=total_days,
            team_size=team_size,
            cost=cost,
            skills_required=skills
        )
    
    def _calculate_effort(self, objectives: List[Objective]) -> float:
        """Calculate total effort in hours"""
        total_hours = 0
        
        for obj in objectives:
            # Estimate based on objective type and complexity
            if obj.type == 'primary':
                base_hours = 240  # 30 days * 8 hours
            elif obj.type == 'secondary':
                base_hours = 112  # 14 days * 8 hours
            else:
                base_hours = 56  # 7 days * 8 hours
            
            # Adjust for complexity
            complexity_multiplier = self._estimate_complexity(obj)
            total_hours += base_hours * complexity_multiplier
        
        return total_hours
    
    def _estimate_complexity(self, objective: Objective) -> float:
        """Estimate objective complexity"""
        # Simple heuristic based on description length and keywords
        description = objective.description.lower()
        
        complexity = 1.0
        
        # Check for complexity keywords
        if any(word in description for word in ['complex', 'advanced', 'sophisticated']):
            complexity *= 1.5
        if any(word in description for word in ['simple', 'basic', 'straightforward']):
            complexity *= 0.7
        if any(word in description for word in ['integration', 'api', 'database']):
            complexity *= 1.2
        
        return complexity
    
    def _identify_skills(self, objectives: List[Objective]) -> List[str]:
        """Identify required skills"""
        skills = set()
        
        for obj in objectives:
            description = obj.description.lower()
            
            # Identify skills from keywords
            if 'frontend' in description or 'ui' in description:
                skills.add('Frontend Development')
            if 'backend' in description or 'api' in description:
                skills.add('Backend Development')
            if 'database' in description or 'sql' in description:
                skills.add('Database Design')
            if 'devops' in description or 'deployment' in description:
                skills.add('DevOps')
            if 'testing' in description or 'qa' in description:
                skills.add('QA/Testing')
            if 'design' in description or 'ux' in description:
                skills.add('UI/UX Design')
        
        return list(skills)
    
    def _recommend_team_size(self, total_hours: float, skills: List[str]) -> int:
        """Recommend team size"""
        # Base team size on total hours
        if total_hours < 500:
            base_size = 2
        elif total_hours < 2000:
            base_size = 4
        elif total_hours < 5000:
            base_size = 6
        else:
            base_size = 8
        
        # Adjust for skill diversity
        skill_adjustment = len(skills) // 2
        
        return base_size + skill_adjustment
```

---

## API Design

### Complete API Specification

#### Projects
- `GET /api/v1/projects` - List all projects
- `POST /api/v1/projects` - Create new project
- `GET /api/v1/projects/{id}` - Get project details
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project
- `GET /api/v1/projects/{id}/dashboard` - Get dashboard data
- `POST /api/v1/projects/{id}/analyze` - Analyze MASTER_PLAN.md
- `GET /api/v1/projects/{id}/progress` - Get progress metrics
- `GET /api/v1/projects/{id}/timeline` - Get timeline
- `POST /api/v1/projects/{id}/timeline/generate` - Generate timeline

#### Objectives
- `GET /api/v1/projects/{id}/objectives` - List objectives
- `POST /api/v1/projects/{id}/objectives` - Create objective
- `GET /api/v1/objectives/{id}` - Get objective details
- `PUT /api/v1/objectives/{id}` - Update objective
- `DELETE /api/v1/objectives/{id}` - Delete objective
- `GET /api/v1/objectives/{id}/gaps` - Get gaps
- `GET /api/v1/objectives/{id}/dependencies` - Get dependencies

#### Tasks
- `GET /api/v1/objectives/{id}/tasks` - List tasks
- `POST /api/v1/objectives/{id}/tasks` - Create task
- `GET /api/v1/tasks/{id}` - Get task details
- `PUT /api/v1/tasks/{id}` - Update task
- `DELETE /api/v1/tasks/{id}` - Delete task
- `POST /api/v1/tasks/{id}/assign` - Assign task

#### Web Search
- `POST /api/v1/search` - Search the web
- `POST /api/v1/search/technology` - Research technology
- `POST /api/v1/search/projects` - Find similar projects
- `POST /api/v1/search/competitive` - Competitive analysis

#### Resources
- `POST /api/v1/projects/{id}/estimate` - Estimate resources
- `GET /api/v1/projects/{id}/resources` - Get resource allocation

#### Risks
- `GET /api/v1/projects/{id}/risks` - List risks
- `POST /api/v1/projects/{id}/risks` - Create risk
- `GET /api/v1/risks/{id}` - Get risk details
- `PUT /api/v1/risks/{id}` - Update risk
- `DELETE /api/v1/risks/{id}` - Delete risk

#### Comments
- `GET /api/v1/objectives/{id}/comments` - Get comments
- `POST /api/v1/objectives/{id}/comments` - Add comment
- `PUT /api/v1/comments/{id}` - Update comment
- `DELETE /api/v1/comments/{id}` - Delete comment

---

## Database Design

See project1_MASTER_PLAN.md for complete database schema.

---

## Security Architecture

### 1. Authentication
- JWT tokens with HMAC-SHA256
- Token expiration (1 hour default)
- Refresh token support
- Secure password hashing (SHA-256 with salt)

### 2. Authorization
- Role-based access control (RBAC)
- Project-level permissions
- User can only access their own projects
- Admin role for system management

### 3. Input Validation
- Validate all user inputs
- Sanitize file paths
- Prevent SQL injection
- Prevent XSS attacks

---

## Configuration Management

### Configuration File Structure

The application uses a standard INI configuration file for all settings.

**File**: `config/config.ini`

```ini
[server]
host = 0.0.0.0
port = 5000
workers = 4
threads = 2
debug = false

[database]
type = sqlite
path = /var/www/planning/data/planning.db

# For MySQL (optional):
# type = mysql
# host = localhost
# port = 3306
# database = planning
# user = planning_user
# password = secure_password
# pool_size = 10
# pool_recycle = 3600

[security]
jwt_secret = CHANGE_THIS_SECRET_KEY_IN_PRODUCTION
jwt_algorithm = HS256
jwt_expiry_seconds = 3600
password_hash_algorithm = sha256
password_salt_rounds = 10
session_timeout_seconds = 7200
max_login_attempts = 5
lockout_duration_seconds = 900

[ollama]
default_server = http://localhost:11434
default_model = qwen2.5-coder:32b
timeout_seconds = 300
max_retries = 3
retry_delay_seconds = 5

[git]
ssh_key_path = /var/www/planning/.ssh/id_rsa
default_branch = main
clone_timeout_seconds = 300
fetch_timeout_seconds = 60

[logging]
level = INFO
file = /var/www/planning/logs/application.log
max_size_bytes = 10485760
backup_count = 5
format = %(asctime)s - %(name)s - %(levelname)s - %(message)s

[paths]
project_root = /var/www/planning
data_dir = /var/www/planning/data
upload_dir = /var/www/planning/uploads
temp_dir = /var/www/planning/temp
static_dir = /var/www/planning/static
log_dir = /var/www/planning/logs

[web_search]
google_api_key = YOUR_GOOGLE_API_KEY
google_cx = YOUR_GOOGLE_CX
max_results = 10
timeout_seconds = 30

[limits]
max_upload_size_mb = 100
max_file_count = 1000
max_project_size_mb = 1000
max_thread_messages = 1000
max_concurrent_requests = 100
```

### Configuration Loading

```python
# config/loader.py
import configparser
import os
from pathlib import Path

class ConfigLoader:
    """Load and validate configuration from INI file."""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.environ.get('PLANNING_CONFIG', 'config/config.ini')
        
        self.config_path = Path(config_path)
        self.config = configparser.ConfigParser()
        self._load()
        self._validate()
    
    def _load(self):
        """Load configuration from file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        self.config.read(self.config_path)
    
    def _validate(self):
        """Validate required configuration sections and keys."""
        required_sections = ['server', 'database', 'security', 'paths']
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Validate critical settings
        if self.config['security']['jwt_secret'] == 'CHANGE_THIS_SECRET_KEY_IN_PRODUCTION':
            raise ValueError("JWT secret must be changed in production")
    
    def get(self, section: str, key: str, fallback=None):
        """Get configuration value."""
        return self.config.get(section, key, fallback=fallback)
    
    def getint(self, section: str, key: str, fallback=None):
        """Get integer configuration value."""
        return self.config.getint(section, key, fallback=fallback)
    
    def getboolean(self, section: str, key: str, fallback=None):
        """Get boolean configuration value."""
        return self.config.getboolean(section, key, fallback=fallback)
```

### Environment Variable Support

Configuration values can be overridden using environment variables:

```bash
# Override database settings
export PLANNING_DB_TYPE=mysql
export PLANNING_DB_HOST=db.example.com
export PLANNING_DB_PASSWORD=secure_password

# Override security settings
export PLANNING_JWT_SECRET=production_secret_key

# Override Ollama settings
export PLANNING_OLLAMA_SERVER=http://ollama.example.com:11434
```

---

## Deployment Architecture

### Directory Structure

```
/var/www/planning/
├── config/
│   ├── config.ini              # Main configuration
│   └── apache/
│       ├── http.conf           # HTTP vhost
│       └── https.conf          # HTTPS vhost
├── wsgi/
│   ├── application.py          # Custom WSGI application
│   ├── router.py              # Custom routing
│   ├── request.py             # Request parser
│   ├── response.py            # Response builder
│   ├── middleware.py          # Middleware
│   └── server.py              # WSGI entry point
├── api/
│   ├── projects.py            # Project endpoints
│   ├── objectives.py          # Objective endpoints
│   ├── chat.py               # Chat endpoints
│   └── ...                   # Other endpoints
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── data/
│   └── planning.db           # SQLite database
├── uploads/                  # User uploads
├── temp/                     # Temporary files
└── logs/                     # Application logs
```

### Apache Configuration

#### HTTP Virtual Host (Port 80)

**File**: `config/apache/http.conf`

```apache
<VirtualHost *:80>
    ServerName planning-platform.example.com
    ServerAdmin admin@example.com
    
    # Redirect all HTTP traffic to HTTPS
    Redirect permanent / https://planning-platform.example.com/
    
    # Logging
    ErrorLog ${APACHE_LOG_DIR}/planning-http-error.log
    CustomLog ${APACHE_LOG_DIR}/planning-http-access.log combined
    LogLevel warn
</VirtualHost>
```

#### HTTPS Virtual Host (Port 443)

**File**: `config/apache/https.conf`

```apache
<VirtualHost *:443>
    ServerName planning-platform.example.com
    ServerAdmin admin@example.com
    
    # SSL/TLS Configuration
    SSLEngine on
    SSLProtocol all -SSLv2 -SSLv3 -TLSv1 -TLSv1.1
    SSLCipherSuite HIGH:!aNULL:!MD5:!3DES
    SSLHonorCipherOrder on
    
    # SSL Certificates
    SSLCertificateFile /etc/ssl/certs/planning-platform.crt
    SSLCertificateKeyFile /etc/ssl/private/planning-platform.key
    SSLCertificateChainFile /etc/ssl/certs/planning-platform-chain.crt
    
    # Security Headers
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
    Header always set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
    
    # WSGI Configuration
    WSGIDaemonProcess planning \
        user=www-data \
        group=www-data \
        processes=4 \
        threads=2 \
        python-path=/var/www/planning \
        home=/var/www/planning \
        display-name=%{GROUP}
    
    WSGIProcessGroup planning
    WSGIApplicationGroup %{GLOBAL}
    WSGIScriptAlias / /var/www/planning/wsgi/server.py
    WSGIPassAuthorization On
    
    # Application Directory
    <Directory /var/www/planning>
        Require all granted
        Options -Indexes +FollowSymLinks
        AllowOverride None
    </Directory>
    
    # WSGI Script
    <Files wsgi/server.py>
        Require all granted
    </Files>
    
    # Static Files
    Alias /static /var/www/planning/static
    <Directory /var/www/planning/static>
        Require all granted
        Options -Indexes -FollowSymLinks
        AllowOverride None
        
        # Cache static files for 1 year
        <IfModule mod_expires.c>
            ExpiresActive On
            ExpiresDefault "access plus 1 year"
        </IfModule>
        
        # Compress static files
        <IfModule mod_deflate.c>
            AddOutputFilterByType DEFLATE text/css text/javascript application/javascript
        </IfModule>
    </Directory>
    
    # Uploads Directory (protected)
    Alias /uploads /var/www/planning/uploads
    <Directory /var/www/planning/uploads>
        Require all denied
    </Directory>
    
    # Logging
    ErrorLog ${APACHE_LOG_DIR}/planning-https-error.log
    CustomLog ${APACHE_LOG_DIR}/planning-https-access.log combined
    LogLevel info
    
    # Performance Tuning
    KeepAlive On
    KeepAliveTimeout 5
    MaxKeepAliveRequests 100
</VirtualHost>
```

### Custom WSGI Application

#### WSGI Entry Point

**File**: `wsgi/server.py`

```python
"""
WSGI Server Entry Point

This is the entry point for Apache mod_wsgi.
Uses only Python standard library - NO external frameworks.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import custom WSGI application
from wsgi.application import WSGIApplication
from config.loader import ConfigLoader

# Load configuration
config = ConfigLoader()

# Create WSGI application instance
application = WSGIApplication(config)

# This 'application' callable is what Apache mod_wsgi will use
```

#### Custom WSGI Application Class

**File**: `wsgi/application.py`

```python
"""
Custom WSGI Application

Implements a complete WSGI application using only Python standard library.
NO external frameworks (Flask, FastAPI, etc.)
"""

from wsgi.router import Router
from wsgi.request import Request
from wsgi.response import Response
from wsgi.middleware import MiddlewareStack
import logging

class WSGIApplication:
    """Custom WSGI application class."""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize router
        self.router = Router()
        
        # Initialize middleware stack
        self.middleware = MiddlewareStack()
        self.middleware.add('cors', self._cors_middleware)
        self.middleware.add('auth', self._auth_middleware)
        self.middleware.add('logging', self._logging_middleware)
        
        # Register routes
        self._register_routes()
    
    def __call__(self, environ, start_response):
        """
        WSGI application callable.
        
        This is called by Apache mod_wsgi for each request.
        """
        try:
            # Parse request
            request = Request(environ)
            
            # Apply middleware
            response = self.middleware.process_request(request)
            if response:
                return response(environ, start_response)
            
            # Route request
            response = self.router.route(request)
            
            # Apply response middleware
            response = self.middleware.process_response(request, response)
            
            # Return WSGI response
            return response(environ, start_response)
            
        except Exception as e:
            self.logger.error(f"Application error: {e}", exc_info=True)
            response = Response(
                body={'error': 'Internal server error'},
                status=500
            )
            return response(environ, start_response)
    
    def _register_routes(self):
        """Register all application routes."""
        from api import projects, objectives, chat, files, git, servers, prompts
        
        # Project routes
        self.router.add_route('GET', '/api/projects', projects.list_projects)
        self.router.add_route('POST', '/api/projects', projects.create_project)
        self.router.add_route('GET', '/api/projects/<id>', projects.get_project)
        self.router.add_route('PUT', '/api/projects/<id>', projects.update_project)
        self.router.add_route('DELETE', '/api/projects/<id>', projects.delete_project)
        
        # Objective routes
        self.router.add_route('GET', '/api/projects/<project_id>/objectives', objectives.list_objectives)
        self.router.add_route('POST', '/api/projects/<project_id>/objectives', objectives.create_objective)
        
        # Chat routes
        self.router.add_route('GET', '/api/threads', chat.list_threads)
        self.router.add_route('POST', '/api/threads', chat.create_thread)
        self.router.add_route('GET', '/api/threads/<id>/messages', chat.get_messages)
        self.router.add_route('POST', '/api/threads/<id>/messages', chat.send_message)
        
        # ... more routes ...
    
    def _cors_middleware(self, request):
        """CORS middleware."""
        # Add CORS headers if needed
        return None
    
    def _auth_middleware(self, request):
        """Authentication middleware."""
        # Check JWT token
        # Validate user session
        return None
    
    def _logging_middleware(self, request):
        """Logging middleware."""
        self.logger.info(f"{request.method} {request.path}")
        return None
```

#### Custom Router

**File**: `wsgi/router.py`

```python
"""
Custom Router

Implements URL routing using only Python standard library.
"""

import re
from typing import Callable, Dict, List, Tuple

class Router:
    """Custom URL router."""
    
    def __init__(self):
        self.routes: List[Tuple[str, str, Callable]] = []
    
    def add_route(self, method: str, pattern: str, handler: Callable):
        """Add a route."""
        # Convert pattern to regex
        # /api/projects/<id> -> /api/projects/(?P<id>[^/]+)
        regex_pattern = re.sub(r'<(\w+)>', r'(?P<\1>[^/]+)', pattern)
        regex_pattern = f'^{regex_pattern}$'
        
        self.routes.append((method, regex_pattern, handler))
    
    def route(self, request):
        """Route a request to the appropriate handler."""
        from wsgi.response import Response
        
        for method, pattern, handler in self.routes:
            if method != request.method:
                continue
            
            match = re.match(pattern, request.path)
            if match:
                # Extract path parameters
                kwargs = match.groupdict()
                
                # Call handler
                try:
                    result = handler(request, **kwargs)
                    
                    # Convert result to Response
                    if isinstance(result, Response):
                        return result
                    elif isinstance(result, dict):
                        return Response(body=result)
                    elif isinstance(result, tuple):
                        body, status = result
                        return Response(body=body, status=status)
                    else:
                        return Response(body=result)
                        
                except Exception as e:
                    return Response(
                        body={'error': str(e)},
                        status=500
                    )
        
        # No route found
        return Response(
            body={'error': 'Not found'},
            status=404
        )
```

#### Custom Request Parser

**File**: `wsgi/request.py`

```python
"""
Custom Request Parser

Parses WSGI environ into a request object.
"""

import json
from urllib.parse import parse_qs
from io import BytesIO

class Request:
    """Custom request object."""
    
    def __init__(self, environ):
        self.environ = environ
        self.method = environ['REQUEST_METHOD']
        self.path = environ['PATH_INFO']
        self.query_string = environ.get('QUERY_STRING', '')
        self.content_type = environ.get('CONTENT_TYPE', '')
        self.content_length = int(environ.get('CONTENT_LENGTH', 0) or 0)
        
        # Parse query parameters
        self.query_params = parse_qs(self.query_string)
        
        # Parse headers
        self.headers = self._parse_headers(environ)
        
        # Parse body
        self._body = None
        self._json = None
    
    def _parse_headers(self, environ):
        """Parse HTTP headers from environ."""
        headers = {}
        for key, value in environ.items():
            if key.startswith('HTTP_'):
                header_name = key[5:].replace('_', '-').title()
                headers[header_name] = value
        return headers
    
    @property
    def body(self):
        """Get request body as bytes."""
        if self._body is None:
            if self.content_length > 0:
                self._body = self.environ['wsgi.input'].read(self.content_length)
            else:
                self._body = b''
        return self._body
    
    @property
    def json(self):
        """Parse request body as JSON."""
        if self._json is None:
            if self.content_type == 'application/json':
                self._json = json.loads(self.body.decode('utf-8'))
            else:
                self._json = {}
        return self._json
    
    def get_header(self, name, default=None):
        """Get a header value."""
        return self.headers.get(name, default)
```

#### Custom Response Builder

**File**: `wsgi/response.py`

```python
"""
Custom Response Builder

Builds WSGI responses.
"""

import json

class Response:
    """Custom response object."""
    
    def __init__(self, body=None, status=200, headers=None):
        self.body = body
        self.status = status
        self.headers = headers or {}
        
        # Set default headers
        if 'Content-Type' not in self.headers:
            if isinstance(body, dict) or isinstance(body, list):
                self.headers['Content-Type'] = 'application/json'
            else:
                self.headers['Content-Type'] = 'text/plain'
    
    def __call__(self, environ, start_response):
        """WSGI response callable."""
        # Convert body to bytes
        if isinstance(self.body, dict) or isinstance(self.body, list):
            body_bytes = json.dumps(self.body).encode('utf-8')
        elif isinstance(self.body, str):
            body_bytes = self.body.encode('utf-8')
        elif isinstance(self.body, bytes):
            body_bytes = self.body
        else:
            body_bytes = str(self.body).encode('utf-8')
        
        # Set Content-Length
        self.headers['Content-Length'] = str(len(body_bytes))
        
        # Build status line
        status_line = f"{self.status} {self._get_status_text(self.status)}"
        
        # Build headers list
        headers_list = [(k, v) for k, v in self.headers.items()]
        
        # Call start_response
        start_response(status_line, headers_list)
        
        # Return body as iterable
        return [body_bytes]
    
    def _get_status_text(self, status):
        """Get status text for status code."""
        status_texts = {
            200: 'OK',
            201: 'Created',
            204: 'No Content',
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not Found',
            500: 'Internal Server Error',
        }
        return status_texts.get(status, 'Unknown')
```

#### Middleware System

**File**: `wsgi/middleware.py`

```python
"""
Custom Middleware System

Implements middleware for request/response processing.
"""

class MiddlewareStack:
    """Middleware stack."""
    
    def __init__(self):
        self.middleware = []
    
    def add(self, name, handler):
        """Add middleware to stack."""
        self.middleware.append((name, handler))
    
    def process_request(self, request):
        """Process request through middleware."""
        for name, handler in self.middleware:
            response = handler(request)
            if response:
                return response
        return None
    
    def process_response(self, request, response):
        """Process response through middleware."""
        # Apply response middleware in reverse order
        for name, handler in reversed(self.middleware):
            # Response middleware can modify response
            pass
        return response
```

### Deployment Instructions

#### 1. Install Apache and mod_wsgi

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install apache2 libapache2-mod-wsgi-py3

# Enable required modules
sudo a2enmod ssl
sudo a2enmod headers
sudo a2enmod rewrite
sudo a2enmod expires
sudo a2enmod deflate
```

#### 2. Create Application Directory

```bash
sudo mkdir -p /var/www/planning
sudo chown -R www-data:www-data /var/www/planning
```

#### 3. Deploy Application Files

```bash
# Copy application files
sudo cp -r wsgi/ /var/www/planning/
sudo cp -r api/ /var/www/planning/
sudo cp -r config/ /var/www/planning/
sudo cp -r static/ /var/www/planning/

# Create data directories
sudo mkdir -p /var/www/planning/data
sudo mkdir -p /var/www/planning/uploads
sudo mkdir -p /var/www/planning/temp
sudo mkdir -p /var/www/planning/logs

# Set permissions
sudo chown -R www-data:www-data /var/www/planning
sudo chmod -R 755 /var/www/planning
sudo chmod -R 775 /var/www/planning/data
sudo chmod -R 775 /var/www/planning/uploads
sudo chmod -R 775 /var/www/planning/temp
sudo chmod -R 775 /var/www/planning/logs
```

#### 4. Configure Application

```bash
# Edit configuration file
sudo nano /var/www/planning/config/config.ini

# IMPORTANT: Change these settings:
# - jwt_secret (use a strong random key)
# - database settings (if using MySQL)
# - ollama server URL
# - web search API keys
```

#### 5. Install SSL Certificate

```bash
# Using Let's Encrypt (recommended)
sudo apt-get install certbot python3-certbot-apache
sudo certbot --apache -d planning-platform.example.com

# Or manually install certificate
sudo cp your-cert.crt /etc/ssl/certs/planning-platform.crt
sudo cp your-key.key /etc/ssl/private/planning-platform.key
sudo cp your-chain.crt /etc/ssl/certs/planning-platform-chain.crt
sudo chmod 600 /etc/ssl/private/planning-platform.key
```

#### 6. Configure Apache

```bash
# Copy vhost configurations
sudo cp /var/www/planning/config/apache/http.conf /etc/apache2/sites-available/planning-http.conf
sudo cp /var/www/planning/config/apache/https.conf /etc/apache2/sites-available/planning-https.conf

# Enable sites
sudo a2ensite planning-http
sudo a2ensite planning-https

# Test configuration
sudo apache2ctl configtest

# Restart Apache
sudo systemctl restart apache2
```

#### 7. Initialize Database

```bash
# Run database initialization script
sudo -u www-data python3 /var/www/planning/scripts/init_db.py
```

#### 8. Verify Deployment

```bash
# Check Apache status
sudo systemctl status apache2

# Check application logs
sudo tail -f /var/www/planning/logs/application.log

# Check Apache logs
sudo tail -f /var/log/apache2/planning-https-error.log

# Test application
curl https://planning-platform.example.com/api/health
```

### Troubleshooting

#### Common Issues

1. **Permission Denied**
   ```bash
   sudo chown -R www-data:www-data /var/www/planning
   sudo chmod -R 755 /var/www/planning
   ```

2. **Module Not Found**
   ```bash
   # Check Python path in Apache config
   # Ensure python-path=/var/www/planning in WSGIDaemonProcess
   ```

3. **Database Connection Failed**
   ```bash
   # Check database file permissions
   sudo chmod 664 /var/www/planning/data/planning.db
   sudo chown www-data:www-data /var/www/planning/data/planning.db
   ```

4. **SSL Certificate Error**
   ```bash
   # Verify certificate files exist and have correct permissions
   sudo ls -la /etc/ssl/certs/planning-platform.crt
   sudo ls -la /etc/ssl/private/planning-platform.key
   ```

---

**Document Version**: 4.0.0  
**Created**: 2024-12-30  
**Updated**: 2024-12-30  
**Status**: Ready for Implementation
