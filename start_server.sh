#!/bin/bash

echo "Starting Co-op Survival RTS Server..."
cd "$(dirname "$0")"
export PYTHONPATH=$PYTHONPATH:$(pwd)
python3 -m server.main