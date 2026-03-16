"""Data output tool - saves pipeline results as JSON files."""
import json
import os
import sys
from crewai.tools import BaseTool
from pydantic import Field
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_config


def get_output_dir() -> Path:
    """Get the output directory from config."""
    cfg = get_config()
    output_dir = cfg.get("output", {}).get("dir", "data")
    base = Path(__file__).parent.parent
    path = base / output_dir
    path.mkdir(parents=True, exist_ok=True)
    return path


class SaveResultsTool(BaseTool):
    """Tool for saving pipeline results as JSON files."""
    name: str = "Save Results to JSON"
    description: str = (
        "Saves structured data as a JSON file in the output directory. "
        "Use this after generating user stories, NFRs, or test scenarios. "
        "Pass the data as a JSON string and specify the filename "
        "(e.g. 'user_stories', 'nfrs', 'test_scenarios')."
    )
    filename: str = Field(default="results", description="Base filename without extension")

    def _run(self, data: str) -> str:
        try:
            parsed = self._parse_json(data) if isinstance(data, str) else data
            
            output_dir = get_output_dir()
            filepath = output_dir / f"{self.filename}.json"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(parsed, f, indent=2, ensure_ascii=False)
            
            count = len(parsed) if isinstance(parsed, list) else 1
            return f"Successfully saved {count} items to {filepath}"
        except Exception as e:
            return f"Error saving results: {e}"

    @staticmethod
    def _parse_json(data: str):
        """Parse JSON with fallback for LLM-generated responses."""
        import re
        # Try direct parse first
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            pass
        
        # Try extracting JSON array from markdown code blocks or surrounding text
        patterns = [
            r'```(?:json)?\s*(\[[\s\S]*?\])\s*```',  # ```json [...] ```
            r'(\[[\s\S]*\])',                          # bare [...] 
            r'(\{[\s\S]*\})',                          # bare {...}
        ]
        for pattern in patterns:
            match = re.search(pattern, data)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    continue
        
        # Last resort: save as raw text
        return {"raw_output": data}


def save_complete_dataset():
    """Consolidate all individual JSONs into complete_dataset.json."""
    output_dir = get_output_dir()
    dataset = {}
    
    for key, filename in [
        ("user_stories", "user_stories.json"),
        ("nfrs", "nfrs.json"),
        ("test_scenarios", "test_scenarios.json"),
    ]:
        filepath = output_dir / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                dataset[key] = json.load(f)
        else:
            dataset[key] = []
    
    output_path = output_dir / "complete_dataset.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    return str(output_path)
