import random
from time import time
from rich import print
from chromadb.errors import NotFoundError
from loguru import logger

from chunking.chunker import get_chunks, get_chunk_descriptions
from vectordb.db import ChromaDB, Doc
from .models import EmbeddingModelKlass

db = ChromaDB()


def run_experiment(embedding_functions: list[EmbeddingModelKlass]):
    logger.info(
        f"Starting experiment with {len(embedding_functions)} embedding functions"
    )
    collection_name = "embedding_model_eval"

    logger.info("Getting chunks for processing")
    chunks = get_chunks()
    logger.info(f"Retrieved {len(chunks)} chunks")

    chunk_descriptions = get_chunk_descriptions()

    for i, ef in enumerate(embedding_functions):
        logger.info(
            f"Processing embedding function {i+1}/{len(embedding_functions)}: {ef.name()}"
        )
        try:
            logger.info(f"Deleting collection '{collection_name}' if it exists")
            db.delete_collection(collection_name)
            logger.info("Collection deleted successfully")
        except NotFoundError:
            logger.info(f"Collection '{collection_name}' does not exist, continuing")
            pass

        start_time = time()
        logger.info(f"Adding documents to collection '{collection_name}'")
        db.add(
            collection_name=collection_name,
            embedding_generator=ef,
            documents=[Doc(text=c.content, id=str(c.id)) for c in chunks],
        )
        logger.info(
            f"Successfully added {len(chunks)} documents with embedding function {ef.name()}"
        )

        num_tests = 50
        score = 0
        chunk_desc_indices = random.sample(range(len(chunk_descriptions)), k=num_tests)
        for index in chunk_desc_indices:
            chunk_desc = chunk_descriptions[index]
            logger.info(
                f"Searching for chunk description '{chunk_desc.description}' for chunk ID '{chunk_desc.chunk.id}'"
            )
            res = db.search(chunk_desc.description, top_k=1)
            if str(res["ids"][0][0]) == str(chunk_desc.chunk.id):
                score += 1

            print(res)

        eval_time_elapsed = int(time() - start_time)

        yield ef.name(), num_tests, score, eval_time_elapsed

    logger.info("Experiment completed successfully")
