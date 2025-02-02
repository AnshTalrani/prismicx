from abc import ABC, abstractmethod
from typing import Any
from models.service_metrics import ServiceMetrics  # Assuming ServiceMetrics is defined

class IServiceHealth(ABC):
    @abstractmethod
    def check_heartbeat(self) -> bool:
        pass

    @abstractmethod
    def get_metrics(self) -> ServiceMetrics:
        pass 