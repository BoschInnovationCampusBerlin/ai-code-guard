import json

import streamlit as st

from ai_code_guard.eu_ai_act_agent import query
from ai_code_guard.github import download_github_repo
from ai_code_guard.usage_extraction import extract_ai_usage

# Page configuration
st.set_page_config(page_title="AI Project Compliance Checker", layout="centered")

st.title("AI Code Guard")
st.markdown("_Analyze any public GitHub repo for AI usage and EU AI Act compliance._")

# Input section
repo_url = st.text_input("Enter GitHub Repository URL:")


# steps = st.container()


def st_progress_callback(message: str):
    """Append a message to the steps container."""

    with st.empty():
        print(message)
        st.markdown(message)


def process_repository(repo_url):
    st.info("Cloning repository...")
    repo_dir = download_github_repo(repo_url, status_callback=st_progress_callback)

    # summarize(repo_dir, st_progress_callback)

    st.info("Detecting AI use cases...")
    use_cases = extract_ai_usage(repo_dir, st_progress_callback)

    if use_cases:
        for use_case in use_cases:
            with st.expander(f"{use_case['use_case']}"):
                description = use_case.get('functionality') or use_case.get('description')
                if description:
                    st.markdown(f"{description}")
                # st.markdown(f"**Code Snippets:** {', '.join(use_case['code_snippets'])}")

        st.info("Checking EU AI Act compliance...")

        query_result = query(use_cases)

        report = query_result.json()
        print(json.dumps(report, indent=3))

        st_progress_callback(report["data"]["message"])
    else:
        st.warning("No AI use cases found in the repository.")


if st.button("Process"):
    process_repository(repo_url)
