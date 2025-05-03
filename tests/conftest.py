import sys
import os
import logging
import pytest

# Insert the project’s src/ directory at the front of sys.path
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src  = os.path.join(root, 'src')
if src not in sys.path:
    sys.path.insert(0, src)

# Silence noisy loggers during tests
@pytest.fixture(autouse=True)
def silence_logs():
    # You can silence specific loggers
    logging.getLogger('app').setLevel(logging.CRITICAL)
    logging.getLogger('repositories').setLevel(logging.CRITICAL)
    logging.getLogger('security').setLevel(logging.CRITICAL)
    # Optionally: silence everything globally
    # logging.getLogger().setLevel(logging.CRITICAL)
