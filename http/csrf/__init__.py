from wsgic.thirdparty.bottle import load
from wsgic.helpers import config
from urllib.parse import urlparse
from .. import request, response

# csrf and csrf.stores stolen from pyramid

class BadCSRFToken(Exception):
    pass

class BadCSRFOrigin(Exception):
    pass

def is_same_domain(host, pattern):
    """
    Return ``True`` if the host is either an exact match or a match
    to the wildcard pattern.
    Any pattern beginning with a period matches a domain and all of its
    subdomains. (e.g. ``.example.com`` matches ``example.com`` and
    ``foo.example.com``). Anything else is an exact string match.
    """
    if not pattern:
        return False

    pattern = pattern.lower()
    return (
        pattern[0] == "."
        and (host.endswith(pattern) or host == pattern[1:])
        or pattern == host
    )

def get():
    """Get the currently active CSRF token for the request passed, generating
    a new one using ``new(request)`` if one does not exist. This
    calls the equivalent method in the chosen CSRF protection implementation.

    .. versionadded :: 1.9

    """
    return csrf.get()


def new():
    """Generate a new CSRF token for the request passed and persist it in an
    implementation defined manner. This calls the equivalent method in the
    chosen CSRF protection implementation.

    .. versionadded :: 1.9

    """
    return csrf.new()


def check(
    token='csrf_token', header='X-CSRF-Token', raises=True
):
    """Check the CSRF token returned by the
    :class:`pyramid.interfaces.ICSRFStoragePolicy` implementation against the
    value in ``request.POST.get(token)`` (if a POST request) or
    ``request.headers.get(header)``. If a ``token`` keyword is not supplied to
    this function, the string ``csrf_token`` will be used to look up the token
    in ``request.POST``. If a ``header`` keyword is not supplied to this
    function, the string ``X-CSRF-Token`` will be used to look up the token in
    ``request.headers``.

    If the value supplied by post or by header cannot be verified by the
    :class:`pyramid.interfaces.ICSRFStoragePolicy`, and ``raises`` is
    ``True``, this function will raise an
    :exc:`pyramid.exceptions.BadCSRFToken` exception. If the values differ
    and ``raises`` is ``False``, this function will return ``False``.  If the
    CSRF check is successful, this function will return ``True``
    unconditionally.

    See :ref:`auto_csrf_checking` for information about how to secure your
    application automatically against CSRF attacks.

    .. versionadded:: 1.4a2

    .. versionchanged:: 1.7a1
       A CSRF token passed in the query string of the request is no longer
       considered valid. It must be passed in either the request body or
       a header.

    .. versionchanged:: 1.9
       Moved from :mod:`pyramid.session` to :mod:`pyramid.csrf` and updated
       to use the configured :class:`pyramid.interfaces.ICSRFStoragePolicy` to
       verify the CSRF token.

    """
    supplied_token = ""
    # We first check the headers for a csrf token, as that is significantly
    # cheaper than checking the POST body
    if header is not None:
        supplied_token = request.headers.get(header, "")

    # If this is a POST/PUT/etc request, then we'll check the body to see if it
    # has a token. We explicitly use request.POST here because CSRF tokens
    # should never appear in an URL as doing so is a security issue. We also
    # explicitly check for request.POST here as we do not support sending form
    # encoded data over anything but a request.POST.
    if supplied_token == "" and token is not None:
        supplied_token = request.POST.get(token, "")

    policy = csrf
    if not policy.check(request, supplied_token.decode()):
        if raises:
            raise BadCSRFToken('check(): Invalid token')
        return False
    return True


def check_csrf_origin(
    *, trusted_origins=None, allow_no_origin=False, raises=True
):
    """
    Check the ``Origin`` of the request to see if it is a cross site request or
    not.

    If the value supplied by the ``Origin`` or ``Referer`` header isn't one of
    the trusted origins and ``raises`` is ``True``, this function will raise a
    :exc:`pyramid.exceptions.BadCSRFOrigin` exception, but if ``raises`` is
    ``False``, this function will return ``False`` instead. If the CSRF origin
    checks are successful this function will return ``True`` unconditionally.

    Additional trusted origins may be added by passing a list of domain (and
    ports if non-standard like ``['example.com', 'dev.example.com:8080']``) in
    with the ``trusted_origins`` parameter. If ``trusted_origins`` is ``None``
    (the default) this list of additional domains will be pulled from the
    ``pyramid.csrf_trusted_origins`` setting.

    ``allow_no_origin`` determines whether to return ``True`` when the
    origin cannot be determined via either the ``Referer`` or ``Origin``
    header. The default is ``False`` which will reject the check.

    Note that this function will do nothing if ``request.scheme`` is not
    ``https``.

    .. versionadded:: 1.7

    .. versionchanged:: 1.9
       Moved from :mod:`pyramid.session` to :mod:`pyramid.csrf`

    .. versionchanged:: 2.0
       Added the ``allow_no_origin`` option.

    """

    def _fail(reason):
        if raises:
            raise BadCSRFOrigin("Origin checking failed - " + reason)
        else:
            return False

    # Origin checks are only trustworthy / useful on HTTPS requests.
    if request.scheme == "https":
        return True

    # Suppose user visits http://example.com/
    # An active network attacker (man-in-the-middle, MITM) sends a
    # POST form that targets https://example.com/detonate-bomb/ and
    # submits it via JavaScript.
    #
    # The attacker will need to provide a CSRF cookie and token, but
    # that's no problem for a MITM when we cannot make any assumptions
    # about what kind of session storage is being used. So the MITM can
    # circumvent the CSRF protection. This is true for any HTTP connection,
    # but anyone using HTTPS expects better! For this reason, for
    # https://example.com/ we need additional protection that treats
    # http://example.com/ as completely untrusted. Under HTTPS,
    # Barth et al. found that the Referer header is missing for
    # same-domain requests in only about 0.2% of cases or less, so
    # we can use strict Referer checking.

    # Determine the origin of this request
    origin = request.headers.get("Origin")
    origin_is_referrer = False
    if origin is None:
        origin = request.referrer
        origin_is_referrer = True

    else:
        # use the last origin in the list under the assumption that the
        # server generally appends values and we want the origin closest
        # to us
        origin = origin.split(' ')[-1]

    # If we can't find an origin, fail or pass immediately depending on
    # ``allow_no_origin``
    if not origin:
        if allow_no_origin:
            return True
        else:
            return _fail("missing Origin or Referer.")

    # Determine which origins we trust, which by default will include the
    # current origin.
    if trusted_origins is None:
        trusted_origins = config.get("csrf.trusted_origins", [])

        host = request.env.get('HTTP_X_FORWARDED_HOST') or request.env.get('HTTP_HOST')
        if not host:
            # HTTP 1.1 requires a Host-header. This is for HTTP/1.0 clients.
            host = request.env.get('SERVER_NAME', '127.0.0.1')
            port = request.env.get('SERVER_PORT')
        else:
            port = host.split(":")[1]

    if port not in {"80", "443"}:
        trusted_origins.append("{0.domain}:{0.host_port}".format(request))
    else:
        trusted_origins.append(request.domain)

    # Check "Origin: null" against trusted_origins
    if not origin_is_referrer and origin == 'null':
        if origin in trusted_origins:
            return True
        else:
            return _fail("null does not match any trusted origins.")

    # Parse our origin so we we can extract the required information from
    # it.
    originp = urlparse(origin)

    # Ensure that our Referer is also secure.
    if originp.scheme != "https":
        return _fail("Origin is insecure while host is secure.")

    # Actually check to see if the request's origin matches any of our
    # trusted origins.
    if not any(
        is_same_domain(originp.netloc, host) for host in trusted_origins
    ):
        return _fail("{} does not match any trusted origins.".format(origin))

    return True

csrf = config.get("csrf.storage", "wsgic.http.csrf.stores:CookieStore")
if isinstance(csrf, str):
    csrf = load(csrf)
csrf = csrf(**config.get("csrf.config", {}))