"""
Patch-based file modification system.

This module provides a robust way to modify files using unified diff patches,
eliminating escape sequence issues and handling any character combinations.

Patches are tracked with change numbers and stored in .patches/ directory.
"""

import difflib
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime
import logging


class PatchManager:
    """Manages patch generation, application, and tracking."""
    
    def __init__(self, patches_dir: Path = None):
        """
        Initialize patch manager.
        
        Args:
            patches_dir: Directory to store patches (default: .patches/)
        """
        self.patches_dir = patches_dir or Path('.patches')
        self.patches_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Track change numbers
        self.change_counter_file = self.patches_dir / '.change_counter'
        self._init_change_counter()
    
    def _init_change_counter(self):
        """Initialize or read the change counter."""
        if not self.change_counter_file.exists():
            self.change_counter_file.write_text('0')
    
    def _get_next_change_number(self) -> int:
        """Get the next change number and increment counter."""
        current = int(self.change_counter_file.read_text().strip())
        next_num = current + 1
        self.change_counter_file.write_text(str(next_num))
        return next_num
    
    def generate_line_patch(
        self,
        filepath: Path,
        line_num: int,
        old_line: str,
        new_line: str
    ) -> Tuple[str, Path]:
        """
        Generate a unified diff patch for a single line change.
        
        Args:
            filepath: Path to the file being modified
            line_num: Line number (1-indexed)
            old_line: Original line content
            new_line: New line content
        
        Returns:
            Tuple of (patch_content, patch_file_path)
        """
        # Read the entire file
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Ensure line has newline
        if not old_line.endswith('\n'):
            old_line += '\n'
        if not new_line.endswith('\n'):
            new_line += '\n'
        
        # Create modified version
        modified_lines = lines.copy()
        modified_lines[line_num - 1] = new_line
        
        # Generate unified diff
        # Note: Don't use lineterm='' as it creates malformed patches
        diff = difflib.unified_diff(
            lines,
            modified_lines,
            fromfile=str(filepath),
            tofile=str(filepath)
        )
        
        patch_content = ''.join(diff)
        
        # Save patch with change number
        change_num = self._get_next_change_number()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = filepath.name.replace('.py', '')
        patch_filename = f"change_{change_num:04d}_{timestamp}_{filename}_line{line_num}.patch"
        patch_path = self.patches_dir / patch_filename
        
        patch_path.write_text(patch_content)
        
        self.logger.info(f"Generated patch: {patch_filename}")
        
        return patch_content, patch_path
    
    def apply_patch(
        self,
        filepath: Path,
        patch_content: str = None,
        patch_file: Path = None,
        dry_run: bool = False
    ) -> Tuple[bool, str]:
        """
        Apply a patch to a file.
        
        Args:
            filepath: Path to the file to patch
            patch_content: Patch content as string (if not using patch_file)
            patch_file: Path to patch file (if not using patch_content)
            dry_run: If True, only test if patch would apply
        
        Returns:
            Tuple of (success, message)
        """
        if not patch_content and not patch_file:
            return False, "Either patch_content or patch_file must be provided"
        
        # Create temporary patch file if content provided
        if patch_content:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
                f.write(patch_content)
                temp_patch = Path(f.name)
            patch_to_use = temp_patch
        else:
            patch_to_use = patch_file
        
        try:
            # Build patch command
            cmd = ['patch']
            if dry_run:
                cmd.append('--dry-run')
            cmd.extend([
                '--unified',
                '--forward',  # Skip patches that appear to be already applied
                '--reject-file=-',  # Don't create .rej files
                str(filepath),
                str(patch_to_use)
            ])
            
            # Execute patch command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=filepath.parent
            )
            
            if result.returncode == 0:
                msg = f"Patch applied successfully to {filepath.name}"
                self.logger.info(msg)
                return True, msg
            else:
                msg = f"Patch failed: {result.stderr}"
                self.logger.error(msg)
                return False, msg
        
        except Exception as e:
            msg = f"Error applying patch: {e}"
            self.logger.error(msg)
            return False, msg
        
        finally:
            # Clean up temporary file
            if patch_content and temp_patch.exists():
                temp_patch.unlink()
    
    def apply_line_change(
        self,
        filepath: Path,
        line_num: int,
        old_line: str,
        new_line: str,
        verify: bool = True
    ) -> Tuple[bool, str]:
        """
        High-level function to change a single line using patches.
        
        Args:
            filepath: Path to the file
            line_num: Line number (1-indexed)
            old_line: Original line content
            new_line: New line content
            verify: If True, verify the change was applied correctly
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Generate patch
            patch_content, patch_file = self.generate_line_patch(
                filepath, line_num, old_line, new_line
            )
            
            # Test if patch would apply
            success, msg = self.apply_patch(filepath, patch_content=patch_content, dry_run=True)
            if not success:
                return False, f"Patch would not apply: {msg}"
            
            # Apply patch
            success, msg = self.apply_patch(filepath, patch_content=patch_content)
            if not success:
                return False, msg
            
            # Verify if requested
            if verify:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                actual_line = lines[line_num - 1]
                expected_line = new_line if new_line.endswith('\n') else new_line + '\n'
                
                if actual_line != expected_line:
                    return False, f"Verification failed: line {line_num} does not match expected content"
            
            return True, f"Successfully changed line {line_num} in {filepath.name}"
        
        except Exception as e:
            return False, f"Error: {e}"
    
    def list_patches(self, limit: int = 999999) -> List[Path]:  # UNLIMITED patches
        """
        List recent patches.
        
        Args:
            limit: Maximum number of patches to return
        
        Returns:
            List of patch file paths, sorted by change number (newest first)
        """
        patches = sorted(
            self.patches_dir.glob('change_*.patch'),
            key=lambda p: int(p.name.split('_')[1]),
            reverse=True
        )
        return patches[:limit]
    
    def get_patch_info(self, patch_file: Path) -> dict:
        """
        Extract information from a patch filename.
        
        Args:
            patch_file: Path to patch file
        
        Returns:
            Dictionary with patch information
        """
        name = patch_file.stem
        parts = name.split('_')
        
        return {
            'change_number': int(parts[1]),
            'timestamp': f"{parts[2]}_{parts[3]}",
            'filename': '_'.join(parts[4:-1]) if len(parts) > 5 else parts[4],
            'line': parts[-1].replace('line', ''),
            'patch_file': patch_file
        }


# Convenience function for simple use cases
def apply_line_fix(
    filepath: Path,
    line_num: int,
    old_line: str,
    new_line: str
) -> Tuple[bool, str]:
    """
    Convenience function to apply a single line fix using patches.
    
    Args:
        filepath: Path to the file
        line_num: Line number (1-indexed)
        old_line: Original line content
        new_line: New line content
    
    Returns:
        Tuple of (success, message)
    """
    manager = PatchManager()
    return manager.apply_line_change(filepath, line_num, old_line, new_line)