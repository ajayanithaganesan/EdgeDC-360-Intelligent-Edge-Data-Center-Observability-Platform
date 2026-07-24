"""Thin optional wrapper around paho-mqtt.

The repository keeps MQTT wiring lightweight and optional so the local
tooling still works even before a broker is available.
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib
from typing import Any, Callable


class MQTTUnavailableError(RuntimeError):
    pass


def _load_paho() -> Any:
    try:
        return importlib.import_module("paho.mqtt.client")
    except ModuleNotFoundError as exc:  # pragma: no cover - runtime guard
        raise MQTTUnavailableError(
            "paho-mqtt is not installed. Install the project requirements to enable MQTT."
        ) from exc


@dataclass(slots=True)
class MQTTClient:
    client: Any

    @classmethod
    def create(cls, client_id: str) -> "MQTTClient":
        module = _load_paho()
        client = module.Client(client_id=client_id)
        return cls(client=client)

    def set_credentials(self, username: str, password: str) -> None:
        if username:
            self.client.username_pw_set(username, password)

    def connect(self, host: str, port: int, keepalive: int) -> None:
        self.client.connect(host, port, keepalive)

    def publish(self, topic: str, payload: str, qos: int = 0, retain: bool = False) -> None:
        result = self.client.publish(topic, payload=payload, qos=qos, retain=retain)
        result.wait_for_publish()

    def subscribe(self, topic: str, qos: int = 0) -> None:
        self.client.subscribe(topic, qos=qos)

    def on_message(self, callback: Callable[[Any, Any, Any], None]) -> None:
        self.client.on_message = callback

    def on_connect(self, callback: Callable[[Any, Any, Any, int], None]) -> None:
        self.client.on_connect = callback

    def loop_forever(self) -> None:
        self.client.loop_forever()

    def loop_start(self) -> None:
        self.client.loop_start()

    def loop_stop(self) -> None:
        self.client.loop_stop()
