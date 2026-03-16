from crewai import Task
from textwrap import dedent
from config import get_story_source, get_jira_config
import os
import json

class MiraTasks:
    def __init__(self):
        self.story_source = get_story_source()
        
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        self.nfr_prompt_path = os.path.join(base_path, "prompts", "rnf_prompt.txt")
        self.ts_prompt_path = os.path.join(base_path, "prompts", "test_scenarios_prompt.txt")
        
        # Load DTO schema as reference for normalization
        dto_path = os.path.join(base_path, "user_stories.json")
        self.dto_schema_example = ""
        if os.path.exists(dto_path):
            with open(dto_path, 'r', encoding='utf-8') as f:
                stories = json.load(f)
                if stories:
                    self.dto_schema_example = json.dumps(stories[0], indent=2, ensure_ascii=False)
        
        try:
            with open(self.nfr_prompt_path, 'r', encoding='utf-8') as f:
                self.nfr_prompt = f.read()
            with open(self.ts_prompt_path, 'r', encoding='utf-8') as f:
                self.ts_prompt = f.read()
        except FileNotFoundError:
             self.nfr_prompt = "Error: NFR Prompt file not found."
             self.ts_prompt = "Error: Test Scenario Prompt file not found."

    def fetch_requirements_task(self, agent):
        if self.story_source == "jira":
            jira_cfg = get_jira_config()
            return Task(
                description=dedent(f"""\
                    1. Use the 'search_stories' tool to fetch user stories from JIRA project '{jira_cfg["project_key"]}' (issue type: '{jira_cfg["issue_type"]}').
                    2. The tool will return stories already normalized to the standard DTO format.
                    3. Store each user story in the 'user_stories' vector collection using the 'Add to Vector DB' tool.
                       - Parse the returned JSON to pass a list of dictionaries to the tool.
                    4. Save the stories to a JSON file using the 'Save Results to JSON' tool.
                       - Pass the full JSON array as a string.
                    5. Return the full list of stories for the next agent to use.
                """),
                agent=agent,
                expected_output="A JSON list of user stories with id, title, story, acceptance_criteria, priority, story_points, persona, and feature."
            )
        else:
            return Task(
                description=dedent("""\
                    1. Read the user stories from 'user_stories.json' using the 'Read User Stories' tool.
                    2. Store each user story in the 'user_stories' vector collection using the 'Add to Vector DB' tool.
                       - Parse the content to pass a list of dictionaries to the tool.
                    3. Save the stories to a JSON file using the 'Save Results to JSON' tool.
                       - Pass the full JSON array as a string.
                    4. Return the full content of the user stories to be used by the next agent.
                """),
                agent=agent,
                expected_output="A JSON list of user stories with id, title, story, acceptance_criteria, priority, story_points, persona, and feature."
            )

    def normalize_stories_task(self, agent, context):
        """Normalize raw stories to the DTO schema (only needed for JIRA source)."""
        return Task(
            description=dedent(f"""\
                Validate and normalize the user stories from the previous task to match the standard DTO schema.
                
                EXPECTED DTO FORMAT (each story must have these fields):
                {self.dto_schema_example}
                
                INSTRUCTIONS:
                1. Verify each story has all required fields: id, title, story, acceptance_criteria, priority.
                2. Optional fields (story_points, persona, feature) should be kept if available, or set to null.
                3. Ensure 'acceptance_criteria' is always a list of strings.
                4. Ensure 'priority' is one of: High, Medium, Low.
                5. Return the validated list as a JSON array.
            """),
            agent=agent,
            context=context,
            expected_output="A validated JSON list of user stories conforming to the DTO schema."
        )

    def generate_nfrs_task(self, agent, context):
        prompt_content = self.nfr_prompt.replace("{user_stories}", "")
        
        return Task(
            description=dedent(f"""\
                Analyze the user stories provided in the context and generate Non-Functional Requirements (NFRs).
                
                PROMPT INSTRUCTIONS:
                {prompt_content}
                
                ADDITIONAL INSTRUCTIONS:
                1. Use the User Stories from the context (output of previous task) as the source.
                2. Each NFR must follow this schema:
                   - id: string (e.g. "NFR-001")
                   - title: string
                   - description: string
                   - acceptance_criteria: string
                   - priority: string (Critical, High, Medium, Low)
                   - rationale: string
                   - category: string (e.g. Performance, Security, General)
                   - source_user_story_id: string (e.g. "US01")
                3. SAVE the NFRs to the 'non_functional_requirements' collection using the 'Add to Vector DB' tool.
                4. SAVE the NFRs to a JSON file using the 'Save Results to JSON' tool.
                   - Pass the full JSON array as a string.
                5. Return the generated NFRs as a JSON array.
            """),
            agent=agent,
            context=context,
            expected_output="A JSON list of NFRs with id, title, description, acceptance_criteria, priority, rationale, category, and source_user_story_id."
        )

    def generate_test_scenarios_task(self, agent, context):
        prompt_content = self.ts_prompt.replace("{nfrs}", "")
        
        return Task(
            description=dedent(f"""\
                Create test scenarios for the Non-Functional Requirements (NFRs) provided in the context.
                
                PROMPT INSTRUCTIONS:
                {prompt_content}
                
                ADDITIONAL INSTRUCTIONS:
                1. Use the NFRs from the context (output of previous task) as the source.
                2. Each Test Scenario must follow this schema:
                   - id: string (e.g. "TS-001")
                   - title: string
                   - test_type: string (e.g. Performance, Security, Reliability)
                   - scenario_description: string
                   - expected_outcome: string
                   - priority: string (Critical, High, Medium, Low)
                   - source_nfr_id: string (e.g. "NFR-001")
                3. SAVE the scenarios to the 'test_scenarios' collection using the 'Add to Vector DB' tool.
                4. SAVE the scenarios to a JSON file using the 'Save Results to JSON' tool.
                   - Pass the full JSON array as a string.
                5. After saving, use the 'Generate Requirements Document' tool to create the .docx requirements document.
                6. Return the generated Test Scenarios as a JSON array.
            """),
            agent=agent,
            context=context,
            expected_output="A JSON list of Test Scenarios with id, title, test_type, scenario_description, expected_outcome, priority, and source_nfr_id."
        )
