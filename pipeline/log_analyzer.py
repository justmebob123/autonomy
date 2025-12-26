"""
Log Analysis System for Application Troubleshooting Phase.

This module provides tools to analyze application logs and identify patterns
that indicate problems.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import Counter, defaultdict


class LogAnalyzer:
    """Analyzes application logs to identify issues."""
    
    def __init__(self, project_root: str):
        """
        Initialize the log analyzer.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.log_files = []
        self.error_patterns = []
        self.warning_patterns = []
        
    def analyze(self, log_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze logs to identify issues.
        
        Args:
            log_path: Optional specific log file to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        if log_path:
            self.log_files = [Path(log_path)]
        else:
            self.log_files = self._find_log_files()
        
        results = {
            'log_files': [str(f.relative_to(self.project_root)) for f in self.log_files],
            'errors': self._extract_errors(),
            'warnings': self._extract_warnings(),
            'patterns': self._identify_patterns(),
            'timeline': self._build_timeline(),
            'statistics': self._calculate_statistics()
        }
        
        return results
    
    def _find_log_files(self) -> List[Path]:
        """Find all log files in the project."""
        log_files = []
        
        # Common log file patterns
        log_patterns = ['*.log', '*.out', '*.err']
        log_dirs = ['logs', 'log', 'var/log']
        
        # Search in common log directories
        for log_dir in log_dirs:
            log_path = self.project_root / log_dir
            if log_path.exists():
                for pattern in log_patterns:
                    log_files.extend(log_path.rglob(pattern))
        
        # Search in project root
        for pattern in log_patterns:
            log_files.extend(self.project_root.glob(pattern))
        
        # Filter out very large files (> 100MB)
        log_files = [
            f for f in log_files
            if f.stat().st_size < 100 * 1024 * 1024
        ]
        
        return log_files
    
    def _extract_errors(self) -> List[Dict[str, Any]]:
        """Extract error messages from logs."""
        errors = []
        
        # Common error patterns
        error_patterns = [
            r'ERROR:?\s*(.+)',
            r'Error:?\s*(.+)',
            r'FATAL:?\s*(.+)',
            r'CRITICAL:?\s*(.+)',
            r'Exception:?\s*(.+)',
            r'Traceback \(most recent call last\):',
            r'Failed:?\s*(.+)',
            r'Failure:?\s*(.+)',
        ]
        
        for log_file in self.log_files:
            try:
                content = log_file.read_text()
                lines = content.split('\n')
                
                for i, line in enumerate(lines):
                    for pattern in error_patterns:
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            error_info = {
                                'file': str(log_file.relative_to(self.project_root)),
                                'line_number': i + 1,
                                'message': line.strip(),
                                'context': self._get_context(lines, i)
                            }
                            
                            # Try to extract timestamp
                            timestamp = self._extract_timestamp(line)
                            if timestamp:
                                error_info['timestamp'] = timestamp
                            
                            errors.append(error_info)
                            break
                            
            except Exception as e:
                continue
        
        return errors
    
    def _extract_warnings(self) -> List[Dict[str, Any]]:
        """Extract warning messages from logs."""
        warnings = []
        
        # Common warning patterns
        warning_patterns = [
            r'WARNING:?\s*(.+)',
            r'WARN:?\s*(.+)',
            r'Deprecated:?\s*(.+)',
        ]
        
        for log_file in self.log_files:
            try:
                content = log_file.read_text()
                lines = content.split('\n')
                
                for i, line in enumerate(lines):
                    for pattern in warning_patterns:
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            warning_info = {
                                'file': str(log_file.relative_to(self.project_root)),
                                'line_number': i + 1,
                                'message': line.strip()
                            }
                            
                            # Try to extract timestamp
                            timestamp = self._extract_timestamp(line)
                            if timestamp:
                                warning_info['timestamp'] = timestamp
                            
                            warnings.append(warning_info)
                            break
                            
            except Exception as e:
                continue
        
        return warnings
    
    def _get_context(self, lines: List[str], index: int, context_size: int = 3) -> List[str]:
        """Get context lines around an error."""
        start = max(0, index - context_size)
        end = min(len(lines), index + context_size + 1)
        return lines[start:end]
    
    def _extract_timestamp(self, line: str) -> Optional[str]:
        """Extract timestamp from a log line."""
        # Common timestamp patterns
        timestamp_patterns = [
            r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}',
            r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}',
            r'\[\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\]',
        ]
        
        for pattern in timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(0).strip('[]')
        
        return None
    
    def _identify_patterns(self) -> Dict[str, Any]:
        """Identify recurring patterns in logs."""
        patterns = {
            'error_types': Counter(),
            'error_locations': Counter(),
            'common_messages': Counter()
        }
        
        for log_file in self.log_files:
            try:
                content = log_file.read_text()
                
                # Count error types
                error_types = re.findall(
                    r'(Error|Exception|Failed|Failure)\w*',
                    content,
                    re.IGNORECASE
                )
                patterns['error_types'].update(error_types)
                
                # Count file/module references
                file_refs = re.findall(
                    r'File "([^"]+)"',
                    content
                )
                patterns['error_locations'].update(file_refs)
                
                # Extract common error messages (simplified)
                error_lines = [
                    line for line in content.split('\n')
                    if re.search(r'error|exception|failed', line, re.IGNORECASE)
                ]
                
                # Normalize messages (remove timestamps, numbers, etc.)
                normalized = [
                    re.sub(r'\d+', 'N', line)
                    for line in error_lines
                ]
                patterns['common_messages'].update(normalized[:100])  # Limit to avoid memory issues
                
            except Exception as e:
                continue
        
        return {
            'error_types': dict(patterns['error_types'].most_common(10)),
            'error_locations': dict(patterns['error_locations'].most_common(10)),
            'common_messages': dict(patterns['common_messages'].most_common(5))
        }
    
    def _build_timeline(self) -> List[Dict[str, Any]]:
        """Build a timeline of events from logs."""
        timeline = []
        
        for log_file in self.log_files:
            try:
                content = log_file.read_text()
                lines = content.split('\n')
                
                for line in lines:
                    timestamp = self._extract_timestamp(line)
                    if timestamp:
                        event_type = self._classify_log_line(line)
                        if event_type:
                            timeline.append({
                                'timestamp': timestamp,
                                'type': event_type,
                                'message': line.strip(),
                                'file': str(log_file.relative_to(self.project_root))
                            })
                            
            except Exception as e:
                continue
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x['timestamp'])
        
        return timeline[:100]  # Return first 100 events
    
    def _classify_log_line(self, line: str) -> Optional[str]:
        """Classify a log line by type."""
        line_lower = line.lower()
        
        if any(word in line_lower for word in ['error', 'exception', 'fatal', 'critical']):
            return 'error'
        elif any(word in line_lower for word in ['warning', 'warn', 'deprecated']):
            return 'warning'
        elif any(word in line_lower for word in ['info', 'information']):
            return 'info'
        elif any(word in line_lower for word in ['debug', 'trace']):
            return 'debug'
        
        return None
    
    def _calculate_statistics(self) -> Dict[str, Any]:
        """Calculate statistics about the logs."""
        stats = {
            'total_files': len(self.log_files),
            'total_size': 0,
            'total_lines': 0,
            'error_count': 0,
            'warning_count': 0
        }
        
        for log_file in self.log_files:
            try:
                stats['total_size'] += log_file.stat().st_size
                content = log_file.read_text()
                lines = content.split('\n')
                stats['total_lines'] += len(lines)
                
                # Count errors and warnings
                for line in lines:
                    if re.search(r'error|exception|fatal|critical', line, re.IGNORECASE):
                        stats['error_count'] += 1
                    elif re.search(r'warning|warn|deprecated', line, re.IGNORECASE):
                        stats['warning_count'] += 1
                        
            except Exception as e:
                continue
        
        # Convert size to human-readable format
        stats['total_size_mb'] = round(stats['total_size'] / (1024 * 1024), 2)
        
        return stats
    
    def search_logs(self, pattern: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
        Search for a specific pattern in logs.
        
        Args:
            pattern: Regular expression pattern to search for
            case_sensitive: Whether the search should be case-sensitive
            
        Returns:
            List of matches with context
        """
        matches = []
        flags = 0 if case_sensitive else re.IGNORECASE
        
        for log_file in self.log_files:
            try:
                content = log_file.read_text()
                lines = content.split('\n')
                
                for i, line in enumerate(lines):
                    if re.search(pattern, line, flags):
                        matches.append({
                            'file': str(log_file.relative_to(self.project_root)),
                            'line_number': i + 1,
                            'line': line.strip(),
                            'context': self._get_context(lines, i, 2)
                        })
                        
            except Exception as e:
                continue
        
        return matches
    
    def format_report(self, results: Dict[str, Any]) -> str:
        """Format analysis results as a readable report."""
        report = []
        report.append("=" * 80)
        report.append("LOG ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Statistics section
        stats = results.get('statistics', {})
        report.append("Log Statistics:")
        report.append("-" * 80)
        report.append(f"  Total Files: {stats.get('total_files', 0)}")
        report.append(f"  Total Size: {stats.get('total_size_mb', 0)} MB")
        report.append(f"  Total Lines: {stats.get('total_lines', 0)}")
        report.append(f"  Error Count: {stats.get('error_count', 0)}")
        report.append(f"  Warning Count: {stats.get('warning_count', 0)}")
        report.append("")
        
        # Errors section
        report.append("Recent Errors:")
        report.append("-" * 80)
        errors = results.get('errors', [])
        if errors:
            for error in errors[:10]:  # Show first 10
                report.append(f"  • {error['file']}:{error['line_number']}")
                report.append(f"    {error['message']}")
                if error.get('timestamp'):
                    report.append(f"    Time: {error['timestamp']}")
                report.append("")
            
            if len(errors) > 10:
                report.append(f"  ... and {len(errors) - 10} more errors")
                report.append("")
        else:
            report.append("  No errors found")
            report.append("")
        
        # Warnings section
        report.append("Recent Warnings:")
        report.append("-" * 80)
        warnings = results.get('warnings', [])
        if warnings:
            for warning in warnings[:5]:  # Show first 5
                report.append(f"  • {warning['file']}:{warning['line_number']}")
                report.append(f"    {warning['message']}")
                report.append("")
            
            if len(warnings) > 5:
                report.append(f"  ... and {len(warnings) - 5} more warnings")
                report.append("")
        else:
            report.append("  No warnings found")
            report.append("")
        
        # Patterns section
        patterns = results.get('patterns', {})
        if patterns:
            report.append("Common Error Patterns:")
            report.append("-" * 80)
            
            error_types = patterns.get('error_types', {})
            if error_types:
                report.append("  Error Types:")
                for error_type, count in list(error_types.items())[:5]:
                    report.append(f"    • {error_type}: {count} occurrences")
                report.append("")
            
            error_locations = patterns.get('error_locations', {})
            if error_locations:
                report.append("  Most Problematic Files:")
                for location, count in list(error_locations.items())[:5]:
                    report.append(f"    • {location}: {count} errors")
                report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)