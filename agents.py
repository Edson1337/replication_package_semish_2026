from crewai import Agent
from tools.file_tools import FileReadTool
from tools.qdrant_tools import QdrantSearchTool, QdrantAddTool
from tools.data_output import SaveResultsTool
from tools.doc_generator import DocGeneratorTool
from config import get_story_source, get_collection_names

class MiraAgents:
    def __init__(self, llm=None, jira_tools=None):
        self.llm = llm
        self.story_source = get_story_source()

        # Story retrieval tools
        self.jira_tools = jira_tools or []
        self.file_read_tool = FileReadTool()
        
        # Qdrant tools (collection names from config.yaml)
        cols = get_collection_names()
        self.story_add_tool = QdrantAddTool(collection_name=cols["user_stories"])
        self.nfr_add_tool = QdrantAddTool(collection_name=cols["nfrs"])
        self.test_add_tool = QdrantAddTool(collection_name=cols["test_scenarios"])
        self.story_search_tool = QdrantSearchTool(collection_name=cols["user_stories"])
        self.nfr_search_tool = QdrantSearchTool(collection_name=cols["nfrs"])

        # Data output tools
        self.save_stories_tool = SaveResultsTool(filename="user_stories")
        self.save_nfrs_tool = SaveResultsTool(filename="nfrs")
        self.save_scenarios_tool = SaveResultsTool(filename="test_scenarios")
        self.doc_generator_tool = DocGeneratorTool()

    def _get_story_tools(self):
        """Get appropriate tools based on story_source config."""
        if self.story_source == "jira" and self.jira_tools:
            return self.jira_tools + [self.story_add_tool, self.save_stories_tool]
        return [self.file_read_tool, self.story_add_tool, self.save_stories_tool]

    def integration_agent(self):
        source_desc = "JIRA project" if self.story_source == "jira" else "JSON file"
        return Agent(
            role='Systems Integration Specialist',
            goal=f'Retrieve requirements and user stories from external sources ({source_desc}) and normalize them for processing.',
            backstory=(
                "You are an expert in system integrations. "
                "Your job is to interface with external tools (like JIRA, ClickUp, or local files), "
                "extract the required data, "
                "and ensure they are correctly identified, normalized to a standard format, "
                "and ready for the team to use."
            ),
            tools=self._get_story_tools(),
            llm=self.llm,
            verbose=True
        )

    def nfr_specialist_agent(self):
        return Agent(
            role='Non-Functional Requirements Specialist',
            goal='Generate comprehensive Non-Functional Requirements (NFRs) based on user stories.',
            backstory=(
                "You are a Senior System Architect with deep knowledge of system quality attributes "
                "like Performance, Security, and Scalability. "
                "You analyze functional requirements (User Stories) and derive the necessary technical constraints (NFRs)."
            ),
            tools=[self.nfr_add_tool, self.save_nfrs_tool],
            llm=self.llm,
            verbose=True
        )

    def qa_engineer_agent(self):
        return Agent(
            role='QA Engineer',
            goal='Generate detailed Test Scenarios from NFRs.',
            backstory=(
                "You are a meticulous Quality Assurance Engineer. "
                "You take Non-Functional Requirements and translate them into actionable test scenarios "
                "to ensure the system meets its quality goals."
            ),
            tools=[self.test_add_tool, self.save_scenarios_tool, self.doc_generator_tool],
            llm=self.llm,
            verbose=True
        )
