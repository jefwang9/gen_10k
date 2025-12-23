"""Vector store for document embeddings."""
from typing import List, Dict, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import VECTOR_DB_DIR, EMBEDDING_MODEL, OPENAI_API_KEY, CHUNK_SIZE, CHUNK_OVERLAP


class VectorStore:
    """Manages vector embeddings and similarity search."""
    
    def __init__(self, company_ticker: str):
        self.company_ticker = company_ticker
        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            openai_api_key=OPENAI_API_KEY
        )
        self.collection_name = f"{company_ticker}_10k"
        
        # Initialize ChromaDB
        self.persist_directory = str(VECTOR_DB_DIR / company_ticker)
        # Create a persistent client
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Get or create the collection
        self.vector_store = Chroma(
            client=self.client,
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
        )
    
    def add_documents(self, documents: List[str], metadata: Optional[List[Dict]] = None):
        """
        Add documents to the vector store.
        
        Args:
            documents: List of document texts
            metadata: Optional metadata for each document
        """
        if metadata is None:
            metadata = [{"source": f"{self.company_ticker}_10k"} for _ in documents]
        
        # Split documents into chunks
        all_chunks = []
        all_metadata = []
        
        for i, doc in enumerate(documents):
            chunks = self.text_splitter.split_text(doc)
            all_chunks.extend(chunks)
            all_metadata.extend([
                {**metadata[i], "chunk_index": j, "total_chunks": len(chunks)}
                for j in range(len(chunks))
            ])
        
        # Add to vector store
        self.vector_store.add_texts(
            texts=all_chunks,
            metadatas=all_metadata
        )
    
    def similarity_search(self, query: str, k: int = 5) -> List[Dict]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of dictionaries with 'content' and 'metadata' keys
        """
        results = self.vector_store.similarity_search_with_score(query, k=k)
        
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score
            }
            for doc, score in results
        ]
    
    def clear(self):
        """Clear all documents from the vector store."""
        # Use the client to delete the collection if it exists
        self.client.delete_collection(name=self.collection_name)

        # Recreate the collection and the LangChain vector store wrapper
        self.vector_store = Chroma(
            client=self.client,
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
        )
