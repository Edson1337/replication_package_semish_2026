"""Test Scenario DTO - contract for test scenario data across the pipeline."""
from pydantic import BaseModel, Field


class TestScenarioDTO(BaseModel):
    """Schema for Test Scenarios.
    
    Matches the structure in experiments/basic-rag/results/test_scenarios.json.
    Used for Qdrant storage and downstream processing.
    """
    id: str = Field(..., description="Test scenario identifier (e.g. TS-001)")
    title: str = Field(..., description="Short title of the test scenario")
    test_type: str = Field(default="Functional", description="Type of test (e.g. Performance, Security)")
    scenario_description: str = Field(..., description="Detailed description of the test conditions")
    expected_outcome: str = Field(..., description="What should happen when the test passes")
    priority: str = Field(default="Medium", description="Priority: Critical, High, Medium, Low")
    source_nfr_id: str = Field(..., description="ID of the source NFR (e.g. NFR-001)")
