"""
Change History Analysis System for Application Troubleshooting Phase.

This module provides tools to analyze git history and identify changes that
may have introduced issues.
"""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import re


class ChangeHistoryAnalyzer:
    """Analyzes git history to identify problematic changes."""
    
    def __init__(self, project_root: str):
        """
        Initialize the change history analyzer.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.git_available = self._check_git_available()
        
    def _check_git_available(self) -> bool:
        """Check if git is available and the directory is a git repository."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def analyze(self, days: int = 7) -> Dict[str, Any]:
        """
        Analyze recent changes in the repository.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary containing analysis results
        """
        if not self.git_available:
            return {
                'error': 'Git not available or not a git repository',
                'commits': [],
                'file_changes': [],
                'risky_changes': []
            }
        
        results = {
            'commits': self._get_recent_commits(days),
            'file_changes': self._analyze_file_changes(days),
            'risky_changes': self._identify_risky_changes(days),
            'blame_analysis': self._analyze_blame()
        }
        
        return results
    
    def _get_recent_commits(self, days: int) -> List[Dict[str, Any]]:
        """Get recent commits from git history."""
        try:
            since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            result = subprocess.run(
                [
                    'git', 'log',
                    f'--since={since_date}',
                    '--pretty=format:%H|%an|%ae|%ad|%s',
                    '--date=iso'
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return []
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('|')
                if len(parts) >= 5:
                    commits.append({
                        'hash': parts[0],
                        'author': parts[1],
                        'email': parts[2],
                        'date': parts[3],
                        'message': '|'.join(parts[4:])
                    })
            
            return commits
            
        except Exception as e:
            return []
    
    def _analyze_file_changes(self, days: int) -> List[Dict[str, Any]]:
        """Analyze which files have changed recently."""
        try:
            since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            result = subprocess.run(
                [
                    'git', 'log',
                    f'--since={since_date}',
                    '--name-status',
                    '--pretty=format:%H'
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return []
            
            file_changes = {}
            current_commit = None
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                # Check if it's a commit hash
                if len(line) == 40 and all(c in '0123456789abcdef' for c in line):
                    current_commit = line
                    continue
                
                # Parse file change
                parts = line.split('\t')
                if len(parts) >= 2:
                    status = parts[0]
                    file_path = parts[1]
                    
                    if file_path not in file_changes:
                        file_changes[file_path] = {
                            'path': file_path,
                            'modifications': 0,
                            'additions': 0,
                            'deletions': 0,
                            'renames': 0
                        }
                    
                    if status == 'M':
                        file_changes[file_path]['modifications'] += 1
                    elif status == 'A':
                        file_changes[file_path]['additions'] += 1
                    elif status == 'D':
                        file_changes[file_path]['deletions'] += 1
                    elif status.startswith('R'):
                        file_changes[file_path]['renames'] += 1
            
            # Sort by total changes
            sorted_changes = sorted(
                file_changes.values(),
                key=lambda x: x['modifications'] + x['additions'] + x['deletions'],
                reverse=True
            )
            
            return sorted_changes[:20]  # Top 20 most changed files
            
        except Exception as e:
            return []
    
    def _identify_risky_changes(self, days: int) -> List[Dict[str, Any]]:
        """Identify potentially risky changes."""
        risky_changes = []
        
        commits = self._get_recent_commits(days)
        
        # Patterns that indicate risky changes
        risky_patterns = [
            (r'\bconfig\b', 'Configuration change'),
            (r'\bserver\b', 'Server-related change'),
            (r'\bapi\b', 'API change'),
            (r'\bdatabase\b|\bdb\b', 'Database change'),
            (r'\bauth\b|\bauthentication\b', 'Authentication change'),
            (r'\bsecurity\b', 'Security change'),
            (r'\bfix\b|\bbug\b', 'Bug fix (may have introduced new issues)'),
            (r'\brefactor\b', 'Refactoring (may have side effects)'),
            (r'\bremove\b|\bdelete\b', 'Removal/deletion'),
            (r'\bmigration\b', 'Migration'),
        ]
        
        for commit in commits:
            message = commit['message'].lower()
            
            for pattern, description in risky_patterns:
                if re.search(pattern, message):
                    risky_changes.append({
                        'commit': commit['hash'][:8],
                        'date': commit['date'],
                        'author': commit['author'],
                        'message': commit['message'],
                        'risk_type': description
                    })
                    break
        
        return risky_changes
    
    def _analyze_blame(self) -> Dict[str, Any]:
        """Analyze git blame for critical files."""
        critical_files = [
            'server.py', 'main.py', 'app.py', 'config.py',
            'settings.py', 'run.py', '__init__.py'
        ]
        
        blame_analysis = {
            'files_analyzed': [],
            'recent_authors': {}
        }
        
        for file_name in critical_files:
            file_path = self._find_file(file_name)
            if file_path:
                blame_info = self._get_file_blame(file_path)
                if blame_info:
                    blame_analysis['files_analyzed'].append({
                        'file': str(file_path.relative_to(self.project_root)),
                        'authors': blame_info
                    })
                    
                    # Aggregate author statistics
                    for author, lines in blame_info.items():
                        if author not in blame_analysis['recent_authors']:
                            blame_analysis['recent_authors'][author] = 0
                        blame_analysis['recent_authors'][author] += lines
        
        return blame_analysis
    
    def _find_file(self, file_name: str) -> Optional[Path]:
        """Find a file in the project."""
        for file_path in self.project_root.rglob(file_name):
            # Skip common non-source directories
            skip_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv'}
            if not any(skip_dir in file_path.parts for skip_dir in skip_dirs):
                return file_path
        return None
    
    def _get_file_blame(self, file_path: Path) -> Optional[Dict[str, int]]:
        """Get git blame information for a file."""
        try:
            result = subprocess.run(
                ['git', 'blame', '--line-porcelain', str(file_path)],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return None
            
            authors = {}
            current_author = None
            
            for line in result.stdout.split('\n'):
                if line.startswith('author '):
                    current_author = line[7:]
                elif line.startswith('\t') and current_author:
                    if current_author not in authors:
                        authors[current_author] = 0
                    authors[current_author] += 1
            
            return authors
            
        except Exception as e:
            return None
    
    def compare_commits(self, commit1: str, commit2: str) -> Dict[str, Any]:
        """
        Compare two commits to see what changed.
        
        Args:
            commit1: First commit hash
            commit2: Second commit hash
            
        Returns:
            Dictionary containing comparison results
        """
        if not self.git_available:
            return {'error': 'Git not available'}
        
        try:
            result = subprocess.run(
                ['git', 'diff', '--stat', commit1, commit2],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {'error': 'Failed to compare commits'}
            
            return {
                'commit1': commit1,
                'commit2': commit2,
                'diff_stat': result.stdout
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def format_report(self, results: Dict[str, Any]) -> str:
        """Format analysis results as a readable report."""
        report = []
        report.append("=" * 80)
        report.append("CHANGE HISTORY ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")
        
        if results.get('error'):
            report.append(f"Error: {results['error']}")
            return "\n".join(report)
        
        # Recent commits section
        report.append("Recent Commits:")
        report.append("-" * 80)
        commits = results.get('commits', [])
        if commits:
            for commit in commits[:10]:  # Show first 10
                report.append(f"  • {commit['hash'][:8]} - {commit['date']}")
                report.append(f"    Author: {commit['author']}")
                report.append(f"    Message: {commit['message']}")
                report.append("")
            
            if len(commits) > 10:
                report.append(f"  ... and {len(commits) - 10} more commits")
                report.append("")
        else:
            report.append("  No recent commits found")
            report.append("")
        
        # File changes section
        report.append("Most Changed Files:")
        report.append("-" * 80)
        file_changes = results.get('file_changes', [])
        if file_changes:
            for change in file_changes[:10]:  # Show top 10
                total = (change['modifications'] + change['additions'] + 
                        change['deletions'] + change['renames'])
                report.append(f"  • {change['path']}")
                report.append(f"    Total changes: {total} " +
                            f"(M:{change['modifications']} " +
                            f"A:{change['additions']} " +
                            f"D:{change['deletions']} " +
                            f"R:{change['renames']})")
                report.append("")
        else:
            report.append("  No file changes found")
            report.append("")
        
        # Risky changes section
        report.append("Potentially Risky Changes:")
        report.append("-" * 80)
        risky_changes = results.get('risky_changes', [])
        if risky_changes:
            for change in risky_changes[:10]:  # Show first 10
                report.append(f"  • {change['commit']} - {change['risk_type']}")
                report.append(f"    Date: {change['date']}")
                report.append(f"    Author: {change['author']}")
                report.append(f"    Message: {change['message']}")
                report.append("")
            
            if len(risky_changes) > 10:
                report.append(f"  ... and {len(risky_changes) - 10} more risky changes")
                report.append("")
        else:
            report.append("  No risky changes identified")
            report.append("")
        
        # Blame analysis section
        blame_analysis = results.get('blame_analysis', {})
        if blame_analysis.get('recent_authors'):
            report.append("Recent Contributors:")
            report.append("-" * 80)
            sorted_authors = sorted(
                blame_analysis['recent_authors'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            for author, lines in sorted_authors[:5]:  # Top 5 contributors
                report.append(f"  • {author}: {lines} lines")
            report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)