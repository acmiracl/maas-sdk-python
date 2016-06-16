from __future__ import unicode_literals

from flask import Flask, redirect, session, request, render_template, flash
from miracl_api import MiraclClient

import logging
import json

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s: %(message)s')


def read_configuration():
    config_file = open("miracl.json")
    config = json.load(config_file)
    config_file.close()
    return config


app = Flask(__name__)

miracl = MiraclClient(**read_configuration())


@app.route("/")
def hello():
    context = {
        'is_authorized': miracl.is_authorized(session)
    }

    if miracl.is_authorized(session):
        context['email'] = miracl.get_email(session)
        context['user_id'] = miracl.get_user_id(session)
    else:
        context['auth_url'] = miracl.get_authorization_request_url(session)
    return render_template('index.html', **context)


@app.route("/c2id")
def c2id():
    print(request.query_string)
    if miracl.validate_authorization(session,
                                     request.query_string.decode()) is not None:
        flash('Successfully logged in!', 'success')

        return redirect("/")

    flash('Login failed!', 'danger')

    return render_template('index.html', retry=True,
                           auth_url=miracl.get_authorization_request_url(
                               session))


@app.route("/refresh")
def refresh():
    miracl.clear_user_info(session)
    return redirect("/")


@app.route("/logout")
def logout():
    miracl.clear_user_info(session, including_auth=True)
    flash('User logged out!', 'info')
    return redirect("/")


app.secret_key = "ReplaceWithValidSecret"

if __name__ == "__main__":
    app.debug = True
    app.run(port=5000)
