from __future__ import print_function

from flask import Flask, redirect, session, request
from miracl_api import MiraclClient

import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s: %(message)s')

app = Flask(__name__)

miracl = MiraclClient(
    client_id="CLIENT_ID",
    client_secret="CLIENT_SECRET",
    redirect_uri="REDIRECT_URI")


@app.route("/")
def hello():
    if not miracl.is_authorized(session):
        return redirect("/auth")
    else:
        return "Welcome, {0}".format(miracl.get_email(session))


@app.route("/c2id")
def c2id():
    print(request.query_string)
    if miracl.validate_authorization(session, request.query_string) is not None:
        return redirect("/")
    return "Error"


@app.route("/auth")
def auth():
    return redirect(miracl.get_authorization_request_url(session))


app.secret_key = "ReplaceWithValidSecret"

if __name__ == "__main__":
    app.debug = True
    app.run()
