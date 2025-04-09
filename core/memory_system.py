"""
Memory System - Vector embeddings and semantic search for context retrieval
"""
import os
import json
import torch
import numpy as np
from typing import List, Dict, Any, Optional, Callable, Union
from sentence_transformers import SentenceTransformer, util
import time

class MemorySystem:
    """Manages vector embeddings and semantic search for context retrieval"""
    
    def __init__(self, 
                 model_name: str = "all-MiniLM-L6-v2", 
                 index_path: str = "data/vector_store/vector_store.json",
                 logger: Optional[Callable] = None):
        """
        Initialize the memory system
        
        Args:
            model_name: Name of the sentence transformer model to use
            index_path: Path to the vector store JSON file
            logger: Optional logging function
        """
        self.model_name = model_name
        self.index_path = index_path
        self.log = logger or print
        
        self.log(f"[Memory] Initializing memory system with model: {model_name}")
        self.model = None
        self.index = []
        self.documents = []
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        
        # Try to load the model
        self.load_model()
        
        # Try to load the index
        self.load_index()
    
    def load_model(self) -> bool:
        """
        Load the embedding model
        
        Returns:
            True if model loaded successfully, False otherwise
        """
        try:
            self.log(f"[Memory] Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.log("[Memory] Model loaded successfully")
            return True
        except Exception as e:
            self.log(f"[Memory Error] Failed to load model: {e}")
            return False
    
    def embed_texts(self, texts: List[str]) -> List[torch.Tensor]:
        """
        Embed a list of texts
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of tensor embeddings
        """
        if not self.model:
            if not self.load_model():
                return []
                
        try:
            return self.model.encode(texts, convert_to_tensor=True)
        except Exception as e:
            self.log(f"[Memory Error] Failed to embed texts: {e}")
            return []
    
    def add_to_index(self, docs: List[str], metadata: List[Dict[str, Any]]) -> bool:
        """
        Add documents to the index
        
        Args:
            docs: List of document text strings
            metadata: List of metadata dictionaries
            
        Returns:
            True if documents were added successfully, False otherwise
        """
        if not docs or not metadata:
            self.log("[Memory Warning] No documents to add")
            return False
            
        if len(docs) != len(metadata):
            self.log("[Memory Error] Number of documents and metadata entries must match")
            return False
            
        try:
            # Get embeddings
            embeddings = self.embed_texts(docs)
            
            if not embeddings:
                return False
                
            # Add to index
            for emb, meta in zip(embeddings, metadata):
                if "timestamp" not in meta:
                    meta["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
                self.index.append(emb)
                self.documents.append(meta)
            
            self.log(f"[Memory] Added {len(docs)} documents to index")
            
            # Save updated index
            return self.save_index()
        except Exception as e:
            self.log(f"[Memory Error] Failed to add documents to index: {e}")
            return False
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the index for documents similar to the query
        
        Args:
            query: Search query string
            top_k: Number of results to return
            
        Returns:
            List of document metadata dictionaries
        """
        if not self.index:
            self.log("[Memory Warning] Index is empty")
            return []
            
        try:
            # Get query embedding
            query_vec = self.embed_texts([query])
            
            if not query_vec:
                return []
                
            # Calculate similarity scores
            scores = util.cos_sim(query_vec[0], torch.stack(self.index))[0]
            
            # Get top K results
            top_scores, top_indices = torch.topk(scores, k=min(top_k, len(scores)))
            
            # Return metadata for top matches
            results = []
            for i, score in zip(top_indices, top_scores):
                meta = self.documents[i]
                meta["score"] = float(score)  # Convert tensor to float for serialization
                results.append(meta)
                
            self.log(f"[Memory] Found {len(results)} matches for query: {query[:50]}...")
            return results
        except Exception as e:
            self.log(f"[Memory Error] Search failed: {e}")
            return []
    
    def save_index(self) -> bool:
        """
        Save the index to disk
        
        Returns:
            True if index saved successfully, False otherwise
        """
        if not self.index:
            self.log("[Memory Warning] No index to save")
            return False
            
        try:
            # Convert tensors to lists for JSON serialization
            data = [
                {
                    "embedding": emb.cpu().tolist(), 
                    "meta": meta
                } 
                for emb, meta in zip(self.index, self.documents)
            ]
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            
            # Save to file
            with open(self.index_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                
            self.log(f"[Memory] Index saved to {self.index_path}")
            return True
        except Exception as e:
            self.log(f"[Memory Error] Failed to save index: {e}")
            return False
    
    def load_index(self) -> bool:
        """
        Load the index from disk
        
        Returns:
            True if index loaded successfully, False otherwise
        """
        if not os.path.exists(self.index_path):
            self.log(f"[Memory] No index file found at {self.index_path}")
            return False
            
        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Clear current index
            self.index = []
            self.documents = []
            
            # Load index
            for item in data:
                self.index.append(torch.tensor(item["embedding"]))
                self.documents.append(item["meta"])
                
            self.log(f"[Memory] Loaded {len(self.index)} items from index")
            return True
        except Exception as e:
            self.log(f"[Memory Error] Failed to load index: {e}")
            return False
    
    def clear_index(self) -> bool:
        """
        Clear the index
        
        Returns:
            True if index cleared successfully, False otherwise
        """
        try:
            self.index = []
            self.documents = []
            
            # Remove the index file if it exists
            if os.path.exists(self.index_path):
                os.remove(self.index_path)
                
            self.log("[Memory] Index cleared")
            return True
        except Exception as e:
            self.log(f"[Memory Error] Failed to clear index: {e}")
            return False
            
    def add_file_to_index(self, file_path: str, 
                          content: Optional[str] = None, 
                          chunk_size: int = 1000, 
                          chunk_overlap: int = 200) -> bool:
        """
        Add a file to the index, optionally with chunking
        
        Args:
            file_path: Path to the file
            content: Optional file content if already read
            chunk_size: Size of chunks to split content into
            chunk_overlap: Overlap between chunks
            
        Returns:
            True if file added successfully, False otherwise
        """
        try:
            # Get file content if not provided
            if content is None:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    
            # Check if we should chunk based on content length
            if len(content) > chunk_size:
                self.log(f"[Memory] Chunking file {os.path.basename(file_path)} into smaller sections")
                return self._add_chunked_file(file_path, content, chunk_size, chunk_overlap)
            else:
                # Add as a single document
                meta = {
                    "source": os.path.basename(file_path),
                    "path": file_path,
                    "text": content,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                return self.add_to_index([content], [meta])
        except Exception as e:
            self.log(f"[Memory Error] Failed to add file {file_path}: {e}")
            return False
            
    def _add_chunked_file(self, file_path: str, content: str, 
                          chunk_size: int, chunk_overlap: int) -> bool:
        """
        Add a file to the index in chunks
        
        Args:
            file_path: Path to the file
            content: File content
            chunk_size: Size of chunks to split content into
            chunk_overlap: Overlap between chunks
            
        Returns:
            True if file added successfully, False otherwise
        """
        try:
            # Split into chunks
            chunks = []
            for i in range(0, len(content), chunk_size - chunk_overlap):
                chunk = content[i:i + chunk_size]
                if len(chunk) >= chunk_size / 2:  # Only add substantial chunks
                    chunks.append(chunk)
            
            # Create metadata for each chunk
            metadata = []
            for i, chunk in enumerate(chunks):
                meta = {
                    "source": os.path.basename(file_path),
                    "path": file_path,
                    "text": chunk,
                    "chunk": i + 1,
                    "total_chunks": len(chunks),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                metadata.append(meta)
                
            # Add chunks to index
            return self.add_to_index(chunks, metadata)
        except Exception as e:
            self.log(f"[Memory Error] Failed to chunk file {file_path}: {e}")
            return False
            
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the memory system
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "model": self.model_name,
            "index_path": self.index_path,
            "documents_count": len(self.documents),
            "sources": {},
            "last_updated": None
        }
        
        # Get unique sources and count
        for doc in self.documents:
            source = doc.get("source", "Unknown")
            if source in stats["sources"]:
                stats["sources"][source] += 1
            else:
                stats["sources"][source] = 1
                
        # Get last updated timestamp
        if self.documents:
            timestamps = [doc.get("timestamp") for doc in self.documents if "timestamp" in doc]
            if timestamps:
                stats["last_updated"] = max(timestamps)
                
        return stats