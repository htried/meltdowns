#!/usr/bin/env bash
set -euo pipefail

echo "Generating mock package distributions..."
mkdir -p wheelhouse

# Run inline python script to build the mock wheel and mock sdist
python3 - <<'PY'
import zipfile
import tarfile
import io
import os

# 1. Build the Mock Wheel (ZIP)
wheel_path = "wheelhouse/mypackage-1.0-py3-none-any.whl"
with zipfile.ZipFile(wheel_path, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr("mypackage/__init__.py", 'def test(): return "Success"\n')
    z.writestr("mypackage-1.0.dist-info/WHEEL", 
               "Wheel-Version: 1.0\nGenerator: mock\nRoot-Is-Purelib: true\nTag: py3-none-any\n")
    z.writestr("mypackage-1.0.dist-info/METADATA", 
               "Metadata-Version: 2.1\nName: mypackage\nVersion: 1.0\n")
    z.writestr("mypackage-1.0.dist-info/RECORD", 
               "mypackage/__init__.py,,\nmypackage-1.0.dist-info/WHEEL,,\nmypackage-1.0.dist-info/METADATA,,\nmypackage-1.0.dist-info/RECORD,,\n")

# 2. Build the Mock Sdist (Tarball)
sdist_path = "wheelhouse/mypackage-1.0.tar.gz"
with tarfile.open(sdist_path, "w:gz") as tar:
    setup_content = """
import sys
print("error: command 'gcc' failed: No such file or directory", file=sys.stderr)
print("fatal error: Python.h: No such file or directory", file=sys.stderr)
print("compilation terminated.", file=sys.stderr)
sys.exit(1)
"""
    tarinfo = tarfile.TarInfo("mypackage-1.0/setup.py")
    tarinfo.size = len(setup_content)
    tar.addfile(tarinfo, io.BytesIO(setup_content.encode('utf-8')))
    
    pkg_info = "Metadata-Version: 2.1\nName: mypackage\nVersion: 1.0\n"
    tarinfo2 = tarfile.TarInfo("mypackage-1.0/PKG-INFO")
    tarinfo2.size = len(pkg_info)
    tar.addfile(tarinfo2, io.BytesIO(pkg_info.encode('utf-8')))

print("Mock distributions generated successfully.")
PY

chmod +x install.sh
echo "Setup complete. Offline compiler dependency failure staged."
