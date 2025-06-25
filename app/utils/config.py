"""Configuration utilities for the application."""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, AzureOpenAI, AzureChatOpenAI

# Load environment variables
load_dotenv()

def get_openai_api_key():
    """Get OpenAI API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment")
    return api_key

def get_github_token():
    """Get GitHub token from environment if available."""
    token = os.getenv("GITHUB_TOKEN")
    return token  # Can be None for public repositories

def get_model():
    """Get the language model."""
    # Check if using Azure OpenAI
    use_azure = os.getenv("USE_AZURE", "false").lower() == "true"
    
    if use_azure:
        # Azure OpenAI configuration
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
        azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "hackathon-gpt-4.1")
        
        if not azure_api_key:
            raise ValueError("AZURE_OPENAI_API_KEY not found in environment")
        
        if not azure_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT not found in environment")
        
        from langchain_openai import AzureChatOpenAI
            
        # Use AzureChatOpenAI instead of AzureOpenAI to ensure we're using the chat completions API
        return AzureChatOpenAI(
            openai_api_version=azure_api_version,
            azure_deployment=azure_deployment,
            azure_endpoint=azure_endpoint,
            api_key=azure_api_key,
            temperature=0.2,
            streaming=True,
        )
    else:
        # Standard OpenAI configuration
        model_name = os.getenv("MODEL_NAME", "gpt-4o")
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
            
        return ChatOpenAI(
            model=model_name,
            temperature=0.2,
            streaming=True,
        )

def get_data_dir():
    """Get data directory."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(base_dir, "app", "data")
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    return data_dir

def get_embeddings():
    """Get embeddings model based on configuration."""
    # Check if using Azure for embeddings
    use_azure = os.getenv("USE_AZURE", "false").lower() == "true"
    
    if use_azure:
        from langchain_openai import AzureOpenAIEmbeddings
        
        # Check if we have specific embeddings endpoint configuration
        embeddings_endpoint = os.getenv("AZURE_EMBEDDINGS_ENDPOINT")
        
        if embeddings_endpoint:
            # Use separate embeddings configuration
            embeddings_api_key = os.getenv("AZURE_EMBEDDINGS_API_KEY")
            embeddings_api_version = os.getenv("AZURE_EMBEDDINGS_API_VERSION", "2023-05-15")
            embeddings_deployment = os.getenv("AZURE_EMBEDDINGS_DEPLOYMENT")
            
            if not embeddings_api_key:
                raise ValueError("AZURE_EMBEDDINGS_API_KEY not found in environment")
                
            if not embeddings_deployment:
                raise ValueError("AZURE_EMBEDDINGS_DEPLOYMENT not found in environment")
                
            print(f"Using dedicated Azure AI embeddings endpoint: {embeddings_endpoint}")
            return AzureOpenAIEmbeddings(
                azure_endpoint=embeddings_endpoint,
                api_version=embeddings_api_version,
                api_key=embeddings_api_key,
                azure_deployment=embeddings_deployment
            )
        else:
            # Fallback to using the same Azure OpenAI endpoint for embeddings
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            if not azure_endpoint:
                raise ValueError("AZURE_OPENAI_ENDPOINT not found in environment")
            
            # Extract the base URL from the endpoint
            import re
            
            base_url_match = re.match(r'(https://[^/]+)', azure_endpoint)
            if base_url_match:
                base_url = base_url_match.group(1)
            else:
                base_url = azure_endpoint
                
            azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
            azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
            # Use a text embedding model deployment
            azure_deployment = os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT", "text-embedding-ada-002")
            
            if not azure_api_key:
                raise ValueError("AZURE_OPENAI_API_KEY not found in environment")
                
            print(f"Using standard Azure OpenAI embeddings endpoint: {base_url}")
            return AzureOpenAIEmbeddings(
                azure_endpoint=base_url,
                api_version=azure_api_version,
                api_key=azure_api_key,
                azure_deployment=azure_deployment
            )
    else:
        # Standard OpenAI configuration
        from langchain_openai import OpenAIEmbeddings
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
            
        return OpenAIEmbeddings()
