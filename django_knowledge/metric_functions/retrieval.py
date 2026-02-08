from dataclasses import dataclass
from typing import Iterable

from chunking.models import Chunk


class MetricFunction:
    def __init__(self):
        self.prefix = None
        self.at = None

    def evaluate(self, correct_chunk: Chunk, retrieved_chunks: Iterable[Chunk]) -> int:
        raise NotImplementedError

    def name(self) -> str:
        raise NotImplementedError


class RetrivalBase(MetricFunction):
    def __init__(self):
        super().__init__()
        self.prefix = "EmbeddingsRetrieval"

    def evaluate(self, correct_chunk: Chunk, retrieved_chunks: Iterable[Chunk]) -> bool:
        assert self.at
        return correct_chunk.id in [chunk.id for chunk in retrieved_chunks[: self.at]]

    def name(self) -> str:
        return f"{self.prefix}@{self.at}"


class RetrievalAt1(RetrivalBase):
    def __init__(self):
        super().__init__()
        self.at = 1
