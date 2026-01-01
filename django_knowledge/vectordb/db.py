import chromadb
from typing import Type, Dict, List, Optional


class ChromaDB:
    def __init__(self, path: Optional[str] = None):
        if path:
            self.client = chromadb.PersistentClient(path=path)
        else:
            self.client = chromadb.Client()
    
    def add(self, collection_name: str, embedding_generator_class: Type, 
            documents: List[str], metadatas: Optional[List[Dict]] = None) -> None:
        collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_generator_class()
        )
        
        collection.add(
            ids=[i for i in range(len(documents))],
            documents=documents,
            metadatas=metadatas
        )
    
    def get_collection(self, collection_name: str, embedding_generator_class: Type):
        return self.client.get_collection(
            name=collection_name,
            embedding_function=embedding_generator_class()
        )
    
    def list_collections(self) -> List[str]:
        return [collection.name for collection in self.client.list_collections()]
    
    def delete_collection(self, collection_name: str) -> None:
        self.client.delete_collection(name=collection_name)