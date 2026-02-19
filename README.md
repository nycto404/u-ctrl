# u-ctrl
With this application it is possible to connect (automatically or manually) to a u-blox GNSS receiver. There is the option to enable the NAV-PVT message in case it is not enabled by default.
The NAV-PVT message needs to be enabled to show the position on the map. More features planned, WIP 🚧!
![alt text](assets/preview.png)

## Development

Run the unit tests:

```bash
python -m pip install -U pip
python -m pip install -r requirements.txt
pytest -q
```

## Docker

Build the image locally:

```bash
docker build -t u-ctrl:local .
```

Run the container (exposes port 5001):

```bash
docker run --rm -p 5001:5001 u-ctrl:local
```

To override the SocketIO async mode (e.g. `threading`):

```bash
docker run --rm -e SOCKETIO_ASYNC_MODE=threading -p 5001:5001 u-ctrl:local
```

CI: A GitHub Actions workflow runs tests and builds a Docker image on push/PR to the default branches.
