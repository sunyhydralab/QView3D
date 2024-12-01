from flask import Blueprint, jsonify, request
from models.issues import Issue

issue_bp = Blueprint("issues", __name__)

@issue_bp.route('/getissues', methods=["GET"])
def getIssues():
    try:
        res = Issue.get_issues()
        return jsonify(res)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@issue_bp.route('/createissue', methods=["POST"])
def createIssue(): 
    try:
        data = request.get_json()
        issue = data['issue']
        res = Issue.create_issue(issue)
        return res
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@issue_bp.route('/deleteissue', methods=["POST"])
def deleteIssue():
    try:
        data = request.get_json()
        issue_id = data['issueid']
        # print(issueid)
        res = Issue.delete_issue(issue_id)
        return res
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@issue_bp.route('/editissue', methods=["POST"])
def editIssue():
    try:
        data = request.get_json()
        issue_id = data['issueid']
        issue_new = data['issuenew']
        res = Issue.edit_issue(issue_id, issue_new)
        return res
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    