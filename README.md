# Setup

Use `python setup.py` for setup. It uses python-setuptools.

Some dependencies require additional system packages to be installed.
For Ubuntu 14.04 dependencies are:

* `build-essential` (for compiling code in dependencies)
* `python-dev` or `python3-dev` (depending on python version used)
* `libssl-dev`
* `libffi-dev`
* `python-setuptools`

## Installation

`python setup.py install`

## Development setup

`python setup.py develop` will install package using symlink to source code.

## Tests

To run tests, use `python setup.py test`.

# Miracl API

## Details and usage

All interaction with API happens through `MiraclClient` object. Each
application needs to construct instance of `MiraclClient`.

Miracl API requires map-like object for storing state and additional data (it
should be preserved between calls to api). In this document it is called
`session`.

### Initialization
To start using Miracl API, `MiraclClient` should be initialized. It can be done
when needed or at application startup. This instance can be shared between
threads and is thread-safe.

```
client = MiraclClient(
    client_id="CLIENT_ID",
    client_secret="CLIENT_SECRET",
    redirect_uri="REDIRECT_URI")
```

`CLIENT_ID` and `CLIENT_SECRET` can be obtained from Miracl(unique per
application). `REDIRECT_URI` is URI of your application end-point that will be
responsible obtaining token. It should be the same as registered in Miracl
system for this client ID.

It is possible to override default issuer with `issuer` parameter.

### Status check and user data

To check if user session has token use `client.is_authorized(session)`. You can
 request additional user data with `client.get_email(session)` and
 `client.get_user_id(session)`. Both methods cache results into `session`. If
 `None` is returned, token is expired and client needs to be authorized once
 more to access required data.

Use `client.clear_user_info(session)` to drop cached user data (e-mail and
user id).

Use `client.clear_user_info(session, including_auth=True)` to clear user
authorization status.

### Authorization flow

Authorization flow depends on `mpad.js` browser library. To show login button:

* Put div with distinct ID where login button should be
* Create authorization URL by using
`client.get_authorization_request_url(session)`
* At the end of page body load `mpad.js` with parameters `data-authurl`
(authorization URL) and `data-element` (login button ID)

```
<script src="https://demo.dev.miracl.net/mpin/mpad.js" data-authurl="{{ auth_url }}" data-element="btmpin"></script>
```

After user
interaction with Miracl system  user will be sent to `redirect_uri` defined at
creation of `MiraclClient` object.

To complete authorization pass query string received on `redirect_uri` to
`client.validate_authorization(session,query_string)`. This method will return
`None` if user denied authorization and token if authorization succeeded. Token
is preserved in `session` so there is no need to save token elsewhere.

### Problems and exceptions

Each call to `MiraclClient` can raise `MiraclError`. It contains `message` and
 `exception` (optional, can be `None`). Usually `MiraclError` is raised when
 API call can't continue and it's best to redirect user to error page if
 `MiraclError` is raised. `MiraclError` can contain helpful messages when
 debugging.

`MiraclClient` uses Python logging package and can be configured to be verbose
for debugging purposes. Here is sample configuration for logging that will
output all debug information from `MiraclClient`:

```
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s: %(message)s')
```

Log levels used:

* `DEBUG` for all requests and retrieved data
* `INFO` for initial provider configuration
* `ERROR` when exception is raised

## Samples

Replace `CLIENT_ID`, `CLIENT_SECRET` and `REDIRECT_URI` with valid data from
https://m-pin.my.id/protected . Samples can be run after setup step is done.

### Flask

Flask sample depends on `python-flask`.