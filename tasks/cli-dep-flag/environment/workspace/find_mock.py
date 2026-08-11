#!/usr/bin/env python3
import sys
import os
import subprocess

def main():
    args = sys.argv[1:]
    
    # Intercept deprecated GNU find permission flags
    for i, arg in enumerate(args):
        if arg == "-perm" and i + 1 < len(args):
            val = args[i+1]
            if val.startswith("+"):
                print(f"find: invalid mode '{val}'", file=sys.stderr)
                print("Usage: find [-H] [-L] [-P] [-Olevel] [-D help] [path...] [expression]", file=sys.stderr)
                sys.exit(1)
                
    # Forward to real find
    real_find = "/usr/bin/find"
    if not os.path.exists(real_find):
        real_find = "/bin/find"
        
    try:
        completed = subprocess.run([real_find] + args)
        sys.exit(completed.returncode)
    except Exception as e:
        print(f"find mock error: failed to execute real find: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
