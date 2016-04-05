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
        return "<a href=\"/auth\">Login</a>"
    else:
        email = miracl.get_email(session)
        if email is None:
            return redirect("/auth")
        return ("Welcome, {0}.<br/>"
                "<a href=\"/refresh\">Refresh data</a><br/>"
                "<a href=\"/logout\">Log out</a>").format(email)


@app.route("/c2id")
def c2id():
    print(request.query_string)
    if miracl.validate_authorization(session,
                                     request.query_string) is not None:
        return redirect("/")
    return "Authorization problem. <a href=\"/auth\">Retry?</a>"


@app.route("/auth")
def auth():
    return redirect(miracl.get_authorization_request_url(session))


@app.route("/refresh")
def refresh():
    miracl.clear_user_info(session)
    return redirect("/")


@app.route("/logout")
def logout():
    miracl.clear_user_info(session, including_auth=True)
    return redirect("/")


app.secret_key = "ReplaceWithValidSecret"

if __name__ == "__main__":
    app.debug = True
    app.run()
