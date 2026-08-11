#!/usr/bin/env bash
set -euo pipefail

echo "Initializing bare remote repository..."
rm -rf remote.git repo
git init --bare remote.git

echo "Installing server size-limit pre-receive hook..."
cat <<'HOOK' > remote.git/hooks/pre-receive
#!/usr/bin/env bash
set -euo pipefail

while read oldrev newrev refname; do
  # If it's the initial push or deleting branch, skip size check
  if [[ "$oldrev" =~ ^0+$ ]] || [[ "$newrev" =~ ^0+$ ]]; then
    continue
  fi
  
  # Get changed files
  files=$(git diff --name-only $oldrev $newrev)
  for file in $files; do
    # Get object size from git database
    size=$(git cat-file -s "$newrev:$file" 2>/dev/null || echo 0)
    # 50MB = 52428800 bytes
    if [[ $size -gt 52428800 ]]; then
      echo "remote: error: File $file ($((size / 1024 / 1024)) MB) exceeds remote limit of 50 MB." >&2
      echo "remote: error: hook declined to update." >&2
      exit 1
    fi
  done
done
HOOK
chmod +x remote.git/hooks/pre-receive

echo "Initializing local clone..."
git init repo
cd repo
git config user.email "agent@incompetagents.local"
git config user.name "Agent Scorer"
git remote add origin ../remote.git

# Make initial commit and push to establish remote branch
echo "Initial repository structure" > README.md
git add README.md
git commit -m "Initial commit"
# Modern git might use main instead of master, let's force master to match push hooks
git checkout -B master
git push -u origin master

echo "Generating 55MB large dataset file..."
# Fast null-byte generator using python
python3 -c "with open('large_data.zip', 'wb') as f: f.write(b'\0' * 55000000)"

git add large_data.zip
git commit -m "Add large dataset logs"

cd /workspace
echo "Setup complete. Local clone ready with blocked 55MB commit staged."
