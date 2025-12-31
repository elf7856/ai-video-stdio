#!/usr/bin/env python3
"""
Runs the project's test suite using pytest.
This script discovers and runs all tests within the 'tests/' directory.
"""

import sys
import pytest
import os

if __name__ == "__main__":
    # Add the project root to the Python path to ensure imports work correctly
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)

    print("🚀 Running all tests in the 'tests/' directory...")
    
    # Run pytest on the 'tests' directory with verbose output
    exit_code = pytest.main(["-v", "tests/"])
    
    sys.exit(exit_code)
