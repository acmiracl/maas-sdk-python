import unittest

import miracl_api
from mock import patch
from oic.oauth2.message import Message


class TestBasics(unittest.TestCase):
    def setUp(self):
        self.api = miracl_api.MiraclClient("MOCK_CLIENT", "MOCK_SECRET",
                                           "http://nothing")

    def tearDown(self):
        pass

    @staticmethod
    def _generate_ok_response(data=None):
        if data is None:
            data = {}
        return Message().from_dict(data)

    @staticmethod
    def _generate_err_response(error, message=""):
        return Message().from_dict({
            "error": error,
            "error_message": message
        })

    def test_auth_request_url(self):
        session = {}
        url = self.api.authorization_request(session)
        self.assertIsNotNone(url)
        self.assertTrue(miracl_api.SESSION_MIRACL_STATE_KEY in session)
        self.assertTrue(miracl_api.SESSION_MIRACL_NONCE_KEY in session)

    def test_request_token_good(self):
        response = self._generate_ok_response({"access_token": "MOCK_TOKEN"})

        with patch("oic.oic.Client.do_access_token_request") as mock:
            mock.return_value = response
            session = {}
            self.api.authorization_request(session)
            query_string = "code=MOCK_CODE&state={0}".format(
                session[miracl_api.SESSION_MIRACL_STATE_KEY])
            token = self.api.request_access_token(session, query_string)
            self.assertEqual("MOCK_TOKEN", token)
