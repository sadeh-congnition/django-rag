import djclick as click
from chonkie import CodeChunker
from loguru import logger
from synthetic_data_generator.models import PythonFile
from chunking.models import Chunk, ChunkConfig
import tiktoken
from dataclasses import dataclass

enc = tiktoken.get_encoding("cl100k_base")

@click.command()
@click.option(
    '--chunk-size',
    default=2048,
    type=int,
    help='Maximum tokens per chunk (default: 2048)'
)
@click.option(
    '--language',
    default='python',
    type=str,
    help='Programming language for chunking (default: python)'
)
@click.option(
    '--clear-existing',
    is_flag=True,
    help='Clear existing chunks before processing'
)
def chunk_code(chunk_size, language, clear_existing=False):
    """Chunk all PythonFile content using CodeChunker from chonkie package."""
    
    # Create chunk configuration
    chunk_config = ChunkConfig.objects.create(
        content={
            'chunk_size': chunk_size,
            'language': language,
            'tokenizer': 'character',
            'chunking_method': 'chonkie.CodeChunker'
        }
    )
    logger.info(f"Created chunk configuration with ID: {chunk_config.id}")
    
    if clear_existing:
        count = Chunk.objects.count()
        Chunk.objects.all().delete()
        logger.info(f"Cleared {count} existing chunks")
    
    chunker = CodeChunker(
        language=language,
        tokenizer="character",
        chunk_size=chunk_size,
        include_nodes=False
    )
    
    python_files = PythonFile.objects.all()
    total_files = python_files.count()
    total_chunks_created = 0
    
    logger.info(f"Processing {total_files} Python files...")
    
    with click.progressbar(python_files, label='Chunking files') as files:
        for python_file in files:
            try:
                if Chunk.objects.filter(python_file=python_file).exists():
                    continue
                
                tokens = enc.encode(python_file.content)
                if len(tokens) > 2048:
                    @dataclass
                    class StubChunk:
                        text: str
                    chunks = [StubChunk(python_file.content)]
                else:
                    chunks = chunker.chunk(python_file.content)
                
                chunk_objects = []
                for chunk in chunks:
                    chunk_objects.append(
                        Chunk(
                            python_file=python_file,
                            config=chunk_config,
                            content=chunk.text
                        )
                    )
                
                if chunk_objects:
                    Chunk.objects.bulk_create(chunk_objects)
                    total_chunks_created += len(chunk_objects)
                
            except Exception as e:
                raise
                logger.error(f"Error processing {python_file.module_path}: {e}")
                continue
    
    logger.info(f"Completed! Created {total_chunks_created} chunks from {total_files} files.")