# Simulate what the code does
context_list = [
    ">>> 51: def some_function():",
    "    52:     pass",
    "    53:     execute_pattern = pattern",
    "    54:     return pattern"
]

# Join with newline (what line 419 does)
context = '\n'.join(context_list)

# Create description (what line 431 does)
error_type = "SyntaxError"
error_line = 53
error_message = "unmatched ']'"
description = f"{error_type} at line {error_line}: {error_message}\n\nContext:\n{context}"

print("Description output:")
print(description)
print("\n" + "="*60)
print("This should show the context with proper line breaks!")
