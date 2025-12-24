# Read the file
with open('run.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Show the problematic area
lines = content.split('\n')
print("Lines 428-435 before fix:")
for i in range(427, min(435, len(lines))):
    print(f"{i+1}: {lines[i]}")

# Replace the broken f-string section
# The broken section spans lines 431-434
old_section = """                        'description': f"{error['type']} at line {error_line}: {error['message']}

Context:
{context}"
                    }"""

new_section = """                        'description': f"{error['type']} at line {error_line}: {error['message']}\\n\\nContext:\\n{context}"
                    }"""

content = content.replace(old_section, new_section)

# Write back
with open('run.py', 'w', encoding='utf-8') as f:
    f.write(content)

# Verify
lines = content.split('\n')
print("\nLines 428-435 after fix:")
for i in range(427, min(435, len(lines))):
    print(f"{i+1}: {lines[i]}")

print("\n✓ Fixed!")
