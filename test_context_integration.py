#!/usr/bin/env python3
"""Test context-aware decoder integration"""

import ast
from pipeline.html_entity_decoder import HTMLEntityDecoder

# Create proper test strings with actual backslash-quote sequences
test2 = 'text = "He said ' + chr(92) + '"Hello' + chr(92) + '""' + '\nprint(text)\n'
test3 = 'html = "<div>&quot;text&quot;</div>"\nprint(html)\n'

print("Test 2 content:", repr(test2))
try:
    ast.parse(test2)
    print("Test 2: Valid Python ✅")
except SyntaxError as e:
    print(f"Test 2: Invalid Python ❌ - {e}")

print("\nTest 3 content:", repr(test3))
try:
    ast.parse(test3)
    print("Test 3: Valid Python ✅")
except SyntaxError as e:
    print(f"Test 3: Invalid Python ❌ - {e}")

# Now test with the decoder
decoder = HTMLEntityDecoder()

print("\n" + "=" * 60)
print("Testing decoder on valid Python with escapes:")
decoded2, modified2 = decoder.decode_html_entities(test2, "test.py")
print(f"Modified: {modified2}")
print("Still valid: ", end="")
try:
    ast.parse(decoded2)
    print("✅")
except:
    print("❌")

print("\nTesting decoder on HTML entities in strings:")
decoded3, modified3 = decoder.decode_html_entities(test3, "test.py")
print(f"Modified: {modified3}")
entity_check = "&quot;" in decoded3
print("Preserved HTML entity:", entity_check)