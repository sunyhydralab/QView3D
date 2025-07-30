from config.db import db # Import the SQLAlchemy datebase instance
from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError

from datetime import datetime
import discord
from config.config import Config
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
    issue = db.Column(db.String(200), nullable=False) # Description of the issue
    job_id = db.Column(db.Integer, nullable=True) # Optional job ID associated with the issue

    def __init__(self, issue, job_id = None):

        """
        Creates a new Issue object and immediately commits it to the database.
        If job_id is provided, it updates the associated Job to link to this issue.
        """
        self.issue = issue
        self.job_id = job_id

        # Automatically save the issue to the database
        if current_app:
            db.session.add(self)
            db.session.commit()

        # If linked to a job, update the Job record with this issue ID
        if job_id is not None:
            from Classes.Jobs import Job
            job = Job.query.get(job_id)
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
            return (
                jsonify({"error": "Failed to get issue. Database error"}),
                500,
            )

    @staticmethod
    def create_issue(issue, exception=None, job_id: int = None):
        """
        Creates a new issue, stores it in the database, and sends a Discord notification.
        If `exception` is provided, details are included in the Discord message.
        """

        # Note: Confirm Discord is function correctly. 

        try:
            from app import sync_send_discord_embed
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
            return (
                jsonify({"error": "Failed to delete issue. Database error"}),
                500,
            )
    
    @classmethod
    def edit_issue(cls, issue_id, issueNew):
        """
        Updates the description of an existing issue.
        """
        
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
