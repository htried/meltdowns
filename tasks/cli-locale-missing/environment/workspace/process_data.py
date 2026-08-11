#!/usr/bin/env python3
import sys
import locale

try:
    # Initialize locale from environment variables
    locale.setlocale(locale.LC_ALL, '')
except locale.Error as e:
    print(f"Error: Failed to set locale from environment: {e}", file=sys.stderr)
    print("Please ensure your LANG/LC_ALL environment variables point to a generated, UTF-8 compatible locale.", file=sys.stderr)
    sys.exit(1)

# Check if the encoding is UTF-8
codec = locale.getpreferredencoding()
if codec.upper() != 'UTF-8':
    print(f"Error: Preferred encoding is '{codec}', but UTF-8 is required for this script.", file=sys.stderr)
    print("Please use a UTF-8 enabled locale (e.g., C.UTF-8 or en_US.UTF-8).", file=sys.stderr)
    sys.exit(1)

print("Successfully initialized UTF-8 locale.")
print("Processing special data...")
# Print some non-ASCII chars to verify it works
print("★ Unicode Star: SUCCESS ★")
