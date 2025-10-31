#!/bin/bash
# auto_trust.sh - automatically trust all notebooks in /notebooks

echo "Auto-trusting all notebooks..."
find /notebooks -name '*.ipynb' -exec jupyter trust {} \;
echo "Done!"