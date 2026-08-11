#!/usr/bin/env python3
import sys
import os
import subprocess

def main():
    args = sys.argv[1:]
    
    # GNU specific flags we block to simulate BSD tar warning
    blocked_flags = ["--overwrite", "--exclude-vcs", "--delay-directory-restore"]
    
    found_blocked = [f for f in blocked_flags if f in args]
    
    if found_blocked:
        flag = found_blocked[0]
        print(f"tar: Option {flag} is not supported", file=sys.stderr)
        print("Usage:", file=sys.stderr)
        print("  List:    tar -tf <archive-filename>", file=sys.stderr)
        print("  Extract: tar -xf <archive-filename>", file=sys.stderr)
        print("  Create:  tar -cf <archive-filename> [filenames...]", file=sys.stderr)
        sys.exit(1)
        
    # Forward to the real system tar
    real_tar = "/bin/tar"
    if not os.path.exists(real_tar):
        real_tar = "/usr/bin/tar"
        
    try:
        completed = subprocess.run([real_tar] + args)
        sys.exit(completed.returncode)
    except Exception as e:
        print(f"tar mock error: failed to execute real tar: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
