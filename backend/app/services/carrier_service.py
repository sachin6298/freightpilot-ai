"""Carrier adapter contract for future live API integrations.

No carrier API credentials or provider contract were included in the supplied
repository. This registry deliberately does not fabricate live offers. Add a
provider-specific adapter after obtaining its API documentation and credentials.
"""

from typing import Protocol, Any

from app.db.models import Shipment


class CarrierAdapter(Protocol):
    code: str
    display_name: str

    def fetch_quotes(self, shipment: Shipment) -> list[dict[str, Any]]:
        """Return normalized provider offers; each offer must identify its source."""
        ...


class CarrierRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, CarrierAdapter] = {}

    def register(self, adapter: CarrierAdapter) -> None:
        key = adapter.code.strip().lower()
        if not key or key in self._adapters:
            raise ValueError("Carrier adapter code must be non-empty and unique.")
        self._adapters[key] = adapter

    def get(self, code: str) -> CarrierAdapter | None:
        return self._adapters.get(code.strip().lower())

    def list(self) -> list[dict[str, str]]:
        return [
            {"code": adapter.code, "name": adapter.display_name, "status": "CONFIGURED"}
            for adapter in self._adapters.values()
        ]


carrier_registry = CarrierRegistry()
