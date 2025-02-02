from abc import ABC, abstractmethod
from ..models.audit_record import AuditRecord  # Updated to relative import

class IAuditable(ABC):
    @abstractmethod
    def generate_audit_trail(self) -> AuditRecord:
        """
        Generates an audit log record.
        """
        raise NotImplementedError 