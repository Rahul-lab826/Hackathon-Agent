import enum

class EventStatus(str, enum.Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETE = "complete"
    ERROR = "error"

class AgentName(str, enum.Enum):
    BRAND = "brand"
    STRUCTURE = "structure"
    CONTENT = "content"
    MARKETING = "marketing"
    EMAIL = "email"
    EXECUTION = "execution"

class AgentStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"
