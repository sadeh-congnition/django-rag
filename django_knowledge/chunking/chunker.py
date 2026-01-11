from .models import Chunk, ChunkDescription


def get_chunks(chunk_config_id: int):
    return Chunk.objects.filter(config_id=chunk_config_id)


def get_chunk_descriptions():
    return ChunkDescription.objects.all()
