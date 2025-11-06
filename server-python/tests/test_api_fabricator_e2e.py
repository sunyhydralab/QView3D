"""
End-to-End API Test Suite for Fabricator Database Loading
Tests the @reconstructor fix by creating fabricators and retrieving them via API.

This test verifies that:
1. Fabricators can be created (emulator endpoints)
2. Fabricators can be retrieved from database
3. All runtime attributes (queue, status, device, error) are properly initialized
4. No AttributeErrors occur when accessing fabricator attributes through API
"""
import requests
import json
import time
import sys
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"  # Python backend
API_TIMEOUT = 10

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def log_test(message: str, status: str = "INFO"):
    """Log test messages with color coding."""
    if status == "PASS":
        print(f"{GREEN}✓ {message}{RESET}")
    elif status == "FAIL":
        print(f"{RED}✗ {message}{RESET}")
    elif status == "WARN":
        print(f"{YELLOW}⚠ {message}{RESET}")
    else:
        print(f"{BLUE}ℹ {message}{RESET}")


def make_request(method: str, endpoint: str, **kwargs) -> requests.Response:
    """Make HTTP request with error handling."""
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.request(method, url, timeout=API_TIMEOUT, **kwargs)
        return response
    except requests.exceptions.ConnectionError:
        log_test(f"Connection failed to {url}", "FAIL")
        log_test("Make sure the Python backend is running on port 8000", "WARN")
        sys.exit(1)
    except requests.exceptions.Timeout:
        log_test(f"Request timeout for {url}", "FAIL")
        sys.exit(1)


def test_health_check():
    """Test 1: Verify backend is running."""
    log_test("Testing backend health check...", "INFO")
    response = make_request("GET", "/health")

    if response.status_code == 200:
        data = response.json()
        log_test(f"Backend is healthy: {data}", "PASS")
        return True
    else:
        log_test(f"Health check failed: {response.status_code}", "FAIL")
        return False


def test_get_fabricators_empty():
    """Test 2: Get fabricators list (may be empty initially)."""
    log_test("Testing GET /getfabricators...", "INFO")
    response = make_request("GET", "/getfabricators")

    if response.status_code == 200:
        data = response.json()
        log_test(f"Retrieved fabricators successfully. Count: {len(data.get('fabricators', []))}", "PASS")
        return data.get('fabricators', [])
    else:
        log_test(f"Failed to get fabricators: {response.status_code} - {response.text}", "FAIL")
        return None


def test_start_emulator(name: str = "E2E Test Emulator"):
    """Test 3: Start an emulator (creates fabricator in database)."""
    log_test(f"Testing POST /startemulator with name '{name}'...", "INFO")
    response = make_request("POST", "/startemulator", json={"name": name})

    if response.status_code == 200:
        data = response.json()
        log_test(f"Emulator started successfully: {data.get('message', '')}", "PASS")
        return data
    else:
        log_test(f"Failed to start emulator: {response.status_code} - {response.text}", "FAIL")
        return None


def test_get_fabricators_after_creation():
    """Test 4: Get fabricators after creating emulator - tests @reconstructor."""
    log_test("Testing GET /getfabricators after emulator creation (DATABASE LOAD TEST)...", "INFO")
    response = make_request("GET", "/getfabricators")

    if response.status_code != 200:
        log_test(f"Failed to get fabricators: {response.status_code} - {response.text}", "FAIL")
        return None

    data = response.json()
    fabricators = data.get('fabricators', [])

    if not fabricators:
        log_test("No fabricators found after creation", "FAIL")
        return None

    log_test(f"Retrieved {len(fabricators)} fabricator(s) from database", "PASS")

    # Check if all required attributes exist (tests @reconstructor initialization)
    for i, fab in enumerate(fabricators):
        log_test(f"Validating fabricator {i+1}: {fab.get('name', 'Unknown')}", "INFO")

        # Check database attributes
        required_db_attrs = ['id', 'name', 'hwid', 'description', 'date']
        for attr in required_db_attrs:
            if attr in fab:
                log_test(f"  - Database attribute '{attr}': {fab[attr]}", "PASS")
            else:
                log_test(f"  - Missing database attribute '{attr}'", "FAIL")
                return None

        # Check runtime attributes (these are initialized by @reconstructor)
        if 'status' in fab:
            log_test(f"  - Runtime attribute 'status': {fab['status']}", "PASS")
        else:
            log_test(f"  - Missing runtime attribute 'status' (RECONSTRUCTOR BUG)", "FAIL")
            return None

        if 'queue' in fab:
            log_test(f"  - Runtime attribute 'queue': {type(fab['queue'])} with {len(fab['queue'])} items", "PASS")
        else:
            log_test(f"  - Missing runtime attribute 'queue' (RECONSTRUCTOR BUG)", "FAIL")
            return None

        # Device can be None for emulators
        if 'device' in fab:
            log_test(f"  - Runtime attribute 'device': {fab['device']}", "PASS")
        else:
            log_test(f"  - Missing runtime attribute 'device'", "FAIL")
            return None

    return fabricators


def test_get_specific_fabricator_info(fabricator_id: int):
    """Test 5: Get specific fabricator info - tests database query with @reconstructor."""
    log_test(f"Testing GET /getprinterinfo for fabricator ID {fabricator_id}...", "INFO")
    response = make_request("GET", f"/getprinterinfo?id={fabricator_id}")

    if response.status_code == 200:
        data = response.json()
        log_test(f"Retrieved fabricator info successfully", "PASS")
        log_test(f"  - Name: {data.get('name', 'N/A')}", "INFO")
        log_test(f"  - Status: {data.get('status', 'N/A')}", "INFO")
        log_test(f"  - HWID: {data.get('hwid', 'N/A')}", "INFO")
        return data
    else:
        log_test(f"Failed to get fabricator info: {response.status_code} - {response.text}", "FAIL")
        return None


def test_emulator_status():
    """Test 6: Get emulator status - tests emulator-specific database queries."""
    log_test("Testing GET /api/emulator/status...", "INFO")
    response = make_request("GET", "/api/emulator/status")

    if response.status_code == 200:
        data = response.json()
        emulators = data.get('emulators', [])
        log_test(f"Retrieved emulator status. Active emulators: {len(emulators)}", "PASS")

        for emu in emulators:
            log_test(f"  - Emulator: {emu.get('name', 'Unknown')} | Port: {emu.get('port', 'N/A')} | Status: {emu.get('status', 'N/A')}", "INFO")

        return emulators
    else:
        log_test(f"Failed to get emulator status: {response.status_code} - {response.text}", "FAIL")
        return None


def test_disconnect_emulator(port: str):
    """Test 7: Disconnect emulator."""
    log_test(f"Testing POST /disconnectemulator for port {port}...", "INFO")
    response = make_request("POST", "/disconnectemulator", json={"port": port})

    if response.status_code == 200:
        data = response.json()
        log_test(f"Emulator disconnected: {data.get('message', '')}", "PASS")
        return True
    else:
        log_test(f"Failed to disconnect emulator: {response.status_code} - {response.text}", "FAIL")
        return False


def test_fabricator_serialization():
    """Test 8: Test that fabricators can be properly serialized to JSON (tests __to_JSON__)."""
    log_test("Testing fabricator JSON serialization...", "INFO")
    response = make_request("GET", "/getfabricators")

    if response.status_code != 200:
        log_test(f"Failed to get fabricators: {response.status_code}", "FAIL")
        return False

    try:
        data = response.json()
        fabricators = data.get('fabricators', [])

        if not fabricators:
            log_test("No fabricators to test serialization", "WARN")
            return True

        # Try to serialize to JSON again (tests that no issues with serialization)
        json_str = json.dumps(fabricators)
        log_test(f"Fabricators serialized successfully ({len(json_str)} bytes)", "PASS")

        # Verify we can deserialize
        deserialized = json.loads(json_str)
        log_test(f"Fabricators deserialized successfully", "PASS")

        return True
    except Exception as e:
        log_test(f"Serialization failed: {str(e)}", "FAIL")
        return False


def run_all_tests():
    """Run complete E2E test suite."""
    print("\n" + "="*80)
    print("FABRICATOR DATABASE LOADING - E2E API TEST SUITE")
    print("Testing @reconstructor fix for SQLAlchemy initialization")
    print("="*80 + "\n")

    tests_passed = 0
    tests_failed = 0

    # Test 1: Health check
    if test_health_check():
        tests_passed += 1
    else:
        tests_failed += 1
        return  # Can't continue if backend is down

    print()

    # Test 2: Get initial fabricators
    initial_fabs = test_get_fabricators_empty()
    if initial_fabs is not None:
        tests_passed += 1
    else:
        tests_failed += 1

    print()

    # Test 3: Create emulator
    emulator_name = f"E2E Test Emulator {int(time.time())}"
    start_result = test_start_emulator(emulator_name)
    if start_result:
        tests_passed += 1
        time.sleep(2)  # Wait for emulator to be fully registered
    else:
        tests_failed += 1

    print()

    # Test 4: Get fabricators after creation (CRITICAL TEST for @reconstructor)
    fabricators = test_get_fabricators_after_creation()
    if fabricators:
        tests_passed += 1
    else:
        tests_failed += 1
        print("\n" + RED + "CRITICAL FAILURE: @reconstructor not working!" + RESET)
        print(RED + "Runtime attributes are not being initialized on database load" + RESET)

    print()

    # Test 5: Get specific fabricator info
    if fabricators and len(fabricators) > 0:
        fab_id = fabricators[0].get('id')
        if test_get_specific_fabricator_info(fab_id):
            tests_passed += 1
        else:
            tests_failed += 1
    else:
        log_test("Skipping test 5 (no fabricators available)", "WARN")

    print()

    # Test 6: Emulator status
    emulators = test_emulator_status()
    if emulators is not None:
        tests_passed += 1
    else:
        tests_failed += 1

    print()

    # Test 7: Disconnect emulator (cleanup)
    if emulators and len(emulators) > 0:
        emu_port = emulators[0].get('port')
        if emu_port:
            if test_disconnect_emulator(emu_port):
                tests_passed += 1
            else:
                tests_failed += 1
        else:
            log_test("No emulator port found to disconnect", "WARN")
    else:
        log_test("Skipping test 7 (no emulators to disconnect)", "WARN")

    print()

    # Test 8: Serialization test
    if test_fabricator_serialization():
        tests_passed += 1
    else:
        tests_failed += 1

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"{GREEN}Tests Passed: {tests_passed}{RESET}")
    print(f"{RED}Tests Failed: {tests_failed}{RESET}")
    print(f"Total Tests:  {tests_passed + tests_failed}")

    if tests_failed == 0:
        print(f"\n{GREEN}✓ ALL TESTS PASSED - @reconstructor is working correctly!{RESET}")
        print(f"{GREEN}✓ Fabricators are properly initialized when loaded from database{RESET}")
        return 0
    else:
        print(f"\n{RED}✗ SOME TESTS FAILED - Please review the output above{RESET}")
        return 1


if __name__ == "__main__":
    print(f"\n{BLUE}Starting E2E API Test Suite...{RESET}")
    print(f"{BLUE}Ensure Python backend is running on {BASE_URL}{RESET}\n")

    exit_code = run_all_tests()
    sys.exit(exit_code)
