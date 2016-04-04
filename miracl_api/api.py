from __future__ import unicode_literals

import json

from oic import rndstr
from oic.oic import Client, PyoidcError
from oic.oic.message import RegistrationResponse, AuthorizationResponse, \
    AccessTokenResponse
from oic.utils.authn.client import CLIENT_AUTHN_METHOD
from oic.oauth2 import SUCCESSFUL
import logging

_issuer = "https://m-pin.my.id/c2id"

_logger = logging.getLogger(__name__)

SESSION_MIRACL_TOKEN_KEY = "miracl_token"
SESSION_MIRACL_NONCE_KEY = "miracl_nonce"
SESSION_MIRACL_STATE_KEY = "miracl_state"


class MiraclClient(object):
    def __init__(self, client_id, client_secret, redirect_uri):
        super(MiraclClient, self).__init__()

        client = Client(client_authn_method=CLIENT_AUTHN_METHOD)

        self.provider_info = client.provider_config(issuer=_issuer)

        _logger.info("Received provider info: %s", self.provider_info)

        self.info = {"client_id": client_id,
                     "client_secret": client_secret,
                     "redirect_uris": [redirect_uri]
                     }

    def _create_client(self, session):
        client = Client(client_authn_method=CLIENT_AUTHN_METHOD)
        client.handle_provider_config(self.provider_info, issuer=_issuer)
        client_reg = RegistrationResponse(**self.info)
        client.store_registration_info(client_reg)

        if SESSION_MIRACL_TOKEN_KEY in session:
            access_token = AccessTokenResponse().from_dict(
                session[SESSION_MIRACL_TOKEN_KEY])

            client.registration_access_token = access_token

        return client

    def authorization_request(self, session):
        """ Returns redirect URL for authorization via M-Pin system
            :arg session mutable dictionary that contains session variables
        """

        client = self._create_client(session)

        if SESSION_MIRACL_STATE_KEY not in session:
            session[SESSION_MIRACL_STATE_KEY] = rndstr()
        if SESSION_MIRACL_NONCE_KEY not in session:
            session[SESSION_MIRACL_NONCE_KEY] = rndstr()

        args = {
            "client_id": client.client_id,
            "response_type": "code",
            "scope": ['openid', 'email', 'user_id', 'name'],
            "nonce": session[SESSION_MIRACL_NONCE_KEY],
            "redirect_uri": client.registration_response["redirect_uris"][0],
            "state": session[SESSION_MIRACL_STATE_KEY]
        }

        _logger.debug("authorization_request: %s", args)

        auth_req = client.construct_AuthorizationRequest(request_args=args)
        request = auth_req.request(client.authorization_endpoint)

        _logger.debug("authorization_request url: %s", request)

        return request

    def request_access_token(self, session, query_string):
        """Returns code that can be used to request access token or None if
        query string doesn't contain code and state.
        """
        if query_string is None or query_string == "":
            # Redirect without parameters means authorization was denied
            return None

        client = self._create_client(session)

        try:
            response = client.parse_response(AuthorizationResponse,
                                             info=query_string,
                                             sformat="urlencoded")
        except PyoidcError as e:
            raise MiraclError("Query string parse failed", e).log_exception()

        if response["state"] != session[SESSION_MIRACL_STATE_KEY]:
            raise MiraclError("Session state differs from response state")

        args = {
            "redirect_uri": client.registration_response["redirect_uris"][0],
            "client_id": client.client_id,
            "client_secret": client.client_secret
        }

        _logger.debug("request_access_token: %s", args)
        try:
            resp = client.do_access_token_request(
                scope=['openid', 'email', 'user_id', 'name'],
                state=session[SESSION_MIRACL_STATE_KEY],
                request_args=args,
                authn_method="client_secret_basic"
            )
        except PyoidcError as e:
            raise MiraclError("Access token request failed", e).log_exception()

        resp_dict = resp.to_dict()
        _logger.debug("request_access_token response: %s", resp_dict)

        if "access_token" in resp_dict:
            session[SESSION_MIRACL_TOKEN_KEY] = resp_dict
            return resp_dict["access_token"]
        else:
            return None

    def _request_user_info(self, session):
        if SESSION_MIRACL_TOKEN_KEY not in session:
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

        _logger.debug("user_info request: %s", request)
        try:
            response = client.http_request(url=request, method='GET')
        except PyoidcError as e:
            raise MiraclError("User info request failed", e).log_exception()

        _logger.debug("user_info response: %s %s", response, response.text)

        return response

    def check_token(self, session):
        response = self._request_user_info(session)
        if response is not None and response.status_code in SUCCESSFUL:
            return True

        return False

    def get_email(self, session):
        response = self._request_user_info(session)
        if response is not None and response.status_code in SUCCESSFUL:
            resp_json = json.loads(response.text)
            if "sub" not in resp_json:
                return None
            return resp_json["sub"]
        return None

    def get_user_id(self, session):
        response = self._request_user_info(session)
        if response is not None and response.status_code in SUCCESSFUL:
            resp_json = json.loads(response.text)
            if "sub" not in resp_json:
                return None
            return resp_json["sub"]
        return None


class MiraclError(Exception):
    def __init__(self, message, exception=None):
        if exception is None:
            Exception.__init__(self, message)
        else:
            Exception.__init__(
                self,
                "{0}, original exception: {1}".format(message, exception))

    def log_exception(self):
        _logger.error("Exception logged: {0}".format(self.message))
        return self
