import random
import json
from time import time

from chromadb.errors import NotFoundError
from chunking.chunker import get_chunk_descriptions, get_chunks
from chunking.models import Chunk
from loguru import logger
from vectordb.db import ChromaDB, Doc

from .models import EmbeddingModelKlass

db = ChromaDB()


def testcases(num: int) -> list:
    res = list()
    chunk_descriptions = get_chunk_descriptions()
    chunk_desc_indices = random.sample(range(len(chunk_descriptions)), k=num)
    for index in chunk_desc_indices:
        chunk_desc = chunk_descriptions[index]
        res.append(chunk_desc)

    return res


num_tests = 20
chunk_descriptions_to_test = testcases(num_tests)


def run_experiment(embedding_functions: list[EmbeddingModelKlass], num_rounds: int):
    logger.info(
        f"Starting experiment with {len(embedding_functions)} embedding functions"
    )
    collection_name = "embedding_model_eval"

    logger.info("Getting chunks for processing")
    chunks = get_chunks()
    logger.info(f"Retrieved {len(chunks)} chunks")

    bad_results = {}

    for i, ef in enumerate(embedding_functions):
        bad_results[ef.name()] = []
        scores = []
        num_tests_all = []
        search_times_all = []

        try:
            logger.info(f"Deleting collection '{collection_name}' if it exists")
            db.delete_collection(collection_name)
            logger.info("Collection deleted successfully")
        except NotFoundError:
            logger.info(f"Collection '{collection_name}' does not exist, continuing")
            pass

        logger.info(f"Adding documents to collection '{collection_name}'")
        embedding_start_time = time()
        db.add(
            collection_name=collection_name,
            embedding_generator=ef,
            documents=[Doc(text=c.content, id=str(c.id)) for c in chunks],
        )
        embedding_time = int(time() - embedding_start_time)
        logger.info(
            f"Successfully added {len(chunks)} documents with embedding function {ef.name()}"
        )
        logger.info(f"Embedding time: {embedding_time} seconds")

        for _ in range(num_rounds):
            logger.info(
                f"Processing embedding function {i+1}/{len(embedding_functions)}: {ef.name()}"
            )

            start_time = time()
            score = 0
            for chunk_desc in chunk_descriptions_to_test:
                res = db.search(chunk_desc.description, top_k=1)
                found_chunk_id = int(res["ids"][0][0])
                found_chunk = Chunk.objects.get(id=found_chunk_id)
                if found_chunk_id == int(chunk_desc.chunk.id):
                    score += 1
                else:
                    bad_results[ef.name()].append(
                        {
                            "correct_chunk_id": chunk_desc.chunk.id,
                            "returned_chunk_id": found_chunk_id,
                            "search_query": chunk_desc.description,
                            "correct_chunk_code": chunk_desc.chunk.content,
                            "wrong_chunk_code": found_chunk.content,
                        }
                    )

            search_time_elapsed = int(time() - start_time)

            logger.info(
                f"Search time: {search_time_elapsed} seconds, {search_time_elapsed / num_tests} per query"
            )

            scores.append(score)
            num_tests_all.append(num_tests)
            search_times_all.append(search_time_elapsed)

        yield ef.name(), num_tests_all, scores, search_times_all, embedding_time
        break

    logger.info("Experiment completed successfully")

    with open("bad_results.json", "w") as f:
        f.write(json.dumps(bad_results))
