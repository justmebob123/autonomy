"""
Patch Analysis Module

Extends PatchManager with analysis capabilities for correlating
patches with errors and suggesting rollbacks.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import re
import logging


class PatchAnalyzer:
    """Analyzes patch history to correlate with errors"""
    
    def __init__(self, project_root: str, logger: Optional[logging.Logger] = None):
        self.project_root = Path(project_root)
        self.patches_dir = self.project_root / '.patches'
        self.logger = logger or logging.getLogger(__name__)
        
        # Ensure patches directory exists
        self.patches_dir.mkdir(exist_ok=True)
    
    def list_patch_files(
        self,
        days_back: int = 7,
        file_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        List patches with metadata from .patches/ directory.
        
        Args:
            days_back: Number of days to look back (default: 7)
            file_filter: Optional filter for specific file (e.g., 'server_pool.py')
        
        Returns:
            List of dicts with patch metadata
        """
        if not self.patches_dir.exists():
            self.logger.warning(f"Patches directory not found: {self.patches_dir}")
            return []
        
        patches = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Pattern: change_NNNN_YYYYMMDD_HHMMSS_filename_lineNN.patch
        patch_pattern = re.compile(r'change_(\d+)_(\d{8})_(\d{6})_(.+)_line(\d+)\.patch')
        
        for patch_file in self.patches_dir.glob('*.patch'):
            match = patch_pattern.match(patch_file.name)
            if not match:
                continue
            
            change_num = int(match.group(1))
            date_str = match.group(2)
            time_str = match.group(3)
            filename = match.group(4)
            line_num = int(match.group(5))
            
            # Parse timestamp
            timestamp_str = f"{date_str}_{time_str}"
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
            except ValueError:
                continue
            
            # Filter by date
            if timestamp < cutoff_date:
                continue
            
            # Filter by file
            if file_filter and file_filter not in filename:
                continue
            
            # Get file size
            size_bytes = patch_file.stat().st_size
            
            # Calculate age
            age_hours = (datetime.now() - timestamp).total_seconds() / 3600
            
            patches.append({
                'filename': patch_file.name,
                'path': str(patch_file),
                'change_number': change_num,
                'timestamp': timestamp.isoformat(),
                'file_modified': f"{filename}.py",
                'line_modified': line_num,
                'age_hours': round(age_hours, 1),
                'size_bytes': size_bytes
            })
        
        # Sort by timestamp (newest first)
        patches.sort(key=lambda p: p['timestamp'], reverse=True)
        
        self.logger.info(f"Found {len(patches)} patches in last {days_back} days")
        return patches
    
    def analyze_patch_file(self, patch_file: str) -> Dict:
        """
        Parse patch file and extract detailed changes.
        
        Args:
            patch_file: Path to patch file (relative to .patches/ or absolute)
        
        Returns:
            Dict with detailed change information
        """
        # Resolve patch file path
        patch_path = Path(patch_file)
        if not patch_path.is_absolute():
            patch_path = self.patches_dir / patch_file
        
        if not patch_path.exists():
            return {
                'success': False,
                'error': f"Patch file not found: {patch_path}"
            }
        
        try:
            with open(patch_path, 'r', encoding='utf-8') as f:
                patch_content = f.read()
        except Exception as e:
            return {
                'success': False,
                'error': f"Error reading patch file: {e}"
            }
        
        # Parse unified diff format
        analysis = {
            'success': True,
            'patch_file': patch_file,
            'files_changed': [],
            'changes': [],
            'lines_added': 0,
            'lines_removed': 0,
            'lines_changed': 0,
            'change_type': 'unknown',
            'impact': 'unknown'
        }
        
        # Parse diff headers and hunks
        current_file = None
        current_change = None
        
        for line in patch_content.split('\n'):
            # File header
            if line.startswith('---'):
                current_file = line.split()[1] if len(line.split()) > 1 else None
            elif line.startswith('+++'):
                if current_file and current_file not in analysis['files_changed']:
                    analysis['files_changed'].append(current_file)
            
            # Hunk header (@@ -line,count +line,count @@)
            elif line.startswith('@@'):
                if current_change:
                    analysis['changes'].append(current_change)
                
                # Parse line numbers
                match = re.search(r'@@ -(\d+),?\d* \+(\d+),?\d* @@', line)
                if match:
                    old_line = int(match.group(1))
                    new_line = int(match.group(2))
                    
                    current_change = {
                        'file': current_file,
                        'line_number': new_line,
                        'old_code': [],
                        'new_code': [],
                        'context_before': [],
                        'context_after': []
                    }
            
            # Change lines
            elif current_change:
                if line.startswith('-') and not line.startswith('---'):
                    current_change['old_code'].append(line[1:])
                    analysis['lines_removed'] += 1
                elif line.startswith('+') and not line.startswith('+++'):
                    current_change['new_code'].append(line[1:])
                    analysis['lines_added'] += 1
                elif line.startswith(' '):
                    # Context line
                    if not current_change['old_code'] and not current_change['new_code']:
                        current_change['context_before'].append(line[1:])
                    else:
                        current_change['context_after'].append(line[1:])
        
        # Add last change
        if current_change:
            analysis['changes'].append(current_change)
        
        # Determine change type
        if analysis['lines_added'] > 0 and analysis['lines_removed'] == 0:
            analysis['change_type'] = 'addition'
        elif analysis['lines_removed'] > 0 and analysis['lines_added'] == 0:
            analysis['change_type'] = 'deletion'
        else:
            analysis['change_type'] = 'modification'
        
        # Estimate impact
        total_lines = analysis['lines_added'] + analysis['lines_removed']
        if total_lines <= 5:
            analysis['impact'] = 'low'
        elif total_lines <= 20:
            analysis['impact'] = 'medium'
        else:
            analysis['impact'] = 'high'
        
        analysis['lines_changed'] = total_lines
        
        return analysis
    
    def correlate_patch_to_error(
        self,
        error_location: str,
        error_message: str,
        days_back: int = 7
    ) -> List[Tuple[Dict, float]]:
        """
        Match patches to error with confidence scores.
        
        Args:
            error_location: File:line where error occurred (e.g., 'src/main.py:120')
            error_message: The error message
            days_back: How far back to search
        
        Returns:
            List of (patch, confidence) tuples sorted by confidence
        """
        # Parse error location
        if ':' in error_location:
            error_file, error_line_str = error_location.rsplit(':', 1)
            try:
                error_line = int(error_line_str)
            except ValueError:
                error_line = 0
        else:
            error_file = error_location
            error_line = 0
        
        # Get recent patches
        patches = self.list_patch_files(days_back=days_back)
        
        # Calculate confidence for each patch
        correlations = []
        for patch in patches:
            confidence = self._calculate_patch_confidence(
                patch,
                error_file,
                error_line,
                error_message
            )
            
            if confidence > 0.3:  # Threshold for relevance
                reasons = self._explain_correlation(patch, error_file, error_line, error_message)
                correlations.append((patch, confidence, reasons))
        
        # Sort by confidence
        correlations.sort(key=lambda x: x[1], reverse=True)
        
        return correlations
    
    def _calculate_patch_confidence(
        self,
        patch: Dict,
        error_file: str,
        error_line: int,
        error_message: str
    ) -> float:
        """Calculate confidence that patch is related to error"""
        confidence = 0.0
        
        # Exact file match
        if patch['file_modified'] in error_file or error_file in patch['file_modified']:
            confidence += 0.50
        # Same directory
        elif Path(patch['file_modified']).parent == Path(error_file).parent:
            confidence += 0.30
        # Related module (same top-level package)
        elif patch['file_modified'].split('/')[0] == error_file.split('/')[0]:
            confidence += 0.10
        
        # Line proximity
        if error_line > 0:
            line_diff = abs(patch['line_modified'] - error_line)
            if line_diff == 0:
                confidence += 0.30
            elif line_diff <= 10:
                confidence += 0.20
            elif line_diff <= 50:
                confidence += 0.10
        
        # Recency
        age_hours = patch['age_hours']
        if age_hours < 24:
            confidence += 0.20
        elif age_hours < 168:  # 7 days
            confidence += 0.10
        elif age_hours < 720:  # 30 days
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def _explain_correlation(
        self,
        patch: Dict,
        error_file: str,
        error_line: int,
        error_message: str
    ) -> List[str]:
        """Explain why patch is correlated with error"""
        reasons = []
        
        # File match
        if patch['file_modified'] in error_file:
            reasons.append("Exact file match")
        elif Path(patch['file_modified']).parent == Path(error_file).parent:
            reasons.append("Same directory")
        
        # Line match
        if error_line > 0:
            line_diff = abs(patch['line_modified'] - error_line)
            if line_diff == 0:
                reasons.append("Exact line match")
            elif line_diff <= 10:
                reasons.append(f"Within 10 lines (diff: {line_diff})")
        
        # Recency
        age_hours = patch['age_hours']
        if age_hours < 24:
            reasons.append(f"Recent change ({age_hours:.1f} hours ago)")
        elif age_hours < 168:
            reasons.append(f"Changed this week ({age_hours/24:.1f} days ago)")
        
        return reasons
    
    def suggest_rollback(
        self,
        error_info: Dict,
        patches: List[Dict]
    ) -> List[Dict]:
        """
        Recommend patches to revert with reasoning.
        
        Args:
            error_info: Dict with error details
            patches: List of patch dicts
        
        Returns:
            List of rollback recommendations
        """
        recommendations = []
        
        for patch in patches:
            # Analyze patch to understand impact
            analysis = self.analyze_patch_file(patch['path'])
            
            if not analysis.get('success'):
                continue
            
            # Calculate rollback confidence
            confidence = 0.5  # Base confidence
            
            # Higher confidence for recent high-impact changes
            if patch['age_hours'] < 24 and analysis['impact'] == 'high':
                confidence += 0.3
            
            # Higher confidence if change type is deletion
            if analysis['change_type'] == 'deletion':
                confidence += 0.2
            
            recommendation = {
                'patch': patch,
                'confidence': min(confidence, 1.0),
                'reason': f"Recent {analysis['impact']}-impact {analysis['change_type']}",
                'impact': analysis['impact'],
                'files_affected': analysis['files_changed'],
                'lines_changed': analysis['lines_changed']
            }
            
            recommendations.append(recommendation)
        
        # Sort by confidence
        recommendations.sort(key=lambda r: r['confidence'], reverse=True)
        
        return recommendations