#!/bin/bash

echo "=========================================="
echo "Starting Co-op Survival RTS Server"
echo "=========================================="
cd "$(dirname "$0")"
export PYTHONPATH=$PYTHONPATH:$(pwd)

echo "python3 path: $PYTHONPATH"
echo "Current directory: $(pwd)"
echo ""

# Clear previous logs
rm -f server.log

echo "Starting server..."
python3 -m server.main 2>&1 | tee server_output.log