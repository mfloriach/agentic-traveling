from dataclasses import dataclass
from enum import StrEnum


class Permission(StrEnum):
    DOCUMENT_READ = "documents:read"
    DOCUMENT_WRITE = "documents:write"
    DOCUMENT_DELETE = "documents:delete"

    PAYMENT_READ = "payments:read"
    PAYMENT_REFUND = "payments:refund"


class Role(StrEnum):
    ANONYMOUS = "anonymous"
    EDITOR = "editor"
    ADMIN = "admin"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ANONYMOUS: frozenset(
        {
            Permission.DOCUMENT_READ,
        }
    ),
    Role.EDITOR: frozenset(
        {
            Permission.DOCUMENT_READ,
            Permission.DOCUMENT_WRITE,
            Permission.DOCUMENT_DELETE,
        }
    ),
}


@dataclass
class Principal:
    user_id: str
    role: Role
    permissions: frozenset[Permission]
    allowed_agent: frozenset[str]

    def can(self, permission: Permission) -> bool:
        return permission in self.permissions

    def can_use_agent(self, agent_name: str) -> bool:
        return agent_name in self.allowed_agent
