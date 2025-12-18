#!/usr/bin/env python3
"""
Allows running the core package as a module: python -m core

This provides an alternative entry point to main.py
Usage:
    python -m core --interactive
    python -m core --help
"""

import sys
import os

# Ensure parent directory is in path for absolute imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import and run main from root main.py
from main_old import main

if __name__ == "__main__":
    main()
