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
            embeddings = self.model.encode(texts, convert_to_tensor=True)
            
            # Handle different return types from different model implementations
            if isinstance(embeddings, list):
                return embeddings
            elif isinstance(embeddings, torch.Tensor):
                # If it's a single tensor with shape [batch_size, embedding_dim]
                # Convert to list of tensors with shape [embedding_dim]
                return [embeddings[i] for i in range(embeddings.shape[0])]
            else:
                self.log(f"[Memory Warning] Unexpected embedding type: {type(embeddings)}")
                return []
                
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
            
            if len(embeddings) == 0:
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
            # Use utf-8-sig to handle UTF-8 BOM (Byte Order Mark)
            with open(self.index_path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
                
            # Clear current index
            self.index = []
            self.documents = []
            
            # Check if data is a list or dict
            if isinstance(data, list):
                # Load index (list format)
                for item in data:
                    if not isinstance(item, dict):
                        self.log(f"[Memory Warning] Invalid item format in index: {type(item)}")
                        continue
                    if "embedding" in item and "meta" in item:
                        self.index.append(torch.tensor(item["embedding"]))
                        self.documents.append(item["meta"])
                    else:
                        self.log(f"[Memory Warning] Missing embedding or meta in item")
            elif isinstance(data, dict):
                # Alternative format (dict with embeddings and documents)
                if "embeddings" in data and "documents" in data:
                    embeddings = data["embeddings"]
                    documents = data["documents"]
                    if len(embeddings) == len(documents):
                        for emb, doc in zip(embeddings, documents):
                            self.index.append(torch.tensor(emb))
                            self.documents.append(doc)
                    else:
                        self.log("[Memory Error] Mismatched lengths of embeddings and documents")
                        return False
                else:
                    self.log("[Memory Error] Invalid index format: missing embeddings or documents")
                    return False
            else:
                self.log(f"[Memory Error] Invalid index data type: {type(data)}")
                return False
                
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
        Add a file to the index in chunks using sentence-aware chunking
        
        Args:
            file_path: Path to the file
            content: File content
            chunk_size: Size of chunks to split content into
            chunk_overlap: Overlap between chunks
            
        Returns:
            True if file added successfully, False otherwise
        """
        try:
            # Get the file name for metadata
            file_name = os.path.basename(file_path)
            
            # Use the sentence-aware chunking method
            chunks = self._chunk_text(content, max_chunk_size=chunk_size, overlap=chunk_overlap)
            
            self.log(f"[Memory] Split file '{file_name}' into {len(chunks)} chunks")
            
            # Create metadata for each chunk
            metadata = []
            for i, chunk in enumerate(chunks):
                meta = {
                    "source": file_name,
                    "path": file_path,
                    "text": chunk,
                    "chunk": i + 1,
                    "total_chunks": len(chunks),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    # Add file extension as a hint about content type
                    "file_type": os.path.splitext(file_path)[1].lower(),
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
    
    def _chunk_text(self, text: str, max_chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks of maximum size"""
        chunks = []
        
        # If text is shorter than max chunk size, return as is
        if len(text) <= max_chunk_size:
            return [text]
        
        # Split into sentences to avoid breaking sentences
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed max_chunk_size
            if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
                # Add current chunk to chunks list
                chunks.append(current_chunk)
                
                # Start new chunk with overlap
                words = current_chunk.split()
                overlap_words = min(len(words), int(overlap / 4))  # Approx 4 chars per word
                overlap_text = " ".join(words[-overlap_words:]) if overlap_words > 0 else ""
                current_chunk = overlap_text + " " + sentence
            else:
                # Add sentence to current chunk
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def add_reflection(self, category: str, content: str, importance: float = 0.5) -> Optional[str]:
        """
        Add a reflection or insight to the memory system
        
        Args:
            category: Category of reflection (e.g., 'conversation', 'learning', 'user_preference')
            content: Text content of the reflection
            importance: Importance score (0.0-1.0) to prioritize in retrieval
            
        Returns:
            ID of the added reflection or None if failed
        """
        if not self.model:
            self.log("[Memory Warning] Cannot add reflection: model not loaded")
            return None
            
        try:
            # Generate a unique ID
            reflection_id = f"refl_{int(time.time())}_{category}"
            
            # Create metadata
            metadata = {
                "id": reflection_id,
                "source": "reflection",
                "category": category,
                "importance": importance,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "text": content
            }
            
            # Add to index
            success = self.add_to_index([content], [metadata])
            
            if success:
                self.log(f"[Memory] Added {category} reflection to memory: {content[:50]}...")
                return reflection_id
            else:
                return None
                
        except Exception as e:
            self.log(f"[Memory Error] Failed to add reflection: {e}")
            return None
        
    def get_context_for_query(self, query: str, max_tokens: int = 1500, 
                             top_k: int = 5, min_score: float = 0.3) -> str:
        """
        Get a formatted context string for a query from memory
        
        Args:
            query: Query to find context for
            max_tokens: Maximum approximate tokens to include in context
            top_k: Maximum number of results to include
            min_score: Minimum similarity score to include
        
        Returns:
            Formatted context string
        """
        # Search for relevant items
        results = self.search(query, top_k=top_k)
        
        if not results:
            return ""
            
        # Filter by minimum score
        results = [r for r in results if r.get("score", 0) >= min_score]
        
        if not results:
            return ""
            
        # Format the context
        context_parts = []
        total_length = 0
        char_per_token = 4  # Rough approximation
        max_chars = max_tokens * char_per_token
        
        for item in results:
            # Get text from the item
            text = item.get("text", "")
            if not text:
                continue
                
            # Extract metadata for context
            source = item.get("source", "Unknown")
            score = item.get("score", 0)
            
            # Format this item
            item_text = f"[Source: {source} (relevance: {score:.2f})]\n{text}\n"
            
            # Check if we've reached the max length
            if total_length + len(item_text) > max_chars:
                # Truncate if needed
                available_chars = max_chars - total_length
                if available_chars > 100:  # Only add if we can include meaningful content
                    item_text = item_text[:available_chars] + "..."
                    context_parts.append(item_text)
                break
                
            context_parts.append(item_text)
            total_length += len(item_text)
        
        return "\n".join(context_parts)

    def search_by_category(self, category: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve items from memory by category
        
        Args:
            category: Category to search for
            top_k: Maximum number of results to return
            
        Returns:
            List of items matching the category
        """
        if not self.documents:
            return []
            
        try:
            # Find all documents with matching category
            matches = [doc for doc in self.documents if doc.get("category") == category]
            
            # Sort by timestamp (newest first)
            matches.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # Limit to top_k
            return matches[:top_k]
                
        except Exception as e:
            self.log(f"[Memory Error] Failed to search by category: {e}")
            return []
    
    def export_memory(self, export_path: str) -> bool:
        """
        Export the memory system to a file
        
        Args:
            export_path: Path to export to
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            # Create data to export
            export_data = {
                "model_name": self.model_name,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "documents": self.documents,
                "embeddings": [emb.cpu().tolist() for emb in self.index]
            }
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            
            # Save to file
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)
                
            self.log(f"[Memory] Exported memory to {export_path}")
            return True
            
        except Exception as e:
            self.log(f"[Memory Error] Failed to export memory: {e}")
            return False
            
    def import_memory(self, import_path: str, merge: bool = False) -> bool:
        """
        Import memory from a file
        
        Args:
            import_path: Path to import from
            merge: Whether to merge with existing memory or replace
            
        Returns:
            True if import successful, False otherwise
        """
        if not os.path.exists(import_path):
            self.log(f"[Memory Error] Import file not found: {import_path}")
            return False
            
        try:
            # Load from file
            with open(import_path, "r", encoding="utf-8") as f:
                import_data = json.load(f)
                
            # Validate data
            if "documents" not in import_data or "embeddings" not in import_data:
                self.log(f"[Memory Error] Invalid memory export file: {import_path}")
                return False
                
            # Clear existing memory if not merging
            if not merge:
                self.index = []
                self.documents = []
                
            # Import data
            for emb_data, doc in zip(import_data["embeddings"], import_data["documents"]):
                emb = torch.tensor(emb_data)
                self.index.append(emb)
                self.documents.append(doc)
                
            self.log(f"[Memory] Imported {len(import_data['documents'])} items from {import_path}")
            
            # Save to index
            self.save_index()
            return True
            
        except Exception as e:
            self.log(f"[Memory Error] Failed to import memory: {e}")
            return False