from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class Project:
    name: str
    id: UUID
    created_at_us: int


@dataclass(slots=True)
class PublicKey:
    pem: str
    created_at: datetime
    project_id: UUID
    id: UUID
