"""Request repository interface and default in-memory implementation export.

This shim satisfies imports that expect `src.infrastructure.repositories.request_repository`.
For now it simply re-exports `InMemoryRequestRepository` so other code can type-hint
against the interface path.
"""

from abc import ABC, abstractmethod
from typing import Protocol, Dict, Any


class IRequestRepository(Protocol):
    """Minimal protocol for request repositories."""

    async def save(self, request: Any) -> None:  # noqa: ANN401
        ...

    async def get(self, request_id: str) -> Dict[str, Any]:  # noqa: D401, ANN401
        ...


# Re-export the existing in-memory implementation so other modules can import consistently
try:
    from .in_memory_request_repository import InMemoryRequestRepository as _InMemory

    InMemoryRequestRepository = _InMemory  # noqa: N816
except ImportError:  # pragma: no cover – shouldn't happen in normal dev env
    InMemoryRequestRepository = None  # type: ignore
