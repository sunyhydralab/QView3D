from flask import Blueprint, jsonify, request
from Classes.Issues import Issue

issue_bp = Blueprint("issues", __name__)

@issue_bp.route('/getissues', methods=["GET"])
def getIssues():
    try:
        res = Issue.get_issues()
        return jsonify(res)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

@issue_bp.route('/getissuebyjob', methods=["POST"])
def getIssueByJob():
    try:
        data = request.get_json()
        job_id = data['jobId']
        return Issue.get_issue_by_job(job_id)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@issue_bp.route('/createissue', methods=["POST"])
def createIssue():
    try:
        data = request.get_json()
        return Issue.create_issue(
            issue=data.get('issue', None),
            job_id=data.get('job_id', None) or data.get('job', None),
            title=data.get('title', None),
            description=data.get('description', None),
            severity=data.get('severity', 'medium'),
            category=data.get('category', 'software'),
            fabricator_id=data.get('fabricator_id', None)
        )
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@issue_bp.route('/deleteissue', methods=["POST"])
def deleteIssue():
    try:
        data = request.get_json()
        issue_id = data.get('id') or data.get('issueid')
        if not issue_id:
            return jsonify({"error": "Issue ID is required"}), 400
        return Issue.delete_issue(issue_id)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@issue_bp.route('/editissue', methods=["POST"])
def editIssue():
    try:
        data = request.get_json()
        return Issue.edit_issue(data['issueid'], data['issuenew'])
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

@issue_bp.route('/updateissue', methods=["POST"])
def updateIssue():
    try:
        data = request.get_json()
        issue_id = data.get('id')
        if not issue_id:
            return jsonify({"error": "Issue ID is required"}), 400

        res = Issue.update_issue(
            issue_id,
            title=data.get('title'),
            description=data.get('description'),
            severity=data.get('severity'),
            category=data.get('category'),
            fabricator_id=data.get('fabricator_id'),
            job_id=data.get('job_id')
        )
        return jsonify(res)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

@issue_bp.route('/resolveissue', methods=["POST"])
def resolveIssue():
    try:
        data = request.get_json()
        issue_id = data.get('id')
        if not issue_id:
            return jsonify({"error": "Issue ID is required"}), 400
        return jsonify(Issue.resolve_issue(issue_id))
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
