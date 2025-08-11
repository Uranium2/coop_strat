#!/bin/bash

echo "Starting Co-op Survival RTS Client..."
cd "$(dirname "$0")"
export PYTHONPATH=$PYTHONPATH:$(pwd)
python3 -m client.main