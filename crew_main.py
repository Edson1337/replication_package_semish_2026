import compat  # noqa: F401 — Windows signal patch, must be first
from crewai import Crew, Process, LLM
from agents import MiraAgents
from tasks import MiraTasks
from config import get_llm_config, get_story_source, get_jira_config, get_config
from tools.data_output import save_complete_dataset
from tools.doc_generator import generate_requirements_doc
import json


def run():
    print("🚀 Starting MIRA Multi-Agent System...")
    
    llm_cfg = get_llm_config()
    story_source = get_story_source()
    
    if not llm_cfg["api_key"]:
        raise ValueError("❌ LLM_API_KEY not found. Check your .env file.")

    print(f"   📖 Story source: {story_source.upper()}")
    print(f"   🤖 Model: {llm_cfg['model']}")
    if llm_cfg["base_url"]:
        print(f"   🔗 Base URL: {llm_cfg['base_url']}")
    
    llm_kwargs = {
        "model": llm_cfg["model"],
        "api_key": llm_cfg["api_key"],
        "temperature": llm_cfg["temperature"],
    }
    if llm_cfg["base_url"]:
        llm_kwargs["base_url"] = llm_cfg["base_url"]
    
    my_llm = LLM(**llm_kwargs)
    
    # Initialize JIRA MCP tools if needed
    jira_tools = []
    mcp_adapter = None
    
    if story_source == "jira":
        jira_cfg = get_jira_config()
        if not jira_cfg["url"]:
            raise ValueError("❌ JIRA_URL not found. Set story_source: json in config.yaml for local fallback.")
        print(f"   🔗 JIRA: {jira_cfg['url']}")
        
        from tools.jira_tools import get_jira_mcp_tools
        mcp_adapter = get_jira_mcp_tools()
    
    try:
        if mcp_adapter:
            with mcp_adapter as tools:
                jira_tools = tools
                _execute_crew(my_llm, jira_tools, story_source)
        else:
            _execute_crew(my_llm, jira_tools, story_source)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


def _execute_crew(my_llm, jira_tools, story_source):
    """Execute the CrewAI pipeline."""
    agents = MiraAgents(llm=my_llm, jira_tools=jira_tools)
    tasks = MiraTasks()
    
    integration_agent_var = agents.integration_agent()
    nfr_specialist = agents.nfr_specialist_agent()
    qa_engineer = agents.qa_engineer_agent()
    
    story_task = tasks.fetch_requirements_task(integration_agent_var)
    
    task_list = [story_task]
    
    if story_source == "jira":
        normalize_task = tasks.normalize_stories_task(integration_agent_var, [story_task])
        task_list.append(normalize_task)
        nfr_context = [normalize_task]
    else:
        nfr_context = [story_task]
    
    nfr_task = tasks.generate_nfrs_task(nfr_specialist, nfr_context)
    qa_task = tasks.generate_test_scenarios_task(qa_engineer, [nfr_task])
    
    task_list.extend([nfr_task, qa_task])
    
    crew = Crew(
        agents=[integration_agent_var, nfr_specialist, qa_engineer],
        tasks=task_list,
        process=Process.hierarchical,
        manager_llm=my_llm,
        verbose=True,
        memory=False  # We use Qdrant tools for storage/retrieval
    )
    
    result = crew.kickoff()
    
    print("\n\n########################")
    print("## Crew Execution Result ##")
    print("########################\n")
    print(result)
    
    # Post-pipeline: consolidate and generate docx
    _post_pipeline()


def _post_pipeline():
    """Consolidate results and generate .docx after crew execution."""
    
    print("\n📦 Consolidating results...")
    dataset_path = save_complete_dataset()
    print(f"   ✅ Complete dataset saved: {dataset_path}")
    
    cfg = get_config()
    if cfg.get("output", {}).get("generate_docx", True):
        print("📄 Generating requirements document...")
        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        model_name = cfg.get("llm", {}).get("model", "CrewAI Agents")
        output_dir = str(dataset_path).rsplit("complete_dataset.json", 1)[0]
        docx_path = output_dir + "documento_requisitos.docx"
        
        generate_requirements_doc(data, docx_path, model_name)
        print(f"   ✅ Document generated: {docx_path}")


if __name__ == "__main__":
    run()

