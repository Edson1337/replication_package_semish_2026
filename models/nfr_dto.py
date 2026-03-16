"""NFR DTO - contract for NFR data across the pipeline."""
from pydantic import BaseModel, Field
from typing import Optional


class NFRDTO(BaseModel):
    """Schema for Non-Functional Requirements.
    
    Matches the structure in experiments/basic-rag/results/nfrs.json.
    Used for Qdrant storage and downstream processing.
    """
    id: str = Field(..., description="NFR identifier (e.g. NFR-001)")
    title: str = Field(..., description="Short title of the NFR")
    description: str = Field(..., description="Full description of the requirement")
    acceptance_criteria: str = Field(default="", description="How to verify this NFR is met")
    priority: str = Field(default="Medium", description="Priority: Critical, High, Medium, Low")
    rationale: str = Field(default="", description="Why this NFR is needed, linked to user story")
    category: str = Field(default="General", description="NFR category (e.g. Performance, Security)")
    source_user_story_id: str = Field(..., description="ID of the source user story (e.g. US01)")
