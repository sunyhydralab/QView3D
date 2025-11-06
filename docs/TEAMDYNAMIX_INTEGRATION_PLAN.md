# TeamDynamix Integration Plan

## Overview
Integrate QView3D issues and print tracking with Rollins TeamDynamix API endpoint:
`https://rollins.teamdynamix.com/TDWebApi/`

## Phase 1: Research & Setup (1-2 hours)

### 1.1 API Discovery
- [ ] Review TeamDynamix API documentation
- [ ] Identify available endpoints for:
  - Creating tickets/issues
  - Updating ticket status
  - Attaching files/metadata
  - Asset/equipment tracking
- [ ] Determine authentication method (likely Bearer token or API key)
- [ ] Get API credentials from IT/admin

### 1.2 Data Mapping
- [ ] Map QView3D issue fields to TeamDynamix ticket fields:
  ```
  QView3D Issue          → TeamDynamix Ticket
  ----------------         --------------------
  title                  → Title
  description            → Description
  severity               → Priority/Urgency
  category               → Type/Category
  fabricator_id          → Custom Attribute (Printer ID)
  job_id                 → Custom Attribute (Job ID)
  created_at             → RequestedDate
  resolved               → StatusID (Open/Closed)
  ```

- [ ] Map QView3D print jobs to TeamDynamix service requests:
  ```
  QView3D Job            → TeamDynamix Request
  ----------------         --------------------
  name                   → Title
  fabricator_name        → Assigned Printer
  status                 → StatusID
  time_elapsed           → Custom Attribute
  file_name              → Attachment
  comments               → Comments
  ```

## Phase 2: Backend Implementation (3-4 hours)

### 2.1 Create TeamDynamix Service
Create new service: `server-python/services/teamdynamix_service.py`

```python
class TeamDynamixService:
    def __init__(self, base_url, api_key, app_id):
        # Authentication and base config

    def create_ticket(self, issue_data):
        # POST /api/{appId}/tickets

    def update_ticket(self, ticket_id, updates):
        # PATCH /api/{appId}/tickets/{id}

    def add_attachment(self, ticket_id, file_data):
        # POST /api/{appId}/tickets/{id}/attachments

    def create_service_request(self, job_data):
        # POST /api/{appId}/requests

    def get_ticket_status(self, ticket_id):
        # GET /api/{appId}/tickets/{id}
```

### 2.2 Configuration
Add to `server-python/config/config.py`:
```python
Config = {
    'teamdynamix': {
        'base_url': 'https://rollins.teamdynamix.com/TDWebApi',
        'api_key': os.getenv('TD_API_KEY'),
        'app_id': os.getenv('TD_APP_ID'),
        'enabled': os.getenv('TD_INTEGRATION_ENABLED', 'false').lower() == 'true'
    }
}
```

### 2.3 Update Issue Model
Modify `server-python/Classes/Issues.py`:
- Add `td_ticket_id` field to track TeamDynamix ticket ID
- Hook into `create_issue()` to auto-create TD tickets
- Hook into `resolve_issue()` to close TD tickets

### 2.4 Update Job Model
Modify `server-python/Classes/Jobs.py`:
- Add `td_request_id` field to track TeamDynamix request ID
- Hook into job status changes to update TD requests
- Optional: Create TD request when job completes

## Phase 3: API Endpoints (1-2 hours)

### 3.1 New Controller Endpoints
Create `server-python/controllers/teamdynamix.py`:
```python
@td_bp.route('/sync-issue/<int:issue_id>', methods=['POST'])
def sync_issue_to_td(issue_id):
    # Manually sync an issue to TeamDynamix

@td_bp.route('/sync-job/<int:job_id>', methods=['POST'])
def sync_job_to_td(job_id):
    # Manually sync a job to TeamDynamix

@td_bp.route('/test-connection', methods=['GET'])
def test_td_connection():
    # Test TeamDynamix API connectivity
```

## Phase 4: Frontend Integration (2-3 hours)

### 4.1 Issue Management UI
- Add "Sync to TeamDynamix" button on issue cards
- Show TD ticket ID and link when synced
- Display sync status indicator

### 4.2 Job History UI
- Add TD request ID column to job history table
- Show TD link for completed jobs
- Add bulk sync option for historical jobs

### 4.3 Settings Page
- Add TeamDynamix configuration section
- Toggle auto-sync for issues
- Toggle auto-sync for completed jobs
- Test connection button

## Phase 5: Testing (1-2 hours)

### 5.1 Unit Tests
```python
# server-python/tests/test_teamdynamix.py
- test_create_ticket()
- test_update_ticket_status()
- test_sync_issue()
- test_sync_job()
- test_authentication_failure()
```

### 5.2 Integration Tests
- Create test issue → verify TD ticket created
- Resolve issue → verify TD ticket closed
- Complete job → verify TD request created
- Test with invalid credentials
- Test with network failures

## Phase 6: Deployment (1 hour)

### 6.1 Environment Setup
```bash
# .env additions
TD_API_KEY=your_api_key_here
TD_APP_ID=your_app_id_here
TD_INTEGRATION_ENABLED=true
```

### 6.2 Migration
```sql
-- Add TeamDynamix ID columns
ALTER TABLE Issues ADD COLUMN td_ticket_id VARCHAR(50);
ALTER TABLE Jobs ADD COLUMN td_request_id VARCHAR(50);
```

### 6.3 Documentation
- Update README with TeamDynamix setup instructions
- Document API key generation process
- Create troubleshooting guide

## Implementation Order

1. **Start Here**: Research TeamDynamix API docs and get credentials
2. **Core**: Implement `teamdynamix_service.py` with basic CRUD operations
3. **Integration**: Hook into Issue.create_issue() and Issue.resolve_issue()
4. **Testing**: Test basic issue sync workflow
5. **Expand**: Add job tracking integration
6. **UI**: Add frontend controls and status displays
7. **Polish**: Add error handling, retries, and logging

## Questions to Answer

1. What TeamDynamix application ID should be used?
2. Should issues auto-sync or require manual trigger?
3. Should all print jobs sync or only errors/completed?
4. What TeamDynamix custom attributes are available?
5. Should we sync historical data or only new items?
6. Who should be the default requester for synced tickets?
7. What ticket type/form should be used?

## Estimated Time
- Total: 8-14 hours
- Minimum viable: 4-6 hours (issues only, no UI)
- Full implementation: 10-14 hours (issues + jobs + UI)

## Success Criteria
- Issues automatically create TeamDynamix tickets
- Resolved issues close TeamDynamix tickets
- Jobs optionally create service requests
- Ticket IDs stored and displayed in QView3D
- Manual sync available for historical data
- Proper error handling and logging

