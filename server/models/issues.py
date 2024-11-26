import asyncio
import base64
from operator import or_
import os
import re

from models.db import db
from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, String, LargeBinary, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from flask import jsonify, current_app
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from tzlocal import get_localzone
from io import BytesIO
from werkzeug.datastructures import FileStorage
import time
import gzip
import discord
from models.config import Config

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
    def create_issue(cls, issue, exception=None):
        try:
            from app import sync_send_discord_embed
            
            new_issue = cls(issue)
            db.session.add(new_issue)
            db.session.commit()
            
            embed = discord.Embed(title='New Issue Created',
                                description='A issue occurred when running a job',
                                color=discord.Color.red())
            
            embed.add_field(name='Issue', value=issue, inline=False)
            if exception:
                import traceback
                embed.add_field(name='Exception', value="".join(traceback.format_exception(None, exception, exception.__traceback__)), inline=False)
            embed.timestamp = datetime.now()
            
            if Config['discord_enabled']:
                if issue.startswith("CODE ISSUE: Print Failed:"):
                    sync_send_discord_embed(embed=embed)
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
