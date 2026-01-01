"""
Architectural Context Provider

Provides architectural context for file placement decisions.
Parses ARCHITECTURE.md and applies placement rules.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class PlacementRule:
    """Rule for where files should be placed."""
    category: str  # e.g., 'models', 'services', 'utils'
    location: str  # e.g., 'app/models/'
    pattern: str  # e.g., '*_model.py'
    description: str
    indicators: List[str]  # Keywords that indicate this category


@dataclass
class ValidationResult:
    """Result of validating a file's location."""
    valid: bool
    violations: List[str]
    suggested_location: Optional[str]
    reason: str
    confidence: float  # 0.0 to 1.0


class ArchitecturalContextProvider:
    """
    Provides architectural context for file placement.
    
    Features:
    - Parse ARCHITECTURE.md for placement rules
    - Suggest optimal file locations
    - Validate file placements
    - Convention-based organization
    """
    
    def __init__(self, project_root: str, logger=None):
        self.project_root = Path(project_root)
        self.logger = logger
        self.placement_rules: List[PlacementRule] = []
        self._load_rules()
        
    def _load_rules(self):
        """Load placement rules from ARCHITECTURE.md and defaults."""
        # Load from ARCHITECTURE.md if exists
        arch_file = self.project_root / 'ARCHITECTURE.md'
        if arch_file.exists():
            self._parse_architecture_file(arch_file)
        
        # Add default rules if none loaded
        if not self.placement_rules:
            self._add_default_rules()
    
    def _parse_architecture_file(self, arch_file: Path):
        """Parse ARCHITECTURE.md for placement rules."""
        try:
            with open(arch_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for directory structure sections
            # Pattern: ## Directory Structure or similar
            structure_section = self._extract_section(content, 'directory structure')
            
            if structure_section:
                self._parse_structure_section(structure_section)
            
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Failed to parse ARCHITECTURE.md: {e}")
    
    def _extract_section(self, content: str, section_name: str) -> Optional[str]:
        """Extract a section from markdown content."""
        # Find section header
        pattern = rf'##\s+{re.escape(section_name)}.*?\n(.*?)(?=\n##|\Z)'
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        
        if match:
            return match.group(1)
        
        return None
    
    def _parse_structure_section(self, section: str):
        """Parse directory structure section for rules."""
        # Look for patterns like:
        # - app/models/ - Database models
        # - app/services/ - Business logic services
        
        lines = section.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Pattern: - path/ - description
            match = re.match(r'[-*]\s+([a-zA-Z0-9_/]+/)\s*[-–—]\s*(.+)', line)
            if match:
                location = match.group(1)
                description = match.group(2).strip()
                
                # Extract category from location
                parts = location.strip('/').split('/')
                category = parts[-1] if parts else 'unknown'
                
                # Determine indicators from description
                indicators = self._extract_indicators(description)
                
                rule = PlacementRule(
                    category=category,
                    location=location,
                    pattern=f'*.py',
                    description=description,
                    indicators=indicators
                )
                
                self.placement_rules.append(rule)
    
    def _extract_indicators(self, description: str) -> List[str]:
        """Extract keywords that indicate a category."""
        indicators = []
        
        # Common patterns
        patterns = {
            'model': ['model', 'database', 'orm', 'table', 'entity'],
            'service': ['service', 'business logic', 'use case', 'application'],
            'controller': ['controller', 'handler', 'endpoint', 'route'],
            'util': ['utility', 'helper', 'common', 'shared'],
            'test': ['test', 'testing', 'spec'],
            'config': ['configuration', 'settings', 'config'],
            'api': ['api', 'rest', 'graphql', 'endpoint'],
            'view': ['view', 'template', 'ui', 'frontend'],
        }
        
        desc_lower = description.lower()
        for category, keywords in patterns.items():
            if any(keyword in desc_lower for keyword in keywords):
                indicators.extend(keywords)
        
        return list(set(indicators))
    
    def _add_default_rules(self):
        """Add default placement rules."""
        default_rules = [
            PlacementRule(
                category='models',
                location='app/models/',
                pattern='*_model.py',
                description='Database models and ORM entities',
                indicators=['model', 'database', 'orm', 'table', 'entity', 'schema']
            ),
            PlacementRule(
                category='services',
                location='app/services/',
                pattern='*_service.py',
                description='Business logic and application services',
                indicators=['service', 'business', 'logic', 'use case', 'application']
            ),
            PlacementRule(
                category='controllers',
                location='app/controllers/',
                pattern='*_controller.py',
                description='Request handlers and controllers',
                indicators=['controller', 'handler', 'endpoint', 'route', 'api']
            ),
            PlacementRule(
                category='utils',
                location='app/utils/',
                pattern='*.py',
                description='Utility functions and helpers',
                indicators=['utility', 'helper', 'common', 'shared', 'tool']
            ),
            PlacementRule(
                category='tests',
                location='tests/',
                pattern='test_*.py',
                description='Test files',
                indicators=['test', 'testing', 'spec', 'fixture']
            ),
            PlacementRule(
                category='config',
                location='app/config/',
                pattern='*.py',
                description='Configuration files',
                indicators=['config', 'configuration', 'settings', 'environment']
            ),
        ]
        
        self.placement_rules.extend(default_rules)
    
    def get_placement_rules(self) -> List[PlacementRule]:
        """Get all placement rules."""
        return self.placement_rules
    
    def suggest_file_location(
        self,
        file_content: str,
        file_name: str
    ) -> Tuple[str, float]:
        """
        Suggest optimal location for a file based on its content.
        
        Args:
            file_content: Content of the file
            file_name: Name of the file
            
        Returns:
            Tuple of (suggested_path, confidence)
        """
        # Analyze file content
        content_lower = file_content.lower()
        name_lower = file_name.lower()
        
        # Score each rule
        scores = []
        
        for rule in self.placement_rules:
            score = 0.0
            
            # Check filename pattern
            if self._matches_pattern(file_name, rule.pattern):
                score += 0.3
            
            # Check indicators in content
            indicator_matches = sum(
                1 for indicator in rule.indicators
                if indicator in content_lower
            )
            if indicator_matches > 0:
                score += min(0.5, indicator_matches * 0.1)
            
            # Check indicators in filename
            name_matches = sum(
                1 for indicator in rule.indicators
                if indicator in name_lower
            )
            if name_matches > 0:
                score += min(0.2, name_matches * 0.1)
            
            scores.append((rule, score))
        
        # Get best match
        if scores:
            best_rule, best_score = max(scores, key=lambda x: x[1])
            suggested_path = best_rule.location + file_name
            return suggested_path, best_score
        
        # Default to root if no match
        return file_name, 0.0
    
    def validate_file_location(self, file_path: str) -> ValidationResult:
        """
        Validate if a file is in the correct location.
        
        Args:
            file_path: Current file path
            
        Returns:
            ValidationResult object
        """
        full_path = self.project_root / file_path
        
        if not full_path.exists():
            return ValidationResult(
                valid=False,
                violations=['File does not exist'],
                suggested_location=None,
                reason='File not found',
                confidence=0.0
            )
        
        # Read file content
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return ValidationResult(
                valid=False,
                violations=[f'Cannot read file: {e}'],
                suggested_location=None,
                reason='File read error',
                confidence=0.0
            )
        
        # Get suggested location
        file_name = Path(file_path).name
        suggested_path, confidence = self.suggest_file_location(content, file_name)
        
        # Check if current location matches suggestion
        current_dir = str(Path(file_path).parent) + '/'
        suggested_dir = str(Path(suggested_path).parent) + '/'
        
        if current_dir == suggested_dir:
            return ValidationResult(
                valid=True,
                violations=[],
                suggested_location=None,
                reason='File is in correct location',
                confidence=confidence
            )
        else:
            return ValidationResult(
                valid=False,
                violations=[f'File should be in {suggested_dir}'],
                suggested_location=suggested_path,
                reason=f'File location does not match architectural conventions',
                confidence=confidence
            )
    
    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches a pattern."""
        # Simple pattern matching (* wildcard)
        if pattern == '*.py':
            return filename.endswith('.py')
        
        if pattern.startswith('*') and pattern.endswith('.py'):
            suffix = pattern[1:-3]  # Remove * and .py
            return filename.endswith(f'{suffix}.py')
        
        if pattern.endswith('*'):
            prefix = pattern[:-1]
            return filename.startswith(prefix)
        
        return filename == pattern