"""MIRA Multi-Agent System — Streamlit Client App."""
import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import compat  # noqa: F401 — Windows signal patch, must be before CrewAI
import streamlit as st
import json
import io
from pathlib import Path

from config import get_config, get_story_source, get_llm_config, get_collection_names

st.set_page_config(
    page_title="MIRA — Multi-Agent System",
    page_icon="🤖",
    layout="wide",
)

# ── Styles ──
st.markdown("""
<style>
    .block-container { max-width: 1100px; }
    .metric-card {
        background: #f0f2f6; border-radius: 10px;
        padding: 16px; text-align: center;
    }
    .metric-card h3 { margin: 0; font-size: 14px; color: #666; }
    .metric-card p { margin: 4px 0 0; font-size: 28px; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ── Header ──
st.title("🤖 MIRA — Multi-Agent System")
st.caption("Automated NFR and Test Scenario generation from User Stories")

# ── Sidebar: Configuration ──
with st.sidebar:
    st.header("⚙️ Configuration")

    cfg = get_config()

    st.subheader("Story Source")
    story_source = cfg.get("story_source", "json")
    st.info(f"Current source: **{story_source.upper()}**")
    if story_source == "jira":
        jira_cfg = cfg.get("providers", {}).get("jira", {})
        st.text(f"Project: {jira_cfg.get('project_key', '—')}")
        st.text(f"Issue type: {jira_cfg.get('issue_type', '—')}")

    st.divider()

    st.subheader("LLM")
    llm_cfg = cfg.get("llm", {})
    st.text(f"Model: {llm_cfg.get('model', '—')}")
    st.text(f"Temperature: {llm_cfg.get('temperature', '—')}")

    st.divider()

    st.subheader("Qdrant Collections")
    cols = get_collection_names()
    for label, name in cols.items():
        st.text(f"{label}: {name}")

    st.divider()

    st.subheader("Output")
    out_cfg = cfg.get("output", {})
    st.text(f"Directory: {out_cfg.get('dir', 'data')}")
    st.text(f"Generate DOCX: {out_cfg.get('generate_docx', True)}")


# ── Data directory ──
DATA_DIR = Path(__file__).parent / cfg.get("output", {}).get("dir", "data")


def load_json_safe(filepath):
    """Load JSON file or return None."""
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


# ── Main area ──
tab_run, tab_results, tab_stories = st.tabs(["▶️ Run Pipeline", "📊 Results", "📖 User Stories"])


# ── Tab: Run Pipeline ──
with tab_run:
    st.subheader("Execute the Multi-Agent Pipeline")
    st.markdown(
        "This will run the full CrewAI pipeline: "
        "**Integration → NFR Generation → Test Scenario Generation**"
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"- **Source:** `{story_source}`")
        st.markdown(f"- **Model:** `{llm_cfg.get('model', '—')}`")
    with col2:
        st.markdown(f"- **Output:** `{out_cfg.get('dir', 'data')}/`")
        st.markdown(f"- **DOCX:** `{out_cfg.get('generate_docx', True)}`")

    if st.button("🚀 Run Pipeline", type="primary", use_container_width=True):
        import subprocess

        project_dir = str(Path(__file__).parent)

        with st.status("Running MIRA pipeline...", expanded=True) as status:
            log_container = st.empty()
            log_lines = []

            try:
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                env["LITELLM_LOG"] = "WARNING"
                env["LITELLM_TELEMETRY"] = "False"

                process = subprocess.Popen(
                    [sys.executable, "crew_main.py"],
                    cwd=project_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=env,
                )

                for line in process.stdout:
                    line = line.rstrip()
                    if line:
                        log_lines.append(line)
                        # Keep last 30 lines for display
                        display_lines = log_lines[-30:]
                        log_container.code("\n".join(display_lines), language="text")

                process.wait()

                if process.returncode == 0:
                    st.write("✅ Pipeline complete!")
                    status.update(label="Pipeline finished!", state="complete")
                else:
                    status.update(label="Pipeline failed!", state="error")
                    st.error(f"Process exited with code {process.returncode}")

            except Exception as e:
                status.update(label="Pipeline failed!", state="error")
                st.error(f"Error: {e}")


# ── Tab: Results ──
with tab_results:
    st.subheader("Generated Results")

    def load_as_list(filepath):
        """Load JSON and ensure it returns a list of dicts."""
        data = load_json_safe(filepath)
        if data is None:
            return []
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict) and "raw_output" not in data:
            return [data]
        return []

    if not DATA_DIR.exists():
        st.info("No results yet. Run the pipeline first.")
    else:
        # Metrics row
        us_data = load_as_list(DATA_DIR / "user_stories.json")
        nfr_data = load_as_list(DATA_DIR / "nfrs.json")
        ts_data = load_as_list(DATA_DIR / "test_scenarios.json")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("User Stories", len(us_data))
        with c2:
            st.metric("NFRs", len(nfr_data))
        with c3:
            st.metric("Test Scenarios", len(ts_data))

        st.divider()

        # NFRs
        if nfr_data:
            with st.expander(f"📋 Non-Functional Requirements ({len(nfr_data)})", expanded=False):
                for nfr in nfr_data:
                    st.markdown(f"**[{nfr.get('id', '—')}] {nfr.get('title', '—')}**")
                    st.markdown(f"> {nfr.get('description', '—')}")
                    st.caption(
                        f"Category: {nfr.get('category', '—')} · "
                        f"Priority: {nfr.get('priority', '—')} · "
                        f"Source: {nfr.get('source_user_story_id', '—')}"
                    )
                    st.divider()
        else:
            st.warning("NFRs not generated yet or data is in unexpected format.")

        # Test Scenarios
        if ts_data:
            with st.expander(f"🧪 Test Scenarios ({len(ts_data)})", expanded=False):
                for ts in ts_data:
                    st.markdown(f"**[{ts.get('id', '—')}] {ts.get('title', '—')}**")
                    st.markdown(f"*Type:* {ts.get('test_type', '—')}")
                    st.markdown(f"> {ts.get('scenario_description', '—')}")
                    st.caption(
                        f"Expected: {ts.get('expected_outcome', '—')} · "
                        f"Priority: {ts.get('priority', '—')} · "
                        f"Source NFR: {ts.get('source_nfr_id', '—')}"
                    )
                    st.divider()
        else:
            st.warning("Test Scenarios not generated yet.")

        # Downloads
        st.divider()
        st.subheader("📥 Downloads")

        dl_cols = st.columns(4)

        complete_path = DATA_DIR / "complete_dataset.json"
        docx_path = DATA_DIR / "documento_requisitos.docx"

        with dl_cols[0]:
            if complete_path.exists():
                st.download_button(
                    "⬇️ Complete Dataset (JSON)",
                    data=complete_path.read_bytes(),
                    file_name="complete_dataset.json",
                    mime="application/json",
                )
            else:
                st.button("⬇️ Complete Dataset", disabled=True)

        with dl_cols[1]:
            if docx_path.exists():
                st.download_button(
                    "⬇️ Requirements (.docx)",
                    data=docx_path.read_bytes(),
                    file_name="documento_requisitos.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            else:
                st.button("⬇️ Requirements (.docx)", disabled=True)

        with dl_cols[2]:
            nfr_path = DATA_DIR / "nfrs.json"
            if nfr_path.exists():
                st.download_button(
                    "⬇️ NFRs (JSON)",
                    data=nfr_path.read_bytes(),
                    file_name="nfrs.json",
                    mime="application/json",
                )
            else:
                st.button("⬇️ NFRs (JSON)", disabled=True)

        with dl_cols[3]:
            ts_path = DATA_DIR / "test_scenarios.json"
            if ts_path.exists():
                st.download_button(
                    "⬇️ Test Scenarios (JSON)",
                    data=ts_path.read_bytes(),
                    file_name="test_scenarios.json",
                    mime="application/json",
                )
            else:
                st.button("⬇️ Test Scenarios (JSON)", disabled=True)


# ── Tab: User Stories ──
with tab_stories:
    st.subheader("Input User Stories")

    stories_path = Path(__file__).parent / "user_stories.json"
    stories = load_json_safe(stories_path)

    if stories:
        st.caption(f"Loaded {len(stories)} stories from `user_stories.json`")
        for s in stories:
            with st.expander(f"[{s.get('id', '—')}] {s.get('title', '—')}"):
                st.markdown(f"**Story:** {s.get('story', '—')}")
                ac = s.get("acceptance_criteria", [])
                if ac:
                    st.markdown("**Acceptance Criteria:**")
                    for criterion in ac:
                        st.markdown(f"- {criterion}")
                st.caption(
                    f"Priority: {s.get('priority', '—')} · "
                    f"Story Points: {s.get('story_points', '—')} · "
                    f"Persona: {s.get('persona', '—')}"
                )
    else:
        st.warning("No `user_stories.json` found.")
