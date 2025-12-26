"""
Architecture Analyzer

Parses MASTER_PLAN.md and compares actual implementation
against intended architecture.
"""

from pathlib import Path
from typing import Dict, List, Optional
import re
import logging


class ArchitectureAnalyzer:
    """Analyzes architecture against MASTER_PLAN.md"""
    
    def __init__(self, project_root: str, logger: Optional[logging.Logger] = None):
        self.project_root = Path(project_root)
        self.logger = logger or logging.getLogger(__name__)
        
        # Try multiple locations for MASTER_PLAN.md
        self.master_plan_paths = [
            self.project_root / 'pipeline_docs' / 'MASTER_PLAN.md',
            self.project_root / 'MASTER_PLAN.md',
            self.project_root / 'docs' / 'MASTER_PLAN.md',
        ]
        
        self.master_plan_path = None
        for path in self.master_plan_paths:
            if path.exists():
                self.master_plan_path = path
                break
    
    def parse_master_plan(self, master_plan_path: Optional[str] = None) -> Dict:
        """
        Extract architecture from MASTER_PLAN.md.
        
        Parses:
        - Component definitions
        - Relationships
        - Data flow
        - Configuration requirements
        
        Returns:
            Dict with components, relationships, requirements
        """
        # Use provided path or default
        if master_plan_path:
            plan_path = Path(master_plan_path)
            if not plan_path.is_absolute():
                plan_path = self.project_root / master_plan_path
        else:
            plan_path = self.master_plan_path
        
        if not plan_path or not plan_path.exists():
            return {
                'success': False,
                'error': f"MASTER_PLAN.md not found. Searched: {[str(p) for p in self.master_plan_paths]}"
            }
        
        try:
            with open(plan_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {
                'success': False,
                'error': f"Error reading MASTER_PLAN.md: {e}"
            }
        
        architecture = {
            'success': True,
            'components': [],
            'relationships': [],
            'data_flow': [],
            'configuration': {},
            'version': 'unknown',
            'last_updated': 'unknown'
        }
        
        # Parse sections
        architecture['components'] = self._parse_components(content)
        architecture['relationships'] = self._parse_relationships(content)
        architecture['data_flow'] = self._parse_data_flow(content)
        architecture['configuration'] = self._parse_configuration(content)
        
        # Extract metadata
        version_match = re.search(r'Version:\s*([^\n]+)', content)
        if version_match:
            architecture['version'] = version_match.group(1).strip()
        
        date_match = re.search(r'Last Updated:\s*([^\n]+)', content)
        if date_match:
            architecture['last_updated'] = date_match.group(1).strip()
        
        self.logger.info(f"Parsed MASTER_PLAN.md: {len(architecture['components'])} components")
        return architecture
    
    def _parse_components(self, content: str) -> List[Dict]:
        """Parse component definitions from markdown"""
        components = []
        
        # Look for component sections (## ComponentName or ### ComponentName)
        component_pattern = r'##\s+([A-Z][A-Za-z]+)\s*\n(.*?)(?=\n##|\Z)'
        
        for match in re.finditer(component_pattern, content, re.DOTALL):
            component_name = match.group(1)
            component_content = match.group(2)
            
            # Skip common section names
            if component_name in ['Overview', 'Architecture', 'Configuration', 'Usage']:
                continue
            
            component = {
                'name': component_name,
                'purpose': '',
                'location': '',
                'dependencies': [],
                'configuration': {}
            }
            
            # Extract purpose
            purpose_match = re.search(r'Purpose:\s*([^\n]+)', component_content)
            if purpose_match:
                component['purpose'] = purpose_match.group(1).strip()
            
            # Extract location
            location_match = re.search(r'Location:\s*([^\n]+)', component_content)
            if location_match:
                component['location'] = location_match.group(1).strip()
            
            # Extract dependencies
            deps_match = re.search(r'Dependencies:\s*([^\n]+)', component_content)
            if deps_match:
                deps_str = deps_match.group(1).strip()
                component['dependencies'] = [d.strip() for d in deps_str.split(',')]
            
            components.append(component)
        
        return components
    
    def _parse_relationships(self, content: str) -> List[Dict]:
        """Parse component relationships"""
        relationships = []
        
        # Look for relationship descriptions
        # Pattern: "ComponentA uses ComponentB"
        uses_pattern = r'([A-Z][A-Za-z]+)\s+uses\s+([A-Z][A-Za-z]+)'
        
        for match in re.finditer(uses_pattern, content):
            relationships.append({
                'from': match.group(1),
                'to': match.group(2),
                'type': 'uses'
            })
        
        # Pattern: "ComponentA depends on ComponentB"
        depends_pattern = r'([A-Z][A-Za-z]+)\s+depends on\s+([A-Z][A-Za-z]+)'
        
        for match in re.finditer(depends_pattern, content):
            relationships.append({
                'from': match.group(1),
                'to': match.group(2),
                'type': 'depends_on'
            })
        
        return relationships
    
    def _parse_data_flow(self, content: str) -> List[Dict]:
        """Parse data flow descriptions"""
        data_flows = []
        
        # Look for data flow descriptions
        # Pattern: "data flows from X to Y"
        flow_pattern = r'([A-Za-z.]+)\s+(?:flows?|passes?)\s+(?:from|to)\s+([A-Za-z.]+)'
        
        for match in re.finditer(flow_pattern, content):
            data_flows.append({
                'source': match.group(1),
                'destination': match.group(2)
            })
        
        return data_flows
    
    def _parse_configuration(self, content: str) -> Dict:
        """Parse configuration requirements"""
        config = {
            'files': [],
            'required_fields': [],
            'optional_fields': []
        }
        
        # Look for configuration file mentions
        config_file_pattern = r'([a-z_]+\.(?:yaml|yml|json|ini|conf))'
        config['files'] = list(set(re.findall(config_file_pattern, content)))
        
        # Look for required fields
        required_pattern = r'required:\s*([^\n]+)'
        for match in re.finditer(required_pattern, content, re.IGNORECASE):
            fields = [f.strip() for f in match.group(1).split(',')]
            config['required_fields'].extend(fields)
        
        return config
    
    def compare_architecture(
        self,
        actual_structure: Optional[Dict] = None
    ) -> Dict:
        """
        Compare actual implementation vs. intended architecture.
        
        Args:
            actual_structure: Optional dict with actual code structure
                             (if None, will analyze project files)
        
        Returns:
            Dict with matches, deviations, violations
        """
        # Parse MASTER_PLAN
        architecture = self.parse_master_plan()
        if not architecture.get('success'):
            return architecture
        
        # Analyze actual structure if not provided
        if actual_structure is None:
            actual_structure = self._analyze_actual_structure()
        
        comparison = {
            'success': True,
            'matches': [],
            'deviations': [],
            'violations': [],
            'missing_components': [],
            'overall_compliance': 0.0,
            'critical_issues': 0
        }
        
        # Compare components
        for component in architecture['components']:
            component_name = component['name']
            expected_location = component['location']
            
            # Check if component exists
            if expected_location:
                component_path = self.project_root / expected_location
                if component_path.exists():
                    comparison['matches'].append({
                        'component': component_name,
                        'status': 'IMPLEMENTED',
                        'location': expected_location,
                        'compliance': 1.0
                    })
                else:
                    comparison['missing_components'].append({
                        'component': component_name,
                        'expected_location': expected_location,
                        'severity': 'HIGH'
                    })
        
        # Check configuration requirements
        config_reqs = architecture.get('configuration', {})
        for config_file in config_reqs.get('files', []):
            config_path = self.project_root / config_file
            if not config_path.exists():
                comparison['violations'].append({
                    'rule': f'Configuration file {config_file} must exist',
                    'violated_by': 'Missing file',
                    'location': config_file,
                    'severity': 'CRITICAL'
                })
                comparison['critical_issues'] += 1
        
        # Calculate overall compliance
        total_checks = len(architecture['components']) + len(config_reqs.get('files', []))
        passed_checks = len(comparison['matches'])
        if total_checks > 0:
            comparison['overall_compliance'] = passed_checks / total_checks
        
        return comparison
    
    def _analyze_actual_structure(self) -> Dict:
        """Analyze actual project structure"""
        structure = {
            'files': [],
            'modules': [],
            'classes': [],
            'functions': []
        }
        
        # List all Python files
        for py_file in self.project_root.rglob('*.py'):
            rel_path = py_file.relative_to(self.project_root)
            structure['files'].append(str(rel_path))
            structure['modules'].append(self._path_to_module(py_file))
        
        return structure
    
    def _path_to_module(self, file_path: Path) -> str:
        """Convert file path to module name"""
        try:
            rel_path = file_path.relative_to(self.project_root)
            module = str(rel_path).replace('/', '.').replace('\\', '.').replace('.py', '')
            return module
        except ValueError:
            return str(file_path)
    
    def suggest_architectural_fix(
        self,
        error_info: Dict,
        architecture: Dict
    ) -> Dict:
        """
        Recommend fix aligned with architecture.
        
        Args:
            error_info: Dict with error details
            architecture: Parsed architecture from MASTER_PLAN
        
        Returns:
            Dict with recommended fix and reasoning
        """
        error_message = error_info.get('error_message', '')
        error_location = error_info.get('error_location', '')
        
        recommendation = {
            'success': True,
            'error': error_message,
            'root_cause': '',
            'architectural_context': {},
            'recommended_fix': {
                'strategy': 'UNKNOWN',
                'description': '',
                'files_to_create': [],
                'files_to_modify': [],
                'template': '',
                'reasoning': [],
                'confidence': 0.5
            },
            'alternative_fixes': []
        }
        
        # Analyze error type
        if 'no available servers' in error_message.lower():
            recommendation['root_cause'] = 'Server configuration missing or incomplete'
            recommendation['architectural_context'] = {
                'component': 'ServerPool',
                'intended_behavior': 'Load servers from configuration with proper URLs',
                'actual_behavior': 'Servers loaded but URLs are None'
            }
            
            # Check if servers.yaml is mentioned in architecture
            config_files = architecture.get('configuration', {}).get('files', [])
            if 'servers.yaml' in config_files:
                recommendation['recommended_fix'] = {
                    'strategy': 'CREATE_MISSING_CONFIG',
                    'description': 'Create servers.yaml with proper server definitions',
                    'files_to_create': ['servers.yaml'],
                    'files_to_modify': [],
                    'template': self._get_servers_yaml_template(),
                    'reasoning': [
                        'MASTER_PLAN.md specifies servers.yaml as configuration source',
                        'Code expects servers with URL and models fields',
                        'Creating servers.yaml aligns with intended architecture'
                    ],
                    'confidence': 0.95
                }
            else:
                recommendation['recommended_fix'] = {
                    'strategy': 'MODIFY_EXISTING_CONFIG',
                    'description': 'Add server URLs to config.yaml',
                    'files_to_create': [],
                    'files_to_modify': ['config.yaml'],
                    'template': self._get_config_yaml_servers_template(),
                    'reasoning': [
                        'config.yaml is the primary configuration file',
                        'Add server definitions with URLs and models'
                    ],
                    'confidence': 0.80
                }
        
        elif 'configuration' in error_message.lower():
            recommendation['root_cause'] = 'Configuration error'
            recommendation['recommended_fix']['strategy'] = 'FIX_CONFIGURATION'
        
        elif 'not found' in error_message.lower():
            recommendation['root_cause'] = 'Missing resource or component'
            recommendation['recommended_fix']['strategy'] = 'CREATE_MISSING_RESOURCE'
        
        return recommendation
    
    def _get_servers_yaml_template(self) -> str:
        """Get template for servers.yaml"""
        return """# Ollama Server Configuration
servers:
  - name: ollama01
    url: http://ollama01.thiscluster.net:11434
    models:
      - qwen2.5-coder:32b
      - qwen2.5-coder:14b
      - phi4
      - qwen2.5:14b
  
  - name: ollama02
    url: http://ollama02.thiscluster.net:11434
    models:
      - qwen2.5-coder:32b
      - deepseek-coder-v2
      - qwen2.5:14b
      - llama3.1:70b
      - deepseek-coder-v2:16b
"""
    
    def _get_config_yaml_servers_template(self) -> str:
        """Get template for servers section in config.yaml"""
        return """# Add to config.yaml:
servers:
  - name: ollama01
    url: http://ollama01.thiscluster.net:11434
  - name: ollama02
    url: http://ollama02.thiscluster.net:11434
"""