#!/bin/bash
# E2E API Test Runner for Fabricator Database Loading
# Tests the @reconstructor fix by creating and retrieving fabricators via API

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=8000
BACKEND_URL="http://localhost:${BACKEND_PORT}"
TEST_SCRIPT="server-python/tests/test_api_fabricator_e2e.py"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                   FABRICATOR E2E API TEST RUNNER                           ║${NC}"
echo -e "${BLUE}║              Testing @reconstructor Database Loading Fix                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to check if backend is running
check_backend() {
    echo -e "${BLUE}[1/3]${NC} Checking if Python backend is running on port ${BACKEND_PORT}..."
    if curl -s --max-time 2 "${BACKEND_URL}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is running${NC}"
        return 0
    else
        echo -e "${YELLOW}✗ Backend is not running${NC}"
        return 1
    fi
}

# Function to start backend
start_backend() {
    echo -e "${YELLOW}Starting Python backend...${NC}"
    echo -e "${YELLOW}Note: This will start the backend in the background${NC}"
    echo ""

    cd server-python

    # Check if virtual environment exists
    if [ ! -d ".python-venv" ]; then
        echo -e "${RED}Error: Python virtual environment not found${NC}"
        echo -e "${YELLOW}Please run: python3 run.py and select [I] to install dependencies${NC}"
        exit 1
    fi

    # Start backend in background
    source .python-venv/bin/activate
    python app.py > /tmp/qview3d-backend.log 2>&1 &
    BACKEND_PID=$!

    echo -e "${BLUE}Backend starting (PID: ${BACKEND_PID})...${NC}"
    echo -e "${BLUE}Waiting for backend to be ready...${NC}"

    # Wait for backend to be ready (max 30 seconds)
    for i in {1..30}; do
        sleep 1
        if curl -s --max-time 1 "${BACKEND_URL}/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Backend is ready${NC}"
            cd ..
            return 0
        fi
        echo -n "."
    done

    echo ""
    echo -e "${RED}✗ Backend failed to start within 30 seconds${NC}"
    echo -e "${YELLOW}Check logs at: /tmp/qview3d-backend.log${NC}"
    cd ..
    exit 1
}

# Function to run tests
run_tests() {
    echo ""
    echo -e "${BLUE}[2/3]${NC} Running E2E API tests..."
    echo ""

    if [ ! -f "${TEST_SCRIPT}" ]; then
        echo -e "${RED}Error: Test script not found at ${TEST_SCRIPT}${NC}"
        exit 1
    fi

    cd server-python
    source .python-venv/bin/activate
    python "tests/test_api_fabricator_e2e.py"
    TEST_EXIT_CODE=$?
    cd ..

    return $TEST_EXIT_CODE
}

# Main execution
main() {
    # Check if backend is running
    if ! check_backend; then
        echo ""
        echo -e "${YELLOW}Backend is not running. Would you like to start it? (y/n)${NC}"
        read -r response

        if [[ "$response" =~ ^[Yy]$ ]]; then
            start_backend
        else
            echo -e "${RED}Cannot run tests without backend. Exiting.${NC}"
            echo ""
            echo -e "${YELLOW}To start the backend manually, run:${NC}"
            echo -e "  cd /Users/nathan/Downloads/QView3D-1"
            echo -e "  python3 run.py"
            echo -e "  Select [D] for Debug mode and [P] for Python backend"
            exit 1
        fi
    fi

    # Run the tests
    if run_tests; then
        echo ""
        echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║                         ALL TESTS PASSED ✓                                 ║${NC}"
        echo -e "${GREEN}║          @reconstructor is working correctly for database loading         ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
        exit 0
    else
        echo ""
        echo -e "${RED}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║                         TESTS FAILED ✗                                     ║${NC}"
        echo -e "${RED}║                  Please review the output above                            ║${NC}"
        echo -e "${RED}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
        exit 1
    fi
}

# Cleanup function
cleanup() {
    echo ""
    echo -e "${BLUE}Cleaning up...${NC}"
    # Add any cleanup code here if needed
}

# Set up trap for cleanup
trap cleanup EXIT

# Run main function
main
