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
    max_iterations: int = 0  # 0 = unlimited (GOOD)
    max_retries_per_task: int = 999999  # UNLIMITED retries per task
    
    # Verbose mode - show prompts and responses
    verbose: int = 0  # 0=normal, 1=verbose, 2=very verbose
    
    # Timeouts (seconds) - None means no timeout (wait forever)
    # ALL TIMEOUTS SET TO NONE = COMPLETELY UNLIMITED PER USER REQUEST
    planning_timeout: Optional[int] = None  # UNLIMITED - wait forever
    coding_timeout: Optional[int] = None    # UNLIMITED - wait forever
    qa_timeout: Optional[int] = None        # UNLIMITED - wait forever
    debug_timeout: Optional[int] = None     # UNLIMITED - wait forever
    request_timeout: Optional[int] = None   # UNLIMITED - wait forever
    specialist_timeout: Optional[int] = None  # UNLIMITED - wait forever
    orchestrator_timeout: Optional[int] = None  # UNLIMITED - wait forever
    tool_advisor_timeout: Optional[int] = None  # UNLIMITED - wait forever
    
    # State management
    state_dir: str = ".pipeline"
    auto_save_state: bool = True
    
    # Model assignments by task type
    # Format: (model_name, preferred_host)
    # 
    # Model selection rationale:
    # - planning: qwen2.5-coder:32b - Better tool calling than general model, code understanding
    # - coding: qwen2.5-coder:32b (32.8B) - BEST open-source coding model, GPT-4o level
    # - qa: qwen2.5-coder:32b - Better tool calling than general model (switched from qwen2.5:32b)
    # - debugging: qwen2.5-coder:32b (32.8B) - BEST at code fixing, scored 73.7 on Aider
    # - routing: functiongemma - Fast, specialized for function calling
    # - tool_formatting: functiongemma - Helps format malformed tool calls
    model_assignments: Dict[str, Tuple[str, str]] = field(default_factory=lambda: {
        # LOAD BALANCED: Distribute tasks across BOTH servers
        # ollama01: Planning with coder model for better tool calling, routing tasks
        "planning":        ("qwen2.5-coder:32b", "ollama01.thiscluster.net"),
        "routing":         ("functiongemma", "ollama01.thiscluster.net"),
        
        # ollama02: QA with coder model for better tool calling
        "qa":              ("qwen2.5-coder:32b", "ollama02.thiscluster.net"),
        
        # ollama02: Coding, debugging, investigation (heavier workloads)
        "coding":          ("qwen2.5-coder:32b", "ollama02.thiscluster.net"),
        "investigation":   ("qwen2.5-coder:32b", "ollama02.thiscluster.net"),  # ADDED
        "debugging":       ("qwen2.5-coder:32b", "ollama02.thiscluster.net"),
        "debug":           ("qwen2.5-coder:32b", "ollama02.thiscluster.net"),
        
        # Utility tasks distributed
        "tool_formatting": ("functiongemma", "ollama02.thiscluster.net"),
        "quick_fix":       ("qwen2.5-coder:7b", "ollama01.thiscluster.net"),
    })
    
       # NOTE: Removed phi4, deepseek-coder-v2 - they do not support native tool calling (HTTP 400 errors)
    # Fallback models when primary not available
    model_fallbacks: Dict[str, List[str]] = field(default_factory=lambda: {
        "planning":  ["llama3.1:70b", "mixtral:8x7b", "phi3:medium", "qwen2.5:7b"],
        "coding":    ["qwen2.5-coder:14b", "codellama:13b", "qwen2.5-coder:7b", "granite-code:8b"],
        "qa":        ["llama3.1:70b", "mixtral:8x7b", "phi3:medium", "qwen2.5:7b"],
        "debugging": ["qwen2.5-coder:32b", "qwen2.5-coder:14b", "qwen2.5:14b", "llama3.1:70b", "llama3.1"],
        "debug":     ["qwen2.5-coder:14b", "codellama:13b", "qwen2.5-coder:7b"],
        "routing":   ["phi3:mini", "llama3.2:3b", "qwen2.5:7b"],
        "tool_formatting": ["phi3:mini", "llama3.2:3b"],
        "quick_fix": ["codellama:7b", "qwen2.5-coder:7b", "starcoder2:7b"],
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
