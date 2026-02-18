from enum import Enum
from dataclasses import dataclass


@dataclass(frozen=True)
class Effect:
    pass


@dataclass(frozen=True)
class UpdateDocumentStatus(Effect):
    new_status: str


@dataclass(frozen=True)
class CreateApprovalStep(Effect):
    status: str


@dataclass(frozen=True)
class CreateAuditLog(Effect):
    action: str


class WorkflowEffect(Enum):
    CREATE_APPROVAL_STEP = "create_approval_step"
    CREATE_AUDIT_LOG = "create_audit_log"
