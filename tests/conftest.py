#!/usr/bin/env python3
"""
Pytest configuration to ensure project root is on sys.path
so imports like `from app.sheets import ...` work when running
tests from the repository root.
"""
import os
import sys

# Add repo root to sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
