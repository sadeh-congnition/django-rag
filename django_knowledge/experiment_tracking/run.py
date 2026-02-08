import random
from time import time
from typing import Iterable

from chunking.chunker import get_chunks
from chunking.models import Chunk
from loguru import logger
from vectordb.db import ChromaDB

from .constants import COLLECTION_NAME
from .models import EmbeddingModel, EmbeddingModelKlass
from embedding_generator.persistence import save_embeddings
from metric_functions.retrieval import RetrievalAt1
from experiment_tracking.models import Sample
from chunking.models import ChunkDescription


def testcases(sample_id: int) -> list[ChunkDescription]:
    sample = Sample.objects.get(id=sample_id)
    res = list()
    for chunk_desc_id in sample.chunk_description_ids:
        chunk_desc = ChunkDescription.objects.get(id=chunk_desc_id)
        res.append(chunk_desc)
    return res


def run_experiment(
    embedding_model_id: int,
    metric_func: RetrievalAt1,
    chunk_config_id: int,
    num_tests: int,
    sample_id: int,
):
    chunk_descriptions_to_test = testcases(sample_id=sample_id)

    ef: EmbeddingModelKlass = EmbeddingModel.embedding_function(embedding_model_id)
    logger.info(f"Starting experiment with {ef.name}")
    assert metric_func.at
    assert metric_func.prefix

    logger.info("Getting chunks for processing")
    chunks = get_chunks(chunk_config_id=chunk_config_id)
    logger.info(f"Retrieved {len(chunks)} chunks")

    bad_results = {}

    collection_name = f"{COLLECTION_NAME}_{ef.name()}"
    db = ChromaDB(
        collection_name=collection_name,
        embedding_generator=ef,
        path="chromadb_data",
    )
    logger.info(f"Collection {collection_name} has {db.collection.count()} documents")

    bad_results = []
    logger.info("Adding documents to collection")
    embedding_time = save_embeddings(db, chunks)

    start_time = time()
    score = 0
    search_time_elapsed = 0

    for chunk_desc in chunk_descriptions_to_test:
        logger.info(f"Testing chunk {chunk_desc.chunk.id}")
        res = db.search(chunk_desc.description, top_k=metric_func.at)
        found_chunk_ids = res["ids"][0]
        found_chunks: Iterable[Chunk] = Chunk.objects.filter(
            id__in=found_chunk_ids
        ).all()
        if metric_func.evaluate(chunk_desc.chunk, found_chunks):
            score += 1
        else:
            bad_result_data = {
                "correct_chunk_id": chunk_desc.chunk.id,
                "returned_chunk_ids": found_chunk_ids,
                "search_query": chunk_desc.description,
                "correct_chunk_content": chunk_desc.chunk.content,
            }
            bad_results.append(bad_result_data)

        search_time_elapsed = time() - start_time

    logger.info(
        f"Search time: {search_time_elapsed} seconds, {search_time_elapsed / num_tests} per query"
    )
    logger.info(f"Final score: {score}/{num_tests} ({(score/num_tests)*100:.1f}% success rate)")

    return ef.name(), score, search_time_elapsed, embedding_time, bad_results
