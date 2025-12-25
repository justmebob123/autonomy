"""
Role Registry

Manages dynamic specialist role registration.
Loads roles from pipeline/roles/custom/ and instantiates SpecialistAgent objects.
"""

import json
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

from .logging_setup import get_logger
from .specialist_agents import SpecialistAgent, SpecialistConfig
from .client import OllamaClient
from .conversation_thread import ConversationThread


class RoleRegistry:
    """
    Registry for dynamically created specialist roles.
    
    Features:
    - Load roles from custom directory
    - Validate role specifications
    - Instantiate SpecialistAgent objects
    - Make specialists available for consultation
    - Manage team composition
    
    Integration:
    - Uses existing SpecialistAgent class
    - Uses existing SpecialistConfig dataclass
    - Loads from pipeline/roles/custom/
    """
    
    def __init__(self, project_dir: Path, client: OllamaClient):
        """
        Initialize the role registry.
        
        Args:
            project_dir: Root directory of the project
            client: OllamaClient instance for specialist communication
        """
        self.project_dir = Path(project_dir)
        self.roles_dir = self.project_dir / "pipeline" / "roles" / "custom"
        self.roles_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = get_logger()
        self.client = client
        self.specialists: Dict[str, SpecialistAgent] = {}
        self.role_specs: Dict[str, Dict] = {}
        
        # Load existing roles
        self._load_roles()
        
        self.logger.info(f"RoleRegistry initialized with {len(self.specialists)} specialists")
    
    def _load_roles(self):
        """Load all role specifications and instantiate specialists"""
        if not self.roles_dir.exists():
            return
        
        for role_file in self.roles_dir.glob("*.json"):
            try:
                spec = self._load_role_spec(role_file)
                if spec and self._validate_spec(spec):
                    specialist = self._instantiate_specialist(spec)
                    if specialist:
                        self.specialists[spec["name"]] = specialist
                        self.role_specs[spec["name"]] = spec
                        self.logger.debug(f"Loaded specialist: {spec['name']}")
            except Exception as e:
                self.logger.error(f"Failed to load role from {role_file}: {e}")
    
    def _load_role_spec(self, role_file: Path) -> Optional[Dict]:
        """
        Load a role specification from a JSON file.
        
        Args:
            role_file: Path to the role JSON file
            
        Returns:
            Role specification dict or None if invalid
        """
        try:
            with open(role_file, 'r') as f:
                spec = json.load(f)
            return spec
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in {role_file}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error reading {role_file}: {e}")
            return None
    
    def _validate_spec(self, spec: Dict) -> bool:
        """
        Validate a role specification.
        
        Required fields:
        - name: Role name
        - expertise: Domain expertise description
        - system_prompt: The prompt for the specialist
        - model: Model to use
        - host: Server to use
        
        Args:
            spec: Role specification to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["name", "expertise", "system_prompt", "model", "host"]
        
        for field in required_fields:
            if field not in spec:
                self.logger.error(f"Role spec missing required field: {field}")
                return False
        
        # Validate name format (alphanumeric + underscore)
        name = spec["name"]
        if not name.replace("_", "").replace(" ", "").isalnum():
            self.logger.error(f"Invalid role name: {name}")
            return False
        
        return True
    
    def _instantiate_specialist(self, spec: Dict) -> Optional[SpecialistAgent]:
        """
        Instantiate a SpecialistAgent from a role specification.
        
        Args:
            spec: Role specification
            
        Returns:
            SpecialistAgent instance or None if failed
        """
        try:
            # Create SpecialistConfig
            config = SpecialistConfig(
                name=spec["name"],
                model=spec["model"],
                host=spec["host"],
                expertise=spec["expertise"],
                system_prompt=spec["system_prompt"],
                temperature=spec.get("temperature", 0.3)
            )
            
            # Instantiate SpecialistAgent
            specialist = SpecialistAgent(
                config=config,
                client=self.client,
                logger=self.logger
            )
            
            return specialist
            
        except Exception as e:
            self.logger.error(f"Failed to instantiate specialist {spec['name']}: {e}")
            return None
    
    def register_role(self, spec: Dict) -> bool:
        """
        Register a new specialist role at runtime.
        
        Process:
        1. Validate specification
        2. Instantiate SpecialistAgent
        3. Add to registry
        4. Persist to file
        5. Make available for consultation
        
        Args:
            spec: Role specification dict
            
        Returns:
            True if registered successfully, False otherwise
            
        Integration:
        - Creates SpecialistConfig from spec
        - Instantiates SpecialistAgent
        - Makes available for consultation
        """
        if not self._validate_spec(spec):
            return False
        
        name = spec["name"]
        
        # Check for duplicate
        if name in self.specialists:
            self.logger.warning(f"Role {name} already exists, will be overwritten")
        
        # Add metadata
        spec["registered_at"] = datetime.now().isoformat()
        spec["version"] = spec.get("version", "1.0")
        
        # Instantiate specialist
        specialist = self._instantiate_specialist(spec)
        if not specialist:
            return False
        
        # Store in registry
        self.specialists[name] = specialist
        self.role_specs[name] = spec
        
        # Persist to file
        role_file = self.roles_dir / f"{name}.json"
        try:
            with open(role_file, 'w') as f:
                json.dump(spec, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to persist role spec: {e}")
            del self.specialists[name]
            del self.role_specs[name]
            return False
        
        self.logger.info(f"✅ Registered specialist role: {name}")
        return True
    
    def get_specialist(self, name: str) -> Optional[SpecialistAgent]:
        """
        Get a specialist by name.
        
        Args:
            name: Specialist name
            
        Returns:
            SpecialistAgent instance or None if not found
        """
        return self.specialists.get(name)
    
    def consult_specialist(self, name: str, thread: ConversationThread, 
                          tools: List[Dict]) -> Dict:
        """
        Consult a specialist for analysis.
        
        Integration:
        - Uses existing SpecialistAgent.analyze() method
        - Passes ConversationThread for context
        - Returns analysis dict
        
        Args:
            name: Specialist name
            thread: ConversationThread with issue context
            tools: List of tools available to specialist
            
        Returns:
            Analysis dict with findings and recommendations
        """
        specialist = self.get_specialist(name)
        if not specialist:
            return {
                "error": f"Specialist {name} not found",
                "available_specialists": list(self.specialists.keys())
            }
        
        try:
            return specialist.analyze(thread, tools)
        except Exception as e:
            self.logger.error(f"Specialist {name} analysis failed: {e}")
            return {
                "error": f"Analysis failed: {e}",
                "specialist": name
            }
    
    def list_specialists(self) -> List[Dict]:
        """
        List all registered specialists with metadata.
        
        Returns:
            List of dicts with specialist metadata
        """
        return [
            {
                "name": spec["name"],
                "expertise": spec["expertise"],
                "responsibilities": spec.get("responsibilities", []),
                "model": spec["model"],
                "registered_at": spec.get("registered_at", "unknown"),
                "version": spec.get("version", "1.0")
            }
            for spec in self.role_specs.values()
        ]
    
    def get_spec(self, name: str) -> Optional[Dict]:
        """
        Get the full specification for a role.
        
        Args:
            name: Role name
            
        Returns:
            Role specification dict or None if not found
        """
        return self.role_specs.get(name)
    
    def delete_role(self, name: str) -> bool:
        """
        Delete a role from the registry.
        
        Args:
            name: Role name
            
        Returns:
            True if deleted, False if not found
        """
        if name not in self.specialists:
            return False
        
        # Remove from registry
        del self.specialists[name]
        del self.role_specs[name]
        
        # Delete file
        role_file = self.roles_dir / f"{name}.json"
        if role_file.exists():
            role_file.unlink()
        
        self.logger.info(f"Deleted specialist role: {name}")
        return True
    
    def search_roles(self, query: str) -> List[Dict]:
        """
        Search roles by name, expertise, or responsibilities.
        
        Args:
            query: Search query
            
        Returns:
            List of matching role metadata
        """
        query_lower = query.lower()
        matches = []
        
        for spec in self.role_specs.values():
            if (query_lower in spec["name"].lower() or 
                query_lower in spec["expertise"].lower() or
                any(query_lower in r.lower() for r in spec.get("responsibilities", []))):
                matches.append({
                    "name": spec["name"],
                    "expertise": spec["expertise"],
                    "responsibilities": spec.get("responsibilities", [])
                })
        
        return matches
    
    def get_team_for_problem(self, problem_description: str) -> List[str]:
        """
        Suggest specialists for a problem based on their decision criteria.
        
        Args:
            problem_description: Description of the problem
            
        Returns:
            List of specialist names that should be consulted
        """
        team = []
        problem_lower = problem_description.lower()
        
        for name, spec in self.role_specs.items():
            # Check decision criteria
            criteria = spec.get("decision_criteria", {})
            engagement_conditions = criteria.get("when_to_engage", [])
            
            # Simple keyword matching
            for condition in engagement_conditions:
                if any(keyword in problem_lower for keyword in condition.lower().split()):
                    team.append(name)
                    break
        
        return team
    
    def get_statistics(self) -> Dict:
        """
        Get registry statistics.
        
        Returns:
            Dict with statistics
        """
        # Group by expertise area
        by_expertise = {}
        for spec in self.role_specs.values():
            expertise = spec.get("expertise", "unknown")
            # Extract first few words as category
            category = " ".join(expertise.split()[:3])
            by_expertise[category] = by_expertise.get(category, 0) + 1
        
        return {
            "total_specialists": len(self.specialists),
            "roles_dir": str(self.roles_dir),
            "specialists": list(self.specialists.keys()),
            "by_expertise": by_expertise
        }