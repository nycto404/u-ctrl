import threading
import logging


class ServerState:
    """Hält serverseitigen Zustand statt globaler Variablen.

    Attributes:
        stream: die aktuell geöffnete Serial-Stream-Instanz oder None
        clients: dict mapping client_id -> sid
        rx_connected: bool
        _is_logging: bool (protected, use property)
    """

    def __init__(self):
        self.stream = None
        self.clients = {}
        self.rx_connected = False
        self._is_logging = False
        self._lock = threading.RLock()

    @property
    def is_logging(self):
        with self._lock:
            return self._is_logging

    @is_logging.setter
    def is_logging(self, value: bool):
        with self._lock:
            self._is_logging = bool(value)

