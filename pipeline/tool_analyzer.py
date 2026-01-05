"""
Tool Analyzer - Intelligent Tool Analysis System

Analyzes existing tools to detect similarities, recommend abstractions,
and prevent duplicate tool creation.
"""

import ast
import inspect
import difflib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from collections import defaultdict

from .logging_setup import get_logger


@dataclass
class ToolSignature:
    """Represents a tool's signature and metadata."""
    name: str
    parameters: Dict[str, Any]
    return_type: Optional[str]
    description: str
    source_file: str
    is_custom: bool


@dataclass
class ToolSimilarity:
    """Represents similarity between two tools."""
    tool1: str
    tool2: str
    similarity_score: float
    similar_parameters: List[str]
    similar_functionality: bool
    recommendation: str


@dataclass
class ToolAnalysisResult:
    """Result of tool analysis."""
    exists: bool
    similar_tools: List[ToolSimilarity]
    should_create_new: bool
    should_modify_existing: bool
    should_abstract: bool
    recommendations: List[str]
    existing_tool_name: Optional[str] = None


class ToolAnalyzer:
    """
    Analyzes tools for similarities, duplicates, and abstraction opportunities.
    
    This class performs deep analysis of existing tools to:
    - Detect duplicate or similar tools
    - Recommend tool abstractions
    - Suggest modifications to existing tools
    - Prevent unnecessary tool creation
    """
    
    def __init__(self, handlers_path: str = "pipeline/handlers.py", 
                 custom_tools_dir: str = "pipeline/tools/custom"):
        """
        Initialize the ToolAnalyzer.
        
        Args:
            handlers_path: Path to handlers.py containing built-in tools
            custom_tools_dir: Directory containing custom tools
        """
        self.logger = get_logger()
        self.handlers_path = Path(handlers_path)
        self.custom_tools_dir = Path(custom_tools_dir)
        
        # Cache for tool signatures
        self.tool_signatures: Dict[str, ToolSignature] = {}
        self.similarity_threshold = 0.7  # 70% similarity threshold
        
        self.logger.info("ToolAnalyzer initialized")
    
    def analyze_tool_request(self, tool_name: str, context: Dict[str, Any]) -> ToolAnalysisResult:
        """
        Analyze a tool request to determine if new tool is needed.
        
        Args:
            tool_name: Name of the requested tool
            context: Context including parameters, usage, description
            
        Returns:
            ToolAnalysisResult with recommendations
        """
        self.logger.info(f"Analyzing tool request: {tool_name}")
        
        # Load all existing tools
        self._load_all_tools()
        
        # Check if exact tool exists
        if tool_name in self.tool_signatures:
            self.logger.info(f"Tool {tool_name} already exists")
            return ToolAnalysisResult(
                exists=True,
                similar_tools=[],
                should_create_new=False,
                should_modify_existing=False,
                should_abstract=False,
                recommendations=[f"Tool '{tool_name}' already exists and can be used directly"],
                existing_tool_name=tool_name
            )
        
        # Find similar tools
        similar_tools = self._find_similar_tools(tool_name, context)
        
        # Analyze if we should create new, modify existing, or abstract
        analysis = self._analyze_similarity_results(tool_name, similar_tools, context)
        
        self.logger.info(f"Analysis complete for {tool_name}: create_new={analysis.should_create_new}, "
                        f"modify={analysis.should_modify_existing}, abstract={analysis.should_abstract}")
        
        return analysis
    
    def _load_all_tools(self):
        """Load signatures of all existing tools."""
        self.logger.debug("Loading all tool signatures")
        
        # Load built-in tools from handlers.py
        if self.handlers_path.exists():
            self._load_builtin_tools()
        
        # Load custom tools
        if self.custom_tools_dir.exists():
            self._load_custom_tools()
        
        self.logger.debug(f"Loaded {len(self.tool_signatures)} tool signatures")
    
    def _load_builtin_tools(self):
        """Load built-in tool signatures from handlers.py."""
        try:
            with open(self.handlers_path, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith('_handle_'):
                    tool_name = node.name.replace('_handle_', '')
                    signature = self._extract_signature(node, str(self.handlers_path), False)
                    if signature:
                        self.tool_signatures[tool_name] = signature
                        self.logger.debug(f"Loaded built-in tool: {tool_name}")
        
        except Exception as e:
            self.logger.error(f"Error loading built-in tools: {e}")
    
    def _load_custom_tools(self):
        """Load custom tool signatures."""
        try:
            for tool_file in self.custom_tools_dir.glob("*.py"):
                if tool_file.name == "__init__.py":
                    continue
                
                with open(tool_file, 'r') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        tool_name = node.name
                        signature = self._extract_signature(node, str(tool_file), True)
                        if signature:
                            self.tool_signatures[tool_name] = signature
                            self.logger.debug(f"Loaded custom tool: {tool_name}")
        
        except Exception as e:
            self.logger.error(f"Error loading custom tools: {e}")
    
    def _extract_signature(self, node: ast.FunctionDef, source_file: str, 
                          is_custom: bool) -> Optional[ToolSignature]:
        """Extract tool signature from AST node."""
        try:
            pass
            # Extract parameters
            parameters = {}
            for arg in node.args.args:
                param_name = arg.arg
                param_type = None
                if arg.annotation:
                    param_type = ast.unparse(arg.annotation)
                parameters[param_name] = {"type": param_type}
            
            # Extract return type
            return_type = None
            if node.returns:
                return_type = ast.unparse(node.returns)
            
            # Extract docstring
            description = ast.get_docstring(node) or ""
            
            return ToolSignature(
                name=node.name,
                parameters=parameters,
                return_type=return_type,
                description=description,
                source_file=source_file,
                is_custom=is_custom
            )
        
        except Exception as e:
            self.logger.error(f"Error extracting signature: {e}")
            return None
    
    def _find_similar_tools(self, tool_name: str, context: Dict[str, Any]) -> List[ToolSimilarity]:
        """Find tools similar to the requested tool."""
        similar_tools = []
        
        requested_params = context.get('parameters', {})
        requested_desc = context.get('description', '')
        
        for existing_name, existing_sig in self.tool_signatures.items():
            pass
            # Calculate name similarity
            name_similarity = difflib.SequenceMatcher(
                None, tool_name.lower(), existing_name.lower()
            ).ratio()
            
            # Calculate parameter similarity
            param_similarity = self._calculate_parameter_similarity(
                requested_params, existing_sig.parameters
            )
            
            # Calculate description similarity
            desc_similarity = difflib.SequenceMatcher(
                None, requested_desc.lower(), existing_sig.description.lower()
            ).ratio()
            
            # Overall similarity score (weighted average)
            similarity_score = (
                name_similarity * 0.3 +
                param_similarity * 0.4 +
                desc_similarity * 0.3
            )
            
            if similarity_score >= self.similarity_threshold:
                pass
                # Find similar parameters
                similar_params = self._find_similar_parameters(
                    requested_params, existing_sig.parameters
                )
                
                recommendation = self._generate_recommendation(
                    similarity_score, existing_name, similar_params
                )
                
                similar_tools.append(ToolSimilarity(
                    tool1=tool_name,
                    tool2=existing_name,
                    similarity_score=similarity_score,
                    similar_parameters=similar_params,
                    similar_functionality=similarity_score >= 0.85,
                    recommendation=recommendation
                ))
        
        # Sort by similarity score
        similar_tools.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return similar_tools
    
    def _calculate_parameter_similarity(self, params1: Dict, params2: Dict) -> float:
        """Calculate similarity between parameter sets."""
        if not params1 and not params2:
            return 1.0
        if not params1 or not params2:
            return 0.0
        
        # Get parameter names
        names1 = set(params1.keys())
        names2 = set(params2.keys())
        
        # Calculate Jaccard similarity
        intersection = len(names1 & names2)
        union = len(names1 | names2)
        
        return intersection / union if union > 0 else 0.0
    
    def _find_similar_parameters(self, params1: Dict, params2: Dict) -> List[str]:
        """Find parameters that appear in both sets."""
        names1 = set(params1.keys())
        names2 = set(params2.keys())
        return list(names1 & names2)
    
    def _generate_recommendation(self, similarity: float, existing_tool: str, 
                                 similar_params: List[str]) -> str:
        """Generate recommendation based on similarity."""
        if similarity >= 0.95:
            return f"Use existing tool '{existing_tool}' - nearly identical functionality"
        elif similarity >= 0.85:
            return f"Consider using '{existing_tool}' with minor modifications"
        elif similarity >= 0.75:
            return f"Tool '{existing_tool}' has similar functionality - consider abstraction"
        else:
            return f"Tool '{existing_tool}' has some overlap - review before creating new tool"
    
    def _analyze_similarity_results(self, tool_name: str, similar_tools: List[ToolSimilarity],
                                   context: Dict[str, Any]) -> ToolAnalysisResult:
        """Analyze similarity results and provide recommendations."""
        recommendations = []
        
        # No similar tools found
        if not similar_tools:
            self.logger.info(f"No similar tools found for {tool_name}")
            return ToolAnalysisResult(
                exists=False,
                similar_tools=[],
                should_create_new=True,
                should_modify_existing=False,
                should_abstract=False,
                recommendations=["No similar tools found - safe to create new tool"]
            )
        
        # Very high similarity - use existing
        if similar_tools[0].similarity_score >= 0.95:
            return ToolAnalysisResult(
                exists=False,
                similar_tools=similar_tools[:3],
                should_create_new=False,
                should_modify_existing=False,
                should_abstract=False,
                recommendations=[
                    f"Use existing tool '{similar_tools[0].tool2}' instead",
                    "Similarity is very high (>95%) - new tool not needed"
                ],
                existing_tool_name=similar_tools[0].tool2
            )
        
        # High similarity - modify existing
        elif similar_tools[0].similarity_score >= 0.85:
            return ToolAnalysisResult(
                exists=False,
                similar_tools=similar_tools[:3],
                should_create_new=False,
                should_modify_existing=True,
                should_abstract=False,
                recommendations=[
                    f"Modify existing tool '{similar_tools[0].tool2}' to support new use case",
                    "High similarity (>85%) - modification preferred over new tool",
                    f"Similar parameters: {', '.join(similar_tools[0].similar_parameters)}"
                ],
                existing_tool_name=similar_tools[0].tool2
            )
        
        # Multiple similar tools - consider abstraction
        elif len(similar_tools) >= 2 and similar_tools[0].similarity_score >= 0.75:
            return ToolAnalysisResult(
                exists=False,
                similar_tools=similar_tools[:5],
                should_create_new=False,
                should_modify_existing=False,
                should_abstract=True,
                recommendations=[
                    "Multiple similar tools detected - consider creating abstraction",
                    f"Similar tools: {', '.join([s.tool2 for s in similar_tools[:3]])}",
                    "Create a more general tool that handles all use cases",
                    "This will improve code maintainability and reduce duplication"
                ]
            )
        
        # Some similarity - create new but note similarities
        else:
            return ToolAnalysisResult(
                exists=False,
                similar_tools=similar_tools[:3],
                should_create_new=True,
                should_modify_existing=False,
                should_abstract=False,
                recommendations=[
                    "Create new tool - similarity is moderate",
                    f"Note: Tool '{similar_tools[0].tool2}' has some overlap",
                    "Consider reusing common functionality where possible"
                ]
            )
    
    def get_tool_statistics(self) -> Dict[str, Any]:
        """Get statistics about existing tools."""
        self._load_all_tools()
        
        builtin_count = sum(1 for sig in self.tool_signatures.values() if not sig.is_custom)
        custom_count = sum(1 for sig in self.tool_signatures.values() if sig.is_custom)
        
        return {
            "total_tools": len(self.tool_signatures),
            "builtin_tools": builtin_count,
            "custom_tools": custom_count,
            "tool_names": list(self.tool_signatures.keys())
        }