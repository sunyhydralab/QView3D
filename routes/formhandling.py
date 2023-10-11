from flask import Blueprint, render_template, request, redirect, url_for

formhandling_bp = Blueprint('formhandling', __name__)

@formhandling_bp.route('/submitbot', methods=['POST'])
def submitbot(): 
    if request.method == 'POST':
        model = request.form['botmodel']
        buildVolume = request.form['length'] + " " + request.form['width'] + request.form['width']
        firmware = request.form['firmware']
        materials = request.form['materials']
        notes = request.form['notes']
        