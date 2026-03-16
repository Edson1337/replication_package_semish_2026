from crewai.tools import BaseTool
import json
import os

class FileReadTool(BaseTool):
    name: str = "Read User Stories"
    description: str = (
        "Reads user stories from a JSON file. "
        "Useful for the Story Retriever agent to fetch requirements."
    )
    file_path: str = "user_stories.json"

    def _run(self) -> str:
        try:
            if not os.path.exists(self.file_path):
                 return f"Error: File {self.file_path} not found."
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            return json.dumps(content, indent=2)
        except Exception as e:
            return f"Error reading file: {str(e)}"
