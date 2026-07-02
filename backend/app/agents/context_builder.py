"""
SharedContext — mutable data container passed down the agent execution pipeline.
Supports A2A (agent-to-agent) context propagation.
"""
from typing import Any, Optional
from pydantic import BaseModel


class SharedContext(BaseModel):
    # Event intake details
    theme: str
    domain: str
    duration_hours: int
    audience_type: str
    expected_participants: int
    location_type: str
    location_detail: Optional[str] = None
    special_requirements: Optional[str] = None

    # Agent outputs compiled incrementally
    brand_output: Optional[dict[str, Any]] = None
    structure_output: Optional[dict[str, Any]] = None
    content_output: Optional[dict[str, Any]] = None
    marketing_output: Optional[dict[str, Any]] = None
    email_output: Optional[dict[str, Any]] = None
    execution_output: Optional[dict[str, Any]] = None

    def serialize_brief(self) -> str:
        """Helper to print out a concise brief summary for LLM prompts."""
        return (
            f"Theme: {self.theme}\n"
            f"Domain: {self.domain}\n"
            f"Duration: {self.duration_hours} Hours\n"
            f"Audience: {self.audience_type}\n"
            f"Size: {self.expected_participants} builders\n"
            f"Logistics: {self.location_type} ({self.location_detail or 'no detail'})\n"
            f"Special Guidelines: {self.special_requirements or 'None'}"
        )
