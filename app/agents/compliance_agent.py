"""LangGraph agent workflow for EU AI Act compliance checking."""

import json
from typing import Dict, List, Any, Annotated, TypedDict
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from app.tools.github_handler import GitHubHandler
from app.tools.code_analyzer import CodeAnalyzer
from app.tools.compliance_analyzer import ComplianceAnalyzer
from app.tools.eu_ai_act_handler import EUAIActHandler
from app.utils.config import get_model

# Define the state for our workflow
class GraphState(TypedDict):
    """State for the compliance checking workflow."""
    repo_url: str
    branch: str
    repo_path: str
    repo_analysis: Dict[str, Any]
    compliance_analysis: Dict[str, Any]
    messages: List[Dict[str, Any]]
    current_step: str
    status: str
    error: str

class RepoNode:
    """Node for handling GitHub repository operations."""
    
    def __init__(self):
        """Initialize the node."""
        self.github_handler = GitHubHandler()
    
    def __call__(
        self, state: GraphState
    ) -> GraphState:
        """Process the state by downloading and extracting the repository.
        
        Args:
            state: Current workflow state.
            
        Returns:
            Updated state.
        """
        # Check if we're in an error state already
        if state["error"]:
            return state
            
        repo_url = state["repo_url"]
        branch = state.get("branch", "main")
        
        try:
            # Download and extract the repository
            repo_path = self.github_handler.download_repo(repo_url, branch)
            
            # Update the state
            return {
                **state,
                "repo_path": repo_path,
                "current_step": "analyze_repo",
                "status": "downloaded_repo",
                "messages": add_messages(
                    state["messages"],
                    {
                        "role": "system",
                        "content": f"Successfully downloaded repository from {repo_url} (branch: {branch}) to {repo_path}"
                    }
                )
            }
            
        except Exception as e:
            error_message = f"Error downloading repository: {str(e)}"
            return {
                **state,
                "error": error_message,
                "status": "error",
                "messages": add_messages(
                    state["messages"],
                    {
                        "role": "system",
                        "content": error_message
                    }
                )
            }

class AnalyzeRepoNode:
    """Node for analyzing the repository code."""
    
    def __init__(self):
        """Initialize the node."""
        self.code_analyzer = CodeAnalyzer()
    
    def __call__(
        self, state: GraphState
    ) -> GraphState:
        """Analyze the repository code.
        
        Args:
            state: Current workflow state.
            
        Returns:
            Updated state.
        """
        repo_path = state["repo_path"]
        
        # Check if we're in an error state already
        if state["error"]:
            return state
            
        try:
            # Analyze the repository
            repo_analysis = self.code_analyzer.analyze_repository(repo_path)
            
            # Update the state
            return {
                **state,
                "repo_analysis": repo_analysis,
                "current_step": "analyze_compliance",
                "status": "analyzed_repo",
                "messages": add_messages(
                    state["messages"],
                    {
                        "role": "system",
                        "content": "Successfully analyzed repository code"
                    }
                )
            }
            
        except Exception as e:
            error_message = f"Error analyzing repository: {str(e)}"
            return {
                **state,
                "error": error_message,
                "status": "error",
                "messages": add_messages(
                    state["messages"],
                    {
                        "role": "system",
                        "content": error_message
                    }
                )
            }

class AnalyzeComplianceNode:
    """Node for analyzing compliance with EU AI Act."""
    
    def __init__(self):
        """Initialize the node."""
        self.compliance_analyzer = ComplianceAnalyzer()
    
    def __call__(
        self, state: GraphState
    ) -> GraphState:
        """Analyze compliance with EU AI Act.
        
        Args:
            state: Current workflow state.
            
        Returns:
            Updated state.
        """
        # Check if we're in an error state already
        if state["error"]:
            return state
            
        repo_analysis = state["repo_analysis"]
        
        try:
            # Analyze compliance
            compliance_analysis = self.compliance_analyzer.analyze_compliance(repo_analysis)
            
            # Update the state
            return {
                **state,
                "compliance_analysis": compliance_analysis,
                "current_step": "end",
                "status": "completed",
                "messages": add_messages(
                    state["messages"],
                    {
                        "role": "system",
                        "content": "Successfully analyzed compliance with EU AI Act"
                    }
                )
            }
            
        except Exception as e:
            error_message = f"Error analyzing compliance: {str(e)}"
            return {
                **state,
                "error": error_message,
                "status": "error",
                "messages": add_messages(
                    state["messages"],
                    {
                        "role": "system",
                        "content": error_message
                    }
                )
            }

def create_workflow() -> StateGraph:
    """Create the workflow graph for compliance checking.
    
    Returns:
        StateGraph instance.
    """
    # Create the workflow
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("download_repo", RepoNode())
    workflow.add_node("analyze_repo", AnalyzeRepoNode())
    workflow.add_node("analyze_compliance", AnalyzeComplianceNode())
    
    # Define edges
    workflow.add_edge("download_repo", "analyze_repo")
    workflow.add_edge("analyze_repo", "analyze_compliance")
    workflow.add_edge("analyze_compliance", END)
    
    # Add error handling with conditional routing
    def handle_errors(state: GraphState) -> str:
        if state["error"]:
            return END
        return state["current_step"]
        
    # Add conditional edge from each node
    workflow.add_conditional_edges(
        "download_repo",
        lambda state: "error" if state["error"] else "analyze_repo"
    )
    workflow.add_conditional_edges(
        "analyze_repo", 
        lambda state: "error" if state["error"] else "analyze_compliance"
    )
    
    # Set the entry point
    workflow.set_entry_point("download_repo")
    
    return workflow

class ComplianceChecker:
    """Main class for checking compliance with EU AI Act."""
    
    def __init__(self):
        """Initialize the checker."""
        self.workflow = create_workflow().compile()
    
    def check_repository(self, repo_url: str, branch: str = "main") -> Dict[str, Any]:
        """Check a repository for compliance with EU AI Act.
        
        Args:
            repo_url: URL of the GitHub repository.
            branch: Branch to analyze.
            
        Returns:
            Results of the compliance check.
        """
        # Initialize state
        initial_state: GraphState = {
            "repo_url": repo_url,
            "branch": branch,
            "repo_path": "",
            "repo_analysis": {},
            "compliance_analysis": {},
            "messages": [],
            "current_step": "download_repo",
            "status": "starting",
            "error": ""
        }
        
        # Execute workflow
        result = self.workflow.invoke(initial_state)
        
        return result
