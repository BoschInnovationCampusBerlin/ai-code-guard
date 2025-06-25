"""Compliance analyzer to compare repository features with EU AI Act."""

import json
from typing import Dict, List, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from app.tools.eu_ai_act_handler import EUAIActHandler
from app.utils.config import get_model

class ComplianceAnalyzer:
    """Analyzer for repository compliance with EU AI Act."""
    
    def __init__(self):
        """Initialize the analyzer."""
        self.model = get_model()
        self.ai_act_handler = EUAIActHandler()
        
        # Define the analysis prompt template
        self.compliance_analysis_prompt = ChatPromptTemplate.from_template(
            """You are a technical compliance expert specializing in AI regulations,
            particularly the EU AI Act. Your task is to analyze a technical description
            of a software repository and identify which sections of the EU AI Act are relevant
            and may apply to this repository.
            
            First, here is the technical description of the repository:
            
            {repo_description}
            
            Next, here are relevant sections from the EU AI Act:
            
            {ai_act_sections}
            
            Based on the repository description and the EU AI Act sections provided, perform a
            detailed analysis to:
            
            1. Identify whether the repository implements AI systems as defined by the EU AI Act
            2. Determine if any AI capabilities fall under prohibited practices (Article 5)
            3. Assess if the AI system would be classified as high-risk (Article 6)
            4. Identify specific requirements that would apply to the system
            5. Recommend compliance measures that should be implemented
            
            Format your response as a structured compliance analysis with the following sections:
            1. AI System Classification
            2. Applicable EU AI Act Sections
            3. Compliance Requirements
            4. Recommended Actions
            
            Be specific in your analysis, citing relevant sections of the EU AI Act and connecting them
            directly to the technical features described in the repository.
            """
        )
    
    def analyze_compliance(self, repo_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze repository compliance with EU AI Act.
        
        Args:
            repo_analysis: Analysis of the repository.
            
        Returns:
            Compliance analysis results.
        """
        repo_description = repo_analysis.get("repository_summary", "")
        
        # Search for relevant sections in the EU AI Act
        relevant_sections = self.ai_act_handler.search_relevant_sections(
            repo_description, k=5
        )
        
        # Format the relevant sections
        formatted_sections = "\n\n".join([
            f"Section: {doc.page_content}\nSource: {doc.metadata.get('source', 'EU AI Act')}"
            for doc in relevant_sections
        ])
        
        # Define the chain for compliance analysis
        chain = (
            {"repo_description": lambda _: repo_description, 
             "ai_act_sections": lambda _: formatted_sections}
            | self.compliance_analysis_prompt
            | self.model
            | StrOutputParser()
        )
        
        # Execute the chain
        compliance_analysis = chain.invoke({})
        
        return {
            "compliance_analysis": compliance_analysis,
            "relevant_sections": [doc.page_content for doc in relevant_sections]
        }
