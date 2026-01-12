from time import time
from loguru import logger
from vectordb.db import Doc


def save_embeddings(db, chunks):
    """Save chunks to the vector database if they don't already exist."""
    embedding_start_time = time()
    for chu in chunks:
        document_id = str(chu.id)
        if db.document_exists(
            document_id=document_id,
        ):
            logger.info(f"Document {document_id} already exists, skipping")
            continue
        else:
            db.add(
                documents=[Doc(text=chu.content, id=document_id)],
            )
            logger.info(f"Added document with ID: {document_id}")
    
    embedding_time = int(time() - embedding_start_time)
    logger.info(
        f"Successfully added {len(chunks)} documents with embedding function"
    )
    logger.info(f"Embedding time: {embedding_time} seconds")
    return embedding_time