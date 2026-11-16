"""Shared CP01 service-test helpers."""
from threading import Thread

from bilqis_mlx.control_plane import ControlPlaneService


def start_service(service: ControlPlaneService) -> Thread:
    thread = Thread(target=service.serve_forever, daemon=True)
    thread.start()
    return thread
