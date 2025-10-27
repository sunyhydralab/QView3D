"""
Comprehensive tests for Issues class - Issue tracking and management
"""
import pytest
from unittest.mock import patch, Mock
from datetime import datetime

from Classes.Issues import Issue
from Classes.Jobs import Job
from config.db import db
import gzip


class TestIssueCreation:
    """Test issue creation and initialization."""

    def test_create_issue_basic(self, app, session):
        """Test creating a basic issue."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                issue = Issue(
                    title="Test Issue",
                    description="Test description",
                    severity="high",
                    category="printer"
                )

                assert issue.title == "Test Issue"
                assert issue.description == "Test description"
                assert issue.severity == "high"
                assert issue.category == "printer"
                assert issue.resolved is False

    def test_create_issue_with_job_id(self, app, session):
        """Test creating issue linked to a job."""
        with app.app_context():
            # Create a job first
            job = Job(
                file=gzip.compress(b'test'),
                name='Test Job',
                fabricator_id=1,
                status='error',
                file_name_original='test.gcode',
                favorite=False,
                td_id=1,
                fabricator_name='Printer1'
            )
            db.session.add(job)
            db.session.commit()

            with patch('Classes.Issues.current_app', app):
                issue = Issue(
                    title="Job Failed",
                    description="Job failed during printing",
                    severity="high",
                    category="job",
                    job_id=job.id
                )

                assert issue.job_id == job.id

                # Check that job was updated with error_id
                job_check = Job.query.get(job.id)
                assert job_check.error_id == issue.id

    def test_create_issue_legacy_format(self, app, session):
        """Test creating issue using legacy 'issue' field."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                issue = Issue(issue="Legacy issue text")

                assert issue.issue == "Legacy issue text"
                assert issue.title == "Legacy issue text"

    def test_create_issue_with_fabricator(self, app, session):
        """Test creating issue with fabricator_id."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                issue = Issue(
                    title="Printer Error",
                    description="Printer connection lost",
                    severity="critical",
                    category="printer",
                    fabricator_id=1
                )

                assert issue.fabricator_id == 1
                assert issue.category == "printer"

    def test_create_issue_default_severity(self, app, session):
        """Test that default severity is 'medium'."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                issue = Issue(
                    title="Default Severity",
                    description="Test"
                )

                assert issue.severity == 'medium'


class TestIssueRetrieval:
    """Test retrieving issues from database."""

    def test_get_issues_empty(self, app, session):
        """Test getting issues when database is empty."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                # Clear all issues
                Issue.query.delete()
                db.session.commit()

                result = Issue.get_issues()

                assert result['success'] is True
                assert result['issues'] == []

    def test_get_issues_with_data(self, app, session):
        """Test getting issues with existing data."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                # Create test issues
                issue1 = Issue(
                    title="Issue 1",
                    description="Description 1",
                    severity="low",
                    category="software"
                )
                issue2 = Issue(
                    title="Issue 2",
                    description="Description 2",
                    severity="high",
                    category="printer"
                )

                result = Issue.get_issues()

                assert result['success'] is True
                assert len(result['issues']) >= 2

                # Check that issues have all expected fields
                for issue in result['issues']:
                    assert 'id' in issue
                    assert 'title' in issue
                    assert 'description' in issue
                    assert 'severity' in issue
                    assert 'category' in issue
                    assert 'resolved' in issue
                    assert 'created_at' in issue

    def test_get_issue_by_job(self, app, session):
        """Test getting issue by job ID."""
        with app.app_context():
            # Create a job first
            job = Job(
                file=gzip.compress(b'test'),
                name='Test Job',
                fabricator_id=1,
                status='error',
                file_name_original='test.gcode',
                favorite=False,
                td_id=1,
                fabricator_name='Printer1'
            )
            db.session.add(job)
            db.session.commit()

            with patch('Classes.Issues.current_app', app):
                # Create issue linked to job
                issue = Issue(
                    title="Job Error",
                    description="Job failed",
                    job_id=job.id
                )

                result = Issue.get_issue_by_job(job.id)

                assert result['success'] is True
                assert result['issue'] is not None

    def test_get_issue_by_job_not_found(self, app, session):
        """Test getting issue for job that has no issue."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                result = Issue.get_issue_by_job(999999)

                assert result['success'] is False
                assert result['issue'] is None


class TestIssueCreationStatic:
    """Test static issue creation method."""

    def test_create_issue_static(self, app, session):
        """Test creating issue using static method."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                result = Issue.create_issue(
                    title="Static Issue",
                    description="Created via static method",
                    severity="medium",
                    category="software"
                )

                assert result['success'] is True
                assert 'issue_id' in result
                assert result['message'] == "Issue successfully created"

                # Verify issue was created
                issue = Issue.query.get(result['issue_id'])
                assert issue is not None
                assert issue.title == "Static Issue"

    def test_create_issue_with_exception(self, app, session):
        """Test creating issue with exception details."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                try:
                    raise ValueError("Test exception")
                except ValueError as e:
                    result = Issue.create_issue(
                        title="Exception Issue",
                        description="Issue with exception",
                        exception=e
                    )

                    assert result['success'] is True

    def test_create_issue_legacy_static(self, app, session):
        """Test creating issue using legacy format with static method."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                result = Issue.create_issue(
                    issue="Legacy static issue"
                )

                assert result['success'] is True
                issue = Issue.query.get(result['issue_id'])
                assert issue.issue == "Legacy static issue"
                assert issue.title == "Legacy static issue"


class TestIssueUpdate:
    """Test updating existing issues."""

    def test_update_issue(self, app, session):
        """Test updating issue fields."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                # Create issue
                issue = Issue(
                    title="Original Title",
                    description="Original Description",
                    severity="low",
                    category="software"
                )
                issue_id = issue.id

                # Update issue
                result = Issue.update_issue(
                    issue_id,
                    title="Updated Title",
                    description="Updated Description",
                    severity="high",
                    category="printer"
                )

                assert result['success'] is True
                assert result['message'] == "Issue successfully updated"

                # Verify updates
                updated_issue = Issue.query.get(issue_id)
                assert updated_issue.title == "Updated Title"
                assert updated_issue.description == "Updated Description"
                assert updated_issue.severity == "high"
                assert updated_issue.category == "printer"

    def test_update_partial_fields(self, app, session):
        """Test updating only some fields."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                # Create issue
                issue = Issue(
                    title="Original",
                    description="Original desc",
                    severity="low"
                )
                issue_id = issue.id

                # Update only title
                result = Issue.update_issue(
                    issue_id,
                    title="New Title"
                )

                assert result['success'] is True

                # Verify only title changed
                updated_issue = Issue.query.get(issue_id)
                assert updated_issue.title == "New Title"
                assert updated_issue.description == "Original desc"
                assert updated_issue.severity == "low"

    def test_update_nonexistent_issue(self, app, session):
        """Test updating issue that doesn't exist."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                result = Issue.update_issue(
                    999999,
                    title="New Title"
                )

                assert result['success'] is False
                assert 'error' in result

    def test_edit_issue_legacy(self, app, session):
        """Test editing issue using legacy method."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                # Create issue
                issue = Issue(issue="Original issue text")
                issue_id = issue.id

                # Edit using legacy method
                result = Issue.edit_issue(issue_id, "New issue text")

                assert result['success'] is True
                assert result['message'] == "Issue successfully edited"

                # Verify update
                updated_issue = Issue.query.get(issue_id)
                assert updated_issue.issue == "New issue text"


class TestIssueResolution:
    """Test resolving issues."""

    def test_resolve_issue(self, app, session):
        """Test marking issue as resolved."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                # Create issue
                issue = Issue(
                    title="Test Issue",
                    description="To be resolved",
                    resolved=False
                )
                issue_id = issue.id

                # Resolve issue
                result = Issue.resolve_issue(issue_id)

                assert result['success'] is True
                assert result['message'] == "Issue successfully resolved"

                # Verify resolution
                resolved_issue = Issue.query.get(issue_id)
                assert resolved_issue.resolved is True

    def test_resolve_nonexistent_issue(self, app, session):
        """Test resolving issue that doesn't exist."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                result = Issue.resolve_issue(999999)

                assert result['success'] is False
                assert 'error' in result


class TestIssueDeletion:
    """Test deleting issues."""

    def test_delete_issue(self, app, session):
        """Test deleting an issue."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                # Create issue
                issue = Issue(
                    title="To Delete",
                    description="Will be deleted"
                )
                issue_id = issue.id

                # Delete issue
                result = Issue.delete_issue(issue_id)

                assert result['success'] is True
                assert result['message'] == "Issue successfully deleted"

                # Verify deletion
                deleted_issue = Issue.query.get(issue_id)
                assert deleted_issue is None

    def test_delete_nonexistent_issue(self, app, session):
        """Test deleting issue that doesn't exist."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                result = Issue.delete_issue(999999)

                assert result['success'] is False
                assert result['message'] == "Issue not found"


class TestIssueSeverityLevels:
    """Test different severity levels."""

    @pytest.mark.parametrize("severity", ["low", "medium", "high", "critical"])
    def test_severity_levels(self, app, session, severity):
        """Test creating issues with different severity levels."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                issue = Issue(
                    title=f"{severity} severity issue",
                    description="Test",
                    severity=severity
                )

                assert issue.severity == severity

                # Verify it's in get_issues
                result = Issue.get_issues()
                found = False
                for iss in result['issues']:
                    if iss['id'] == issue.id:
                        assert iss['severity'] == severity
                        found = True
                        break
                assert found


class TestIssueCategories:
    """Test different issue categories."""

    @pytest.mark.parametrize("category", ["printer", "job", "software"])
    def test_categories(self, app, session, category):
        """Test creating issues with different categories."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                issue = Issue(
                    title=f"{category} issue",
                    description="Test",
                    category=category
                )

                assert issue.category == category

                # Verify it's in get_issues
                result = Issue.get_issues()
                found = False
                for iss in result['issues']:
                    if iss['id'] == issue.id:
                        assert iss['category'] == category
                        found = True
                        break
                assert found


class TestIssueTimestamps:
    """Test issue timestamp functionality."""

    def test_created_at_timestamp(self, app, session):
        """Test that created_at is set automatically."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                issue = Issue(
                    title="Timestamp Test",
                    description="Test"
                )

                assert issue.created_at is not None
                assert isinstance(issue.created_at, datetime)

    def test_timestamp_in_serialization(self, app, session):
        """Test that timestamp appears in JSON serialization."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                issue = Issue(
                    title="Timestamp Test",
                    description="Test"
                )

                result = Issue.get_issues()

                # Find our issue in results
                for iss in result['issues']:
                    if iss['id'] == issue.id:
                        assert 'created_at' in iss
                        assert iss['created_at'] is not None
                        break


class TestIssueLegacyCompatibility:
    """Test backward compatibility with legacy issue format."""

    def test_legacy_field_in_new_format(self, app, session):
        """Test that legacy 'issue' field appears in JSON."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                issue = Issue(
                    title="New Format",
                    description="New description"
                )

                result = Issue.get_issues()

                # Find our issue
                for iss in result['issues']:
                    if iss['id'] == issue.id:
                        assert 'issue' in iss
                        break

    def test_title_fallback_from_issue(self, app, session):
        """Test that title falls back to 'issue' field if not provided."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                issue = Issue(issue="Legacy issue without title")

                assert issue.title == "Legacy issue without title"

    def test_long_issue_text_truncation(self, app, session):
        """Test that long legacy issue text is truncated for title."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                long_text = "A" * 250  # More than 200 characters
                issue = Issue(issue=long_text)

                assert len(issue.title) <= 200
                assert issue.title == long_text[:200]


class TestIssueEdgeCases:
    """Test edge cases and error handling."""

    def test_create_issue_with_none_values(self, app, session):
        """Test creating issue with None for optional fields."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                issue = Issue(
                    title="Minimal Issue",
                    fabricator_id=None,
                    job_id=None
                )

                assert issue.fabricator_id is None
                assert issue.job_id is None

    def test_update_with_empty_string(self, app, session):
        """Test updating fields with empty strings."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                issue = Issue(
                    title="Original",
                    description="Original"
                )
                issue_id = issue.id

                # Update with empty description
                result = Issue.update_issue(
                    issue_id,
                    description=""
                )

                assert result['success'] is True

                updated_issue = Issue.query.get(issue_id)
                assert updated_issue.description == ""

    def test_multiple_issues_same_job(self, app, session):
        """Test creating multiple issues for same job."""
        with app.app_context():
            job = Job(
                file=gzip.compress(b'test'),
                name='Test Job',
                fabricator_id=1,
                status='error',
                file_name_original='test.gcode',
                favorite=False,
                td_id=1,
                fabricator_name='Printer1'
            )
            db.session.add(job)
            db.session.commit()

            with patch('Classes.Issues.current_app', app):
                issue1 = Issue(
                    title="Issue 1",
                    description="First issue",
                    job_id=job.id
                )
                issue2 = Issue(
                    title="Issue 2",
                    description="Second issue",
                    job_id=job.id
                )

                # Both issues should be created
                assert issue1.id != issue2.id
                assert issue1.job_id == issue2.job_id
