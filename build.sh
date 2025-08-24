#!/bin/bash
cd "$(dirname "${BASH_SOURCE[0]}")"
uv build --out-dir dist

# Create standalone zipapp
TEMP_DIR=$(mktemp -d)
uv pip install --target "$TEMP_DIR" dist/ok-*.whl
echo "from client.cli.ok import main; main()" > "$TEMP_DIR/__main__.py"
uv run python -m zipapp --output dist/ok --python "/usr/bin/env python3" "$TEMP_DIR"
rm -rf "$TEMP_DIR"
