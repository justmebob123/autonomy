"""
File Conflict Resolver

Handles detection and resolution of conflicting/duplicate files
through multi-step AI collaboration.
"""

from pathlib import Path
from typing import List, Dict, Optional
import ast
import shutil
from datetime import datetime


class FileConflictResolver:
    """Resolves file conflicts through AI collaboration"""
    
    def __init__(self, project_dir: Path, logger, file_discovery):
        self.project_dir = Path(project_dir)
        self.logger = logger
        self.file_discovery = file_discovery
    
    def find_conflicts(self) -> List[Dict]:
        """Find all file conflicts in the project"""
        return self.file_discovery.find_conflicting_files()
    
    def build_conflict_review_message(self, conflict_group: Dict) -> str:
        """Build message for AI to review a conflict group"""
        parts = []
        
        parts.append(f"# File Conflict Review: {conflict_group['pattern']}\n")
        parts.append(f"**Severity:** {conflict_group['severity']}")
        parts.append(f"**Files involved:** {conflict_group['count']}\n")
        
        # Load and analyze each file
        for i, filepath in enumerate(conflict_group['files'], 1):
            parts.append(f"\n## File {i}: `{filepath}`\n")
            
            file_path = self.project_dir / filepath
            if not file_path.exists():
                parts.append("*File not found*")
                continue
            
            # Get file info
            try:
                content = file_path.read_text()
                size = len(content)
                lines = content.split('\n')
                
                parts.append(f"- **Size:** {size} bytes ({len(lines)} lines)")
                
                # Extract structure
                try:
                    tree = ast.parse(content)
                    
                    # Get docstring
                    docstring = ast.get_docstring(tree)
                    if docstring:
                        first_line = docstring.split('\n')[0]
                        parts.append(f"- **Purpose:** {first_line}")
                    
                    # Get classes
                    classes = [node.name for node in ast.walk(tree) 
                              if isinstance(node, ast.ClassDef)]
                    if classes:
                        parts.append(f"- **Classes:** {', '.join(classes)}")
                    
                    # Get functions
                    functions = [node.name for node in ast.walk(tree) 
                                if isinstance(node, ast.FunctionDef) 
                                and not node.name.startswith('_')]
                    if functions:
                        funcs = ', '.join(functions[:10])
                        if len(functions) > 10:
                            funcs += f" ... and {len(functions) - 10} more"
                        parts.append(f"- **Public Functions:** {funcs}")
                    
                except SyntaxError:
                    parts.append("- **Error:** File has syntax errors")
                
                # Show preview
                parts.append("\n**Content Preview:**")
                parts.append("```python")
                parts.append('\n'.join(lines[:30]))
                if len(lines) > 30:
                    parts.append("... (truncated)")
                parts.append("```")
            except Exception as e:
                parts.append(f"*Error reading file: {e}*")
        
        # Add decision prompt
        parts.append("\n## 🎯 Resolution Required\n")
        parts.append("Please analyze these files and provide a resolution plan:")
        parts.append("\n1. **Which file should be the PRIMARY implementation?**")
        parts.append("   - Consider: completeness, code quality, location")
        parts.append("\n2. **What functionality should be MERGED?**")
        parts.append("   - List specific classes/functions to preserve")
        parts.append("   - Identify any advanced features that must not be lost")
        parts.append("\n3. **Which files should be ARCHIVED?**")
        parts.append("   - Files will be moved to `archive/deprecated/` (not deleted)")
        parts.append("\n4. **Are there DIFFERENT PURPOSES?**")
        parts.append("   - If files serve different purposes, explain and suggest renaming")
        parts.append("\nUse the `resolve_file_conflict` tool to provide your decision.")
        
        return "\n".join(parts)
    
    def execute_resolution(self, resolution: Dict) -> Dict:
        """Execute the conflict resolution plan"""
        keep_file = resolution.get('keep_file')
        merge_from = resolution.get('merge_from', [])
        archive_files = resolution.get('archive_files', [])
        merge_plan = resolution.get('merge_plan', '')
        
        results = {
            'success': True,
            'actions': [],
            'errors': []
        }
        
        self.logger.info(f"Executing conflict resolution:")
        self.logger.info(f"  Keep: {keep_file}")
        self.logger.info(f"  Merge from: {', '.join(merge_from)}")
        self.logger.info(f"  Archive: {', '.join(archive_files)}")
        
        # Create archive directory
        archive_dir = self.project_dir / "archive" / "deprecated"
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Archive files
        for filepath in archive_files:
            try:
                source = self.project_dir / filepath
                if source.exists():
                    pass
                    # Preserve directory structure in archive
                    rel_path = Path(filepath)
                    dest = archive_dir / rel_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Add timestamp to archived file
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    dest_with_timestamp = dest.parent / f"{dest.stem}_{timestamp}{dest.suffix}"
                    
                    shutil.move(str(source), str(dest_with_timestamp))
                    results['actions'].append(f"Archived: {filepath} -> {dest_with_timestamp}")
            except Exception as e:
                results['errors'].append(f"Failed to archive {filepath}: {e}")
                results['success'] = False
                self.logger.error(f"  ✗ Failed to archive {filepath}: {e}")
        
        # Note: Actual merging would be done by AI through file modification tools
        results['actions'].append(f"Merge plan documented: {merge_plan}")
        
        return results
    
    def compare_files(self, filepaths: List[str]) -> Dict:
        """Compare multiple files for duplication analysis"""
        comparison = {
            'files': [],
            'similarities': [],
            'recommendations': []
        }
        
        for filepath in filepaths:
            file_path = self.project_dir / filepath
            if not file_path.exists():
                continue
            
            try:
                content = file_path.read_text()
                
                # Extract structure
                tree = ast.parse(content)
                classes = [node.name for node in ast.walk(tree) 
                          if isinstance(node, ast.ClassDef)]
                functions = [node.name for node in ast.walk(tree) 
                            if isinstance(node, ast.FunctionDef)]
                
                comparison['files'].append({
                    'path': filepath,
                    'classes': classes,
                    'functions': functions,
                    'size': len(content),
                    'lines': len(content.split('\n'))
                })
            except Exception as e:
                self.logger.warning(f"Could not parse {filepath}: {e}")
        
        # Analyze similarities
        if len(comparison['files']) >= 2:
            for i in range(len(comparison['files'])):
                for j in range(i + 1, len(comparison['files'])):
                    file1 = comparison['files'][i]
                    file2 = comparison['files'][j]
                    
                    classes1 = set(file1['classes'])
                    classes2 = set(file2['classes'])
                    common_classes = classes1 & classes2
                    
                    funcs1 = set(file1['functions'])
                    funcs2 = set(file2['functions'])
                    common_funcs = funcs1 & funcs2
                    
                    if common_classes or common_funcs:
                        similarity = {
                            'file1': file1['path'],
                            'file2': file2['path'],
                            'common_classes': list(common_classes),
                            'common_functions': list(common_funcs),
                            'overlap_score': (len(common_classes) + len(common_funcs)) / 
                                           max(len(classes1) + len(funcs1), len(classes2) + len(funcs2), 1)
                        }
                        comparison['similarities'].append(similarity)
                        
                        # Add recommendation if high overlap
                        if similarity['overlap_score'] > 0.5:
                            comparison['recommendations'].append(
                                f"Consider merging {file1['path']} and {file2['path']} "
                                f"(overlap: {similarity['overlap_score']:.0%})"
                            )
        
        return comparison