from enum import Enum


class TransferStatus(Enum):
    NOT_STARTED = "NOT_STARTED"
    FAILED = "FAILED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class SealedStatus(Enum):
    SEALED = "SEALED"
    UNSEALED = "UNSEALED"
    UNSEALING = "UNSEALING"
    PERMANENT_UNSEALED = "PERMANENT_UNSEALED"
