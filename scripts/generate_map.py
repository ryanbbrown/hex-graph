#!/usr/bin/env python3
"""
Entry point script for generating hexagon territory maps
"""

import sys
import os

# Add the parent directory to the Python path to import hexmap
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hexmap.cli import main

if __name__ == "__main__":
    main()