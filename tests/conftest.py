# tests/conftest.py
import sys
import os

# Insert the project’s src/ directory at the front of sys.path
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src  = os.path.join(root, 'src')
if src not in sys.path:
    sys.path.insert(0, src)
