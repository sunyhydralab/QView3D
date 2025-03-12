from models.db import db
from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError

from datetime import datetime
import discord
from models.config import Config
from globals import current_app

class Issue(db.Model):
    __tablename__ = "Issues"
    id = db.Column(db.Integer, primary_key=True)
    issue = db.Column(db.String(200), nullable=False)
    job_id = db.Column(db.Integer, nullable=True)

    def __init__(self, issue, job_id = None):
        self.issue = issue
        self.job_id = job_id
        if current_app:
            db.session.add(self)
            db.session.commit()
        if job_id is not None:
            from Classes.Jobs import Job
            job = Job.query.get(job_id)
            job.error_id = self.id
            db.session.commit()

    @classmethod
    def get_issues(cls):
        try:
            issues = cls.query.all()
            if issues:
                issues = [
                    {"id": issue.id, "issue": issue.issue} for issue in issues
                ]
                return {"success": True, "issues": issues}
            else: 
                return {"success": True, "issues": []}
            # return issues
        except SQLAlchemyError as e:
            if current_app:
                current_app.handle_errors_and_logging(e)
            return (
                jsonify({"error": "Failed to get issues. Database error"}),
                500,
            )

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
            return (
                jsonify({"error": "Failed to get issue. Database error"}),
                500,
            )

    @staticmethod
    def create_issue(issue, exception=None, job_id: int = None):
        try:
            from Discord_bot import sync_send_discord_embed
            Issue(issue, job_id)

            embed = discord.Embed(title='New Issue Created',
                                  description='A issue occurred when running a job',
                                  color=discord.Color.red())

            embed.add_field(name='Issue', value=issue, inline=False)
            if exception:
                import traceback
                exceptionFormatted = "".join(traceback.format_exception(None, exception, exception.__traceback__)).replace("  ", "‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ")
                embed.add_field(name='Exception', value=exceptionFormatted, inline=False)
            embed.timestamp = datetime.now()

            if Config['discord_enabled'] and issue.startswith("CODE ISSUE: Print Failed:"):
                sync_send_discord_embed(embed=embed)
            return {"success": True, "message": "Issue successfully created"}
        except SQLAlchemyError as e:
            if current_app:
                current_app.handle_errors_and_logging(e)
            return (
                jsonify({"error": "Failed to add job. Database error"}),
                500,
            )
        except Exception as e:
            if current_app:
                current_app.handle_errors_and_logging(e)
            return (
                jsonify({"error": "Failed to add job. Unknown error"}),
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
            if current_app:
                current_app.handle_errors_and_logging(e)
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
            if current_app:
                current_app.handle_errors_and_logging(e)
            return (
                jsonify({"error": "Failed to edit issue. Database error"}),
                500,
            )
