import os
import sys
import time

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import main


def test_register_client_updates_state():
    client = main.socketio.test_client(main.app)
    assert client.is_connected()

    client.emit('register_client', {'clientId': 'integration-test-1'})
    # small delay to let server-side handler run
    time.sleep(0.1)

    assert 'integration-test-1' in main.state.clients
    client.disconnect()