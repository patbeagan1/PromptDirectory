#!/usr/bin/env zsh

# This script is kept for backward compatibility
# It now calls the new promptdir module using the Python -m option

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Execute the promptdir module with all arguments passed to this script
python3 -m pd.cli "$@"