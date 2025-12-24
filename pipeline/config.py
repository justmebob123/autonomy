"""
Pipeline Configuration
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple, Optional


@dataclass
class ServerConfig:
    """Configuration for an Ollama server"""
    name: str
    host: str
    port: int = 11434
    capabilities: List[str] = field(default_factory=list)
    models: List[str] = field(default_factory=list)
    online: bool = False
    
    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


@dataclass
class PipelineConfig:
    """Main pipeline configuration"""
    
    servers: List[ServerConfig] = field(default_factory=lambda: [
        ServerConfig(
            name="ollama01",
               host="ollama01.thiscluster.net",
            capabilities=["coding", "planning", "qa", "debugging"]
        ),
        ServerConfig(
            name="ollama02", 
            host="ollama02.thiscluster.net",
            capabilities=["routing", "quick_fix", "tool_formatting"]
        ),
    ])
    
    project_dir: Path = field(default_factory=lambda: Path.cwd())
    git_enabled: bool = True
    max_iterations: int = 0  # 0 = unlimited
    max_retries_per_task: int = 3
    
    # Verbose mode - show prompts and responses
    verbose: bool = False
    
    # Timeouts (seconds) - None means no timeout (wait forever)
    planning_timeout: Optional[int] = None
    coding_timeout: Optional[int] = None
    qa_timeout: Optional[int] = None
    debug_timeout: Optional[int] = None
    request_timeout: Optional[int] = None
    
    # State management
    state_dir: str = ".pipeline"
    auto_save_state: bool = True
    
    # Model assignments by task type
    # Format: (model_name, preferred_host)
    # 
    # Model selection rationale:
    # - planning: qwen2.5:14b - Good at structured thinking, uses native tools
    # - coding: qwen2.5-coder:14b - Best code generation
    # - qa: qwen2.5:14b - Uses native tool calls properly
    # - debugging: qwen2.5-coder:14b - Good at code analysis
    # - routing: functiongemma - Fast, specialized for function calling
    # - tool_formatting: functiongemma - Helps format malformed tool calls
    model_assignments: Dict[str, Tuple[str, str]] = field(default_factory=lambda: {
        # Primary tasks - use large models on ollama02 (MUCH faster)
        "planning":        ("qwen2.5:14b", "ollama02.thiscluster.net"),
        "coding":          ("qwen2.5-coder:14b", "ollama02.thiscluster.net"),
        "qa":              ("qwen2.5:14b", "ollama02.thiscluster.net"),
        "debugging":       ("qwen2.5-coder:14b", "ollama02.thiscluster.net"),
        "debug":           ("qwen2.5-coder:14b", "ollama02.thiscluster.net"),
        
        # Utility tasks - use smaller/specialized models on ollama02
        "routing":         ("functiongemma", "ollama02.thiscluster.net"),
        "tool_formatting": ("functiongemma", "ollama02.thiscluster.net"),
        "quick_fix":       ("qwen2.5-coder:7b", "ollama02.thiscluster.net"),
    })
    
    # Fallback models when primary not available
    model_fallbacks: Dict[str, List[str]] = field(default_factory=lambda: {
        "planning":  ["llama3.1:70b", "mixtral:8x7b", "phi3:medium", "qwen2.5:7b"],
        "coding":    ["deepseek-coder-v2:16b", "codellama:13b", "qwen2.5-coder:7b", "granite-code:8b"],
        "qa":        ["llama3.1:70b", "mixtral:8x7b", "phi3:medium", "qwen2.5:7b"],
        "debugging": ["deepseek-coder-v2:16b", "codellama:13b", "qwen2.5-coder:7b"],
        "debug":     ["deepseek-coder-v2:16b", "codellama:13b", "qwen2.5-coder:7b"],
        "routing":   ["phi3:mini", "llama3.2:3b", "qwen2.5:7b"],
        "tool_formatting": ["phi3:mini", "llama3.2:3b"],
        "quick_fix": ["codellama:7b", "deepseek-coder:6.7b", "starcoder2:7b"],
    })
    
    # Temperature settings by task type
    temperatures: Dict[str, float] = field(default_factory=lambda: {
        "routing":         0.1,  # Very deterministic
        "tool_formatting": 0.1,  # Very deterministic
        "planning":        0.5,  # Some creativity for task breakdown
        "coding":          0.2,  # Low for consistent code
        "qa":              0.3,  # Moderate for thorough review
        "debugging":       0.2,  # Low for precise fixes
        "debug":           0.2,
        "quick_fix":       0.1,  # Very deterministic
    })
