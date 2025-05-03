import sys
import os
import logging
import pytest

# Insert the project's src/ directory at the front of sys.path
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src = os.path.join(root, 'src')
if src not in sys.path:
    sys.path.insert(0, src)

# Silence noisy loggers before tests run
def pytest_configure(config):
    """Silence loggers before any tests run."""
    # Silence specific loggers
    logging.getLogger('app').setLevel(logging.CRITICAL)
    logging.getLogger('repositories').setLevel(logging.CRITICAL)
    logging.getLogger('security').setLevel(logging.CRITICAL)
    
    # Disable propagation to root logger to ensure messages don't show up
    logging.getLogger('app').propagate = False
    logging.getLogger('repositories').propagate = False
    logging.getLogger('security').propagate = False
    
    # Optional: If you want to silence everything
    # logging.getLogger().setLevel(logging.CRITICAL)

# Also keep the fixture for additional control during tests
@pytest.fixture(autouse=True)
def silence_logs():
    """Fixture to silence logs during each test."""
    # This provides a way to manage logging during tests if needed
    previous_levels = {
        'app': logging.getLogger('app').level,
        'repositories': logging.getLogger('repositories').level,
        'security': logging.getLogger('security').level,
    }
    
    # Set to CRITICAL during tests
    logging.getLogger('app').setLevel(logging.CRITICAL)
    logging.getLogger('repositories').setLevel(logging.CRITICAL)
    logging.getLogger('security').setLevel(logging.CRITICAL)
    
    yield
    
    # Restore previous levels after test
    logging.getLogger('app').setLevel(previous_levels['app'])
    logging.getLogger('repositories').setLevel(previous_levels['repositories'])
    logging.getLogger('security').setLevel(previous_levels['security'])
