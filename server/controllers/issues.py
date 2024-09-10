from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from models.issues import Issue

issue_bp = Blueprint("issues", __name__)

@issue_bp.route('/getissues', methods=["GET"])
def getIssues():
    try:
        # no need to assign to a variable, just return the result
        return jsonify(Issue.get_issues())
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@issue_bp.route('/createissue', methods=["POST"])
def createIssue(): 
    try:
        data = request.get_json()
        issue = data['issue']
        # no need to assign to a variable, just return the result
        return Issue.create_issue(issue)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@issue_bp.route('/deleteissue', methods=["POST"])
def deleteIssue():
    try:
        data = request.get_json()
        issue_id = data['issueid']
        # print(issue_id)
        # no need to assign to a variable, just return the result
        return Issue.delete_issue(issue_id)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@issue_bp.route('/editissue', methods=["POST"])
def editIssue():
    try:
        data = request.get_json()
        issue_id = data['issueid']
        issue_new = data['issuenew']
        # no need to assign to a variable, just return the result
        return Issue.edit_issue(issue_id, issue_new)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    