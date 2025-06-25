"""EU AI Act handler."""

import os
import requests
import tempfile
import time
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
        
        # Load the EU AI Act
        with open(self.ai_act_path, 'r', encoding='utf-8') as f:
            ai_act_text = f.read()
        
        # Split the text into logical sections (articles, chapters) for more effective chunking
        logical_sections = self._split_into_logical_sections(ai_act_text)
        
        # Process each logical section with more appropriate chunk sizes
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # Smaller chunks to avoid API limits
            chunk_overlap=100,  # Still maintain context across chunks
            separators=["\n\nArticle", "\n\nTitle", "\nARTICLE ", "\nCHAPTER ", "\n\n", "\n", " ", ""]
        )
        
        all_documents = []
        
        for section_idx, section in enumerate(logical_sections):
            # Split section into smaller chunks
            texts = text_splitter.split_text(section)
            section_documents = []
            
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
                    "section_id": section_idx,
                    "total_chunks": len(texts)
                }
                
                if article_match:
                    metadata["article"] = article_match
                    
                if section_title:
                    metadata["title"] = section_title
                    
                section_documents.append(Document(page_content=text, metadata=metadata))
            
            # Add this section's documents to our collection
            all_documents.extend(section_documents)
        
        # Process documents in batches to avoid rate limiting
        return self._create_vectorstore_in_batches(all_documents)
    
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
    
    def _split_into_logical_sections(self, text: str) -> List[str]:
        """Split the EU AI Act text into logical sections based on articles, chapters, etc.
        
        Args:
            text: The full text of the EU AI Act
            
        Returns:
            List of text sections
        """
        import re
        
        # Look for major section dividers in the document
        section_markers = [
            r'CHAPTER \w+', r'Chapter \w+',
            r'ARTICLE \d+', r'Article \d+',
            r'TITLE \w+', r'Title \w+',
            r'ANNEX \w+', r'Annex \w+',
            r'SECTION \d+', r'Section \d+'
        ]
        
        # Combine regex patterns
        combined_pattern = '|'.join([f'({pattern})' for pattern in section_markers])
        
        # Find all section starts
        matches = list(re.finditer(combined_pattern, text))
        
        sections = []
        for i in range(len(matches)):
            start_pos = matches[i].start()
            # If this is the last match, go to the end of the document
            if i == len(matches) - 1:
                section_text = text[start_pos:]
            else:
                # Otherwise, go to the start of the next section
                end_pos = matches[i+1].start()
                section_text = text[start_pos:end_pos]
            
            # Only add non-empty sections
            if section_text.strip():
                sections.append(section_text)
        
        # Add the preamble (everything before the first match) if it exists
        if matches and matches[0].start() > 0:
            sections.insert(0, text[:matches[0].start()])
            
        # If no sections were found or the document is small, return the whole document
        if not sections:
            sections = [text]
            
        print(f"Split EU AI Act into {len(sections)} logical sections")
        return sections
            
    def _create_vectorstore_in_batches(self, documents: List[Document]) -> FAISS:
        """Process documents in batches to avoid rate limits.
        
        Args:
            documents: List of documents to process
            
        Returns:
            FAISS vector store
        """
        print(f"Creating vector store from {len(documents)} documents in batches")
        
        # Process in batches of a reasonable size
        batch_size = 20  # Adjust based on Azure rate limits
        delay_seconds = 3  # Delay between batches to respect rate limits
        
        # Initialize an empty vector store
        vectorstore = None
        
        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch_end = min(i + batch_size, len(documents))
            batch = documents[i:batch_end]
            
            print(f"Processing batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size} " +
                  f"(documents {i+1} to {batch_end})")
            
            # For the first batch, create the initial vector store
            if vectorstore is None:
                try:
                    vectorstore = FAISS.from_documents(batch, self.embeddings)
                except Exception as e:
                    print(f"Error processing batch: {e}")
                    # Wait longer and try again with a smaller batch if rate limited
                    print("Waiting longer due to rate limit...")
                    time.sleep(delay_seconds * 2)
                    
                    # Try with half the batch size
                    half_batch = batch[:len(batch)//2]
                    if half_batch:  # Ensure we have at least one document
                        vectorstore = FAISS.from_documents(half_batch, self.embeddings)
                        # Process the rest of this half-batch normally
                        for doc in batch[len(batch)//2:]:
                            try:
                                vectorstore.add_documents([doc])
                                time.sleep(0.5)  # Small delay between individual documents
                            except Exception as inner_e:
                                print(f"Skipping document due to error: {inner_e}")
            else:
                # For subsequent batches, add documents to the existing store
                try:
                    vectorstore.add_documents(batch)
                except Exception as e:
                    print(f"Error adding batch to vector store: {e}")
                    # If we hit a rate limit, process documents one by one with a delay
                    print("Processing documents individually...")
                    for doc in batch:
                        try:
                            time.sleep(1)  # Add delay between individual documents
                            vectorstore.add_documents([doc])
                        except Exception as inner_e:
                            print(f"Skipping document due to error: {inner_e}")
            
            # Wait between batches to avoid rate limiting
            if i + batch_size < len(documents):
                print(f"Waiting {delay_seconds} seconds before processing next batch...")
                time.sleep(delay_seconds)
        
        # Save vector store - generated by the application, safe to load with allow_dangerous_deserialization=True
        print("Saving vector store...")
        vectorstore.save_local(self.vectorstore_path)
        
        return vectorstore
