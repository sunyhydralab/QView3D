from models.db import db
from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError


class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    issue = db.Column(db.String(200), nullable=False)

    def __init__(self, issue):
        self.issue = issue

    @classmethod
    def get_issues(cls):
        try:
            issues = cls.query.all()
            if(issues):
                issues = [
                    {"id": issue.id, "issue": issue.issue} for issue in issues
                ]
                return {"success": True, "issues": issues}
            else: 
                return {"success": True, "issues": []}
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
            
    @classmethod
    def delete_issue(cls, issue_id):
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
            print(f"Database error: {e}")
            return (
                jsonify({"error": "Failed to delete issue. Database error"}),
                500,
            )
    
    @classmethod
    def edit_issue(cls, issue_id, issueNew):
        try:
            issueToEdit = cls.query.get(issue_id)
            issueToEdit.issue = issueNew
            db.session.commit()
            return {"success": True, "message": "Issue successfully edited"}
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return (
                jsonify({"error": "Failed to edit issue. Database error"}),
                500,
            )
