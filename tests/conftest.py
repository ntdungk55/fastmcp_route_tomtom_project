"""Pytest configuration and fixtures."""

import pytest
import os
from tests.fixtures.mock_database import test_db_manager


@pytest.fixture(scope="function")
def mock_database():
    """Fixture for mock database."""
    # Setup test database
    test_db_manager.setup_test_database()
    
    yield test_db_manager
    
    # Teardown test database
    test_db_manager.teardown_test_database()


@pytest.fixture(scope="function")
def clean_database():
    """Fixture for clean database."""
    # Clear test data before each test
    test_db_manager.clear_test_data()
    
    yield test_db_manager


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment."""
    # Set test environment variables
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["DATABASE_PATH"] = ":memory:"
    
    yield
    
    # Cleanup environment
    os.environ.pop("LOG_LEVEL", None)
    os.environ.pop("DATABASE_PATH", None)
