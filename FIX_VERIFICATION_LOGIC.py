#!/usr/bin/env python3
"""
Fix for the verification logic bug that causes infinite loops
when AI wraps code in try/except blocks.
"""

def fixed_verification_logic(original_code: str, new_code: str, written_content: str) -> tuple[bool, list[str]]:
    """
    Fixed verification logic that handles code wrapping correctly.
    
    Returns:
        (verification_passed, verification_errors)
    """
    verification_errors = []
    
    # Normalize whitespace for comparison
    original_normalized = ' '.join(original_code.split())
    new_normalized = ' '.join(new_code.split())
    written_normalized = ' '.join(written_content.split())
    
    # Check if this is a wrapping operation (code is being wrapped, not replaced)
    is_wrapping = (
        original_normalized in new_normalized and  # Original is inside new code
        len(new_normalized) > len(original_normalized) * 1.3  # New code is significantly larger (30%+)
    )
    
    if is_wrapping:
        # For wrapping operations (try/except, if/else, etc.)
        # Just verify the new wrapped code was added
        if new_normalized not in written_normalized:
            verification_errors.append(
                "Wrapped code not found in file - wrapping operation may have failed"
            )
    else:
        # For replacement operations
        # Verify original was removed AND new was added
        if new_normalized not in written_normalized:
            verification_errors.append(
                "New code not found in file - replacement may have failed"
            )
        
        # Only check if original was completely replaced (not just wrapped)
        if original_normalized not in new_normalized:
            if original_normalized in written_normalized:
                verification_errors.append(
                    "Original code still present - replacement incomplete"
                )
    
    verification_passed = len(verification_errors) == 0
    return verification_passed, verification_errors


# Example usage demonstrating the fix
if __name__ == "__main__":
    # Test Case 1: Wrapping in try/except (should PASS)
    original = "curses.cbreak()"
    new = """try:
    curses.cbreak()
except curses.error:
    pass"""
    written = """try:
    curses.cbreak()
except curses.error:
    pass"""
    
    passed, errors = fixed_verification_logic(original, new, written)
    print(f"Test 1 (Wrapping): {'PASS' if passed else 'FAIL'}")
    if errors:
        print(f"  Errors: {errors}")
    
    # Test Case 2: Complete replacement (should PASS)
    original = "curses.cbreak()"
    new = "curses.nocbreak()"
    written = "curses.nocbreak()"
    
    passed, errors = fixed_verification_logic(original, new, written)
    print(f"Test 2 (Replacement): {'PASS' if passed else 'FAIL'}")
    if errors:
        print(f"  Errors: {errors}")
    
    # Test Case 3: Failed replacement (should FAIL)
    original = "curses.cbreak()"
    new = "curses.nocbreak()"
    written = "curses.cbreak()"  # Original still there!
    
    passed, errors = fixed_verification_logic(original, new, written)
    print(f"Test 3 (Failed replacement): {'PASS' if passed else 'FAIL'}")
    if errors:
        print(f"  Errors: {errors}")