#!/usr/bin/python
from flask import Flask, render_template
from decouple import config
from database import setup

app = Flask(__name__)

DB_HOST = config('DB_HOST')
DB_USER = config('DB_USER')
DB_PASSWORD = config('DB_PASSWORD')
DB_NAME = config('DB_NAME')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'


@app.route("/")
def main():
    return "Working!"

if __name__ == "__main__":
    setup.setup_database()
    app.run(port=8000, debug=True)
