import time
import streamlit as st

# Page configuration
st.set_page_config(page_title="AI Project Compliance Checker", layout="centered")

st.title("AI Code Guard")
st.markdown("_Analyze any public GitHub repo for AI usage and EU AI Act compliance._")

# Input section
repo_url = st.text_input("Enter GitHub Repository URL:")

if st.button("Process"):
    # Define steps
    steps = [
        "Downloading Repository",
        "Extracting Repository",
        "Summarizing Project",
        "Checking if AI is used",
        "Extracting and identifying types of AI usage",
        "Finding EU AI Act Use Cases",
        "Checking if EU AI Act applies",
        "Generating Compliance Report"
    ]

    # Initialize status containers with waiting text
    status_containers = {step: st.empty() for step in steps}
    for step in steps:
        with status_containers[step].container():
            st.subheader(f"**{step}**")
            st.write("Waiting for previous step...")

    def show_running(step, message, function):
        with status_containers[step].container():
            st.subheader(f"**{step}**")
            st.badge("Running", color="blue")
            with st.spinner(f"{step} in progress..."):
                return function()

    # Helper to update status
    def show_result(step, message, success=True):
        if success:
            with status_containers[step].container():
                st.subheader(f"**{step}**")
                st.badge("Success", icon=":material/check:", color="green")
                st.expander("Details", expanded=True).write(message)
        else:
            with status_containers[step].container():
                st.subheader(f"**{step}**")
                st.badge("Error", color="red")
                st.write(message)
                st.stop()

    # Step 1
    def download_repository():
        time.sleep(2)
        return "Repository downloaded successfully."

    step = steps[0]
    with status_containers[step].container():
        result = show_running(step, "Downloading repository...", download_repository)

    # After delay, show completed status
    show_result(step, result, success=True if result else False)

    # Step 2
    def extract_repository():
        time.sleep(2)
        return "Repository extracted successfully."

    step = steps[1]
    with status_containers[step].container():
        result = show_running(step, "Extracting repository...", extract_repository)

    # After delay, show completed status
    show_result(step, result, success=True if result else False)
