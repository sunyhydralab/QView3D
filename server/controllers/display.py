from flask import Blueprint, render_template
from Classes import serialCommunication
from Classes.Printer import Printer 
from flask import request
import requests 
# from server.main import create_job

display_bp = Blueprint('display', __name__)

@display_bp.route("/", methods=['GET'])
def main():
    return "testing"

@display_bp.route('/selectport', methods=['GET'])
def selectPort():
    return "test"




