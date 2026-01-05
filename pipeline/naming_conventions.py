"""
Naming Convention Manager

Extracts, validates, and enforces naming conventions from ARCHITECTURE.md
"""

from pathlib import Path
from typing import Dict, List, Optional
import re


class NamingConventionManager:
    """Manages naming conventions for the project"""
    
    def __init__(self, project_dir: Path, logger):
        self.project_dir = Path(project_dir)
        self.logger = logger
        self.conventions = self._load_conventions()
    
    def _load_conventions(self) -> Dict:
        """Load conventions from ARCHITECTURE.md"""
        arch_file = self.project_dir / "ARCHITECTURE.md"
        
        if not arch_file.exists():
            self.logger.warning("ARCHITECTURE.md not found, using defaults")
            return self._get_default_conventions()
        
        content = arch_file.read_text()
        conventions = self._parse_conventions(content)
        
        if not conventions or not any(conventions.values()):
            self.logger.warning("No conventions found in ARCHITECTURE.md, using defaults")
            return self._get_default_conventions()
        
        return conventions
    
    def _parse_conventions(self, content: str) -> Dict:
        """Parse conventions from ARCHITECTURE.md content"""
        conventions = {
            'directories': {},
            'file_patterns': {},
            'class_patterns': {},
            'function_patterns': {}
        }
        
        # Look for Naming Conventions section
        pattern = r'##\s+Naming Conventions(.*?)(?=##|\Z)'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        
        if not match:
            return conventions
        
        section = match.group(1)
        
        # Parse directory conventions
        dir_pattern = r'-\s+\*\*([^/]+)/\*\*:\s+(.+?)(?=\n|$)'
        for match in re.finditer(dir_pattern, section):
            directory = match.group(1)
            purpose = match.group(2).strip()
            conventions['directories'][directory] = {
                'purpose': purpose,
                'pattern': self._extract_pattern(purpose)
            }
        
        # Parse file patterns
        file_pattern = r'-\s+Pattern:\s+`([^`]+)`'
        for match in re.finditer(file_pattern, section):
            pattern = match.group(1)
            conventions['file_patterns'][pattern] = True
        
        return conventions
    
    def _get_default_conventions(self) -> Dict:
        """Get default conventions if none defined"""
        return {
            'directories': {
                'api': {'purpose': 'REST API endpoints', 'pattern': 'api/{resource}.py'},
                'services': {'purpose': 'Business logic', 'pattern': 'services/*_service.py'},
                'models': {'purpose': 'Data models', 'pattern': 'models/{entity}.py'},
                'core': {'purpose': 'Core utilities', 'pattern': 'core/{utility}.py'},
            },
            'file_patterns': {
                '*_service.py': 'Business logic services',
                '*_manager.py': 'Resource managers',
                '*_generator.py': 'Content generators',
                '*_engine.py': 'Processing engines',
            },
            'class_patterns': {
                '*Service': 'Service classes',
                '*Manager': 'Manager classes',
                '*Generator': 'Generator classes',
                '*Engine': 'Engine classes',
            },
            'function_patterns': {
                'create_*': 'Creation functions',
                'get_*': 'Retrieval functions',
                'update_*': 'Update functions',
                'delete_*': 'Deletion functions',
            }
        }
    
    def _extract_pattern(self, purpose: str) -> Optional[str]:
        """Extract file pattern from purpose description"""
        # Look for pattern in parentheses or after "Pattern:"
        pattern_match = re.search(r'Pattern:\s*`([^`]+)`', purpose)
        if pattern_match:
            return pattern_match.group(1)
        
        pattern_match = re.search(r'\(([^)]+\.py)\)', purpose)
        if pattern_match:
            return pattern_match.group(1)
        
        return None
    
    def validate_filename(self, filepath: str) -> Dict:
        """
        Validate filename against conventions.
        
        Returns:
            Dict with 'valid', 'issues', 'suggestions'
        """
        path = Path(filepath)
        issues = []
        suggestions = []
        
        # Check directory pattern (if directory is in conventions)
        directory = str(path.parent)
        if directory in self.conventions['directories']:
            dir_info = self.conventions['directories'][directory]
            expected_pattern = dir_info.get('pattern')
            
            if expected_pattern:
                pass
                # For directory patterns, check the full path relative to directory
                # e.g., "services/*_service.py" should match "services/task_service.py"
                if not self._matches_pattern(filepath, expected_pattern):
                    issues.append(f"Filename doesn't match directory pattern: {expected_pattern}")
                    suggestions.append(self._suggest_name(path.name, expected_pattern))
        
        # Check file pattern (just the filename)
        matched_pattern = False
        for pattern, purpose in self.conventions['file_patterns'].items():
            if self._matches_pattern(path.name, pattern):
                matched_pattern = True
                break
        
        # Only flag as issue if it's a Python file and doesn't match any pattern
        # AND it's not in a known directory (those have their own patterns)
        if not matched_pattern and path.suffix == '.py' and directory not in self.conventions['directories']:
            issues.append("Filename doesn't match any known pattern")
            suggestions.append("Consider using a standard pattern like *_service.py or *_manager.py")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'suggestions': suggestions
        }
    
    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches pattern"""
        # Handle different pattern types
        if '{' in pattern and '}' in pattern:
            pass
            # Pattern like "api/{resource}.py" or "models/{entity}.py"
            # Extract the parts before and after the placeholder
            parts = pattern.split('{')
            if len(parts) == 2:
                prefix = parts[0]
                suffix_parts = parts[1].split('}')
                if len(suffix_parts) == 2:
                    suffix = suffix_parts[1]
                    # Check if filename starts with prefix and ends with suffix
                    return filename.startswith(prefix) and filename.endswith(suffix)
        elif '*' in pattern:
            pass
            # Pattern like "*_service.py" - glob pattern
            # Convert to regex: *_service.py -> ^.*_service\.py$
            # IMPORTANT: Escape dots first, THEN replace * with .*
            regex_pattern = pattern.replace('.', r'\.')  # Escape dots
            regex_pattern = regex_pattern.replace('*', '.*')  # Replace * with .*
            regex_pattern = '^' + regex_pattern + '$'  # Add anchors
            return bool(re.match(regex_pattern, filename))
        else:
            pass
            # Exact match
            return filename == pattern
        
        return False
    
    def _suggest_name(self, filename: str, pattern: str) -> str:
        """Suggest correct name based on pattern"""
        # Extract base name
        base = Path(filename).stem
        
        # Apply pattern
        if '*' in pattern:
            return pattern.replace('*', base)
        else:
            return pattern
    
    def get_expected_directory(self, filepath: str) -> Optional[str]:
        """Get expected directory for a file based on its name"""
        filename = Path(filepath).name
        
        # Check file patterns
        for pattern, purpose in self.conventions['file_patterns'].items():
            if self._matches_pattern(filename, pattern):
                pass
                # Find directory that uses this pattern
                for directory, info in self.conventions['directories'].items():
                    if info.get('pattern') and pattern in info['pattern']:
                        return directory
        
        return None
    
    def generate_conventions_markdown(self) -> str:
        """Generate markdown documentation of conventions"""
        lines = ["## Naming Conventions\n"]
        
        lines.append("### Directory Structure\n")
        for directory, info in sorted(self.conventions['directories'].items()):
            lines.append(f"- **{directory}/**: {info['purpose']}")
            if info.get('pattern'):
                lines.append(f"  - Pattern: `{info['pattern']}`")
        
        lines.append("\n### File Naming Patterns\n")
        for pattern, purpose in sorted(self.conventions['file_patterns'].items()):
            lines.append(f"- **{pattern}**: {purpose}")
        
        return "\n".join(lines)