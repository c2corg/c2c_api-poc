from flask import Flask
from flask_camp import RestApi

app = Flask(__name__)
api = RestApi(app=app)
