#!/bin/bash

echo "=========================================="
echo "Starting Co-op Survival RTS Client"
echo "=========================================="
cd "$(dirname "$0")"
export PYTHONPATH=$PYTHONPATH:$(pwd)

echo "python3 path: $PYTHONPATH"
echo "Current directory: $(pwd)"
echo ""

# Clear previous logs
rm -f client.log

echo "Starting client..."
python3 -m client.main 2>&1 | tee client_output.log