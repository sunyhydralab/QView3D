from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy.sql import text  # Import text from sqlalchemy.sql
from database import read

formhandling_bp = Blueprint('formhandling', __name__)

# This is a form to register your bots. 
@formhandling_bp.route('/submitbot', methods=['GET', 'POST'])
def submitbot(): 
    if request.method == 'POST':
        model = request.form['botmodel']
        buildVolume = request.form['length'] + " " + request.form['width'] + request.form['width']
        firmware = request.form['firmware']
        materials = request.form['materials']
        notes = request.form['notes']
        read.query_supported_printers()
        return "model + buildVolume + firmware + materials + notes"
        