from config.db import db # Import the SQLAlchemy datebase instance
from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError

from datetime import datetime
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
    __tablename__ = "Issues" # Explicitly sets the table name in the database

    # Columns in the database
    id = db.Column(db.Integer, primary_key=True) #Primary key for the issue
    issue = db.Column(db.String(200), nullable=True) # Legacy: Description of the issue (kept for backward compatibility)
    title = db.Column(db.String(200), nullable=True) # Title of the issue
    description = db.Column(db.Text, nullable=True) # Detailed description
    severity = db.Column(db.String(20), nullable=True) # low, medium, high, critical
    category = db.Column(db.String(50), nullable=True) # printer, job, software
    fabricator_id = db.Column(db.Integer, nullable=True) # Optional fabricator/printer ID
    job_id = db.Column(db.Integer, nullable=True) # Optional job ID associated with the issue
    resolved = db.Column(db.Boolean, default=False) # Whether issue is resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # When issue was created

    def __init__(self, issue=None, job_id=None, title=None, description=None, severity=None, category=None, fabricator_id=None):

        """
        Creates a new Issue object and immediately commits it to the database.
        If job_id is provided, it updates the associated Job to link to this issue.
        """
        # Handle new format (title, description, etc.)
        self.title = title
        self.description = description
        self.severity = severity or 'medium'
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
                        "title": issue.title or issue.issue,  # Fallback to legacy field
                        "description": issue.description or issue.issue,
                        "severity": issue.severity or 'medium',
                        "category": issue.category or 'software',
                        "fabricator_id": issue.fabricator_id,
                        "job_id": issue.job_id,
                        "resolved": issue.resolved or False,
                        "created_at": issue.created_at.isoformat() if issue.created_at else None,
                        # Legacy field for backward compatibility
                        "issue": issue.issue
                    } for issue in issues
                ]
                return {"success": True, "issues": issues}
            else:
                return {"success": True, "issues": []}
        except SQLAlchemyError as e:
            if current_app:
                current_app.handle_errors_and_logging(e)
            raise  # Re-raise the exception so the controller can handle it

    @classmethod
    def get_issue_by_job(cls, job_id):
        """
        Retrieve the issue associated with a specific job.
        """

        try:
            issue = cls.query.filter_by(job_id=job_id).first()
            if issue:
                return {"success": True, "issue": issue.issue}
            else:
                return {"success": False, "issue": None}
        except SQLAlchemyError as e:
            if current_app:
                current_app.handle_errors_and_logging(e)
            raise  # Re-raise the exception so the controller can handle it

    @staticmethod
    def create_issue(issue=None, exception=None, job_id: int = None, title=None, description=None, severity=None, category=None, fabricator_id=None):
        """
        Creates a new issue and stores it in the database.
        Supports both old format (issue string) and new format (title, description, severity, etc.)
        If `exception` is provided, it is logged for debugging.
        """

        try:
            new_issue = Issue(
                issue=issue,
                job_id=job_id,
                title=title,
                description=description,
                severity=severity,
                category=category,
                fabricator_id=fabricator_id
            )

            # Log exception if provided
            if exception:
                import traceback
                exception_details = "".join(traceback.format_exception(None, exception, exception.__traceback__))
                print(f"Issue created with exception: {exception_details}")

            return {"success": True, "message": "Issue successfully created", "issue_id": new_issue.id}
        except SQLAlchemyError as e:
            if current_app:
                current_app.handle_errors_and_logging(e)
            raise  # Re-raise the exception so the controller can handle it
        except Exception as e:
            if current_app:
                current_app.handle_errors_and_logging(e)
            raise  # Re-raise the exception so the controller can handle it

    @classmethod
    def delete_issue(cls, issue_id):
        """
        Deletes an issue by its ID.
        """

        try:
            # issue = cls.query.filter_by(id=issue_id).first()
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
            raise  # Re-raise the exception so the controller can handle it
    
    @classmethod
    def edit_issue(cls, issue_id, issueNew):
        """
        Updates the description of an existing issue (legacy method).
        """

        try:
            issueToEdit = cls.query.get(issue_id)
            if not issueToEdit:
                return {"success": False, "error": "Issue not found"}
            issueToEdit.issue = issueNew
            db.session.commit()
            return {"success": True, "message": "Issue successfully edited"}
        except SQLAlchemyError as e:
            if current_app:
                current_app.handle_errors_and_logging(e)
            raise  # Re-raise the exception so the controller can handle it

    @classmethod
    def update_issue(cls, issue_id, title=None, description=None, severity=None, category=None, fabricator_id=None, job_id=None):
        """
        Updates an existing issue with new field values.
        """

        try:
            issue_to_update = cls.query.get(issue_id)
            if not issue_to_update:
                return {"success": False, "error": "Issue not found"}

            # Update fields if provided
            if title is not None:
                issue_to_update.title = title
            if description is not None:
                issue_to_update.description = description
            if severity is not None:
                issue_to_update.severity = severity
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
            raise  # Re-raise the exception so the controller can handle it

    @classmethod
    def resolve_issue(cls, issue_id):
        """
        Marks an issue as resolved.
        """

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
            raise  # Re-raise the exception so the controller can handle it
