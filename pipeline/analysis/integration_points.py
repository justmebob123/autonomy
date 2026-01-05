"""
Registry of known integration points that should not be flagged as gaps.

Integration points are components that are intentionally not used yet because
they are waiting to be wired up during the integration phase. They are NOT
dead code or bugs.
"""

INTEGRATION_POINTS = {
    # Services waiting for integration
    'services/git_integration.py': {
        'classes': ['GitIntegration'],
        'reason': 'Service interface for git operations - will be wired during integration'
    },
    'services/gap_detection.py': {
        'functions': ['detect_gaps'],
        'reason': 'Integration point for gap detection service - will be called by analysis system'
    },
    'services/recommendation_service.py': {
        'functions': ['generate_recommendations'],
        'reason': 'Service endpoint for recommendations - will be integrated with planning phase'
    },
    
    # API endpoints waiting for integration
    'api/ollama_servers.py': {
        'classes': ['OllamaServersAPI'],
        'reason': 'API endpoint class - will be registered with Flask app during integration'
    },
    'api/charts.py': {
        'classes': ['ChartsAPI'],
        'reason': 'API endpoint class - will be registered with Flask app during integration'
    },
    'api/reports.py': {
        'classes': ['ReportsAPI'],
        'reason': 'API endpoint class - will be registered with Flask app during integration'
    },
    
    # Models waiting for integration
    'models/prompt.py': {
        'classes': ['Prompt'],
        'reason': 'Data model - will be instantiated by services during integration'
    },
    'models/ollama_server.py': {
        'classes': ['OllamaServer'],
        'reason': 'Data model - will be instantiated by services during integration'
    },
    
    # Core components waiting for integration
    'core/config.py': {
        'classes': ['ConfigLoader'],
        'reason': 'Configuration loader - will be instantiated at application startup'
    },
    
    # Monitors waiting for integration
    'monitors/base.py': {
        'classes': ['BaseMonitor'],
        'reason': 'Abstract base class - not meant to be instantiated directly'
    },
    'monitors/system.py': {
        'classes': ['SystemMonitor'],
        'reason': 'Monitor class - will be instantiated by monitoring service during integration'
    },
    'monitors/network.py': {
        'classes': ['NetworkMonitor'],
        'reason': 'Monitor class - will be instantiated by monitoring service during integration'
    },
    
    # Handlers waiting for integration
    'handlers/alerts.py': {
        'classes': ['AlertHandler'],
        'reason': 'Handler class - will be instantiated by alert service during integration'
    },
    
    # Analysis tools waiting for integration
    'analysis/semantic_analysis.py': {
        'classes': ['SemanticAnalysis'],
        'reason': 'Analysis tool - will be used by planning phase during integration'
    },
    'analysis/dependency_graph.py': {
        'classes': ['DependencyGraphBuilder'],
        'reason': 'Analysis tool - will be used by planning phase during integration'
    },
    
    # Planning tools waiting for integration
    'planning/timeline_generator.py': {
        'classes': ['TimelineGenerator'],
        'reason': 'Planning tool - will be used by project planning phase during integration'
    },
    'planning/resource_estimator.py': {
        'classes': ['ResourceEstimator'],
        'reason': 'Planning tool - will be used by project planning phase during integration'
    },
    
    # Tools waiting for integration
    'tools/technology_research.py': {
        'classes': ['TechnologyResearch'],
        'reason': 'Research tool - will be used by investigation phase during integration'
    },
    
    # Services waiting for integration
    'services/progress_service.py': {
        'classes': ['ProgressService'],
        'reason': 'Service class - will be instantiated by application during integration'
    },
    
    # Add more integration points as they are identified
}


def is_integration_point(filepath: str, symbol_type: str, symbol_name: str) -> bool:
    """
    Check if a symbol is a known integration point.
    
    Args:
        filepath: Path to the file (relative to project root)
        symbol_type: Type of symbol ('class', 'function', 'method')
        symbol_name: Name of the symbol
        
    Returns:
        True if this is a known integration point that should not be flagged
    """
    # HEURISTIC 1: Check explicit registry
    if filepath in INTEGRATION_POINTS:
        points = INTEGRATION_POINTS[filepath]
        
        # Handle plural forms: 'class' -> 'classes', 'function' -> 'functions'
        if symbol_type == 'class':
            symbol_list = points.get('classes', [])
        elif symbol_type == 'function':
            symbol_list = points.get('functions', [])
        elif symbol_type == 'method':
            symbol_list = points.get('methods', [])
        else:
            return False
        
        if symbol_name in symbol_list:
            return True
    
    # HEURISTIC 2: Service layer methods are integration points
    # Services are meant to be called by API/UI layers
    if symbol_type == 'method' and filepath.startswith('services/'):
        pass
        # Common service method patterns that are integration points
        integration_patterns = [
            'create_', 'get_', 'update_', 'delete_',  # CRUD operations
            'list_', 'find_', 'search_',  # Query operations
            'add_', 'remove_', 'set_',  # Modification operations
            'generate_', 'calculate_', 'process_',  # Processing operations
            'upload_', 'download_', 'export_', 'import_',  # I/O operations
            'start_', 'stop_', 'restart_',  # Control operations
            'assess_', 'analyze_', 'track_',  # Analysis operations
        ]
        
        if any(symbol_name.startswith(pattern) for pattern in integration_patterns):
            return True
    
    # HEURISTIC 3: Feature modules are integration points
    # These directories contain features waiting to be integrated
    integration_directories = [
        'analytics/', 'chat/', 'collaboration/', 'file_management/',
        'integration/', 'ollama/', 'prompt/', 'recommendation/',
        'risk/', 'visualization/', 'monitoring/', 'reporting/'
    ]
    
    if symbol_type == 'method' and any(filepath.startswith(d) for d in integration_directories):
        pass
        # These are feature modules - their public methods are integration points
        if not symbol_name.startswith('_'):  # Public methods only
            return True
    
    return False


def get_integration_point_reason(filepath: str) -> str:
    """
    Get the reason why something is an integration point.
    
    Args:
        filepath: Path to the file
        
    Returns:
        Explanation of why this is an integration point
    """
    return INTEGRATION_POINTS.get(filepath, {}).get('reason', 'Unknown integration point')


def add_integration_point(filepath: str, symbol_type: str, symbol_name: str, reason: str):
    """
    Dynamically add a new integration point to the registry.
    
    Args:
        filepath: Path to the file
        symbol_type: Type of symbol ('class', 'function', 'method')
        symbol_name: Name of the symbol
        reason: Explanation of why this is an integration point
    """
    if filepath not in INTEGRATION_POINTS:
        INTEGRATION_POINTS[filepath] = {'reason': reason}
    
    # Handle plural forms
    if symbol_type == 'class':
        key = 'classes'
    elif symbol_type == 'function':
        key = 'functions'
    elif symbol_type == 'method':
        key = 'methods'
    else:
        raise ValueError(f"Unknown symbol type: {symbol_type}")
    
    if key not in INTEGRATION_POINTS[filepath]:
        INTEGRATION_POINTS[filepath][key] = []
    
    if symbol_name not in INTEGRATION_POINTS[filepath][key]:
        INTEGRATION_POINTS[filepath][key].append(symbol_name)


def list_integration_points() -> dict:
    """
    Get a list of all registered integration points.
    
    Returns:
        Dictionary of all integration points with their details
    """
    return INTEGRATION_POINTS.copy()