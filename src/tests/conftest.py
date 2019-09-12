# Fix: coverage tool doesn't run nested conftest files on start
def pytest_sessionstart():
    import tests.integration.conftest
    tests.integration.conftest.pytest_sessionstart()
