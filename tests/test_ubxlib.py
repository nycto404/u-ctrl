import sys
import os
import types

# Ensure project root is on sys.path so `app` package is importable during tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.library import ubxlib


class DummyPort:
    def __init__(self, device, description=""):
        self.device = device
        self.description = description


def test_list_available_serial_ports_no_ports(monkeypatch):
    monkeypatch.setattr(ubxlib.serial.tools.list_ports, 'comports', lambda: [])
    res = ubxlib.list_available_serial_ports()
    assert res == [[], []]


def test_list_available_serial_ports_with_ports(monkeypatch):
    ports = [DummyPort('COM1', 'desc1'), DummyPort('COM2', 'desc2')]
    monkeypatch.setattr(ubxlib.serial.tools.list_ports, 'comports', lambda: ports)
    res = ubxlib.list_available_serial_ports()
    assert res[1] == ['COM1', 'COM2']


def test_connect_receiver_success(monkeypatch):
    class FakeSerial:
        def __init__(self, port, timeout=1, baudrate=None):
            self._port = port

        def write(self, data):
            return None

        def read(self, n):
            return b'ROM BASE'

        def close(self):
            return None

        def __str__(self):
            return f'<FakeSerial {self._port}>'

    monkeypatch.setattr(ubxlib, 'Serial', FakeSerial)
    res = ubxlib.connect_receiver('COMX', '115200', socketio=None)
    assert res is not None
    assert res[0] == 'COMX'


def test_auto_connect_receiver_no_ports(monkeypatch):
    monkeypatch.setattr(ubxlib, 'list_available_serial_ports', lambda: [[], []])
    res = ubxlib.auto_connect_receiver(None)
    assert res is None


def test_poll_mon_ver(monkeypatch):
    class FakeParsed:
        def __init__(self):
            self.swVersion = b'sw\x00'
            self.hwVersion = b'hw\x00'
            self.extension_01 = b'a\x00'
            self.extension_02 = b'b\x00'
            self.extension_03 = b'c\x00'
            self.extension_04 = b'd\x00'
            self.extension_05 = b'e\x00'
            self.extension_06 = b'f\x00'

        def __str__(self):
            return 'MON-VER'

    class FakeUBXReader:
        def __init__(self, stream, protfilter=None):
            pass

        def read(self):
            return (b'', FakeParsed())

    monkeypatch.setattr(ubxlib, 'UBXReader', FakeUBXReader)
    class FakeStream:
        def write(self, data):
            return None
    res = ubxlib.poll_mon_ver(stream=FakeStream(), socketio=None)
    assert res and 'sw' in res[0]


def test_log_rx_output_emits_nav_pvt(monkeypatch):
    class FakeParsed:
        def __init__(self):
            self.identity = 'NAV-PVT'
            self.iTOW = 1
            self.year = 2020
            self.month = 1
            self.day = 1
            self.fixType = 3
            self.lat = 1
            self.lon = 2
            self.height = 3
            self.gSpeed = 4

        def __str__(self):
            return 'NAV-PVT'

    class FakeUBXReader:
        def __init__(self, stream, protfilter=None):
            pass

        def read(self):
            return (b'', FakeParsed())

    class FakeSocketIO:
        def __init__(self):
            self.emits = []

        def emit(self, evt, data):
            self.emits.append((evt, data))

        def sleep(self, t):
            return None

    monkeypatch.setattr(ubxlib, 'UBXReader', FakeUBXReader)
    sock = FakeSocketIO()

    state = {'called': 0}

    def is_logging():
        state['called'] += 1
        return state['called'] <= 1

    ubxlib.log_rx_output(stream=None, socketio=sock, is_logging=is_logging)
    assert any(e[0] == 'nav-pvt' for e in sock.emits)
