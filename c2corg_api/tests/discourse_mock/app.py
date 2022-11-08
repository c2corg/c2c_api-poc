import json
from flask import Flask, Response

app = Flask(__name__)


@app.route("/<path:path>", methods=["GET", "POST"])
def hello(path):
    return Response(response=json.dumps({}), headers={"content-type": "application/json; charset=utf-8"})
