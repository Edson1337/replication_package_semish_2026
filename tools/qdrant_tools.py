from crewai.tools import BaseTool
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_qdrant_url, get_qdrant_api_key, get_embedding_model
from typing import Any, List, Optional, Dict
from pydantic import Field, PrivateAttr


class QdrantHandler:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QdrantHandler, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        qdrant_url = get_qdrant_url()
        qdrant_api_key = get_qdrant_api_key()
        
        if qdrant_url:
            self.client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            self.client = QdrantClient(host="localhost", port=6333)
            
        model_name = get_embedding_model()
        self.model = SentenceTransformer(model_name)
        self.vector_size = self.model.get_sentence_embedding_dimension()
        
    def ensure_collection(self, collection_name: str):
        collections = self.client.get_collections()
        existing_names = [c.name for c in collections.collections]
        
        if collection_name not in existing_names:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE)
            )

class QdrantSearchTool(BaseTool):
    name: str = "Search Vector DB"
    description: str = "Search for similar items (stories, NFRs, tests) in the vector database."
    collection_name: str = Field(..., description="Name of the collection to search in")
    
    def _run(self, query: str, limit: int = 5) -> str:
        handler = QdrantHandler()
        
        try:
            query_vector = handler.model.encode([query])[0]
            
            results = handler.client.query_points(
                collection_name=self.collection_name,
                query=query_vector.tolist(),
                limit=limit
            ).points
            
            formatted_results = []
            for res in results:
                payload = res.payload
                formatted_results.append(payload)
                
            return str(formatted_results)
            
        except Exception as e:
            return f"Error searching Qdrant: {str(e)}"

class QdrantAddTool(BaseTool):
    name: str = "Add to Vector DB"
    description: str = "Add items to the vector database. Expects a list of dictionaries."
    collection_name: str = Field(..., description="Name of the collection to add to")
    
    def _run(self, items: List[Dict[str, Any]]) -> str:
        handler = QdrantHandler()
        
        try:
            handler.ensure_collection(self.collection_name)
            
            texts = []
            for item in items:
                text_parts = []
                for k, v in item.items():
                    if isinstance(v, str) and k != "id": 
                        text_parts.append(f"{k}: {v}")
                    elif isinstance(v, list) and k == "acceptance_criteria":
                         text_parts.append(f"Acceptance Criteria: {'; '.join(v)}")
                texts.append(" | ".join(text_parts))
            
            embeddings = handler.model.encode(texts)
            
            points = []
            
            info = handler.client.get_collection(self.collection_name)
            start_id = info.points_count if info.points_count else 0
            
            for i, (item, embedding) in enumerate(zip(items, embeddings)):
                item['text'] = texts[i] # Store text representation
                point = PointStruct(
                    id=start_id + i,
                    vector=embedding.tolist(),
                    payload=item
                )
                points.append(point)
                
            handler.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            return f"Successfully added {len(items)} items to {self.collection_name}"
            
        except Exception as e:
            return f"Error adding to Qdrant: {str(e)}"
