from models.db import db
from sqlalchemy.exc import SQLAlchemyError
from flask import jsonify, current_app

from dotenv import load_dotenv

load_dotenv()

class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    issue = db.Column(db.String(200), nullable=False)

    def __init__(self, issue):
        self.issue = issue

    @classmethod
    def get_issues(cls):
        try:
            issues = cls.query.all()
            issues = [
                {"id": issue.id, "issue": issue.issue} for issue in issues
            ]
            return {"success": True, "issues": issues}
            # return issues
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return (
                jsonify({"error": "Failed to get issues. Database error"}),
                500,
            )

    @classmethod
    def create_issue(cls, issue):
        try:
            new_issue = cls(issue)
            db.session.add(new_issue)
            db.session.commit()
            return {"success": True, "message": "Issue successfully created"}
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return (
                jsonify({"error": "Failed to add job. Database error"}),
                500,
            )
    
