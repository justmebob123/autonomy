"""
Configuration Investigation System for Application Troubleshooting Phase.

This module provides tools to investigate configuration issues in applications,
including environment variables, config files, and runtime settings.
"""

import os
import json
import yaml
import configparser
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import re


class ConfigInvestigator:
    """Investigates configuration issues in applications."""
    
    def __init__(self, project_root: str):
        """
        Initialize the configuration investigator.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.config_files = []
        self.env_vars = {}
        self.config_issues = []
        
    def investigate(self) -> Dict[str, Any]:
        """
        Perform comprehensive configuration investigation.
        
        Returns:
            Dictionary containing investigation results
        """
        results = {
            'config_files': self._find_config_files(),
            'env_vars': self._analyze_env_vars(),
            'config_issues': self._detect_config_issues(),
            'recommendations': self._generate_recommendations()
        }
        
        return results
    
    def _find_config_files(self) -> List[Dict[str, Any]]:
        """Find all configuration files in the project."""
        config_patterns = [
            '*.json', '*.yaml', '*.yml', '*.toml', '*.ini',
            '*.conf', '*.config', '.env*', 'config.*'
        ]
        
        config_files = []
        
        for pattern in config_patterns:
            for file_path in self.project_root.rglob(pattern):
                if self._is_config_file(file_path):
                    config_info = self._analyze_config_file(file_path)
                    if config_info:
                        config_files.append(config_info)
        
        return config_files
    
    def _is_config_file(self, file_path: Path) -> bool:
        """Check if a file is likely a configuration file."""
        # Skip common non-config directories
        skip_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv'}
        
        if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
            return False
        
        # Check file size (skip very large files)
        try:
            if file_path.stat().st_size > 1024 * 1024:  # 1MB
                return False
        except:
            return False
        
        return True
    
    def _analyze_config_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Analyze a configuration file."""
        try:
            content = file_path.read_text()
            
            config_info = {
                'path': str(file_path.relative_to(self.project_root)),
                'type': self._detect_config_type(file_path),
                'size': file_path.stat().st_size,
                'keys': [],
                'issues': []
            }
            
            # Parse based on type
            if config_info['type'] == 'json':
                data = json.loads(content)
                config_info['keys'] = self._extract_keys(data)
            elif config_info['type'] in ['yaml', 'yml']:
                data = yaml.safe_load(content)
                config_info['keys'] = self._extract_keys(data)
            elif config_info['type'] == 'ini':
                parser = configparser.ConfigParser()
                parser.read_string(content)
                config_info['keys'] = list(parser.sections())
            elif config_info['type'] == 'env':
                config_info['keys'] = self._extract_env_keys(content)
            
            # Detect issues
            config_info['issues'] = self._detect_file_issues(file_path, content)
            
            return config_info
            
        except Exception as e:
            return {
                'path': str(file_path.relative_to(self.project_root)),
                'type': 'unknown',
                'error': str(e)
            }
    
    def _detect_config_type(self, file_path: Path) -> str:
        """Detect the type of configuration file."""
        suffix = file_path.suffix.lower()
        name = file_path.name.lower()
        
        if suffix == '.json':
            return 'json'
        elif suffix in ['.yaml', '.yml']:
            return 'yaml'
        elif suffix == '.toml':
            return 'toml'
        elif suffix in ['.ini', '.conf', '.config']:
            return 'ini'
        elif name.startswith('.env'):
            return 'env'
        
        return 'unknown'
    
    def _extract_keys(self, data: Any, prefix: str = '') -> List[str]:
        """Extract keys from nested configuration data."""
        keys = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                keys.append(full_key)
                
                if isinstance(value, (dict, list)):
                    keys.extend(self._extract_keys(value, full_key))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    keys.extend(self._extract_keys(item, f"{prefix}[{i}]"))
        
        return keys
    
    def _extract_env_keys(self, content: str) -> List[str]:
        """Extract keys from .env file content."""
        keys = []
        
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key = line.split('=')[0].strip()
                    keys.append(key)
        
        return keys
    
    def _detect_file_issues(self, file_path: Path, content: str) -> List[str]:
        """Detect issues in a configuration file."""
        issues = []
        
        # Check for empty values
        if re.search(r':\s*$', content, re.MULTILINE):
            issues.append("Contains empty values")
        
        # Check for placeholder values
        placeholders = ['TODO', 'FIXME', 'CHANGEME', 'YOUR_', 'REPLACE_']
        for placeholder in placeholders:
            if placeholder in content:
                issues.append(f"Contains placeholder: {placeholder}")
        
        # Check for localhost/development URLs in production-like configs
        if 'prod' in file_path.name.lower() or 'production' in file_path.name.lower():
            if 'localhost' in content or '127.0.0.1' in content:
                issues.append("Production config contains localhost references")
        
        # Check for hardcoded credentials
        credential_patterns = [
            r'password\s*[:=]\s*["\']?\w+["\']?',
            r'api[_-]?key\s*[:=]\s*["\']?\w+["\']?',
            r'secret\s*[:=]\s*["\']?\w+["\']?',
            r'token\s*[:=]\s*["\']?\w+["\']?'
        ]
        
        for pattern in credential_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append("May contain hardcoded credentials")
                break
        
        return issues
    
    def _analyze_env_vars(self) -> Dict[str, Any]:
        """Analyze environment variables."""
        env_analysis = {
            'total': len(os.environ),
            'relevant': [],
            'missing': [],
            'issues': []
        }
        
        # Find relevant environment variables
        relevant_prefixes = ['APP_', 'API_', 'DB_', 'DATABASE_', 'SERVER_', 'PORT']
        
        for key, value in os.environ.items():
            if any(key.startswith(prefix) for prefix in relevant_prefixes):
                env_analysis['relevant'].append({
                    'key': key,
                    'value_length': len(value),
                    'is_empty': len(value) == 0
                })
        
        # Check for common missing variables
        common_vars = ['PATH', 'HOME', 'USER']
        for var in common_vars:
            if var not in os.environ:
                env_analysis['missing'].append(var)
        
        return env_analysis
    
    def _detect_config_issues(self) -> List[Dict[str, Any]]:
        """Detect configuration issues across the project."""
        issues = []
        
        # Check for multiple config files with same purpose
        config_types = {}
        for config_file in self.config_files:
            config_type = config_file.get('type', 'unknown')
            if config_type not in config_types:
                config_types[config_type] = []
            config_types[config_type].append(config_file['path'])
        
        for config_type, files in config_types.items():
            if len(files) > 3:
                issues.append({
                    'type': 'duplicate_configs',
                    'severity': 'medium',
                    'message': f"Multiple {config_type} config files found",
                    'files': files
                })
        
        # Check for missing common config files
        common_configs = ['package.json', 'requirements.txt', 'Dockerfile']
        for config in common_configs:
            if not (self.project_root / config).exists():
                issues.append({
                    'type': 'missing_config',
                    'severity': 'low',
                    'message': f"Common config file not found: {config}"
                })
        
        return issues
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on investigation."""
        recommendations = []
        
        # Check if any config files have issues
        files_with_issues = [f for f in self.config_files if f.get('issues')]
        if files_with_issues:
            recommendations.append(
                f"Review {len(files_with_issues)} config files with potential issues"
            )
        
        # Check for environment variable issues
        if self.env_vars.get('missing'):
            recommendations.append(
                f"Set missing environment variables: {', '.join(self.env_vars['missing'])}"
            )
        
        # Check for empty relevant env vars
        empty_vars = [
            var['key'] for var in self.env_vars.get('relevant', [])
            if var.get('is_empty')
        ]
        if empty_vars:
            recommendations.append(
                f"Set empty environment variables: {', '.join(empty_vars)}"
            )
        
        # General recommendations
        if not recommendations:
            recommendations.append("No critical configuration issues detected")
        
        return recommendations
    
    def investigate_specific_config(self, config_key: str) -> Dict[str, Any]:
        """
        Investigate a specific configuration key across all config files.
        
        Args:
            config_key: The configuration key to investigate
            
        Returns:
            Dictionary containing investigation results
        """
        results = {
            'key': config_key,
            'found_in': [],
            'values': [],
            'conflicts': []
        }
        
        # Search in config files
        for config_file in self.config_files:
            if config_key in config_file.get('keys', []):
                results['found_in'].append(config_file['path'])
        
        # Search in environment variables
        if config_key in os.environ:
            results['found_in'].append('environment')
            results['values'].append({
                'source': 'environment',
                'value': os.environ[config_key]
            })
        
        # Check for conflicts
        if len(results['values']) > 1:
            unique_values = set(v['value'] for v in results['values'])
            if len(unique_values) > 1:
                results['conflicts'].append(
                    f"Different values found in {len(results['values'])} locations"
                )
        
        return results
    
    def format_report(self, results: Dict[str, Any]) -> str:
        """Format investigation results as a readable report."""
        report = []
        report.append("=" * 80)
        report.append("CONFIGURATION INVESTIGATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Config files section
        report.append("Configuration Files:")
        report.append("-" * 80)
        for config_file in results['config_files']:
            report.append(f"  • {config_file['path']}")
            report.append(f"    Type: {config_file.get('type', 'unknown')}")
            report.append(f"    Keys: {len(config_file.get('keys', []))}")
            
            if config_file.get('issues'):
                report.append(f"    Issues:")
                for issue in config_file['issues']:
                    report.append(f"      - {issue}")
            
            if config_file.get('error'):
                report.append(f"    Error: {config_file['error']}")
            
            report.append("")
        
        # Environment variables section
        report.append("Environment Variables:")
        report.append("-" * 80)
        env_vars = results['env_vars']
        report.append(f"  Total: {env_vars['total']}")
        report.append(f"  Relevant: {len(env_vars['relevant'])}")
        
        if env_vars['relevant']:
            report.append("  Relevant variables:")
            for var in env_vars['relevant']:
                status = "EMPTY" if var['is_empty'] else f"{var['value_length']} chars"
                report.append(f"    • {var['key']}: {status}")
        
        if env_vars['missing']:
            report.append(f"  Missing: {', '.join(env_vars['missing'])}")
        
        report.append("")
        
        # Issues section
        if results['config_issues']:
            report.append("Configuration Issues:")
            report.append("-" * 80)
            for issue in results['config_issues']:
                report.append(f"  • [{issue['severity'].upper()}] {issue['message']}")
                if issue.get('files'):
                    for file in issue['files'][:3]:  # Show first 3
                        report.append(f"    - {file}")
                    if len(issue['files']) > 3:
                        report.append(f"    ... and {len(issue['files']) - 3} more")
            report.append("")
        
        # Recommendations section
        report.append("Recommendations:")
        report.append("-" * 80)
        for i, rec in enumerate(results['recommendations'], 1):
            report.append(f"  {i}. {rec}")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)