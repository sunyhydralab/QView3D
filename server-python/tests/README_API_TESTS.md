# Fabricator Database Loading - E2E API Tests

## Overview

This test suite verifies that the **@reconstructor fix** for SQLAlchemy properly initializes fabricator runtime attributes when loading objects from the database.

## The Problem

When SQLAlchemy loads objects from the database using methods like:
- `Fabricator.query.filter_by()`
- `Fabricator.query.get()`
- `Fabricator.query.all()`

It **bypasses `__init__`** and only populates database columns. This left runtime attributes uninitialized:
- `queue` - Job queue for the fabricator
- `status` - Current status (idle, printing, offline, etc.)
- `device` - Hardware device object
- `error` - Error tracking

This caused `AttributeError` crashes when accessing these attributes.

## The Solution

Added a `@reconstructor` decorated method (`init_on_load()`) that SQLAlchemy automatically calls after loading objects from the database:

```python
@reconstructor
def init_on_load(self):
    """Initializes runtime attributes after database load."""
    from Classes.Queue import Queue
    if not hasattr(self, 'queue') or self.queue is None:
        self.queue = Queue()
    if not hasattr(self, 'status'):
        self.status = 'offline'
    if not hasattr(self, 'device'):
        self.device = None
    if not hasattr(self, 'error'):
        self.error = None
```

## What These Tests Do

The E2E API test suite verifies:

1. **Backend Health Check** - Ensures the Python backend is running
2. **Get Fabricators (Empty)** - Tests initial fabricator list retrieval
3. **Create Emulator** - Creates a fabricator in the database via API
4. **Get Fabricators (After Creation)** - **CRITICAL TEST** - Loads fabricators from database and verifies all runtime attributes are initialized
5. **Get Specific Fabricator** - Tests individual fabricator queries
6. **Emulator Status** - Tests emulator-specific database queries
7. **Disconnect Emulator** - Cleanup test
8. **JSON Serialization** - Tests that fabricators can be serialized properly

## Running the Tests

### Option 1: Automated Runner (Recommended)

From the project root:

```bash
./run-api-tests.sh
```

This script will:
- Check if the backend is running
- Offer to start it if not running
- Run all API tests
- Display colorized results

### Option 2: Manual Execution

1. **Start the Python backend** (if not already running):
   ```bash
   cd /Users/nathan/Downloads/QView3D-1
   python3 run.py
   # Select [D] for Debug mode
   # Select [P] for Python backend
   ```

2. **Run the test script**:
   ```bash
   cd /Users/nathan/Downloads/QView3D-1/server-python
   source .python-venv/bin/activate
   python tests/test_api_fabricator_e2e.py
   ```

### Option 3: Using requests directly (Postman-style)

You can also test the endpoints manually using curl or Postman:

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Get fabricators
curl http://localhost:8000/getfabricators

# 3. Start emulator (creates fabricator in database)
curl -X POST http://localhost:8000/startemulator \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Emulator"}'

# 4. Get fabricators again (tests database loading with @reconstructor)
curl http://localhost:8000/getfabricators

# 5. Get specific fabricator info
curl "http://localhost:8000/getprinterinfo?id=1"

# 6. Get emulator status
curl http://localhost:8000/api/emulator/status

# 7. Disconnect emulator
curl -X POST http://localhost:8000/disconnectemulator \
  -H "Content-Type: application/json" \
  -d '{"port": "EMU_0"}'
```

## Expected Results

### Passing Tests

```
✓ Backend is healthy
✓ Retrieved fabricators successfully
✓ Emulator started successfully
✓ Retrieved N fabricator(s) from database
  ✓ Database attribute 'id': 1
  ✓ Database attribute 'name': Test Emulator
  ✓ Runtime attribute 'status': offline
  ✓ Runtime attribute 'queue': <class 'list'> with 0 items
  ✓ Runtime attribute 'device': None
✓ ALL TESTS PASSED - @reconstructor is working correctly!
```

### Failing Tests (if @reconstructor is broken)

```
✗ Missing runtime attribute 'status' (RECONSTRUCTOR BUG)
✗ Missing runtime attribute 'queue' (RECONSTRUCTOR BUG)
CRITICAL FAILURE: @reconstructor not working!
Runtime attributes are not being initialized on database load
```

## Test Coverage

### Endpoints Tested
- `GET /health` - Backend health check
- `GET /getfabricators` - List all fabricators (tests database loading)
- `POST /startemulator` - Create emulator fabricator
- `GET /getprinterinfo` - Get specific fabricator details
- `GET /api/emulator/status` - Get emulator status
- `POST /disconnectemulator` - Disconnect emulator

### Database Operations Tested
- Creating fabricators via API
- Querying all fabricators from database
- Querying specific fabricator by ID
- Filtering fabricators by devicePort
- JSON serialization of fabricators

### Attributes Validated

**Database Attributes (persisted):**
- `id` (dbID)
- `name`
- `hwid`
- `description`
- `date`
- `devicePort`

**Runtime Attributes (initialized by @reconstructor):**
- `queue` - Must be initialized as Queue object
- `status` - Must be initialized (usually 'offline')
- `device` - Must exist (can be None)
- `error` - Must exist (can be None)

## Troubleshooting

### Backend Not Starting
```
Error: Python virtual environment not found
```
**Solution**: Run `python3 run.py` and select `[I]` to install dependencies

### Connection Failed
```
✗ Connection failed to http://localhost:8000/health
```
**Solution**: Ensure the Python backend is running on port 8000

### AttributeError in API Response
```
AttributeError: 'Fabricator' object has no attribute 'queue'
```
**Solution**: The @reconstructor fix is not applied. Check `Classes/Fabricators/Fabricator.py` line 34-51

## Files

- `test_api_fabricator_e2e.py` - Main E2E API test suite
- `test_fabricator_reconstruction.py` - Unit tests for @reconstructor
- `/run-api-tests.sh` - Automated test runner script (project root)

## Integration with CI/CD

To run these tests in CI/CD:

```bash
# Start backend
cd server-python
source .python-venv/bin/activate
python app.py &
BACKEND_PID=$!

# Wait for backend
sleep 5

# Run tests
python tests/test_api_fabricator_e2e.py
TEST_EXIT=$?

# Cleanup
kill $BACKEND_PID

# Exit with test result
exit $TEST_EXIT
```

## Related Files

- `/server-python/Classes/Fabricators/Fabricator.py:34-51` - @reconstructor implementation
- `/server-python/Classes/Fabricators/Fabricator.py:273-282` - Simplified queryAll()
- `/server-python/controllers/emulator.py` - Emulator endpoints
- `/server-python/controllers/ports.py` - Fabricator query endpoints
