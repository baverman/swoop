from httplib import HTTPConnection, HTTPSConnection

CONNECTION_TIMEOUT = 10

class ConnectionPool(object):
    def __init__(self, connection_timeout=None, debuglevel=None):
        self.connections = {}
        self.default_timeout = connection_timeout or CONNECTION_TIMEOUT
        self.debuglevel = debuglevel or 0

    def get_connection(self, host, port, secure, timeout=None):
        key = host, port, secure
        try:
            return self.connections[key]
        except KeyError:
            pass

        cls = HTTPSConnection if secure else HTTPConnection
        conn = self.connections[key] = cls(host, port, timeout=timeout or self.default_timeout)
        conn.debuglevel = self.debuglevel
        return conn
