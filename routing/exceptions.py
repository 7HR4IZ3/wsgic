class RouteError(Exception):
    """ This is a base class for all routing related exceptions """

class RouteReset(Exception):
    """ If raised by a plugin or request handler, the route is reset and all
        plugins are re-applied. """

class RouterUnknownModeError(RouteError):
    pass

class RouteSyntaxError(RouteError):
    """ The route parser found something not supported by this router. """

class RouteBuildError(RouteError):
    """ The route could not be built. """
