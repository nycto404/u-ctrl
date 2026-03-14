export function createSocketClient() {
    if (!window.io) {
        throw new Error('Socket.IO client is not available in the browser context.');
    }
    return window.io();
}
