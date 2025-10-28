from config.db import db
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from services.app_service import current_app

class Issue(db.Model):
    __tablename__ = "Issues"
    id = db.Column(db.Integer, primary_key=True)
    issue = db.Column(db.String(200), nullable=True)
    title = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    severity = db.Column(db.String(20), nullable=True)
    category = db.Column(db.String(50), nullable=True)
    fabricator_id = db.Column(db.Integer, nullable=True)
    job_id = db.Column(db.Integer, nullable=True)
    resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __init__(self, issue=None, job_id=None, title=None, description=None, severity=None, category=None, fabricator_id=None):
        self.title = title
        self.description = description
        self.severity = severity or 'medium'
        self.category = category
        self.fabricator_id = fabricator_id
        self.job_id = job_id
        self.resolved = False
        if issue is not None:
            self.issue = issue
            if not self.title:
                self.title = issue[:200] if len(issue) > 200 else issue
        if current_app:
            db.session.add(self)
            db.session.commit()
        if job_id is not None:
            from Classes.Jobs import Job
            job = Job.query.get(job_id)
            if job:
                job.error_id = self.id
                db.session.commit()

    @classmethod
    def get_issues(cls):
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
