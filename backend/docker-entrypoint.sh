#!/bin/bash
set -e

echo "🚀 Catalyst Backend - Runtime Setup"

# Install huggingface-hub 1.0.1 at runtime (avoids build-time dependency conflicts)
echo "📦 Installing huggingface-hub 1.0.1..."
pip install --no-cache-dir huggingface-hub==1.0.1 > /dev/null 2>&1

# Patch transformers dependency check to accept huggingface-hub 1.0.1
echo "🔧 Patching transformers for huggingface-hub 1.0.1 compatibility..."
python3 << 'PYTHON_SCRIPT'
import os

# Find transformers installation
transformers_path = None
for path in ['/usr/local/lib/python3.11/site-packages', '/root/.venv/lib/python3.11/site-packages']:
    if os.path.exists(f'{path}/transformers'):
        transformers_path = f'{path}/transformers'
        break

if transformers_path:
    versions_file = f'{transformers_path}/dependency_versions_table.py'
    
    if os.path.exists(versions_file):
        with open(versions_file, 'r') as f:
            content = f.read()
        
        # Patch the huggingface-hub version constraint
        content = content.replace(
            '"huggingface-hub": "huggingface-hub>=0.34.0,<1.0"',
            '"huggingface-hub": "huggingface-hub>=0.34.0"'
        )
        
        with open(versions_file, 'w') as f:
            f.write(content)
        
        print("✅ Transformers patched successfully")
    else:
        print("⚠️  dependency_versions_table.py not found")
else:
    print("⚠️  Transformers installation not found")
PYTHON_SCRIPT

echo "✅ Runtime setup complete"
echo ""

# Execute the main command
exec "$@"
