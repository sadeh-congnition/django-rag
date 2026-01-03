from loguru import logger
import djclick as click
import tiktoken

from synthetic_data_generator.models import PythonFile
from chunking.models import Chunk, ChunkDescription


@click.command()
def command():
    count_tokens()
    count_python_modules()
    count_code_chunks()
    count_chunk_descriptions()


def count_chunk_descriptions():
    count = ChunkDescription.objects.count()
    logger.info("TOTAL_CHUNK_DESCRIPTIONS:\t" + str(count))


def count_python_modules():
    count = PythonFile.objects.count()
    logger.info("TOTAL_PYTHON_MODULES:\t" + str(count))


def count_code_chunks():
    count = Chunk.objects.count()
    logger.info("TOTAL_CODE_CHUNKS:\t" + str(count))


def count_tokens():
    all_texts = []
    for pf in PythonFile.objects.all():
        if pf.content:
            all_texts.append(pf.content)

    combined = "\n\n".join(all_texts)

    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(combined)
    logger.info("TOTAL_TOKENS:\t" + str(len(tokens)))
    logger.info("TOTAL_CHARS:\t" + str(len(combined)))

