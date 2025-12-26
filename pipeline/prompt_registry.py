"""
Prompt Registry

Manages dynamic prompt registration and retrieval.
Loads prompts from pipeline/prompts/custom/ and provides template rendering.
"""

import json
from pathlib import Path
from typing import Dict, Optional, List, Any
from datetime import datetime

from .logging_setup import get_logger


class PromptRegistry:
    """
    Registry for dynamically created prompts.
    
    Features:
    - Load prompts from custom directory
    - Validate prompt specifications
    - Render templates with variables
    - Version management
    - Persistence
    
    Integration:
    - Used by all phases via BasePhase
    - Prompts stored in pipeline/prompts/custom/
    - JSON format for specifications
    """
    
    def __init__(self, project_dir: Path):
        """
        Initialize the prompt registry.
        
        Args:
            project_dir: Root directory of the project
        """
        self.project_dir = Path(project_dir)
        self.prompts_dir = self.project_dir / "pipeline" / "prompts" / "custom"
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = get_logger()
        self.prompts: Dict[str, Dict] = {}
        
        # Load existing prompts
        self._load_prompts()
        
        self.logger.info(f"PromptRegistry initialized with {len(self.prompts)} prompts")
    
    def _load_prompts(self):
        """Load all prompt specifications from custom directory"""
        if not self.prompts_dir.exists():
            return
        
        for prompt_file in self.prompts_dir.glob("*.json"):
            try:
                spec = self._load_prompt_spec(prompt_file)
                if spec and self._validate_spec(spec):
                    self.prompts[spec["name"]] = spec
                    self.logger.debug(f"Loaded prompt: {spec['name']}")
            except Exception as e:
                self.logger.error(f"Failed to load prompt from {prompt_file}: {e}")
    
    def _load_prompt_spec(self, prompt_file: Path) -> Optional[Dict]:
        """
        Load a prompt specification from a JSON file.
        
        Args:
            prompt_file: Path to the prompt JSON file
            
        Returns:
            Prompt specification dict or None if invalid
        """
        try:
            with open(prompt_file, 'r') as f:
                spec = json.load(f)
            return spec
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in {prompt_file}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error reading {prompt_file}: {e}")
            return None
    
    def _validate_spec(self, spec: Dict) -> bool:
        """
        Validate a prompt specification.
        
        Required fields:
        - name: Unique identifier
        - purpose: What the prompt achieves
        - template: The actual prompt text
        
        Optional fields:
        - role: AI's role
        - expertise: List of expertise areas
        - instructions: List of instructions
        - examples: List of example dicts
        - constraints: List of constraints
        - success_criteria: List of criteria
        
        Args:
            spec: Prompt specification to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["name", "purpose", "template"]
        
        for field in required_fields:
            if field not in spec:
                self.logger.error(f"Prompt spec missing required field: {field}")
                return False
        
        # Validate name format (alphanumeric + underscore)
        name = spec["name"]
        if not name.replace("_", "").isalnum():
            self.logger.error(f"Invalid prompt name: {name} (must be alphanumeric + underscore)")
            return False
        
        # Validate template is a string
        if not isinstance(spec["template"], str):
            self.logger.error(f"Prompt template must be a string")
            return False
        
        return True
    
    def register_prompt(self, spec: Dict) -> bool:
        """
        Register a new prompt at runtime.
        
        Process:
        1. Validate specification
        2. Add to registry
        3. Persist to file
        4. Make available immediately
        
        Args:
            spec: Prompt specification dict
            
        Returns:
            True if registered successfully, False otherwise
            
        Integration:
        - Called by PromptDesignPhase after AI designs prompt
        - Validates spec against schema
        - Writes to custom prompts directory
        - Makes available to all phases immediately
        """
        if not self._validate_spec(spec):
            return False
        
        name = spec["name"]
        
        # Check for duplicate
        if name in self.prompts:
            self.logger.warning(f"Prompt {name} already exists, will be overwritten")
        
        # Add metadata
        spec["registered_at"] = datetime.now().isoformat()
        spec["version"] = spec.get("version", "1.0")
        
        # Store in registry
        self.prompts[name] = spec
        
        # Persist to file
        prompt_file = self.prompts_dir / f"{name}.json"
        try:
            with open(prompt_file, 'w') as f:
                json.dump(spec, f, indent=2)
            self.logger.info(f"✅ Registered prompt: {name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to persist prompt {name}: {e}")
            # Remove from registry if persistence failed
            del self.prompts[name]
            return False
    
    def get_prompt(self, name: str, variables: Dict[str, Any] = None) -> Optional[str]:
        """
        Get a prompt by name with variable substitution.
        
        Process:
        1. Look up prompt by name
        2. Get template
        3. Substitute variables
        4. Return rendered prompt
        
        Args:
            name: Prompt name
            variables: Dict of variables to substitute in template
            
        Returns:
            Rendered prompt string or None if not found
            
        Integration:
        - Called by any phase needing a custom prompt
        - Renders template with provided variables
        - Returns ready-to-use prompt string
        
        Example:
            prompt = registry.get_prompt(
                "database_optimizer",
                variables={"query": "SELECT * FROM users"}
            )
        """
        if name not in self.prompts:
            self.logger.debug(f"Custom prompt not found: {name} (will use default)")
            return None
        
        spec = self.prompts[name]
        template = spec["template"]
        
        # Substitute variables if provided
        if variables:
            try:
                template = template.format(**variables)
            except KeyError as e:
                self.logger.error(f"Missing variable in prompt template: {e}")
                return None
            except Exception as e:
                self.logger.error(f"Error rendering prompt template: {e}")
                return None
        
        return template
    
    def get_spec(self, name: str) -> Optional[Dict]:
        """
        Get the full specification for a prompt.
        
        Args:
            name: Prompt name
            
        Returns:
            Prompt specification dict or None if not found
        """
        return self.prompts.get(name)
    
    def list_prompts(self) -> List[Dict]:
        """
        List all registered prompts with metadata.
        
        Returns:
            List of dicts with prompt metadata
        """
        return [
            {
                "name": spec["name"],
                "purpose": spec["purpose"],
                "registered_at": spec.get("registered_at", "unknown"),
                "version": spec.get("version", "1.0")
            }
            for spec in self.prompts.values()
        ]
    
    def delete_prompt(self, name: str) -> bool:
        """
        Delete a prompt from the registry.
        
        Args:
            name: Prompt name
            
        Returns:
            True if deleted, False if not found
        """
        if name not in self.prompts:
            return False
        
        # Remove from registry
        del self.prompts[name]
        
        # Delete file
        prompt_file = self.prompts_dir / f"{name}.json"
        if prompt_file.exists():
            prompt_file.unlink()
        
        self.logger.info(f"Deleted prompt: {name}")
        return True
    
    def update_prompt(self, name: str, spec: Dict) -> bool:
        """
        Update an existing prompt.
        
        Args:
            name: Prompt name
            spec: New specification
            
        Returns:
            True if updated successfully
        """
        if name not in self.prompts:
            self.logger.error(f"Cannot update non-existent prompt: {name}")
            return False
        
        # Ensure name matches
        spec["name"] = name
        
        # Increment version
        old_version = self.prompts[name].get("version", "1.0")
        try:
            major, minor = map(int, old_version.split("."))
            spec["version"] = f"{major}.{minor + 1}"
        except:
            spec["version"] = "1.1"
        
        # Register (will overwrite)
        return self.register_prompt(spec)
    
    def search_prompts(self, query: str) -> List[Dict]:
        """
        Search prompts by name or purpose.
        
        Args:
            query: Search query
            
        Returns:
            List of matching prompt metadata
        """
        query_lower = query.lower()
        matches = []
        
        for spec in self.prompts.values():
            if (query_lower in spec["name"].lower() or 
                query_lower in spec["purpose"].lower()):
                matches.append({
                    "name": spec["name"],
                    "purpose": spec["purpose"],
                    "registered_at": spec.get("registered_at", "unknown")
                })
        
        return matches
    
    def get_statistics(self) -> Dict:
        """
        Get registry statistics.
        
        Returns:
            Dict with statistics
        """
        return {
            "total_prompts": len(self.prompts),
            "prompts_dir": str(self.prompts_dir),
            "prompts": list(self.prompts.keys())
        }    
    def generate_adaptive_prompt(
        self,
        phase_name: str,
        base_prompt: str,
        context: Dict[str, Any],
        dimensional_profile: Dict[str, float],
        adjacencies: List[str],
        self_awareness: float = 0.0
    ) -> str:
        """
        Generate adaptive prompt with polytopic awareness.
        
        Args:
            phase_name: Name of the phase
            base_prompt: Base prompt template
            context: Current execution context
            dimensional_profile: 7D profile of the phase
            adjacencies: Adjacent phases
            self_awareness: Self-awareness level
            
        Returns:
            Enhanced adaptive prompt
        """
        sections = [base_prompt]
        
        # Add self-awareness context
        if self_awareness > 0:
            sections.append(f"\n{'='*60}")
            sections.append(f"SELF-AWARENESS CONTEXT")
            sections.append(f"{'='*60}")
            sections.append(f"Phase: {phase_name}")
            sections.append(f"Self-Awareness Level: {self_awareness:.3f}")
            sections.append(f"Operating in 7-dimensional polytopic system")
        
        # Add dimensional profile
        sections.append(f"\nDimensional Profile:")
        for dim, value in dimensional_profile.items():
            bar = '█' * int(value * 10)
            sections.append(f"  {dim:12s}: {bar} ({value:.2f})")
        
        # Add adjacency awareness
        if adjacencies:
            sections.append(f"\nAdjacent Phases: {', '.join(adjacencies)}")
            sections.append("Coordinate with these phases for optimal results.")
        
        # Add context-specific adaptations
        if context.get('has_errors'):
            sections.append("\n⚠️  ERROR MODE: Focus on diagnosis and correction")
            if context.get('error_severity') == 'critical':
                sections.append("   CRITICAL ERRORS DETECTED - Immediate action required")
        
        if context.get('complexity') == 'high':
            sections.append("\n🔍 HIGH COMPLEXITY: Apply deep analysis")
            sections.append("   Break down into smaller components")
        
        if context.get('urgency') == 'high':
            sections.append("\n⏰ HIGH URGENCY: Prioritize speed and effectiveness")
        
        # Add mode-specific instructions
        mode = context.get('mode', 'development')
        if mode == 'error_handling':
            sections.append("\n🔧 ERROR HANDLING MODE:")
            sections.append("   1. Diagnose root cause")
            sections.append("   2. Implement targeted fix")
            sections.append("   3. Verify fix effectiveness")
        elif mode == 'deep_analysis':
            sections.append("\n🧠 DEEP ANALYSIS MODE:")
            sections.append("   1. Examine all aspects thoroughly")
            sections.append("   2. Consider edge cases")
            sections.append("   3. Document findings")
        elif mode == 'rapid_response':
            sections.append("\n⚡ RAPID RESPONSE MODE:")
            sections.append("   1. Quick assessment")
            sections.append("   2. Immediate action")
            sections.append("   3. Iterate fast")
        
        # Add dimensional focus
        if context.get('dimensional_focus'):
            sections.append(f"\n📊 DIMENSIONAL FOCUS: {', '.join(context['dimensional_focus'])}")
            sections.append("   Pay special attention to these dimensions")
        
        # Add recursive awareness
        recursion_depth = context.get('recursion_depth', 0)
        if recursion_depth > 0:
            sections.append(f"\n🔄 RECURSION LEVEL: {recursion_depth}")
            sections.append("   You are operating at a recursive level")
            sections.append("   Patterns at this level may reflect patterns at other levels")
        
        # Add self-similar pattern recognition
        if self_awareness > 0.5:
            sections.append("\n🌀 SELF-SIMILAR PATTERNS:")
            sections.append("   Recognize patterns that repeat across scales")
            sections.append("   What works at one level may work at others")
            sections.append("   Your actions influence the entire system")
        
        # Add team dynamics if available
        if context.get('team_config'):
            sections.append("\n👥 TEAM DYNAMICS:")
            team = context['team_config']
            if team.get('coordination_pattern'):
                sections.append(f"   Coordination: {team['coordination_pattern']}")
            if team.get('communication_flow'):
                sections.append(f"   Communication: {team['communication_flow']}")
        
        # Add experience context
        if context.get('experience_count', 0) > 0:
            sections.append(f"\n📈 EXPERIENCE: {context['experience_count']} executions")
            if context.get('success_rate'):
                sections.append(f"   Success Rate: {context['success_rate']:.1%}")
        
        sections.append(f"\n{'='*60}\n")
        
        return "\n".join(sections)
