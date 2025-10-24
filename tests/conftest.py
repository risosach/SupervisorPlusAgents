"""
Pytest configuration and shared fixtures.
"""
import pytest
import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def test_config_path():
    """Fixture providing path to test configuration file."""
    return 'tests/fixtures/test_config.json'


@pytest.fixture
def custom_config_path():
    """Fixture providing path to custom configuration file."""
    return 'tests/fixtures/custom_prompt_config.json'


@pytest.fixture
def disabled_doc_config_path():
    """Fixture providing path to config with disabled doc tool."""
    return 'tests/fixtures/disabled_doc_tool_config.json'
