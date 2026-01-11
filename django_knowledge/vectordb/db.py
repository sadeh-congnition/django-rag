from dataclasses import dataclass
from typing import Dict, List, Optional, Type

import chromadb


@dataclass
class Doc:
    text: str
    id: str


class ChromaDB:
    def __init__(
        self,
        collection_name: str,
        embedding_generator: Type,
        path: Optional[str] = None,
    ):
        if path:
            self.client = chromadb.PersistentClient(path=path)
        else:
            self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(
            name=collection_name, embedding_function=embedding_generator
        )
        self.collection_name = collection_name

    def add(
        self,
        documents: List[Doc],
        metadatas: Optional[List[Dict]] = None,
    ) -> None:
        self.collection.add(
            ids=[d.id for d in documents],
            documents=[d.text for d in documents],
            metadatas=metadatas,
        )

    def get_collection(self, collection_name: str, embedding_generator_class: Type):
        return self.client.get_collection(
            name=collection_name, embedding_function=embedding_generator_class()
        )

    def list_collections(self) -> List[str]:
        return [collection.name for collection in self.client.list_collections()]

    def delete_collection(self):
        self.client.delete_collection(name=self.collection_name)

    def search(self, text: str, top_k: int):
        return self.collection.query(query_texts=[text], n_results=top_k)

    def document_exists(self, document_id: str) -> bool:
        try:
            result = self.collection.get(ids=[document_id])
            return len(result["ids"]) > 0
        except Exception:
            return False
