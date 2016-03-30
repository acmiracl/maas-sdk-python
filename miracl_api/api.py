from __future__ import print_function

import json

from oic import rndstr
from oic.oic import Client
from oic.oic.message import RegistrationResponse, AuthorizationResponse, \
    AccessTokenResponse
from oic.utils.authn.client import CLIENT_AUTHN_METHOD
from oic.oauth2 import SUCCESSFUL

_issuer = "https://m-pin.my.id/c2id"


class MiraclClient(object):
    def __init__(self, client_id, client_secret, redirect_uri):
        super(MiraclClient, self).__init__()

        client = Client(client_authn_method=CLIENT_AUTHN_METHOD)

        self.provider_info = client.provider_config(issuer=_issuer)

        print(self.provider_info)

        self.info = {"client_id": client_id,
                     "client_secret": client_secret,
                     "redirect_uris": [redirect_uri]
                     }

    def _create_client(self, session):
        client = Client(client_authn_method=CLIENT_AUTHN_METHOD)
        client.handle_provider_config(self.provider_info, issuer=_issuer)
        client_reg = RegistrationResponse(**self.info)
        client.store_registration_info(client_reg)

        if "miracl_token" in session:
            access_token = AccessTokenResponse().from_dict(
                session["miracl_token"])

            client.registration_access_token = access_token

        return client

    def authorization_request(self, session):
        """ Returns redirect URL for authorization via M-Pin system
            :arg session mutable dictionary that contains session variables
        """
        client = self._create_client(session)

        if "miracl_state" not in session:
            session["miracl_state"] = rndstr()
        if "miracl_nonce" not in session:
            session["miracl_nonce"] = rndstr()

        args = {
            "client_id": client.client_id,
            "response_type": "code",
            "scope": ['openid', 'email', 'user_id', 'name'],
            "nonce": session["miracl_nonce"],
            "redirect_uri": client.registration_response["redirect_uris"][0],
            "state": session["miracl_state"]
        }

        auth_req = client.construct_AuthorizationRequest(request_args=args)
        print(auth_req)

        return auth_req.request(client.authorization_endpoint)

    def request_access_token(self, session, query_string):
        """Returns code that can be used to request access token"""
        client = self._create_client(session)

        response = client.parse_response(AuthorizationResponse,
                                         info=query_string,
                                         sformat="urlencoded")
        assert response["state"] == session["miracl_state"]

        args = {
            "code": response["code"],
            "redirect_uri": client.registration_response["redirect_uris"][0],
            "client_id": client.client_id,
            "client_secret": client.client_secret
        }

        resp = client.do_access_token_request(
            scope=['openid', 'email', 'user_id', 'name'],
            state=session["miracl_state"],
            request_args=args,
            authn_method="client_secret_basic"
        )

        session["miracl_token"] = resp.to_dict()

        return resp.to_dict()["access_token"] or None

    def check_token(self, session):
        if "miracl_token" not in session:
            return False

        client = self._create_client(session)

        if "access_token" not in client.registration_access_token:
            return False

        # noinspection PyUnresolvedReferences
        request = client.construct_UserInfoRequest(
            request_args={
                "access_token": client.registration_access_token[
                    "access_token"],
                "client_id": client.client_id,
                "client_secret": client.client_secret
            }
        ).request(client.userinfo_endpoint)

        response = client.http_request(url=request, method='GET')

        if response.status_code in SUCCESSFUL:
            return True

        return False

    def get_email(self, session):
        if "miracl_token" not in session:
            return None

        client = self._create_client(session)

        if "access_token" not in client.registration_access_token:
            return None

        # noinspection PyUnresolvedReferences
        request = client.construct_UserInfoRequest(
            request_args={
                "access_token": client.registration_access_token[
                    "access_token"],
                "client_id": client.client_id,
                "client_secret": client.client_secret
            }
        ).request(client.userinfo_endpoint)

        response = client.http_request(url=request, method='GET')

        if response.status_code in SUCCESSFUL:
            return json.loads(response.text)["sub"]

        return None
