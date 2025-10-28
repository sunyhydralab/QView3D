#!/usr/bin/env python
"""
Test runner for QView3D
Run with: python run-tests.py
"""

import sys
import subprocess
import os

def run_tests():
    """Run the test suite with pytest."""
    print("=" * 60)
    print("QView3D Test Suite")
    print("=" * 60)

    # Check if pytest is installed
    try:
        import pytest
    except ImportError:
        print("pytest not installed. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest", "pytest-cov"])
        print("pytest installed")

    # Change to server-python directory
    os.chdir('server-python')

    # Run tests with coverage
    print("\nRunning Python backend tests...\n")
    result = subprocess.call([sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"])

    if result == 0:
        print("\nAll tests passed!")
    else:
        print(f"\nTests failed with exit code {result}")

    # Run frontend tests if they exist
    os.chdir('../client')
    if os.path.exists('package.json'):
        print("\n" + "=" * 60)
        print("Running frontend tests...")
        print("=" * 60)

        # Check if tests exist
        try:
            result = subprocess.call(["npm", "run", "test:unit"], shell=True)
            if result == 0:
                print("\nFrontend tests passed!")
            else:
                print("\nFrontend tests failed or not configured")
        except Exception as e:
            print(f"Could not run frontend tests: {e}")

    return result


if __name__ == "__main__":
    try:
        exit_code = run_tests()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError running tests: {e}")
        sys.exit(1)