"""EU AI Act handler."""

import os
import requests
import tempfile
from typing import Dict, List, Optional
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
import tiktoken
from app.utils.config import get_data_dir, get_embeddings
from app.utils.download_ai_act import download_eu_ai_act

class EUAIActHandler:
    """Handler for the EU AI Act.
    
    This class processes the EU AI Act and creates a FAISS vector store for efficient retrieval.
    Note: The vector store uses pickle for serialization, which is loaded with allow_dangerous_deserialization=True.
    This is safe because we're only loading files that were created by this application.
    """
    
    def __init__(self):
        """Initialize the handler."""
        self.data_dir = get_data_dir()
        self.ai_act_path = os.path.join(self.data_dir, "eu_ai_act.txt")
        self.vectorstore_path = os.path.join(self.data_dir, "vectorstores", "eu_ai_act")
        
        # Create directory for vector stores
        os.makedirs(os.path.dirname(self.vectorstore_path), exist_ok=True)
        
        # URL to the EU AI Act
        self.ai_act_url = "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32024R1689"
        
        # Initialize embeddings based on configuration
        self.embeddings = get_embeddings()
    
    def download_ai_act(self) -> str:
        """Download the EU AI Act if it doesn't exist locally.
        
        Returns:
            Path to the AI Act file.
        """
        if os.path.exists(self.ai_act_path):
            return self.ai_act_path
            
        try:
            # Use the dedicated module to download and process the EU AI Act
            from app.utils.download_ai_act import download_eu_ai_act
            print(f"Downloading EU AI Act from {self.ai_act_url}")
            download_eu_ai_act(self.ai_act_path)
            return self.ai_act_path
            
        except Exception as e:
            print(f"Error downloading EU AI Act: {e}")
            raise
    
    def process_ai_act(self) -> FAISS:
        """Process the EU AI Act and create a vector store.
        
        Returns:
            FAISS vector store containing the processed AI Act.
        """
        # Download the AI Act if necessary
        self.download_ai_act()
        
        # Check if vector store already exists
        if os.path.exists(self.vectorstore_path):
            try:
                # Load the existing vector store with allow_dangerous_deserialization=True
                # This is safe because we're loading our own files that we created
                return FAISS.load_local(
                    self.vectorstore_path, 
                    self.embeddings, 
                    allow_dangerous_deserialization=True
                )
            except Exception as e:
                print(f"Error loading vector store, creating a new one: {e}")
        
        # Load the AI Act
        with open(self.ai_act_path, 'r', encoding='utf-8') as f:
            ai_act_text = f.read()
        
        # Split the text into sections based on the structure of the EU AI Act
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,  # Larger chunks to capture more context
            chunk_overlap=200,  # More overlap to maintain context across chunks
            separators=["\n\nArticle", "\n\nTitle", "\nARTICLE ", "\nCHAPTER ", "\n\n", "\n", " ", ""]
        )
        
        # Create documents with improved metadata
        texts = text_splitter.split_text(ai_act_text)
        documents = []
        
        for i, text in enumerate(texts):
            # Extract article number or section title if available
            article_match = None
            section_title = None
            
            if "Article " in text:
                article_match = text.split("Article ")[1].split("\n")[0].strip()
            elif "ARTICLE " in text:
                article_match = text.split("ARTICLE ")[1].split("\n")[0].strip()
                
            if "Title " in text:
                section_title = text.split("Title ")[1].split("\n")[0].strip()
            elif "TITLE " in text:
                section_title = text.split("TITLE ")[1].split("\n")[0].strip()
                
            # Create metadata
            metadata = {
                "source": "EU AI Act",
                "chunk_id": i,
                "total_chunks": len(texts)
            }
            
            if article_match:
                metadata["article"] = article_match
                
            if section_title:
                metadata["title"] = section_title
                
            documents.append(Document(page_content=text, metadata=metadata))
        
        # Create vector store
        vectorstore = FAISS.from_documents(documents, self.embeddings)
        
        # Save vector store - generated by the application, safe to load with allow_dangerous_deserialization=True
        vectorstore.save_local(self.vectorstore_path)
        
        return vectorstore
    
    def search_relevant_sections(self, query: str, k: int = 5) -> List[Document]:
        """Search for relevant sections in the AI Act.
        
        Args:
            query: The query to search for.
            k: Number of results to return.
            
        Returns:
            List of relevant document sections.
        """
        vectorstore = self.process_ai_act()
        results = vectorstore.similarity_search(query, k=k)
        return results
