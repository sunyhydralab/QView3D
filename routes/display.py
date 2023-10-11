from flask import Blueprint, render_template

display_bp = Blueprint('display', __name__)

@display_bp.route("/")
def main():
    return render_template("nav.html")

@display_bp.route('/registerbot')
def register():
    return render_template("registerbot.html")