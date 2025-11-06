from config.db import db  # Import the SQLAlchemy datebase instance
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from services.app_service import current_app

class Issue(db.Model):

    """
    Represents an issue record stored in the database.

    Inherits from `db.Model`, which means it is an SQLAlchemy model class
    mapped to the `Issues` table in the database.

    Attributes:
        id (int): Primary key, unique identifier for each issue.
        issue (str): Description or details of the issue.
        job_id (int, optional): ID of the job associated with the issue.

    Methods:
        __init__(issue, job_id=None):
            Initializes a new Issue, saves it to the database,
            and links it to a job if job_id is provided.
        get_issues():
            Returns all issues as a JSON-like dictionary.
        get_issue_by_job(job_id):
            Returns the issue linked to a given job ID.
        create_issue(issue, exception=None, job_id=None):
            Creates a new issue, optionally logs exception details,
            and sends a Discord notification.
        delete_issue(issue_id):
            Deletes an issue by its ID.
        edit_issue(issue_id, issueNew):
            Edits the description of an existing issue.
    """
    __tablename__ = "Issues"  # Explicitly sets the table name in the database

    # Valid severity levels (must match frontend options)
    VALID_SEVERITIES = ['low', 'medium', 'high', 'critical']

    # Columns in the database
    id = db.Column(db.Integer, primary_key=True)  # Primary key for the issue
    issue = db.Column(db.String(200), nullable=True)  # Legacy: Description of the issue (kept for backward compatibility)
    title = db.Column(db.String(200), nullable=True)  # Title of the issue
    description = db.Column(db.Text, nullable=True)  # Detailed description
    severity = db.Column(db.String(20), nullable=True)  # low, medium, high, critical
    category = db.Column(db.String(50), nullable=True)  # printer, job, software
    fabricator_id = db.Column(db.Integer, nullable=True)  # Optional fabricator/printer ID
    job_id = db.Column(db.Integer, nullable=True)  # Optional job ID associated with the issue
    resolved = db.Column(db.Boolean, default=False)  # Whether issue is resolved
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # When issue was created

    @classmethod
    def validate_severity(cls, severity):
        """
        Validate and normalize severity level.

        Args:
            severity (str): Severity level to validate

        Returns:
            str: Valid severity level (defaults to 'medium' if invalid)
        """
        if severity and severity.lower() in cls.VALID_SEVERITIES:
            return severity.lower()
        return 'medium'

    def __init__(self, issue=None, job_id=None, title=None, description=None, severity=None, category=None, fabricator_id=None):

        """
        Creates a new Issue object and immediately commits it to the database.
        If job_id is provided, it updates the associated Job to link to this issue.
        """
        # Handle new format (title, description, etc.)
        self.title = title
        self.description = description
        self.severity = self.validate_severity(severity)
        self.category = category
        self.fabricator_id = fabricator_id
        self.job_id = job_id
        self.resolved = False

        # For backward compatibility, if 'issue' is provided (old format), use it
        if issue is not None:
            self.issue = issue
            # If no title provided, use issue as title
            if not self.title:
                self.title = issue[:200] if len(issue) > 200 else issue

        # Automatically save the issue to the database
        if current_app:
            db.session.add(self)
            db.session.commit()

        # If linked to a job, update the Job record with this issue ID
        if job_id is not None:
            from Classes.Jobs import Job
            job = Job.query.get(job_id)
            if job:
                job.error_id = self.id
                db.session.commit()

    @classmethod
    def get_issues(cls):
        """
        Retrieve all issues from the database.

        Returns:
            dict: Success status and a list of issue objects.
        """
        try:
            issues = cls.query.all()
            if issues:
                issues = [
                    {
                        "id": issue.id,
                        "title": issue.title or issue.issue,
                        "description": issue.description or issue.issue,
                        "severity": issue.severity or 'medium',
                        "category": issue.category or 'software',
                        "fabricator_id": issue.fabricator_id,
                        "job_id": issue.job_id,
                        "resolved": issue.resolved or False,
                        "status": "resolved" if issue.resolved else "open",  # Map boolean to status string for frontend
                        "created_at": issue.created_at.isoformat() if issue.created_at else None,
                        "issue": issue.issue
                    } for issue in issues
                ]
                return {"success": True, "issues": issues}
            else:
                return {"success": True, "issues": []}
        except SQLAlchemyError as e:
            if current_app:
                current_app.handle_errors_and_logging(e)
            raise

    @classmethod
    def get_issue_by_job(cls, job_id):
        try:
            issue = cls.query.filter_by(job_id=job_id).first()
            if issue:
                return {"success": True, "issue": issue.issue}
            else:
                return {"success": False, "issue": None}
        except SQLAlchemyError as e:
            if current_app:
                current_app.handle_errors_and_logging(e)
            raise

    @staticmethod
    def create_issue(issue=None, exception=None, job_id=None, title=None, description=None, severity=None, category=None, fabricator_id=None):
        try:
            new_issue = Issue(issue=issue, job_id=job_id, title=title, description=description,
                            severity=severity, category=category, fabricator_id=fabricator_id)
            if exception:
                import traceback
                exception_details = "".join(traceback.format_exception(None, exception, exception.__traceback__))
                print(f"Issue created with exception: {exception_details}")
            return {"success": True, "message": "Issue successfully created", "issue_id": new_issue.id}
        except SQLAlchemyError as e:
            if current_app:
                current_app.handle_errors_and_logging(e)
            raise
        except Exception as e:
            if current_app:
                current_app.handle_errors_and_logging(e)
            raise

    @classmethod
    def delete_issue(cls, issue_id):
        try:
            issue = cls.query.get(issue_id)
            if issue:
                db.session.delete(issue)
                db.session.commit()
                return {"success": True, "message": "Issue successfully deleted"}
            else:
                return {"success": False, "message": "Issue not found"}
        except SQLAlchemyError as e:
            if current_app:
                current_app.handle_errors_and_logging(e)
            raise

    @classmethod
    def edit_issue(cls, issue_id, issue_new):
        try:
            issue_to_edit = cls.query.get(issue_id)
            if not issue_to_edit:
                return {"success": False, "error": "Issue not found"}
            issue_to_edit.issue = issue_new
            db.session.commit()
            return {"success": True, "message": "Issue successfully edited"}
        except SQLAlchemyError as e:
            if current_app:
                current_app.handle_errors_and_logging(e)
            raise

    @classmethod
    def update_issue(cls, issue_id, title=None, description=None, severity=None, category=None, fabricator_id=None, job_id=None):
        try:
            issue_to_update = cls.query.get(issue_id)
            if not issue_to_update:
                return {"success": False, "error": "Issue not found"}
            if title is not None:
                issue_to_update.title = title
            if description is not None:
                issue_to_update.description = description
            if severity is not None:
                issue_to_update.severity = cls.validate_severity(severity)
            if category is not None:
                issue_to_update.category = category
            if fabricator_id is not None:
                issue_to_update.fabricator_id = fabricator_id
            if job_id is not None:
                issue_to_update.job_id = job_id
            db.session.commit()
            return {"success": True, "message": "Issue successfully updated"}
        except SQLAlchemyError as e:
            if current_app:
                current_app.handle_errors_and_logging(e)
            raise

    @classmethod
    def resolve_issue(cls, issue_id):
        try:
            issue = cls.query.get(issue_id)
            if not issue:
                return {"success": False, "error": "Issue not found"}

            issue.resolved = True
            db.session.commit()
            return {"success": True, "message": "Issue successfully resolved"}
        except SQLAlchemyError as e:
            if current_app:
                current_app.handle_errors_and_logging(e)
            raise

    @classmethod
    def create_issue_from_error(cls, title, description, category, fabricator_id=None, job_id=None, auto_severity='high', deduplicate=True):
        """
        Automatically create an issue from an error event with optional deduplication.

        Args:
            title (str): Brief title of the error
            description (str): Detailed error description
            category (str): Category of issue ('printer', 'job', or 'software')
            fabricator_id (int, optional): Printer ID if applicable
            job_id (int, optional): Job ID if applicable
            auto_severity (str): Severity level for the issue (default: 'high')
            deduplicate (bool): Whether to check for duplicate issues (default: True)

        Returns:
            dict: Success status and issue ID (new or existing)
        """
        try:
            # Determine severity based on error keywords
            severity = cls._determine_severity_from_error(description, auto_severity)

            # Check for duplicate issues if deduplication is enabled
            if deduplicate:
                duplicate = cls._find_duplicate_issue(
                    title=title,
                    category=category,
                    fabricator_id=fabricator_id,
                    job_id=job_id
                )
                if duplicate:
                    print(f"[AutoIssue] Duplicate issue found (ID: {duplicate.id}), skipping creation")
                    return {
                        "success": True,
                        "message": "Duplicate issue found, skipping creation",
                        "issue_id": duplicate.id,
                        "duplicate": True
                    }

            # Create new issue
            new_issue = cls(
                title=title,
                description=description,
                severity=severity,
                category=category,
                fabricator_id=fabricator_id,
                job_id=job_id
            )

            print(f"[AutoIssue] Created new issue (ID: {new_issue.id}): {title}")
            return {
                "success": True,
                "message": "Issue automatically created from error",
                "issue_id": new_issue.id,
                "duplicate": False
            }

        except Exception as e:
            print(f"[AutoIssue] Failed to create issue from error: {e}")
            if current_app:
                current_app.handle_errors_and_logging(e)
            return {"success": False, "error": str(e)}

    @classmethod
    def _determine_severity_from_error(cls, error_text, default_severity='high'):
        """
        Analyze error text to determine appropriate severity level.

        Args:
            error_text (str): The error message text
            default_severity (str): Default severity if no keywords match

        Returns:
            str: Determined severity level
        """
        if not error_text:
            return cls.validate_severity(default_severity)

        error_lower = error_text.lower()

        # Critical keywords
        critical_keywords = ['critical', 'fatal', 'emergency', 'catastrophic', 'fire', 'thermal runaway']
        if any(keyword in error_lower for keyword in critical_keywords):
            return 'critical'

        # High severity keywords
        high_keywords = ['failed', 'error', 'timeout', 'disconnected', 'lost connection', 'exception']
        if any(keyword in error_lower for keyword in high_keywords):
            return 'high'

        # Medium severity keywords
        medium_keywords = ['warning', 'retry', 'slow', 'degraded']
        if any(keyword in error_lower for keyword in medium_keywords):
            return 'medium'

        # Default to provided severity
        return cls.validate_severity(default_severity)

    @classmethod
    def _find_duplicate_issue(cls, title, category, fabricator_id=None, job_id=None, time_window_hours=24):
        """
        Search for duplicate unresolved issues within a time window.

        Args:
            title (str): Issue title to match
            category (str): Issue category
            fabricator_id (int, optional): Printer ID to match
            job_id (int, optional): Job ID to match
            time_window_hours (int): Time window in hours to search for duplicates

        Returns:
            Issue or None: Duplicate issue if found, None otherwise
        """
        from datetime import timedelta

        # Calculate time threshold
        time_threshold = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)

        # Build query for unresolved issues in the same category
        query = cls.query.filter(
            cls.resolved == False,
            cls.category == category,
            cls.created_at >= time_threshold
        )

        # Add fabricator_id filter if provided (for printer issues)
        if fabricator_id is not None:
            query = query.filter(cls.fabricator_id == fabricator_id)

        # Add job_id filter if provided (for job issues)
        if job_id is not None:
            query = query.filter(cls.job_id == job_id)

        # Search for similar titles (exact match or contained substring)
        existing_issues = query.all()
        for issue in existing_issues:
            if issue.title and title:
                # Check if titles match (case-insensitive partial match)
                if (title.lower() in issue.title.lower() or
                    issue.title.lower() in title.lower()):
                    return issue

        return None
