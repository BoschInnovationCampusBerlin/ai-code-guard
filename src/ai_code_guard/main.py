import json

import streamlit as st

from ai_code_guard.eu_ai_act_agent import query
from ai_code_guard.github import download_github_repo
from ai_code_guard.summarize_project import summarize
from ai_code_guard.usage_extraction import extract_ai_usage

# Page configuration
st.set_page_config(page_title="AI Project Compliance Checker", layout="centered")

st.title("AI Code Guard")
st.markdown("_Analyze any public GitHub repo for AI usage and EU AI Act compliance._")

# Input section
repo_url = st.text_input("Enter GitHub Repository URL:")

steps = st.container()


def st_progress_callback(message: str):
    """Append a message to the steps container."""

    with steps:
        print(message)
        st.markdown(message)


def process_repository(repo_url):
    repo_dir = download_github_repo(repo_url, status_callback=st_progress_callback)

    # summarize(repo_dir, st_progress_callback)

    use_cases = extract_ai_usage(repo_dir, st_progress_callback)

    query_result = query(use_cases)

    st_progress_callback(query_result.json()['data']['message'])



if st.button("Process"):
    process_repository(repo_url)

    # # Define steps
    # steps = [
    #     "Downloading Repository",
    #     "Extracting Repository",
    #     "Summarizing Project",
    #     "Checking if AI is used",
    #     "Extracting and identifying types of AI usage",
    #     "Finding EU AI Act Use Cases",
    #     "Checking if EU AI Act applies",
    #     "Generating Compliance Report",
    # ]

    # # Initialize status containers with waiting text
    # status_containers = {step: st.empty() for step in steps}
    # for step in steps:
    #     with status_containers[step].container():
    #         st.subheader(f"**{step}**")
    #         st.write("Waiting for previous step...")

    # def show_running(step, message, function):
    #     with status_containers[step].container():
    #         st.subheader(f"**{step}**")
    #         st.badge("Running", color="blue")
    #         with st.spinner(f"{step} in progress..."):
    #             return function()

    # # Helper to update status
    # def show_result(step, message, success=True):
    #     if success:
    #         with status_containers[step].container():
    #             st.subheader(f"**{step}**")
    #             st.badge("Success", icon=":material/check:", color="green")
    #             st.expander("Details", expanded=True).write(message)
    #     else:
    #         with status_containers[step].container():
    #             st.subheader(f"**{step}**")
    #             st.badge("Error", color="red")
    #             st.write(message)
    #             st.stop()

    # # Step 1
    # def download_repository():
    #     time.sleep(2)
    #     return "Repository downloaded successfully."

    # step = steps[0]
    # with status_containers[step].container():
    #     result = show_running(step, "Downloading repository...", download_repository)

    # # After delay, show completed status
    # show_result(step, result, success=True if result else False)

    # # Step 2
    # def extract_repository():
    #     time.sleep(2)
    #     return "Repository extracted successfully."

    # step = steps[1]
    # with status_containers[step].container():
    #     result = show_running(step, "Extracting repository...", extract_repository)

    # # After delay, show completed status
    # show_result(step, result, success=True if result else False)
